import os
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
from utilities import extrair_campos, preprocessamento
from config import PATH_POPPLER

def extrair_dados_PDFImagem(arquivo_imagem, nome_arquivo_original):
    try:
        imagem_pil = Image.open(arquivo_imagem)
        # Primeira tentativa de OCR sem filtros
        texto_original = pytesseract.image_to_string(imagem_pil, lang='por', config='--psm 6 --oem 3')
        dados_img = extrair_campos(texto_original, False, nome_arquivo_original)
        
        # Filtros para tentar resgatar dados ilegíveis
        filtros = ['max','median', 'minfilter', 'unsharp_mask', 'sharpen', 'blur', 'smooth']
        campos_faltantes = [k for k, v in dados_img.items() if v is None]

        # Loop inteligente: só aplica o próximo filtro se ainda faltar algum campo
        for filtro in filtros:
            if not campos_faltantes: 
                break
            
            img_processada = preprocessamento(arquivo_imagem, filtro)
            if img_processada:
                texto_novo = pytesseract.image_to_string(img_processada, lang='por', config='--psm 6 --oem 3')
                dados_novos = extrair_campos(texto_novo, False, nome_arquivo_original)
                
                # Atualiza apenas os campos que estavam vazios e agora foram encontrados
                for campo in list(campos_faltantes): 
                    if dados_img.get(campo) is None and dados_novos.get(campo):
                        dados_img[campo] = dados_novos[campo]
                        
                # Recalcula o que falta para a próxima rodada
                campos_faltantes = [k for k, v in dados_img.items() if v is None]
                
        return dados_img
    except Exception as e:
        print(f"Erro no OCR da imagem {arquivo_imagem}: {e}")
        return {}

def executa_PDFImg(caminho_pdf, nome_arquivo):
    dados_finais = []
    try:
        # Fatiador de PDF usando o Poppler (com o caminho dinâmico do config.py)
        imagens = convert_from_path(caminho_pdf, poppler_path=PATH_POPPLER, dpi=600)
        
        # Limitado a ler apenas a PÁGINA 1 (imagens[:1]) para evitar sujeira de anexos
        for i, imagem in enumerate(imagens[:1]):
            nome_temp = f'temp_{nome_arquivo}_{i}.png'
            imagem.save(nome_temp, 'PNG')
            
            dados = extrair_dados_PDFImagem(nome_temp, nome_arquivo)
            if dados: 
                dados_finais.append(dados)
                
            os.remove(nome_temp) # Limpa o arquivo temporário
    except Exception as e:
        print(f"Erro ao converter PDF {nome_arquivo}: {e}")
        
    return dados_finais