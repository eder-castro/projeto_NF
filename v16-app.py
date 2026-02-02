import streamlit as st
import pandas as pd
import database as db
from datetime import datetime
import base64
import socket

# --- CONFIGURAÇÃO ---
st.set_page_config(layout="wide", page_title="Notas Fiscais", initial_sidebar_state="collapsed")
db.init_db()

# --- FUNÇÕES ---
def get_user_machine():
    try:
        return socket.gethostname()
    except:
        return "Desconhecido"

def show_pdf(file_bytes):
    base64_pdf = base64.b64encode(file_bytes).decode('utf-8')
    # AJUSTE FINO: 620px para alinhar exatamente com o formulário
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}#view=FitH" width="100%" height="620" type="application/pdf" style="border:none;"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

# --- CSS VISUAL ---
st.markdown("""
<style>
    header {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}
    
    .block-container {
        padding: 1rem 1.5rem !important;
        max-width: 100% !important;
    }

    /* UPLOAD */
    [data-testid="stFileUploader"] { padding: 0px !important; margin: 0px !important; }
    [data-testid="stFileUploader"] label { display: none; }
    [data-testid="stFileUploader"] ul { display: none; }
    [data-testid="stFileUploader"] .st-emotion-cache-1fttcpj { display: none; }
    
    /* Botão Browse Files */
    button[kind="secondary"] {
        height: 32px !important;
        border: 1px solid #ccc !important;
        font-size: 0.8rem !important;
    }

    /* Botões do Formulário */
    [data-testid="stForm"] button {
        height: 35px !important;       
        min-height: 0px !important;    
        padding: 0px 10px !important;  
        white-space: nowrap !important;
    }
    
    [data-testid="stForm"] button[kind="secondary"] {
        border: 1px solid #ccc !important;
        color: #333 !important;
        font-size: 0.85rem !important;
    }
    
    [data-testid="stForm"] button[kind="primary"] {
        font-size: 0.85rem !important;
    }

    [data-testid="column"] { padding: 0.5rem !important; }
</style>
""", unsafe_allow_html=True)

# --- ESTADO INICIAL ---
usuario_atual = get_user_machine()
DATA_PADRAO = datetime(1900, 1, 1)

keys_padrao = [
    "emp_tomador", "cnpj_tomador", "cnpj_fornecedor", "razao_fornecedor",
    "num_nota", "num_requisicao", "id_contrato", "num_pedido", "observacao"
]

if 'dados_form' not in st.session_state:
    st.session_state['dados_form'] = {k: "" for k in keys_padrao}
    st.session_state['dados_form']['valor_nf'] = 0.0
    st.session_state['dados_form']['data_emissao'] = DATA_PADRAO
    st.session_state['dados_form']['data_vencimento'] = DATA_PADRAO
    st.session_state['dados_form']['envio_pgto'] = DATA_PADRAO

if 'ultimo_arquivo' not in st.session_state:
    st.session_state['ultimo_arquivo'] = ""
if 'filtro_busca' not in st.session_state:
    st.session_state['filtro_busca'] = None 

# --- FUNÇÃO DE LIMPEZA ---
def reset_form():
    st.session_state['dados_form'] = {k: "" for k in keys_padrao}
    st.session_state['dados_form']['valor_nf'] = 0.0
    st.session_state['dados_form']['data_emissao'] = DATA_PADRAO
    st.session_state['dados_form']['data_vencimento'] = DATA_PADRAO
    st.session_state['dados_form']['envio_pgto'] = DATA_PADRAO
    st.session_state['filtro_busca'] = None

# --- TOPO ---
c1, c2, c3 = st.columns([0.25, 0.50, 0.25], gap="small", vertical_alignment="center")

with c1:
    st.markdown("##### :material/factory: Entrada de Notas")

with c2:
    uploaded_file = st.file_uploader("Upload", type="pdf", label_visibility="collapsed")

with c3:
    st.markdown(f"<div style='text-align:right; white-space:nowrap;'>👤 <b>{usuario_atual}</b></div>", unsafe_allow_html=True)

# EXTRAÇÃO
if uploaded_file and uploaded_file.name != st.session_state['ultimo_arquivo']:
    st.session_state['dados_form']['num_nota'] = "12345"
    st.session_state['dados_form']['razao_fornecedor'] = "Fornecedor Detectado Ltda"
    st.session_state['dados_form']['valor_nf'] = 1550.00
    st.session_state['dados_form']['data_emissao'] = datetime.today()
    st.session_state['ultimo_arquivo'] = uploaded_file.name
    st.toast("Dados extraídos!", icon="⚡")

# --- ÁREA PRINCIPAL ---
col_form, col_doc = st.columns([1, 1.5], gap="small")

# 🟦 ESQUERDA: FORMULÁRIO
with col_form:
    
    with st.form("painel_controle", border=False):
        # --- CABEÇALHO DO FORMULÁRIO ---
        c_head_title, c_head_btns = st.columns([0.3, 0.7], vertical_alignment="center")
        
        with c_head_title:
             st.markdown("##### :material/edit_document: Dados")
        
        with c_head_btns:
            b_clear, b_search, b_save = st.columns([1, 1, 1])
            
            clear_clk = b_clear.form_submit_button("Limpar", type="secondary", use_container_width=True, icon=":material/delete_sweep:")
            search_clk = b_search.form_submit_button("Buscar", type="secondary", use_container_width=True, icon=":material/search:")
            save_clk = b_save.form_submit_button("Salvar", type="primary", use_container_width=True, icon=":material/save:")

        if clear_clk:
            reset_form()
            st.rerun()

        # --- CAMPOS ---
        c_t1, c_t2 = st.columns([1, 2])
        dados = st.session_state['dados_form']
        dados['cnpj_tomador'] = c_t1.text_input("CNPJ Tomador", value=dados['cnpj_tomador'])
        dados['emp_tomador'] = c_t2.text_input("Razão Social Tomador", value=dados['emp_tomador'])
        
        c_f1, c_f2 = st.columns([1, 2])
        dados['cnpj_fornecedor'] = c_f1.text_input("CNPJ Fornecedor", value=dados['cnpj_fornecedor'])
        dados['razao_fornecedor'] = c_f2.text_input("Razão Social Fornecedor", value=dados['razao_fornecedor'])

        l1_c1, l1_c2, l1_c3 = st.columns([1, 1, 1])
        dados['num_nota'] = l1_c1.text_input("Nº Nota", value=dados['num_nota'])
        dados['data_emissao'] = l1_c2.date_input("Emissão", value=dados['data_emissao'], format="DD/MM/YYYY")
        dados['data_vencimento'] = l1_c3.date_input("Vencimento", value=dados['data_vencimento'], format="DD/MM/YYYY")
        
        dados['valor_nf'] = st.number_input("Valor da NF (R$)", value=float(dados['valor_nf']), step=0.01)

        l2_c1, l2_c2 = st.columns(2)
        dados['num_requisicao'] = l2_c1.text_input("Nº Requisição", value=dados['num_requisicao'])
        dados['id_contrato'] = l2_c2.text_input("Nº Contrato", value=dados['id_contrato'])
        
        l3_c1, l3_c2 = st.columns(2)
        dados['num_pedido'] = l3_c1.text_input("Nº Pedido", value=dados['num_pedido'])
        dados['envio_pgto'] = l3_c2.date_input("Envio Pagamento", value=dados['envio_pgto'], format="DD/MM/YYYY")

        dados['observacao'] = st.text_area("Observação", value=dados['observacao'], height=68)

        if save_clk:
            if not dados['num_nota']:
                st.warning("Número da Nota é obrigatório.")
            else:
                final_data = dados.copy()
                final_data['id'] = None 
                final_data['responsavel'] = usuario_atual
                final_data['data_registro'] = datetime.now()
                
                for campo_data in ['data_emissao', 'data_vencimento', 'envio_pgto']:
                    if final_data[campo_data]:
                        final_data[campo_data] = final_data[campo_data].strftime("%Y-%m-%d")

                db.salvar_nota(final_data)
                st.success("Nota Salva!")
                reset_form()
                st.rerun()
        
        if search_clk:
            st.session_state['filtro_busca'] = {
                "nf": dados['num_nota'],
                "cnpj": dados['cnpj_fornecedor'],
                "forn": dados['razao_fornecedor']
            }
            st.toast("Filtro aplicado!")

# 🟨 DIREITA: PDF (HEIGHT AJUSTADO PARA 620px)
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

# --- TABELA DE BAIXO ---
st.divider()

df = db.carregar_dados()

filtros = st.session_state.get('filtro_busca')
if filtros:
    if filtros.get('nf'):
        df = df[df['num_nota'].astype(str).str.contains(filtros['nf'], case=False)]
    if filtros.get('cnpj'):
        df = df[df['cnpj_fornecedor'].str.contains(filtros['cnpj'], case=False)]
    if filtros.get('forn'):
        df = df[df['razao_fornecedor'].str.contains(filtros['forn'], case=False)]
    st.markdown(f"##### :material/search: Resultados da Busca ({len(df)})")
else:
    st.markdown("##### :material/history: Recentes")
    df = df.head(10)

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

df_editado = st.data_editor(
    df,
    key="tabela_full",
    width="stretch", 
    num_rows="fixed",
    disabled=["id", "data_registro", "responsavel"],
    column_config=column_cfg,
    column_order=ordem_colunas,
    hide_index=True,
    height=300
)

if not df.equals(df_editado):
    if st.button("Gravar Alterações da Tabela", icon=":material/save_as:"):
        registros = df_editado.to_dict('records')
        progresso = st.progress(0)
        
        for i, reg in enumerate(registros):
            if isinstance(reg['data_registro'], pd.Timestamp):
                 reg['data_registro'] = reg['data_registro'].to_pydatetime()
            
            for campo_data in ['data_emissao', 'data_vencimento', 'envio_pgto']:
                val = reg.get(campo_data)
                if val:
                    if hasattr(val, 'strftime'):
                        reg[campo_data] = val.strftime("%Y-%m-%d")
                    else:
                        reg[campo_data] = str(val)
                else:
                    reg[campo_data] = None

            reg['responsavel'] = usuario_atual 
            db.salvar_nota(reg)
            progresso.progress((i + 1) / len(registros))
            
        st.success("Tabela atualizada!")
        st.rerun()