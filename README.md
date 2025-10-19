
# 📄 Extrator Financeiro de PDFs (pt-BR) — Streamlit

Converte seu código do Colab em um app web no Streamlit para analisar relatórios contábeis/financeiros em PDF:
- Extração de texto (PyPDF2)
- Limpeza, tokenização e lematização (spaCy `pt_core_news_sm`)
- Nuvem de palavras e frequência de tokens
- Extração de valores numéricos próximos a palavras‑chave (ex.: "lucro", "captação")
- Gráficos de barras com Matplotlib

## 🚀 Como rodar localmente

```bash
# 1) Crie e ative um ambiente virtual (opcional mas recomendado)
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 2) Instale as dependências
pip install -r requirements.txt

# 3) Execute o app
streamlit run app.py
```

## ☁️ Deploy no Streamlit Community Cloud

1. Suba este repositório no GitHub.
2. Acesse **share.streamlit.io** e conecte sua conta do GitHub.
3. Selecione o repositório, branch e o arquivo principal `app.py`.
4. Confirme o deploy.
5. Se preciso, reinicie o app após a primeira instalação (o modelo spaCy será instalado a partir da URL no `requirements.txt`).

> **Dica:** Caso o deploy leve muito tempo ao baixar o modelo spaCy durante a instalação, mantenha a versão do `requirements.txt` atualizada e verifique os logs do Streamlit Cloud.

## 📁 Estrutura do projeto

```text
.
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
└── .streamlit/
    └── config.toml
```

## 🔧 Personalizações rápidas
- Ajuste as listas de palavras‑chave e períodos na **sidebar** do app.
- Altere a regra de limpeza do texto na função `clean_text` conforme seu relatório.
- Aumente `num_values` para ler mais números após cada palavra‑chave.

## 🔒 Observações
- PDFs digitalizados (imagem) não são suportados por este app (seria necessário OCR como Tesseract).
- O app assume números no padrão brasileiro (ponto como separador de milhar e vírgula como decimal), mas normaliza automaticamente para ponto decimal.
