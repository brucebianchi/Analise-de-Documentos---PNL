
import streamlit as st
import re
from typing import List
import PyPDF2
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud

st.set_page_config(page_title="Extrator Financeiro de PDFs (pt-BR)", page_icon="📄", layout="wide")
st.title("📄 Extrator Financeiro de PDFs (pt-BR)")
st.caption("Analise relatórios contábeis e financeiros em PDF — compatível com Streamlit Cloud (sem spaCy).")

BASIC_PT_STOPWORDS = {"a","à","ao","aos","ainda","além","algum","alguns","alguma","algumas","ambos","antes","após","até","com","como","contra","cada","cujo","cuja","cujos","cujas","de","da","das","do","dos","dela","dele","delas","deles","desde","depois","dentro","e","é","era","eram","essa","essas","esse","esses","esta","estas","este","estes","está","estão","eu","foi","foram","havia","há","isso","isto","já","lá","lhe","lhes","mais","mas","mesmo","muito","muitos","muita","muitas","na","nas","não","nem","nos","nós","o","os","ou","para","pela","pelas","pelo","pelos","per","por","qual","quais","quando","que","se","sem","seu","seus","sua","suas","sob","sobre","são","também","te","tem","têm","tinha","têm","tu","tua","tuas","um","uma","uns","umas","vai","vão","você","vocês"}

def extract_text_from_pdf(file) -> str:
    try:
        reader = PyPDF2.PdfReader(file)
        texts = []
        for page in reader.pages:
            try:
                txt = page.extract_text() or ""
            except Exception:
                txt = ""
            texts.append(txt)
        return " ".join(texts)
    except Exception as e:
        st.error(f"Erro ao ler o PDF: {e}")
        return ""

def clean_text(text: str) -> str:
    text = re.sub(r"\\s+", " ", text)
    text = re.sub(r"[^\\w\\s,\\.\\d]", "", text)
    return text.lower()

def tokenize_basic(text: str) -> List[str]:
    text_sep = re.sub(r"[,\\.]", " ", text)
    raw = re.split(r"[^\\w\\d]+", text_sep)
    tokens = [t for t in (w.strip() for w in raw) if t]
    tokens = [t for t in tokens if t not in BASIC_PT_STOPWORDS]
    return tokens

def find_keywords(tokens: List[str], keywords: List[str]):
    kw = set(k.lower().strip() for k in keywords if k.strip())
    return [i for i, tok in enumerate(tokens) if tok in kw]

def extract_values(tokens: List[str], indices: List[int], num_values: int = 3):
    for idx in indices:
        vals = []
        ok = True
        for i in range(1, num_values + 1):
            try:
                t = tokens[idx + i]
                norm = t.replace(".", "").replace(",", ".")
                vals.append(float(norm))
            except Exception:
                ok = False
                break
        if ok and vals:
            return vals
    return []

def plot_bar(labels, vals, title, ylabel):
    fig = plt.figure(figsize=(6, 4))
    bars = plt.bar(labels, vals)
    for bar in bars:
        h = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, h, f"{h:.2f}", ha="center", va="bottom")
    plt.title(title)
    plt.ylabel(ylabel)
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    st.pyplot(fig)

with st.sidebar:
    st.header("⚙️ Configurações")
    default_periodos = "3T24,2T24,3T23"
    periodos_str = st.text_input("Períodos (separados por vírgula)", value=default_periodos)
    periodos = [p.strip() for p in periodos_str.split(",") if p.strip()]

    st.subheader("🔎 Palavras-chave")
    kw_lucro = st.text_input("Lucro (lista separada por vírgula)", value="lucro, líquido")
    kw_capt = st.text_input("Captação (lista separada por vírgula)", value="captação, total")
    irrelevant = st.text_input("Tokens irrelevantes (remover)", value="p.p, r, milhão")
    num_vals = st.number_input("Qtd. de valores após a palavra-chave", min_value=1, max_value=6, value=3, step=1)
    st.subheader("☁️ Nuvem de palavras")
    min_freq = st.number_input("Frequência mínima para exibir", min_value=1, value=1, step=1)
    max_words = st.number_input("Máx. palavras na nuvem", min_value=10, value=200, step=10)

uploaded = st.file_uploader("📎 Envie um PDF com relatório contábil/financeiro", type=["pdf"])

if uploaded is not None:
    text = extract_text_from_pdf(uploaded)
    cleaned = clean_text(text)
    tokens = tokenize_basic(cleaned)

    st.subheader("🧾 Amostra do texto")
    st.code(cleaned[:800] + ("..." if len(cleaned) > 800 else ""), language="text")

    st.subheader("🧠 Amostra de tokens (50)")
    st.write(tokens[:50])

    irrelevant_tokens = [t.strip().lower() for t in irrelevant.split(",") if t.strip()]
    tokens_filtered = [t for t in tokens if t not in irrelevant_tokens]

    if tokens_filtered:
        word_freq = pd.Series(tokens_filtered).value_counts()
        word_freq = word_freq[word_freq >= int(min_freq)]
        if not word_freq.empty:
            wc = WordCloud(width=800, height=400, background_color="white", max_words=int(max_words)).generate_from_frequencies(word_freq.to_dict())
            fig = plt.figure(figsize=(10, 5))
            plt.imshow(wc, interpolation="bilinear")
            plt.axis("off")
            st.pyplot(fig)
            with st.expander("📊 Tabela de frequência de palavras"):
                st.dataframe(word_freq.rename("frequência").to_frame())
        else:
            st.info("Sem palavras com a frequência mínima para a nuvem.")

    keywords_lucro = [k.strip().lower() for k in kw_lucro.split(",") if k.strip()]
    keywords_captacao = [k.strip().lower() for k in kw_capt.split(",") if k.strip()]

    indices_lucro = find_keywords(tokens, keywords_lucro)
    indices_captacao = find_keywords(tokens, keywords_captacao)

    lucros_liquidos = extract_values(tokens, indices_lucro, num_values=int(num_vals))
    captacoes_totais = extract_values(tokens, indices_captacao, num_values=int(num_vals))

    st.subheader("📈 Resultados extraídos")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Lucros Líquidos**")
        st.write(lucros_liquidos if lucros_liquidos else "—")
    with col2:
        st.markdown("**Captações Totais**")
        st.write(captacoes_totais if captacoes_totais else "—")

    if lucros_liquidos:
        labels = periodos[:len(lucros_liquidos)] or [f"V{i+1}" for i in range(len(lucros_liquidos))]
        plot_bar(labels, lucros_liquidos, "Lucros Líquidos por Período", "Valores (em milhões)")
    if captacoes_totais:
        labels = periodos[:len(captacoes_totais)] or [f"V{i+1}" for i in range(len(captacoes_totais))]
        plot_bar(labels, captacoes_totais, "Captações Totais por Período", "Valores (em milhões)")
    if not lucros_liquidos and not captacoes_totais:
        st.warning("⚠️ Não foi possível extrair dados suficientes para exibir os gráficos.")
else:
    st.info("Envie um arquivo PDF para começar 👆")
