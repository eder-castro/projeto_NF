import PyPDF2
from utilities import extrair_campos

def extrair_dados_PDFSelecionavel(caminho_arquivo, nome_arquivo):
    with open(caminho_arquivo, "rb") as arquivo_pdf:
        reader = PyPDF2.PdfReader(arquivo_pdf)
        texto = ""
        for page in reader.pages:
            texto += page.extract_text() or "-"
            
        # Passa True para "is_selecionavel" e o nome do arquivo
        dados_extraidos = extrair_campos(texto, True, nome_arquivo)
        
        # Conta quantos campos vieram vazios (None)
        campos_faltantes = [key for key, value in dados_extraidos.items() if value is None]
        
        status = "sucesso"
        if len(campos_faltantes) >= 5: 
            # Se falhou em muitos campos, provavelmente é escaneado. Manda pro OCR.
            status = "reprocessar"
        elif len(campos_faltantes) > 0:
            # Leu quase tudo, mas faltou algum detalhe.
            status = "problema_parcial"
            
    return dados_extraidos, status