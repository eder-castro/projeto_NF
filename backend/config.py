import platform
import os

# Descobre qual é o sistema operacional rodando o script agora
sistema_operacional = platform.system()

if sistema_operacional == 'Windows':
    # Pega dinamicamente a pasta AppData\Local do usuário atual (ex: C:\Users\QualquerNome\AppData\Local)
    local_appdata = os.environ.get('LOCALAPPDATA')
    
    # Monta o caminho unindo as pastas, sem depender de barras fixas
    PATH_POPPLER = os.path.join(local_appdata, 'Programs', 'poppler-24.08.0', 'Library', 'bin')

elif sistema_operacional == 'Darwin': 
    # 'Darwin' é o macOS. Caminho padrão do Homebrew para Apple Silicon
    PATH_POPPLER = '/opt/homebrew/bin'

else:
    # Caso rode em um Linux no futuro
    PATH_POPPLER = '/usr/bin' 

# Pasta padrão onde os PDFs serão lidos
PASTA_PDFS = './PDFs'