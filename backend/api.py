import os
import shutil
import sqlite3
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException
from apscheduler.schedulers.background import BackgroundScheduler
import pandas as pd
import re

# Importando as suas funções originais
from text_pdf import extrair_dados_PDFSelecionavel
from image_pdf import executa_PDFImg
from export import salvar_no_excel
from config import NOME_PLANILHA, NOME_BANCO

# --- 1. CONFIGURAÇÃO DO BANCO DE DADOS TEMPORÁRIO (A SALA DE ESPERA) ---
def inicializar_banco():
    conn = sqlite3.connect(NOME_BANCO)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Numero_Nota TEXT,
            Data_Emissao TEXT,
            Data_Vencimento TEXT,
            CNPJ_Prestador TEXT,
            CNPJ_Tomador TEXT,
            Contrato TEXT,
            Pedido TEXT,
            Valor_Total REAL,
            Nome_Arquivo TEXT,
            status TEXT DEFAULT 'pendente'
        )
    """)
    conn.commit()
    conn.close()

# --- 2. O ROBÔ EXPORTADOR (RODA EM SEGUNDO PLANO) ---
def processar_fila_para_excel():
    conn = sqlite3.connect(NOME_BANCO)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Busca apenas o que o front já salvou e ainda não foi pro Excel
    cursor.execute("SELECT * FROM notas WHERE status = 'pendente'")
    registros = cursor.fetchall()
    
    if not registros:
        conn.close()
        return

    print(f"\n[SISTEMA] {len(registros)} NFs na fila. Iniciando exportação em lote...")
    
    lista_dados = []
    ids_processados = []
    
    for row in registros:
        lista_dados.append(dict(row))
        ids_processados.append(str(row['id']))

    try:
        # Chama a SUA função blindada do xlwings
        salvar_no_excel(lista_dados)
        
        # Se o Excel fechou com sucesso, marca como 'exportado'
        ids_formatados = ",".join(ids_processados)
        cursor.execute(f"UPDATE notas SET status = 'exportado' WHERE id IN ({ids_formatados})")
        conn.commit()
        print("[SISTEMA] Fila atualizada. Notas salvas no Excel com sucesso.")
        
    except Exception as e:
        print(f"[ERRO DO ROBÔ] Falha ao gravar no Excel neste ciclo: {e}")
        # Se der erro (ex: alguém com arquivo aberto), ele tenta de novo no próximo ciclo
        
    finally:
        conn.close()

# --- 3. INICIALIZAÇÃO DA API E DO AGENDADOR ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Quando a API liga:
    inicializar_banco()
    scheduler = BackgroundScheduler()
    # Robô configurado para rodar a cada 3 minutos
    scheduler.add_job(processar_fila_para_excel, 'interval', minutes=3)
    scheduler.start()
    
    yield # API rodando...
    
    # Quando a API desliga:
    scheduler.shutdown()

app = FastAPI(title="Motor de Processamento de NFs", lifespan=lifespan)

def buscar_razao_social_no_excel(cnpj_procurado):
    print(f"\n🔎 [DEBUG] Iniciando busca para o CNPJ original: '{cnpj_procurado}'")
    if not cnpj_procurado:
        print("🔎 [DEBUG] O CNPJ chegou vazio. Cancelando busca.")
        return ""
    
    # 1. Remove pontos/barras e tira TODOS os zeros à esquerda
    cnpj_limpo = re.sub(r'\D', '', str(cnpj_procurado)).lstrip('0')
    print(f"🔎 [DEBUG] CNPJ para pesquisa (sem zeros à esquerda): '{cnpj_limpo}'")
    
    try:
        df = pd.read_excel(NOME_PLANILHA, sheet_name="Cadastro Fornecedor e Tomador")
        
        # 2. Limpa a coluna do Excel: remove '.0', remove não-números e tira zeros à esquerda
        df['CNPJ_STR'] = df['CNPJ'].astype(str).str.replace(r'\.0$', '', regex=True)
        df['CNPJ_LIMPO'] = df['CNPJ_STR'].str.replace(r'\D', '', regex=True).str.lstrip('0')
        
        # 3. Compara as duas strings puras
        resultado = df[df['CNPJ_LIMPO'] == cnpj_limpo]
        print(f"🔎 [DEBUG] Total de linhas que bateram: {len(resultado)}")
        
        if not resultado.empty:
            try:
                nome = str(resultado.iloc[0]['Razão Social'])
                print(f"🔎 [DEBUG] SUCESSO! Nome encontrado: '{nome}'")
                return nome
            except KeyError:
                print("🚨 [ERRO] A coluna 'Razão Social' não foi encontrada.")
                return ""
        else:
            print("🔎 [DEBUG] O CNPJ não existe na planilha do Excel.")
            return ""
            
    except Exception as e:
        print(f"🚨 [ERRO GERAL] Falha na busca: {e}")
        return ""

# --- 4. ENDPOINTS (AS PORTAS DE ENTRADA DO FRONTEND) ---

@app.post("/extrair-pdf")
async def extrair_pdf(file: UploadFile = File(...)):
    """Recebe o PDF do Streamlit, processa a extração e devolve os dados na hora."""
    caminho_temp = f"temp_{file.filename}"
    
    # Salva o arquivo temporariamente para suas funções poderem ler
    with open(caminho_temp, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        dados = None
        # Tenta texto primeiro
        dados, status = extrair_dados_PDFSelecionavel(caminho_temp, file.filename)
        
        # Se falhar, tenta OCR Imagem
        if status == "reprocessar" or not dados:
            resultados_ocr = executa_PDFImg(caminho_temp, file.filename)
            dados = resultados_ocr[0] if isinstance(resultados_ocr, list) else resultados_ocr
            
        if isinstance(dados, list) and len(dados) > 0:
            dados = dados[0]

        if dados and isinstance(dados, dict):
            # 1. Busca o nome do Prestador/Fornecedor
            cnpj_prestador = dados.get('CNPJ_Prestador', '')
            if cnpj_prestador:
                nome_fornecedor = buscar_razao_social_no_excel(cnpj_prestador)
                if nome_fornecedor:
                    dados['Razao_Prestador'] = nome_fornecedor 
                    
            # 2. Busca o nome do Tomador
            cnpj_tomador = dados.get('CNPJ_Tomador', '')
            if cnpj_tomador:
                nome_tomador = buscar_razao_social_no_excel(cnpj_tomador)
                if nome_tomador:
                    dados['Empresa_Tomador'] = nome_tomador

        return {"status": "sucesso", "dados": dados}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Apaga o PDF temporário para não lotar o servidor
        if os.path.exists(caminho_temp):
            os.remove(caminho_temp)

@app.post("/salvar-bd")
async def salvar_bd(dados: dict):
    """Recebe os dados validados pelo usuário e joga na sala de espera."""
    try:
        conn = sqlite3.connect(NOME_BANCO)
        cursor = conn.cursor()
        
        # Importante: As chaves do dicionário devem bater com o que o Front enviar
        cursor.execute("""
            INSERT INTO notas 
            (Numero_Nota, Data_Emissao, Data_Vencimento, CNPJ_Prestador, CNPJ_Tomador, Contrato, Pedido, Valor_Total, Nome_Arquivo)
            VALUES 
            (:num_nota, :data_emissao, :data_vencimento, :cnpj_fornecedor, :cnpj_tomador, :id_contrato, :num_pedido, :valor_nf, :nome_arquivo)
        """, dados) 
        
        conn.commit()
        conn.close()
        return {"status": "sucesso", "mensagem": "Nota salva na fila de processamento!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar no banco: {e}")
    
@app.get("/ultimas-notas")
async def ultimas_notas():
    """Busca as 10 últimas notas salvas no banco para exibir na tabela do front."""
    try:
        conn = sqlite3.connect(NOME_BANCO)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Puxa os 10 registros mais recentes
        cursor.execute("SELECT * FROM notas ORDER BY id DESC LIMIT 10")
        registros = cursor.fetchall()
        conn.close()
        
        # Converte para lista de dicionários
        dados = [dict(row) for row in registros]
        return {"status": "sucesso", "dados": dados}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar histórico: {e}")
