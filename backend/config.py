import platform
import os

# ==========================================
# 1. CONFIGURAÇÕES DE SISTEMA (POPPLER)
# ==========================================
sistema_operacional = platform.system()

if sistema_operacional == 'Windows':
    local_appdata = os.environ.get('LOCALAPPDATA')
    PATH_POPPLER = os.path.join(local_appdata, 'Programs', 'poppler-24.08.0', 'Library', 'bin')
elif sistema_operacional == 'Darwin': 
    PATH_POPPLER = '/opt/homebrew/bin'
else:
    PATH_POPPLER = '/usr/bin' 

# ==========================================
# 2. CONFIGURAÇÕES DE ARQUIVOS E DIRETÓRIOS
# ==========================================

# Nome oficial da planilha de controle de fluxo de caixa
NOME_PLANILHA = "PLANILHA DE CONTROLE.xlsx"

# Nome oficial do banco de dados local SQLite (fila)
NOME_BANCO = "fila_notas.db"