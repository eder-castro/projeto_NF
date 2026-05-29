# 🧾 Motor Automático de Processamento de Notas Fiscais (NFs)

Um sistema completo (End-to-End) desenvolvido em Python para automação de rotinas de backoffice e gestão administrativa. Este projeto resolve o gargalo da digitação manual de Notas Fiscais, unindo extração inteligente de dados (OCR/Texto), enriquecimento de informações em tempo real e uma fila de processamento segura para integração com planilhas financeiras de controle.

## 🏗️ Arquitetura do Sistema

O projeto foi desenhado com uma arquitetura de microserviços para garantir performance e evitar travamentos no uso do Excel:

1. **Front-end (Streamlit):** Interface amigável onde o usuário arrasta e solta o PDF da Nota Fiscal. Permite visualização prévia, cálculo automático de datas e exibição do histórico de notas.
2. **Back-end API (FastAPI):** O "cérebro" do sistema. Recebe o PDF, extrai os dados nativos ou via OCR, cruza os CNPJs com a base de dados interna (PROCV em memória via Pandas) para descobrir as Razões Sociais, e envia os dados para a fila.
3. **Fila de Processamento (SQLite):** Banco de dados local que atua como uma "sala de espera" (Status: Pendente / Exportado), garantindo que nenhuma nota seja perdida caso o sistema seja fechado.
4. **Worker de Exportação (xlwings + APScheduler):** Um robô em segundo plano que roda a cada 3 minutos. Ele consome a fila do banco de dados e escreve as notas de forma segura na `PLANILHA DE CONTROLE.xlsx`, sem quebrar fórmulas existentes e bloqueando duplicidades.

## ✨ Principais Funcionalidades

* **Extração Híbrida de PDFs:** Lê PDFs nativos selecionáveis ou utiliza Poppler/OCR para ler notas escaneadas.
* **Enriquecimento de Dados Automático:** O sistema ignora zeros à esquerda ou formatações incorretas e busca automaticamente as Razões Sociais do Tomador e do Fornecedor direto na planilha de controle.
* **Cálculo Inteligente de Vencimento:** A partir da Data de Emissão extraída, o sistema calcula o vencimento (+ 28 dias) e possui inteligência de calendário para empurrar datas que caem no final de semana para o próximo dia útil.
* **Prevenção de Concorrência e Bloqueio:** O uso de fila (SQLite) impede o erro de "Arquivo Bloqueado" no Excel, permitindo que a planilha seja atualizada nos bastidores sem congelar a tela do usuário.
* **Proteção de Fórmulas:** O motor de exportação mapeia colunas dinamicamente e respeita as células do Excel que possuem fórmulas nativas.

## 🛠️ Tecnologias Utilizadas

* **Linguagem:** Python 3.10+
* **Front-end:** Streamlit, Pandas
* **Back-end:** FastAPI, Uvicorn, APScheduler
* **Manipulação de Excel:** Pandas (Leitura ultra-rápida), xlwings (Gravação segura em background)
* **Extração de PDF:** pdfplumber / pdf2image (Dependência: Poppler)
* **Banco de Dados:** SQLite3

## ⚙️ Configuração e Instalação

### Pré-requisitos
* É necessário ter o **Poppler** instalado na máquina para o processamento de imagens/OCR de PDFs.
* Ter o Microsoft Excel instalado (para a biblioteca `xlwings` funcionar).

### Passos para rodar localmente

1. **Clone o repositório:**
```bash
git clone https://github.com/eder-castro/projeto_NF
cd projeto_NF
```

2. **Crie e ative um ambiente virtual:**
```bash
python -m venv .venv
# No Windows:
.venv\Scripts\activate
# No Mac/Linux:
source .venv/bin/activate
```

3. **Instale as dependências:**
```bash
pip install -r requirements.txt
```

4. **Inicie o Back-end (API):**
Abra um terminal, navegue até a pasta `backend` e rode:
```bash
uvicorn api:app --reload
```

5. **Inicie o Front-end:**
Abra um segundo terminal, ative o ambiente virtual novamente, navegue até a pasta `frontend` e rode:
```bash
streamlit run app.py
```

## 📂 Estrutura do Projeto

```text
📦 Motor_NFs
 ┣ 📂 backend
 ┃ ┣ 📜 api.py             # Rotas do FastAPI e inicialização do banco
 ┃ ┣ 📜 config.py          # Variáveis globais de ambiente (Caminhos, Nomes)
 ┃ ┣ 📜 export.py          # Motor de gravação no Excel via xlwings
 ┃ ┣ 📜 image_pdf.py       # Lógica de OCR para notas escaneadas
 ┃ ┗ 📜 text_pdf.py        # Lógica de extração de texto em PDFs nativos
 ┣ 📂 frontend
 ┃ ┗ 📜 app.py             # Interface do usuário em Streamlit
 ┣ 📜 .gitignore           # Proteção de dados e arquivos locais
 ┣ 📜 requirements.txt     # Dependências do projeto
 ┗ 📜 README.md
```
## 🔒 Segurança de Dados

Este repositório não expõe informações financeiras reais. O arquivo `PLANILHA DE CONTROLE.xlsx` presente na pasta `backend/` é apenas um template estrutural (vazio) com os cabeçalhos necessários para o funcionamento do motor de exportação. Nenhuma nota fiscal autêntica, valor corporativo ou dado sensível (PII) está armazenado no controle de versão deste projeto.