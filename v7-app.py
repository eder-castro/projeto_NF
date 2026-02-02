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
    # Altura ajustada
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf" style="border:none;"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

# --- CSS "ULTRA COMPACTO" ---
st.markdown("""
<style>
    /* Geral */
    header {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 100% !important;
    }

    /* Drag & Drop Mínimo */
    [data-testid="stFileUploader"] {
        padding: 0px !important;
        margin: 0px !important;
    }
    [data-testid="stFileUploader"] div div {
        padding: 0px !important;
        min-height: 0px !important;
        line-height: 1;
    }
    [data-testid="stFileUploader"] section {
        padding: 0.5rem !important;
        min-height: 0px !important;
        background-color: #f0f2f6; 
        border: 1px solid #ddd;
    }
    [data-testid="stFileUploader"] .st-emotion-cache-1fttcpj {
        display: none; 
    }
    button[kind="secondary"] {
        height: 25px !important;
        padding: 0px 10px !important;
        font-size: 0.8rem !important;
        line-height: 25px !important;
        border: none !important;
    }

    /* Títulos e Espaços */
    h3, h4, h5 { margin: 0px !important; padding: 0px !important; color: #444; }
    p, label, div { font-size: 0.85rem !important; }
    [data-testid="column"] { padding: 0.5rem !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# ESTADO
# ==========================================
usuario_atual = get_user_machine()

if 'dados_form' not in st.session_state:
    st.session_state['dados_form'] = {"nf": "", "forn": "", "val": 0.0, "data": datetime.today(), "status": "Recebido"}
if 'ultimo_arquivo' not in st.session_state:
    st.session_state['ultimo_arquivo'] = ""
if 'filtro_busca' not in st.session_state:
    st.session_state['filtro_busca'] = None 

# ==========================================
# 🔝 TOPO
# ==========================================
c1, c2, c3 = st.columns([0.2, 0.6, 0.2], gap="small", vertical_alignment="center")

with c1:
    st.markdown("##### 🏭 Notas Fiscais")

with c2:
    # CORREÇÃO 1: Adicionei um texto no label ("Upload PDF") em vez de vazio ""
    uploaded_file = st.file_uploader("Upload PDF", type="pdf", label_visibility="collapsed")

with c3:
    st.markdown(f"<div style='text-align:right;'>👤 <b>{usuario_atual}</b></div>", unsafe_allow_html=True)

# Extração Automática
if uploaded_file and uploaded_file.name != st.session_state['ultimo_arquivo']:
    st.session_state['dados_form'] = {
        "nf": "12345", 
        "forn": "Fornecedor Detectado Ltda",
        "val": 1550.00,
        "data": datetime.today(),
        "status": "Recebido"
    }
    st.session_state['ultimo_arquivo'] = uploaded_file.name
    st.toast("Dados extraídos!", icon="⚡")

# ==========================================
# 🏗️ ÁREA PRINCIPAL
# ==========================================
col_form, col_doc = st.columns([1, 2], gap="small")

# 🟦 ESQUERDA
with col_form:
    st.markdown("##### 📝 Dados / Filtros")
    
    with st.form("painel_controle", border=False):
        nf_input = st.text_input("Número NF", value=st.session_state['dados_form']['nf'])
        forn_input = st.text_input("Fornecedor / CNPJ", value=st.session_state['dados_form']['forn'])
        
        c_a, c_b = st.columns(2)
        val_input = c_a.number_input("Valor (R$)", value=st.session_state['dados_form']['val'], step=0.01)
        data_input = c_b.date_input("Emissão", value=st.session_state['dados_form']['data'])
        
        status_input = st.selectbox("Status", ["Recebido", "Pendente Pedido", "Finalizado"], index=0)
        
        st.write("") 
        
        btn_col1, btn_col2 = st.columns(2)
        
        # CORREÇÃO 2: Troquei use_container_width=True por width="stretch"
        busca_clicada = btn_col1.form_submit_button("🔍 Buscar", type="secondary", width="stretch")
        salvar_clicado = btn_col2.form_submit_button("💾 Salvar", type="primary", width="stretch")

        if salvar_clicado:
            if not nf_input:
                st.warning("NF obrigatória.")
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
                st.success(f"Salvo!")
                st.session_state['dados_form'] = {"nf": "", "forn": "", "val": 0.0, "data": datetime.today(), "status": "Recebido"}
                st.rerun()
        
        if busca_clicada:
            st.session_state['filtro_busca'] = {
                "nf": nf_input,
                "forn": forn_input
            }
            st.toast("Filtro aplicado!")

# 🟨 DIREITA
with col_doc:
    if uploaded_file:
        st.markdown(f"<div style='font-size:0.8rem; color:#888;'>📄 Visualizando: <b>{uploaded_file.name}</b></div>", unsafe_allow_html=True)
        show_pdf(uploaded_file.getvalue())
    else:
        st.markdown(
            """
            <div style='background-color:#f4f4f4; height:600px; display:flex; 
            flex-direction:column; align-items:center; justify-content:center; 
            border-radius:4px; border: 1px solid #ddd; color:#aaa;'>
                <div style="font-size: 2rem;">📄</div>
                <div>Visualizador de PDF</div>
            </div>
            """, unsafe_allow_html=True
        )

# ==========================================
# ⬇️ RODAPÉ
# ==========================================
st.divider()

df = db.carregar_dados()

filtros = st.session_state.get('filtro_busca')
if filtros:
    if filtros['nf']:
        df = df[df['numero_nf'].astype(str).str.contains(filtros['nf'], case=False)]
    if filtros['forn']:
        df = df[df['fornecedor'].str.contains(filtros['forn'], case=False)]
    
    st.markdown(f"##### 🔎 Resultados ({len(df)})")
else:
    st.markdown("##### 🕒 Recentes")
    df = df.head(10)

# CORREÇÃO 3: Troquei use_container_width=True por width="stretch"
df_editado = st.data_editor(
    df,
    key="tabela_full",
    width="stretch", 
    num_rows="fixed",
    disabled=["id", "data_registro", "responsavel"],
    column_config={
        "numero_nf": "NF",
        "fornecedor": "Fornecedor",
        "valor": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
        "data_emissao": st.column_config.DateColumn("Emissão", format="DD/MM/YYYY"),
        "status": st.column_config.SelectboxColumn("Status", options=["Recebido", "Pendente Pedido", "Finalizado"]),
    },
    hide_index=True,
    height=300
)

if not df.equals(df_editado):
    if st.button("Gravar Alterações da Tabela"):
        registros = df_editado.to_dict('records')
        for reg in registros:
            if isinstance(reg['data_registro'], pd.Timestamp):
                 reg['data_registro'] = reg['data_registro'].to_pydatetime()
            reg['responsavel'] = usuario_atual 
            db.salvar_nota(reg)
        st.success("Tabela atualizada!")
        st.rerun()