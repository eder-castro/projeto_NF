import streamlit as st
import pandas as pd
import database as db
from datetime import datetime
import base64
import socket

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(layout="wide", page_title="Notas Fiscais", initial_sidebar_state="collapsed")
db.init_db()

# --- FUNÇÕES AUXILIARES ---
def get_user_machine():
    try:
        return socket.gethostname()
    except:
        return "Desconhecido"

def show_pdf(file_bytes):
    base64_pdf = base64.b64encode(file_bytes).decode('utf-8')
    # PDF ocupando altura total disponível
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="900" type="application/pdf" style="border:none;"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

# --- CSS MINIMALISTA (OTIMIZAÇÃO DE ESPAÇO) ---
st.markdown("""
<style>
    /* 1. Remove cabeçalho padrão e ajusta margens gerais da página */
    header {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}
    
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
        padding-left: 2rem !important;  /* Margem lateral reduzida */
        padding-right: 2rem !important;
        max-width: 100% !important;
    }
    
    /* 2. Compacta o Drag & Drop */
    [data-testid="stFileUploader"] {
        padding: 0px !important;
        margin: 0px !important;
    }
    [data-testid="stFileUploader"] div div {
        padding: 4px 10px !important; /* Deixa o botão mais fino */
        min-height: 0px !important;
    }
    [data-testid="stFileUploader"] section {
        padding: 10px !important; /* Altura da área de drop */
        min-height: 0px !important;
    }
    [data-testid="stFileUploader"] section + div {
        display: none; /* Esconde lista de arquivos padrão */
    }
    /* Deixa o botão 'Browse' minúsculo e discreto */
    button[kind="secondary"] {
        height: 28px !important;
        font-size: 0.8rem !important;
        border: 1px solid #e0e0e0 !important;
    }
    
    /* 3. Títulos e Textos mais compactos */
    h1, h2, h3, h4, h5 {
        margin-bottom: 0.5rem !important;
        padding-bottom: 0px !important;
        font-weight: 600 !important;
        color: #2c3e50;
    }
    p, div, label {
        font-size: 0.9rem !important; /* Fonte geral levemente menor */
    }
    
    /* 4. Remove espaços brancos extras entre colunas */
    [data-testid="column"] {
        padding: 0px !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 🧠 LÓGICA & ESTADO
# ==========================================
usuario_atual = get_user_machine()

if 'dados_form' not in st.session_state:
    st.session_state['dados_form'] = {"nf": "", "forn": "", "val": 0.0, "data": datetime.today()}
if 'ultimo_arquivo' not in st.session_state:
    st.session_state['ultimo_arquivo'] = ""

# ==========================================
# 🔝 BARRA DE FERRAMENTAS SUPERIOR (Compacta)
# ==========================================
# Layout: Título | Upload | Usuário
# Ajuste de gap="small" para aproximar colunas
c1, c2, c3 = st.columns([0.25, 0.60, 0.15], gap="small", vertical_alignment="center")

with c1:
    # Ícone estilo Lucide usando Material Symbols
    st.markdown("##### :material/factory: Entrada de Notas")

with c2:
    uploaded_file = st.file_uploader("", type="pdf", label_visibility="collapsed")

with c3:
    st.markdown(f"<div style='text-align:right; color:#666; font-size:0.85rem'>:material/person: <b>{usuario_atual}</b></div>", unsafe_allow_html=True)

# Sem divider aqui para economizar espaço vertical

# ==========================================
# ⚡ LÓGICA AUTOMÁTICA
# ==========================================
if uploaded_file and uploaded_file.name != st.session_state['ultimo_arquivo']:
    st.session_state['dados_form'] = {
        "nf": "NF-" + str(datetime.now().microsecond)[:4], 
        "forn": "Tech Solutions S.A." if "tech" in uploaded_file.name.lower() else "Fornecedor Diverso",
        "val": 1250.00,
        "data": datetime.today()
    }
    st.session_state['ultimo_arquivo'] = uploaded_file.name
    st.toast("Dados detectados!", icon=":material/bolt:")

# ==========================================
# 🏗️ ÁREA PRINCIPAL (Formulário Esquerda | PDF Direita)
# ==========================================
# gap="small" para diminuir o espaço entre formulário e PDF
col_form, col_doc = st.columns([1, 1.2], gap="small")

# ------------------------------------------
# 🟦 ESQUERDA: FORMULÁRIO (Sem Borda)
# ------------------------------------------
with col_form:
    st.markdown("##### :material/edit_document: Conferência")
    
    # Formulário direto, sem st.container(border=True)
    with st.form("form_entrada", border=False): 
        # Inputs compactos
        nf_input = st.text_input("Número NF", value=st.session_state['dados_form']['nf'])
        forn_input = st.text_input("Fornecedor", value=st.session_state['dados_form']['forn'])
        
        c_a, c_b = st.columns(2)
        val_input = c_a.number_input("Valor (R$)", value=st.session_state['dados_form']['val'], step=0.01)
        data_input = c_b.date_input("Emissão", value=st.session_state['dados_form']['data'])
        
        status_input = st.selectbox("Status", ["Recebido", "Pendente Pedido", "Finalizado"])
        
        st.write("") # Espaçamento mínimo
        
        # Botão Salvar
        # use_container_width=True faz ocupar a largura toda
        if st.form_submit_button("Salvar Lançamento", type="primary", use_container_width=True, icon=":material/save:"):
            if not nf_input:
                st.warning("Informe o número da NF.")
            else:
                dados = {
                    "id": None,
                    "numero_nf": nf_input, "fornecedor": forn_input, 
                    "valor": val_input, "data_emissao": data_input.strftime("%Y-%m-%d"),
                    "numero_pedido": None, "data_envio": None,
                    "status": status_input, "responsavel": usuario_atual,
                    "data_registro": datetime.now()
                }
                db.salvar_nota(dados)
                st.toast(f"Nota {nf_input} salva!", icon=":material/check_circle:")
                st.session_state['dados_form'] = {"nf": "", "forn": "", "val": 0.0, "data": datetime.today()}
                st.rerun()

    # Tabela logo abaixo do form para aproveitar o espaço vertical da esquerda
    st.markdown("##### :material/history: Recentes")
    df = db.carregar_dados()
    st.dataframe(
        df[['numero_nf', 'fornecedor', 'valor', 'status']], 
        hide_index=True, 
        use_container_width=True,
        height=300 # Altura fixa para não empurrar muito
    )

# ------------------------------------------
# 🟨 DIREITA: PDF (Full Height)
# ------------------------------------------
with col_doc:
    if uploaded_file:
        # Título discreto em cima do PDF
        st.markdown(f"<div style='font-size:0.9rem; color:#555; margin-bottom:5px'>:material/description: Visualizando: <b>{uploaded_file.name}</b></div>", unsafe_allow_html=True)
        show_pdf(uploaded_file.getvalue())
    else:
        # Placeholder minimalista
        st.markdown(
            """
            <div style='background-color:#f9f9f9; height:850px; display:flex; 
            flex-direction:column; align-items:center; justify-content:center; 
            border-radius:4px; border: 1px solid #eee; color:#bbb;'>
                <div style="font-size: 2rem; margin-bottom: 10px;">:material/upload_file:</div>
                <div style="font-size: 0.9rem;">Arraste o PDF na barra superior</div>
            </div>
            """, unsafe_allow_html=True
        )