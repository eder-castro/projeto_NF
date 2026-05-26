from datetime import datetime
from dateutil import parser
from PIL import Image, ImageFilter
import extracao

def parse_data_emissao(data_str):
    try:
        dt = parser.parse(data_str)
        if dt.tzinfo is not None:
            dt = dt.replace(tzinfo=None)
        return dt
    except Exception:
        try:
            return datetime.strptime(data_str, "%d/%m/%Y")
        except Exception:
            print(f"[AVISO] Data inválida ignorada: {data_str}")
            return None

def preprocessamento(image_path, filter_type):
    try:
        img = Image.open(image_path).convert('L') # Converte para escala de cinza
        
        # Dicionário mapeando as strings para os filtros reais do Pillow
        filtros = {
            'max': ImageFilter.MaxFilter,
            'median': ImageFilter.MedianFilter,
            'unsharp_mask': ImageFilter.UnsharpMask(),
            'sharpen': ImageFilter.SHARPEN,
            'minfilter': ImageFilter.MinFilter,
            'smooth_more': ImageFilter.SMOOTH_MORE,
            'blur': ImageFilter.BLUR,
            'contour': ImageFilter.CONTOUR,
            'detail': ImageFilter.DETAIL,
            'edge_enhance': ImageFilter.EDGE_ENHANCE,
            'edge_enhance_more': ImageFilter.EDGE_ENHANCE_MORE,
            'emboss': ImageFilter.EMBOSS,
            'find_edges': ImageFilter.FIND_EDGES,
            'smooth': ImageFilter.SMOOTH
        }
        
        filtro_aplicar = filtros.get(filter_type)
        if filtro_aplicar:
            return img.filter(filtro_aplicar)
        else:
            print(f"Aviso: Filtro '{filter_type}' não reconhecido. Retornando original.")
            return img
            
    except Exception as e:
        print(f"Erro ao pré-processar a imagem com {filter_type}: {e}")
        return None

def extrair_campos(texto, is_selecionavel, nome_arquivo):
    """
    is_selecionavel (bool): Substitui o antigo proc_selec global.
    nome_arquivo (str): Passado diretamente para não depender de global.
    """
    dados_nf = {
        "Numero_Nota": None,
        "Data_Emissao": None,
        "CNPJ_Prestador": None,
        "CNPJ_Tomador": None,
        "Pedido": None,
        "Contrato": None,
        "Valor_Total": None,
        "Nome_Arquivo": None
    }

    if is_selecionavel:
        dados_nf["Numero_Nota"] = extracao.extrai_numero_nota_pdf_selecionavel(texto)
    else:
        dados_nf["Numero_Nota"] = extracao.extrai_numero_nota_pdf_imagem(texto)
        
    dados_nf["Data_Emissao"] = extracao.extrai_data_emissao(texto)
    
    lista_CNPJs = extracao.extrai_documentos(texto, extracao.extrai_Cnpjs, extracao.extrai_Cpfs)
    # Proteção caso a regex não encontre 2 CNPJs
    dados_nf["CNPJ_Prestador"] = lista_CNPJs[0] if len(lista_CNPJs) > 0 else None
    dados_nf["CNPJ_Tomador"] = lista_CNPJs[1] if len(lista_CNPJs) > 1 else None
    
    lista_pedido_contrato = extracao.extrai_pedido_e_contrato(texto)
    # Proteção caso a regex não encontre pedido e contrato
    dados_nf["Pedido"] = lista_pedido_contrato[0] if len(lista_pedido_contrato) > 0 else None
    dados_nf["Contrato"] = lista_pedido_contrato[1] if len(lista_pedido_contrato) > 1 else None
    
    dados_nf["Valor_Total"] = extracao.extrai_valores(texto)
    dados_nf["Nome_Arquivo"] = nome_arquivo
    
    return dados_nf