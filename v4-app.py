import streamlit as st
import pandas as pd
import database as db
from datetime import datetime
import base64
import socket

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(layout="wide", page_title="Sistema de Notas")
db.init_db()

# --- FUNÇÕES AUXILIARES ---
def get_user_machine():
    try:
        hostname = socket.gethostname()
        return hostname
    except:
        return "Desconhecido"

def show_pdf(file_bytes):
    base64_pdf = base64.b64encode(file_bytes).decode('utf-8')
    # Altura aumentada para 900px para maximizar visualização
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="900" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

# --- CSS REFINADO (ALINHAMENTO E LIMPEZA) ---
st.markdown("""
<style>
    header {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}
    
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 1rem;
    }
    
    /* REMOVE o nome do arquivo debaixo do Drag & Drop (para colocarmos onde quisermos) */
    [data-testid="stFileUploader"] section + div {
        display: none;
    }
    
    /* Deixa o Drag & Drop mais compacto na altura */
    [data-testid="stFileUploader"] {
        padding-top: 0px;
        margin-top: 0px;
    }
    
    /* Ajuste do botão 'Browse files' para ficar mais discreto */
    button[kind="secondary"] {
        padding-top: 0px;
        padding-bottom: 0px;
        height: 35px;
        border: 1px solid #ddd;
    }
    
    /* Remove margens extras dos títulos */
    h3 { margin-top: 0; padding-top: 0; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 🧠 LÓGICA DE USUÁRIO
# ==========================================
usuario_atual = get_user_machine()

# Inicializa variaveis de sessão
if 'dados_form' not in st.session_state:
    st.session_state['dados_form'] = {"nf": "", "forn": "", "val": 0.0, "data": datetime.today()}
if 'ultimo_arquivo' not in st.session_state:
    st.session_state['ultimo_arquivo'] = ""

# ==========================================
# 🔝 CABEÇALHO (ALINHADO PELO FUNDO)
# ==========================================

# vertical_alignment="bottom" faz a mágica de alinhar texto com botão
c_title, c_upload, c_user = st.columns([0.3, 0.5, 0.2], gap="medium", vertical_alignment="bottom")

with c_title:
    st.markdown("### 🏭 Entrada de Notas")

with c_upload:
    # O Drag & Drop fica aqui no meio
    uploaded_file = st.file_uploader("", type="pdf", label_visibility="collapsed")

with c_user:
    st.info(f"👤 **{usuario_atual}**")

st.divider()

# ==========================================
# ⚡ LÓGICA DE EXTRAÇÃO AUTOMÁTICA
# ==========================================
# Se tem arquivo E ele é diferente do último processado -> Extrai sozinho!
if uploaded_file and uploaded_file.name != st.session_state['ultimo_arquivo']:
    with st.spinner("🔍 Detectando dados automaticamente..."):
        # SIMULAÇÃO DA EXTRAÇÃO (AQUI ENTRARÁ SEU CÓDIGO REAL DEPOIS)
        # Exemplo: Se o arquivo tiver "Tech" no nome, simula dados da Tech
        st.session_state['dados_form'] = {
            "nf": "NF-" + str(datetime.now().microsecond)[:4], 
            "forn": "Tech Solutions S.A." if "tech" in uploaded_file.name.lower() else "Fornecedor Genérico",
            "val": 1250.00,
            "data": datetime.today()
        }
        
        # Atualiza o controle para não rodar de novo sem necessidade
        st.session_state['ultimo_arquivo'] = uploaded_file.name
        st.toast("✅ Dados extraídos com sucesso!", icon="⚡")

# ==========================================
# 🏗️ ÁREA DE TRABALHO
# ==========================================
col_form, col_doc = st.columns([1, 1.3], gap="large")

# 🟨 LADO DIREITO: VISUALIZAÇÃO DO PDF
with col_doc:
    if uploaded_file:
        # Título do arquivo fica AQUI agora, em cima da visualização
        st.markdown(f"#### 📄 Arquivo: `{uploaded_file.name}`")
        show_pdf(uploaded_file.getvalue())
    else:
        st.markdown(
            """
            <div style='background-color:#f8f9fa; height:900px; display:flex; 
            flex-direction:column; align-items:center; justify-content:center; 
            border-radius:8px; border: 1px dashed #ddd; color:#aaa;'>
                <h3>👁️ Visualizador</h3>
                <p>Arraste o PDF no topo para visualizar aqui.</p>
            </div>
            """, unsafe_allow_html=True
        )

# 🟦 LADO ESQUERDO: FORMULÁRIO DE DADOS
with col_form:
    st.markdown("#### 📝 Conferência")

    with st.container(border=True):
        with st.form("form_entrada"):
            # Os valores vêm do session_state (que foi preenchido na extração automática)
            nf_input = st.text_input("Número NF", value=st.session_state['dados_form']['nf'])
            forn_input = st.text_input("Fornecedor", value=st.session_state['dados_form']['forn'])
            
            c1, c2 = st.columns(2)
            val_input = c1.number_input("Valor (R$)", value=st.session_state['dados_form']['val'], step=0.01)
            data_input = c2.date_input("Data Emissão", value=st.session_state['dados_form']['data'])
            
            status_input = st.selectbox("Status", ["Recebido", "Pendente Pedido", "Finalizado"])
            
            st.markdown("---")
            
            if st.form_submit_button("💾 SALVAR LANÇAMENTO", type="primary", use_container_width=True):
                if not nf_input:
                    st.error("O número da NF é obrigatório!")
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
                    st.success(f"Nota salva!")
                    # Limpa os dados para a próxima (mas mantém o arquivo visualizado se quiser)
                    st.session_state['dados_form'] = {"nf": "", "forn": "", "val": 0.0, "data": datetime.today()}
                    st.rerun()

# ==========================================
# ⬇️ RODAPÉ: HISTÓRICO
# ==========================================
st.divider()
st.markdown("#### 🕒 Histórico Recente")

df = db.carregar_dados()
df_editado = st.data_editor(
    df,
    key="tabela_historico",
    use_container_width=True,
    num_rows="fixed",
    disabled=["id", "data_registro", "responsavel"],
    column_config={
        "valor": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
        "data_emissao": st.column_config.DateColumn("Emissão", format="DD/MM/YYYY"),
    },
    hide_index=True
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