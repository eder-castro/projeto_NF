import sqlite3
import pandas as pd
from datetime import datetime

DB_NAME = "notas.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS notas (
            id TEXT PRIMARY KEY,
            emp_tomador TEXT,
            cnpj_tomador TEXT,
            cnpj_fornecedor TEXT,
            razao_fornecedor TEXT,
            num_nota TEXT,
            data_emissao TEXT,
            data_vencimento TEXT,
            valor_nf REAL,
            observacao TEXT,
            num_requisicao TEXT,
            id_contrato TEXT,
            num_pedido TEXT,
            envio_pgto TEXT,
            responsavel TEXT,
            data_registro TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def carregar_dados():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM notas ORDER BY data_registro DESC", conn)
    conn.close()
    
    # ATUALIZADO: Incluí 'envio_pgto' na lista de conversão de datas
    cols_data = ['data_emissao', 'data_vencimento', 'envio_pgto', 'data_registro']
    for col in cols_data:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
            
    return df

def salvar_nota(dados: dict):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    campos = list(dados.keys())
    valores = list(dados.values())
    placeholders = ",".join(["?"] * len(campos))
    colunas = ",".join(campos)
    
    sql = f"INSERT OR REPLACE INTO notas ({colunas}) VALUES ({placeholders})"
    
    c.execute(sql, valores)
    conn.commit()
    conn.close()