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
    # Altura fixa para alinhar com o form
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf" style="border:none;"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

# --- CSS VISUAL ---
st.markdown("""
<style>
    /* Remove cabeçalho e ajusta margens */
    header {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}
    
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
        max-width: 100% !important;
    }

    /* CSS DO UPLOAD (Restaurado para o modelo funcional anterior) */
    [data-testid="stFileUploader"] {
        margin-top: -20px; /* Sobe um pouco para alinhar com o título */
    }
    /* Tenta esconder o texto 'Drag and drop file here' para economizar espaço vertical */
    [data-testid="stFileUploader"] section > div > div > span {
        display: none;
    }
    
    /* Botões compactos */
    button[kind="secondary"] {
        height: 30px !important;
        line-height: 1 !important;
    }
    
    /* Títulos e Espaços */
    h3, h4, h5 { margin: 0px !important; padding: 0px !important; color: #333; }
    p, label, div { font-size: 0.9rem !important; }
    
    /* Remove padding das colunas */
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
# 🔝 TOPO: TÍTULO | UPLOAD | USUÁRIO
# ==========================================
# Ajuste de proporção para dar espaço aos ícones
c1, c2, c3 = st.columns([0.20, 0.60, 0.20], gap="medium", vertical_alignment="bottom")

with c1:
    # Título com ícone Material
    st.markdown("##### :material/factory: Entrada de Notas")

with c2:
    # Uploader limpo
    uploaded_file = st.file_uploader("Upload", type="pdf", label_visibility="collapsed")

with c3:
    # Usuário alinhado (sem HTML para o ícone funcionar)
    st.markdown(f":material/person: **{usuario_atual}**")

# Lógica de Extração
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

st.divider()

# ==========================================
# 🏗️ ÁREA PRINCIPAL
# ==========================================
# 1/3 para Form, 2/3 para PDF (Prioridade Visualização)
col_form, col_doc = st.columns([1, 2], gap="small")

# 🟦 ESQUERDA: FORMULÁRIO
with col_form:
    st.markdown("##### :material/edit_document: Dados da Nota")
    
    with st.form("painel_controle", border=False):
        nf_input = st.text_input("Número NF", value=st.session_state['dados_form']['nf'])
        forn_input = st.text_input("Fornecedor / CNPJ", value=st.session_state['dados_form']['forn'])
        
        c_a, c_b = st.columns(2)
        val_input = c_a.number_input("Valor (R$)", value=st.session_state['dados_form']['val'], step=0.01)
        data_input = c_b.date_input("Emissão", value=st.session_state['dados_form']['data'])
        
        status_input = st.selectbox("Status", ["Recebido", "Pendente Pedido", "Finalizado"], index=0)
        
        st.write("") 
        
        btn_col1, btn_col2 = st.columns(2)
        
        # Botões com ícones Material
        busca_clicada = btn_col1.form_submit_button("Buscar", type="secondary", width="stretch", icon=":material/search:")
        salvar_clicado = btn_col2.form_submit_button("Salvar", type="primary", width="stretch", icon=":material/save:")

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

# 🟨 DIREITA: PDF
with col_doc:
    if uploaded_file:
        st.markdown(f"<div style='font-size:0.8rem; color:#666; margin-bottom:5px'>:material/description: <b>{uploaded_file.name}</b></div>", unsafe_allow_html=True)
        show_pdf(uploaded_file.getvalue())
    else:
        st.markdown(
            """
            <div style='background-color:#f8f9fa; height:600px; display:flex; 
            flex-direction:column; align-items:center; justify-content:center; 
            border-radius:4px; border: 1px dashed #ccc; color:#aaa;'>
                <div style="font-size: 2.5rem;">:material/upload_file:</div>
                <div style="margin-top: 10px;">Visualizador de PDF</div>
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
    
    st.markdown(f"##### :material/search: Resultados ({len(df)})")
else:
    st.markdown("##### :material/history: Recentes")
    df = df.head(10)

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
    if st.button("Gravar Alterações da Tabela", icon=":material/save_as:"):
        registros = df_editado.to_dict('records')
        for reg in registros:
            if isinstance(reg['data_registro'], pd.Timestamp):
                 reg['data_registro'] = reg['data_registro'].to_pydatetime()
            reg['responsavel'] = usuario_atual 
            db.salvar_nota(reg)
        st.success("Tabela atualizada!")
        st.rerun()