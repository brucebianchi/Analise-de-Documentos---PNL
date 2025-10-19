
import streamlit as st
import PyPDF2
import spacy
from spacy.util import get_package_path
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import re

# -----------------------------
# ⚙️ Configurações iniciais
# -----------------------------
st.set_page_config(page_title="Extrator Financeiro de PDFs (pt-BR)", page_icon="📄", layout="wide")
st.title("📄 Extrator Financeiro de PDFs (pt-BR)")
st.caption("Converta relatórios contábeis/financeiros em insights rapidamente.")

# -----------------------------
# 🧠 Carregar modelo spaCy pt_core_news_sm
# -----------------------------
@st.cache_resource(show_spinner=False)
def load_spacy_pt():
    try:
        # Tenta carregar o pacote nominalmente (recomendado se o modelo está em requirements.txt)
        return spacy.load("pt_core_news_sm")
    except Exception:
        # Último recurso: baixa em tempo de execução (pode deixar o deploy mais lento)
        from spacy.cli import download
        try:
            download("pt_core_news_sm")
            return spacy.load("pt_core_news_sm")
        except Exception as e:
            st.error(f"Falha ao carregar/baixar o modelo spaCy: {e}")
            raise

nlp = load_spacy_pt()

# -----------------------------
# 🔧 Funções utilitárias
# -----------------------------
def extract_text_from_pdf(file):
    """Extrai texto de um PDF enviado (arquivo em memória)."""
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
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s,\.\d]', '', text)
    return text.lower()

def preprocess_text(text: str):
    doc = nlp(text)
    tokens = [t.lemma_ for t in doc if not t.is_punct and not t.is_stop]
    return tokens

def find_keywords(tokens, keywords):
    kws = set([k.lower() for k in keywords])
    return [i for i, tok in enumerate(tokens) if tok in kws]

def extract_values(tokens, indices, num_values=3):
    results = []
    for idx in indices:
        try:
            # tenta ler os próximos N tokens como números
            vals = []
            for i in range(1, num_values + 1):
                t = tokens[idx + i]
                # normaliza formato (1.234,56 -> 1234.56)
                tnorm = t.replace('.', '').replace(',', '.')
                vals.append(float(tnorm))
            results.append(vals)
        except (ValueError, IndexError):
            continue
    return results[0] if results else []

# -----------------------------
# 🎛️ Sidebar
# -----------------------------
with st.sidebar:
    st.header("⚙️ Configurações")
    default_periodos = "3T24,2T24,3T23"
    periodos_str = st.text_input("Períodos (separados por vírgula)", value=default_periodos, help="Ex.: 3T24,2T24,3T23")
    periodos = [p.strip() for p in periodos_str.split(",") if p.strip()]

    st.subheader("🔎 Palavras-chave")
    kw_lucro = st.text_input("Lucro (lista separada por vírgula)", value="lucro, líquido")
    kw_capt = st.text_input("Captação (lista separada por vírgula)", value="captação, total")

    irrelevant = st.text_input("Tokens irrelevantes (remover)", value="p.p, r, milhão")

    num_vals = st.number_input("Qtd. de valores após a palavra-chave", min_value=1, max_value=6, value=3, step=1)

    st.subheader("☁️ Nuvem de palavras")
    min_freq = st.number_input("Frequência mínima para exibir", min_value=1, value=1, step=1)
    max_words = st.number_input("Máx. palavras na nuvem", min_value=10, value=200, step=10)

# -----------------------------
# 📎 Upload & processamento
# -----------------------------
uploaded = st.file_uploader("📎 Envie um PDF com relatório contábil/financeiro", type=["pdf"])

if uploaded is not None:
    # 1) Texto bruto
    text = extract_text_from_pdf(uploaded)
    cleaned = clean_text(text)
    tokens = preprocess_text(cleaned)

    st.subheader("🧾 Amostra do texto")
    st.code(cleaned[:800] + ("..." if len(cleaned) > 800 else ""), language="text")

    st.subheader("🧠 Amostra de tokens (50)")
    st.write(tokens[:50])

    # 2) Remoções ajustáveis
    irrelevant_tokens = [t.strip().lower() for t in irrelevant.split(",") if t.strip()]
    tokens_filtered = [t for t in tokens if t not in irrelevant_tokens]

    # 3) Frequência & nuvem de palavras
    if tokens_filtered:
        word_freq = pd.Series(tokens_filtered).value_counts()
        # aplica filtros
        word_freq = word_freq[word_freq >= int(min_freq)]
        if not word_freq.empty:
            wc = WordCloud(width=800, height=400, background_color="white", max_words=int(max_words)).generate_from_frequencies(word_freq.to_dict())

            st.subheader("☁️ Nuvem de Palavras")
            fig = plt.figure(figsize=(10, 5))
            plt.imshow(wc, interpolation="bilinear")
            plt.axis("off")
            st.pyplot(fig)

            with st.expander("📊 Tabela de frequência de palavras"):
                st.dataframe(word_freq.rename("frequência").to_frame())

    # 4) Extrações orientadas a palavra-chave
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

    # 5) Gráficos
    def plot_bar(vals, title, ylabel):
        if vals:
            labels = periodos[:len(vals)]
            fig = plt.figure(figsize=(6, 4))
            bars = plt.bar(labels, vals)
            # anotações
            for bar in bars:
                h = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2, h, f"{h:.2f}", ha="center", va="bottom")
            plt.title(title)
            plt.ylabel(ylabel)
            plt.grid(axis="y", linestyle="--", alpha=0.7)
            st.pyplot(fig)

    plot_bar(lucros_liquidos, "Lucros Líquidos por Período", "Valores (em milhões)")
    plot_bar(captacoes_totais, "Captações Totais por Período", "Valores (em milhões)")

    if not lucros_liquidos and not captacoes_totais:
        st.warning("⚠️ Não foi possível extrair dados suficientes para exibir os gráficos.")

else:
    st.info("Envie um arquivo PDF para começar 👆")
