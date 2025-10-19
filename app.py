
import streamlit as st
import re
import pandas as pd
import PyPDF2
import matplotlib.pyplot as plt

st.set_page_config(page_title="Extrator Financeiro de PDFs (pt-BR)", page_icon="📄", layout="wide")
st.title("📄 Extrator Financeiro de PDFs (pt-BR)")
st.caption("Versão simples e compatível com Streamlit Cloud (sem spaCy, sem Colab).")

# -----------------------------
# 🧾 Extração de texto do PDF
# -----------------------------
def extract_text_from_pdf(file):
    try:
        reader = PyPDF2.PdfReader(file)
        return " ".join([page.extract_text() or "" for page in reader.pages])
    except Exception as e:
        st.error(f"Erro ao ler o PDF: {e}")
        return ""

# ✅ Extrai 3 valores após o rótulo (padrão brasileiro 1.234,56)
def extract_multiple_numbers(text, label):
    pattern = rf"{label}\s+(\d{{1,3}}(?:\.\d{{3}})*,\d{{1,2}})\s+(\d{{1,3}}(?:\.\d{{3}})*,\d{{1,2}})\s+(\d{{1,3}}(?:\.\d{{3}})*,\d{{1,2}})"
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if match:
        return [float(v.replace(".", "").replace(",", ".")) for v in match.groups()]
    return []

# 🎯 Tenta múltiplos rótulos sinônimos
def try_extract_any(text, label_options):
    for label in label_options:
        result = extract_multiple_numbers(text, label)
        if result:
            return result, label
    return [], None

# 🗓️ Extrai períodos (ex.: 3T24)
def extract_periods(text):
    period_pattern = r"\b\d{1,2}T\d{2}\b"
    periods = re.findall(period_pattern, text)
    # Remove duplicatas mantendo ordem
    seen = set()
    ordered = []
    for p in periods:
        if p not in seen:
            seen.add(p)
            ordered.append(p)
    return ordered

# -----------------------------
# 🔧 Configurações (sidebar)
# -----------------------------
with st.sidebar:
    st.header("⚙️ Configurações")
    st.write("Ajuste os sinônimos dos rótulos se seu PDF usa nomenclaturas diferentes.")

    default_labels = {
        "Lucro Líquido": "Lucro Líquido, Lucro Líquido Recorrente, Lucro Líquido Contábil",
        "Captação Total": "Captação Total, Captações Totais",
        "Total de Ativos": "Total de Ativos, Ativos Totais"
    }

    lucro_opts = st.text_input("Sinônimos - Lucro Líquido", value=default_labels["Lucro Líquido"])
    capt_opts  = st.text_input("Sinônimos - Captação Total", value=default_labels["Captação Total"])
    ativo_opts = st.text_input("Sinônimos - Total de Ativos", value=default_labels["Total de Ativos"])

    min_bars = st.number_input("Mínimo de períodos para mostrar gráficos", min_value=1, max_value=6, value=2)

labels = {
    "Lucro Líquido": [s.strip() for s in lucro_opts.split(",") if s.strip()],
    "Captação Total": [s.strip() for s in capt_opts.split(",") if s.strip()],
    "Total de Ativos": [s.strip() for s in ativo_opts.split(",") if s.strip()],
}

# -----------------------------
# 📎 Upload
# -----------------------------
uploaded = st.file_uploader("📎 Envie um PDF com os dados financeiros", type=["pdf"])

if uploaded is not None:
    # Etapa 1: Extração do texto
    raw_text = extract_text_from_pdf(uploaded)

    # Etapa 2: Limpeza de quebras de linha e espaços
    text = re.sub(r"\n+", " ", raw_text)
    text = re.sub(r"\s{2,}", " ", text)

    # Etapa 3: Períodos
    periods = extract_periods(text)
    st.subheader("📅 Períodos identificados")
    st.write(periods if periods else "—")

    # Etapa 4: Extração
    lucros_liquidos, lbl_lucro = try_extract_any(text, labels["Lucro Líquido"])
    captacoes_totais, lbl_capt = try_extract_any(text, labels["Captação Total"])
    ativos_totais, lbl_ativo   = try_extract_any(text, labels["Total de Ativos"])

    st.subheader("📈 Valores extraídos")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**Lucros Líquidos**")
        st.write(lucros_liquidos if lucros_liquidos else "—")
        if lbl_lucro: st.caption(f"Rótulo encontrado: *{lbl_lucro}*")
    with col2:
        st.markdown("**Captações Totais**")
        st.write(captacoes_totais if captacoes_totais else "—")
        if lbl_capt: st.caption(f"Rótulo encontrado: *{lbl_capt}*")
    with col3:
        st.markdown("**Ativos Totais**")
        st.write(ativos_totais if ativos_totais else "—")
        if lbl_ativo: st.caption(f"Rótulo encontrado: *{lbl_ativo}*")

    # Etapa 5: Gráficos
    min_len = min(len(lucros_liquidos), len(captacoes_totais), len(ativos_totais), len(periods))

    if min_len >= int(min_bars):
        df = pd.DataFrame({
            "Períodos": periods[:min_len],
            "Lucros Líquidos": lucros_liquidos[:min_len],
            "Captações Totais": captacoes_totais[:min_len],
            "Ativos Totais": ativos_totais[:min_len],
        })

        st.subheader("📊 Gráficos")
        indicadores = ["Lucros Líquidos", "Captações Totais", "Ativos Totais"]

        for indicador in indicadores:
            fig = plt.figure(figsize=(8, 6))
            bars = plt.bar(df["Períodos"], df[indicador], alpha=0.7)
            for bar in bars:
                h = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2, h, f"{h:.2f}", ha="center", va="bottom")
            plt.title(indicador)
            plt.xlabel("Períodos")
            plt.ylabel("Valores (em milhões)")
            plt.grid(axis="y", linestyle="--", alpha=0.7)
            st.pyplot(fig)

    else:
        st.warning("⚠️ Dados insuficientes para exibir os gráficos (mínimo configurado na sidebar).")

    with st.expander("🔍 Trecho do texto bruto"):
        st.code(text[:1200] + ("..." if len(text) > 1200 else ""), language="text")

    st.info("💡 Dica: garanta que o PDF contenha expressões como 'Lucro Líquido', 'Captação Total' e 'Total de Ativos'.")

else:
    st.info("Envie um arquivo PDF para começar 👆")
