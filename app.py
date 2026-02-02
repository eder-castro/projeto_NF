import streamlit as st
import pandas as pd
import database as db
from datetime import datetime, date
import base64
import socket
import time
import uuid # Importante para gerar IDs únicos

# --- CONFIGURAÇÃO ---
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
    # ALTURA 650px
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}#view=FitH" width="100%" height="650" type="application/pdf" style="border:none;"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

def show_custom_message(texto, tipo='info'):
    cor_fundo = "#D97706" if tipo == 'warning' else "#059669" 
    cor_texto = "#FFFFFF"
    icone = "⚠️" if tipo == 'warning' else "💾"
    
    st.markdown(f"""
    <style>
        @keyframes fadeOut {{
            0% {{ opacity: 1; }}
            80% {{ opacity: 1; }}
            100% {{ opacity: 0; visibility: hidden; }}
        }}
    </style>
    <div style="
        position: fixed;
        top: 10%;
        left: 50%;
        transform: translate(-50%, -50%);
        z-index: 9999;
        background-color: {cor_fundo};
        color: {cor_texto};
        padding: 12px 24px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        font-weight: 500;
        font-size: 15px;
        text-align: center;
        border: 1px solid rgba(255,255,255,0.1);
        animation: fadeOut 3.5s forwards;
    ">
        {icone} {texto}
    </div>
    """, unsafe_allow_html=True)

# --- CSS VISUAL ---
st.markdown("""
<style>
    header {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}
    .block-container { padding: 1rem 1.5rem !important; max-width: 100% !important; }
    [data-testid="stFileUploader"] { padding: 0px !important; margin: 0px !important; }
    [data-testid="stFileUploader"] label { display: none; }
    [data-testid="stFileUploader"] ul { display: none; }
    [data-testid="stFileUploader"] .st-emotion-cache-1fttcpj { display: none; }
    
    button[kind="secondary"] { height: 32px !important; border: 1px solid #ccc !important; font-size: 0.8rem !important; }
    [data-testid="stForm"] button { height: 35px !important; min-height: 0px !important; padding: 0px 10px !important; white-space: nowrap !important; }
    [data-testid="stForm"] button[kind="secondary"] { border: 1px solid #ccc !important; color: #333 !important; font-size: 0.85rem !important; }
    [data-testid="stForm"] button[kind="primary"] { font-size: 0.85rem !important; }
    [data-testid="column"] { padding: 0.5rem !important; }
</style>
""", unsafe_allow_html=True)

# --- ESTADO INICIAL ---
usuario_atual = get_user_machine()
DATA_PADRAO = None

campos_texto = [
    "emp_tomador", "cnpj_tomador", "cnpj_fornecedor", "razao_fornecedor",
    "num_nota", "num_requisicao", "id_contrato", "num_pedido", "observacao", "id"
]
campos_valor = ["valor_nf"]
campos_data = ["data_emissao", "data_vencimento", "envio_pgto"]

# Inicializa State
for campo in campos_texto:
    if campo not in st.session_state: st.session_state[campo] = ""
for campo in campos_valor:
    if campo not in st.session_state: st.session_state[campo] = 0.0
for campo in campos_data:
    if campo not in st.session_state: st.session_state[campo] = DATA_PADRAO

if 'ultimo_arquivo' not in st.session_state: st.session_state['ultimo_arquivo'] = ""
if 'msg_topo' not in st.session_state: st.session_state['msg_topo'] = None 

# --- CARREGAMENTO DE DADOS (TOPO) ---
df = db.carregar_dados()

# Filtros
df_show = df.copy()
filtro_ativo = False

for campo in campos_texto:
    if campo == "id": continue
    valor = st.session_state.get(campo, "")
    if valor:
        filtro_ativo = True
        df_show = df_show[df_show[campo].astype(str).str.contains(valor, case=False, na=False)]

valor_nf = st.session_state.get('valor_nf', 0.0)
if valor_nf > 0:
    filtro_ativo = True
    df_show = df_show[abs(df_show['valor_nf'] - valor_nf) < 0.01]

for campo in campos_data:
    valor = st.session_state.get(campo)
    if valor:
        filtro_ativo = True
        df_show = df_show[df_show[campo].dt.date == valor]

if not filtro_ativo:
    df_show = df_show.head(10)

# Lógica de Seleção
def carregar_dados_para_edicao(linha_selecionada):
    for c in campos_texto:
        if c in linha_selecionada:
            st.session_state[c] = linha_selecionada[c] if linha_selecionada[c] else ""
    for c in campos_valor:
        if c in linha_selecionada:
            st.session_state[c] = float(linha_selecionada[c]) if linha_selecionada[c] else 0.0
    for c in campos_data:
        val = linha_selecionada.get(c)
        if pd.isna(val) or val == "" or val is None:
            st.session_state[c] = None
        else:
            if isinstance(val, pd.Timestamp): st.session_state[c] = val.date()
            elif isinstance(val, date): st.session_state[c] = val

if "tabela_full" in st.session_state:
    selection = st.session_state.tabela_full.get("selection", {})
    rows = selection.get("rows", [])
    if rows:
        idx_visual = rows[0]
        if idx_visual < len(df_show):
            linha = df_show.iloc[idx_visual].to_dict()
            # Só carrega se for um ID diferente do atual para não travar
            if linha.get('id') != st.session_state.get('id'):
                carregar_dados_para_edicao(linha)
                st.session_state['msg_topo'] = ("Dados carregados para edição!", "warning")

# --- CALLBACKS BOTÕES ---
def reset_form_callback():
    for c in campos_texto: st.session_state[c] = ""
    for c in campos_valor: st.session_state[c] = 0.0
    for c in campos_data: st.session_state[c] = DATA_PADRAO
    st.session_state['msg_topo'] = None
    if "tabela_full" in st.session_state: del st.session_state["tabela_full"]

def salvar_callback():
    if not st.session_state['num_nota']:
        st.session_state['msg_topo'] = ("Número da Nota é obrigatório.", "warning")
        return
    if not st.session_state['data_emissao']:
        st.session_state['msg_topo'] = ("Data de Emissão é obrigatória.", "warning")
        return

    final_data = {}
    for k in campos_texto:
        if k != "id": final_data[k] = st.session_state[k]
    for k in campos_valor: final_data[k] = st.session_state[k]
    for k in campos_data:
        d = st.session_state[k]
        final_data[k] = d.strftime("%Y-%m-%d") if d else None

    # Lógica de ID: 
    # Se existe ID no state, é edição. 
    # Se não existe, geramos um UUID novo para evitar duplicidade ou NULL.
    id_atual = st.session_state.get('id')
    if id_atual:
        final_data['id'] = id_atual
        msg_acao = "atualizada"
    else:
        final_data['id'] = str(uuid.uuid4())
        msg_acao = "salva"
        
    final_data['responsavel'] = usuario_atual
    final_data['data_registro'] = datetime.now()

    db.salvar_nota(final_data)
    st.session_state['msg_topo'] = (f"Nota {msg_acao} com Sucesso!", "success")
    reset_form_callback()

def buscar_callback():
    st.session_state['msg_topo'] = ("Filtro Aplicado!", "warning")

# --- UI: TOPO ---
c1, c2, c3 = st.columns([0.25, 0.50, 0.25], gap="small", vertical_alignment="center")
with c1: st.markdown("##### :material/factory: Entrada de Notas")
with c2: uploaded_file = st.file_uploader("Upload", type="pdf", label_visibility="collapsed")
with c3: st.markdown(f"<div style='text-align:right; white-space:nowrap;'>👤 <b>{usuario_atual}</b></div>", unsafe_allow_html=True)

# EXTRAÇÃO AUTOMÁTICA
if uploaded_file and uploaded_file.name != st.session_state['ultimo_arquivo']:
    reset_form_callback()
    st.session_state['num_nota'] = "12345"
    st.session_state['razao_fornecedor'] = "Fornecedor Detectado Ltda"
    st.session_state['valor_nf'] = 1550.00
    st.session_state['data_emissao'] = date.today()
    st.session_state['ultimo_arquivo'] = uploaded_file.name
    st.session_state['msg_topo'] = ("Dados extraídos do PDF!", "warning")

if st.session_state['msg_topo']:
    msg, tipo = st.session_state['msg_topo']
    show_custom_message(msg, tipo)
    st.session_state['msg_topo'] = None 

# --- UI: PRINCIPAL ---
col_form, col_doc = st.columns([1, 1.5], gap="small")

# ESQUERDA: FORMULÁRIO
with col_form:
    with st.form("painel_controle", border=False):
        c_head_title, c_head_btns = st.columns([0.3, 0.7], vertical_alignment="center")
        with c_head_title: st.markdown("##### :material/edit_document: Dados")
        with c_head_btns:
            b_clear, b_search, b_save = st.columns([1, 1, 1])
            b_clear.form_submit_button("Limpar", type="secondary", use_container_width=True, icon=":material/delete_sweep:", on_click=reset_form_callback)
            b_search.form_submit_button("Buscar", type="secondary", use_container_width=True, icon=":material/search:", on_click=buscar_callback)
            b_save.form_submit_button("Salvar", type="primary", use_container_width=True, icon=":material/save:", on_click=salvar_callback)

        c_t1, c_t2 = st.columns([1, 2])
        c_t1.text_input("CNPJ Tomador", key="cnpj_tomador")
        c_t2.text_input("Razão Social Tomador", key="emp_tomador")
        
        c_f1, c_f2 = st.columns([1, 2])
        c_f1.text_input("CNPJ Fornecedor", key="cnpj_fornecedor")
        c_f2.text_input("Razão Social Fornecedor", key="razao_fornecedor")

        l1_c1, l1_c2, l1_c3 = st.columns([1, 1, 1])
        l1_c1.text_input("Nº Nota", key="num_nota")
        
        # --- AQUI ESTÁ A CORREÇÃO DO WARNING (SEM value=...) ---
        l1_c2.date_input("Emissão", key="data_emissao", format="DD/MM/YYYY")
        l1_c3.date_input("Vencimento", key="data_vencimento", format="DD/MM/YYYY")
        
        st.number_input("Valor da NF (R$)", key="valor_nf", step=0.01)

        l2_c1, l2_c2 = st.columns(2)
        l2_c1.text_input("Nº Requisição", key="num_requisicao")
        l2_c2.text_input("Nº Contrato", key="id_contrato")
        
        l3_c1, l3_c2 = st.columns(2)
        l3_c1.text_input("Nº Pedido", key="num_pedido")
        
        # --- CORREÇÃO (SEM value=...) ---
        l3_c2.date_input("Envio Pagamento", key="envio_pgto", format="DD/MM/YYYY")

        st.text_area("Observação", key="observacao", height=68)

# DIREITA: PDF
with col_doc:
    if uploaded_file:
        st.markdown(f"<div style='font-size:0.9rem; color:#555; margin-bottom:5px'>📄 Visualizando: <b>{uploaded_file.name}</b></div>", unsafe_allow_html=True)
        show_pdf(uploaded_file.getvalue())
    else:
        st.markdown(
            """
            <div style='background-color:#f8f9fa; height:650px; display:flex; 
            flex-direction:column; align-items:center; justify-content:center; 
            border-radius:4px; border: 1px dashed #ccc; color:#aaa;'>
                <div style="font-size: 3rem;">📂</div>
                <div style="margin-top: 10px;">Arraste o PDF para visualizar</div>
            </div>
            """, unsafe_allow_html=True
        )

# --- UI: TABELA DE BAIXO ---
st.divider()

if filtro_ativo:
    st.markdown(f"##### :material/search: Resultados da Busca ({len(df_show)}) - Selecione para Editar")
else:
    st.markdown("##### :material/history: Recentes")

column_cfg = {
    "envio_pgto": st.column_config.DateColumn("Envio Pgto.", format="DD/MM/YYYY"),
    "emp_tomador": "Emp",
    "cnpj_tomador": "ERP2",
    "num_requisicao": "RC",
    "id_contrato": "ID do Ctr",
    "num_pedido": "Pedido",
    "cnpj_fornecedor": "CNPJ",
    "razao_fornecedor": "Razão Social",
    "num_nota": "NF",
    "data_emissao": st.column_config.DateColumn("Data NF", format="DD/MM/YYYY"),
    "data_vencimento": st.column_config.DateColumn("Dt Venc", format="DD/MM/YYYY"),
    "valor_nf": st.column_config.NumberColumn("Valor NF", format="R$ %.2f"),
    "observacao": "Observação"
}

ordem_colunas = [
    "envio_pgto", "emp_tomador", "cnpj_tomador", "num_requisicao", 
    "id_contrato", "num_pedido", "cnpj_fornecedor", "razao_fornecedor", 
    "num_nota", "data_emissao", "data_vencimento", "valor_nf", "observacao"
]

event = st.dataframe(
    df_show,
    key="tabela_full",
    width="stretch", 
    hide_index=True,
    column_config=column_cfg,
    column_order=ordem_colunas,
    selection_mode="single-row", 
    on_select="rerun",
    height=300
)