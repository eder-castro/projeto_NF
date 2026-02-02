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
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}#view=FitH" width="100%" height="600" type="application/pdf" style="border:none;"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

# --- CSS REFINADO ---
st.markdown("""
<style>
    header {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}
    
    .block-container {
        padding: 1rem 1.5rem !important;
        max-width: 100% !important;
    }

    /* UPLOAD COMPACTO */
    [data-testid="stFileUploader"] {
        padding: 0px !important; 
        margin: 0px !important;
    }
    [data-testid="stFileUploader"] label {
        display: none;
    }
    [data-testid="stFileUploader"] ul {
        display: none;
    }
    [data-testid="stFileUploader"] .st-emotion-cache-1fttcpj {
        display: none;
    }
    
    button[kind="secondary"] {
        height: 32px !important;
        border: 1px solid #ccc !important;
    }

    /* Remove padding das colunas */
    [data-testid="column"] { padding: 0.5rem !important; }
</style>
""", unsafe_allow_html=True)

# --- ESTADO ---
usuario_atual = get_user_machine()

keys_padrao = [
    "emp_tomador", "cnpj_tomador", "cnpj_fornecedor", "razao_fornecedor",
    "num_nota", "data_emissao", "data_vencimento", "valor_nf", "observacao",
    "num_requisicao", "id_contrato", "num_pedido", "envio_pgto"
]

if 'dados_form' not in st.session_state:
    st.session_state['dados_form'] = {k: "" for k in keys_padrao}
    st.session_state['dados_form']['valor_nf'] = 0.0
    st.session_state['dados_form']['data_emissao'] = datetime.today()
    st.session_state['dados_form']['data_vencimento'] = datetime.today()

if 'ultimo_arquivo' not in st.session_state:
    st.session_state['ultimo_arquivo'] = ""
if 'filtro_busca' not in st.session_state:
    st.session_state['filtro_busca'] = None 

# --- TOPO ---
c1, c2, c3 = st.columns([0.25, 0.50, 0.25], gap="small", vertical_alignment="center")

with c1:
    st.markdown("##### :material/factory: Entrada de Notas")

with c2:
    uploaded_file = st.file_uploader("Upload", type="pdf", label_visibility="collapsed")

with c3:
    st.markdown(f"<div style='text-align:right; white-space:nowrap;'>👤 <b>{usuario_atual}</b></div>", unsafe_allow_html=True)

# EXTRAÇÃO AUTOMÁTICA
if uploaded_file and uploaded_file.name != st.session_state['ultimo_arquivo']:
    st.session_state['dados_form']['num_nota'] = "12345"
    st.session_state['dados_form']['razao_fornecedor'] = "Fornecedor Detectado Ltda"
    st.session_state['dados_form']['valor_nf'] = 1550.00
    st.session_state['ultimo_arquivo'] = uploaded_file.name
    st.toast("Dados extraídos!", icon="⚡")

# --- ÁREA PRINCIPAL ---
col_form, col_doc = st.columns([1, 1.5], gap="small")

# 🟦 ESQUERDA: FORMULÁRIO LIMPO (SEM TÍTULOS DE SEÇÃO)
with col_form:
    st.markdown("##### :material/edit_document: Dados da Nota")
    
    with st.form("painel_controle", border=False):
        
        # Linha 1: Tomador
        c_t1, c_t2 = st.columns([1, 2])
        dados = st.session_state['dados_form']
        dados['cnpj_tomador'] = c_t1.text_input("CNPJ Tomador", value=dados['cnpj_tomador'])
        dados['emp_tomador'] = c_t2.text_input("Razão Social Tomador", value=dados['emp_tomador'])
        
        # Linha 2: Fornecedor
        c_f1, c_f2 = st.columns([1, 2])
        dados['cnpj_fornecedor'] = c_f1.text_input("CNPJ Fornecedor", value=dados['cnpj_fornecedor'])
        dados['razao_fornecedor'] = c_f2.text_input("Razão Social Fornecedor", value=dados['razao_fornecedor'])

        # Linha 3: Dados da Nota
        l1_c1, l1_c2, l1_c3 = st.columns([1, 1, 1])
        dados['num_nota'] = l1_c1.text_input("Nº Nota", value=dados['num_nota'])
        dados['data_emissao'] = l1_c2.date_input("Data Emissão", value=dados['data_emissao'])
        dados['data_vencimento'] = l1_c3.date_input("Data Vencimento", value=dados['data_vencimento'])
        
        # Linha 4: Valor
        dados['valor_nf'] = st.number_input("Valor da NF (R$)", value=float(dados['valor_nf']), step=0.01)

        # Linha 5: Vínculos
        l2_c1, l2_c2 = st.columns(2)
        dados['num_requisicao'] = l2_c1.text_input("Nº Requisição", value=dados['num_requisicao'])
        dados['id_contrato'] = l2_c2.text_input("Nº Contrato", value=dados['id_contrato'])
        
        # Linha 6: Pedido e Status
        l3_c1, l3_c2 = st.columns(2)
        dados['num_pedido'] = l3_c1.text_input("Nº Pedido", value=dados['num_pedido'])
        dados['envio_pgto'] = l3_c2.selectbox("Envio Pagamento", ["", "Pendente", "Enviado", "Pago"], index=0 if dados['envio_pgto'] == "" else ["", "Pendente", "Enviado", "Pago"].index(dados['envio_pgto']))

        dados['observacao'] = st.text_area("Observação", value=dados['observacao'], height=68)

        st.write("") 
        
        # Botões
        btn_col1, btn_col2 = st.columns(2)
        busca_clicada = btn_col1.form_submit_button("Buscar", type="secondary", width="stretch", icon=":material/search:")
        salvar_clicado = btn_col2.form_submit_button("Salvar", type="primary", width="stretch", icon=":material/save:")

        if salvar_clicado:
            if not dados['num_nota']:
                st.warning("Número da Nota é obrigatório.")
            else:
                final_data = dados.copy()
                final_data['id'] = None 
                final_data['responsavel'] = usuario_atual
                final_data['data_registro'] = datetime.now()
                
                final_data['data_emissao'] = final_data['data_emissao'].strftime("%Y-%m-%d")
                final_data['data_vencimento'] = final_data['data_vencimento'].strftime("%Y-%m-%d")
                
                db.salvar_nota(final_data)
                st.success("Nota Salva!")
                
                # Limpa Form
                st.session_state['dados_form'] = {k: "" for k in keys_padrao}
                st.session_state['dados_form']['valor_nf'] = 0.0
                st.session_state['dados_form']['data_emissao'] = datetime.today()
                st.session_state['dados_form']['data_vencimento'] = datetime.today()
                st.rerun()
        
        if busca_clicada:
            st.session_state['filtro_busca'] = {
                "nf": dados['num_nota'],
                "cnpj": dados['cnpj_fornecedor']
            }
            st.toast("Filtro aplicado!")

# 🟨 DIREITA: PDF
with col_doc:
    if uploaded_file:
        st.markdown(f"<div style='font-size:0.9rem; color:#555; margin-bottom:5px'>📄 Visualizando: <b>{uploaded_file.name}</b></div>", unsafe_allow_html=True)
        show_pdf(uploaded_file.getvalue())
    else:
        st.markdown(
            """
            <div style='background-color:#f8f9fa; height:600px; display:flex; 
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
    if filtros['nf']:
        df = df[df['num_nota'].astype(str).str.contains(filtros['nf'], case=False)]
    if filtros['cnpj']:
        df = df[df['cnpj_fornecedor'].str.contains(filtros['cnpj'], case=False)]
    st.markdown(f"##### :material/search: Resultados ({len(df)})")
else:
    st.markdown("##### :material/history: Recentes")
    df = df.head(10)

# ... (código anterior continua igual)

# CONFIGURAÇÃO DAS COLUNAS
column_cfg = {
    "envio_pgto": "Envio Pgto.",
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

df_editado = st.data_editor(
    df,
    key="tabela_full",
    width="stretch", 
    num_rows="fixed",
    disabled=["id", "data_registro", "responsavel"],
    column_config=column_cfg,
    hide_index=True,
    height=300
)

if not df.equals(df_editado):
    if st.button("Gravar Alterações da Tabela", icon=":material/save_as:"):
        registros = df_editado.to_dict('records')
        
        # Barra de progresso para dar feedback visual
        progresso = st.progress(0)
        
        for i, reg in enumerate(registros):
            # 1. Converte Timestamp do registro para datetime python puro
            if isinstance(reg['data_registro'], pd.Timestamp):
                 reg['data_registro'] = reg['data_registro'].to_pydatetime()
            
            # 2. Converte as Datas (Date/Timestamp) para String (YYYY-MM-DD) para o SQLite
            # O Pandas pode devolver Timestamp, datetime.date ou datetime.datetime
            for campo_data in ['data_emissao', 'data_vencimento']:
                val = reg.get(campo_data)
                if val:
                    if hasattr(val, 'strftime'):
                        reg[campo_data] = val.strftime("%Y-%m-%d")
                    else:
                        # Se já for string ou outro tipo, mantém
                        reg[campo_data] = str(val)
                else:
                    reg[campo_data] = None

            reg['responsavel'] = usuario_atual 
            db.salvar_nota(reg)
            progresso.progress((i + 1) / len(registros))
            
        st.success("Tabela atualizada!")
        st.rerun()