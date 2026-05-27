import math
import os
from datetime import datetime
from dateutil import parser
import xlwings as xw
import pandas as pd

# --- Mapeamento das colunas ---
COLUNAS_MAPEAMENTO = {
    'Envio Pgto.': {'dict_key': 'Envio_Pgto', 'type': str},
    'CNPJ Tomador': {'dict_key': 'CNPJ_Tomador', 'type': str},
    'RC': {'dict_key': 'Num_Requisicao', 'type': str},
    'ID do Ctr': {'dict_key': 'Contrato', 'type': str},
    'Pedido': {'dict_key': 'Pedido', 'type': str},
    'CNPJ Fornecedor': {'dict_key': 'CNPJ_Prestador', 'type': str},
    'NF': {'dict_key': 'Numero_Nota', 'type': int},
    'Data NF': {'dict_key': 'Data_Emissao', 'type': str},
    'Valor NF': {'dict_key': 'Valor_Total', 'type': float},
    'Observação': {'dict_key': 'Observacao', 'type': str}
}

def parse_data_emissao(data_str):
    if not isinstance(data_str, str) or not data_str:
        return None
    try:
        dt = parser.parse(data_str)
        if dt.tzinfo is not None:
            dt = dt.replace(tzinfo=None)
        return dt
    except Exception:
        try:
            return datetime.strptime(data_str, "%d/%m/%Y")
        except Exception:
            return None

def formatar_valor_para_planilha(excel_col_name, value, expected_type):
    if pd.isna(value) or value is None or (isinstance(value, str) and not value.strip()):
        return None
    
    if isinstance(value, str):
        val_lower = value.strip().lower()
        if val_lower in ['inf', '-inf', 'nan']:
            return None
            
    if isinstance(value, float) and (math.isinf(value) or math.isnan(value)):
        return None

    if expected_type == datetime:
        return parse_data_emissao(value)
        
    elif expected_type == float:
        try:
            if isinstance(value, str):
                value = value.replace(".", "").replace(",", ".")
            f_val = float(value)
            if math.isinf(f_val) or math.isnan(f_val):
                return None
            return f_val
        except (ValueError, TypeError):
            return None
            
    elif expected_type == int:
        try:
            if isinstance(value, str):
                clean_str = ''.join(filter(str.isdigit, value))
                if clean_str:
                    return int(clean_str)
                return None
            f_val = float(value)
            if math.isinf(f_val) or math.isnan(f_val):
                return None
            return int(f_val)
        except (ValueError, TypeError):
            return None
            
    elif expected_type == str:
        s_value = str(value)
        if s_value.endswith('.0') and s_value[:-2].isdigit():
            s_value = s_value[:-2]
        return s_value.strip()

    return str(value).strip()

def salvar_no_excel(lista_dados, arquivo_excel="CONTROLE FLUXO ORIGINAL.xlsx", sheet_name="#NFs#", header_row=1):
    if not lista_dados:
        print("[EXPORT] Nenhuma nota para processar.")
        return

    caminho_absoluto = os.path.abspath(arquivo_excel)
    if not os.path.exists(caminho_absoluto):
        # Agora ele levanta um erro real, parando a execução e avisando a API
        raise FileNotFoundError(f"O arquivo '{arquivo_excel}' não foi encontrado em {caminho_absoluto}")

    data_start_row = header_row + 1
    
    print("\n[EXPORT] Iniciando comunicação com o motor do Excel (xlwings)...", flush=True)
    app = xw.App(visible=False)
    
    try:
        # --- TURBO DE PERFORMANCE ---
        app.screen_updating = False  
        app.calculation = 'manual'   
        
        wb = app.books.open(caminho_absoluto)
        sheet = wb.sheets[sheet_name]
        
        # 1. Obter cabeçalhos
        print(f"[EXPORT] Lendo estrutura da planilha...", flush=True)
        excel_headers = sheet.range(f"A{header_row}:AZ{header_row}").value
        
        col_indices = {}
        for col in COLUNAS_MAPEAMENTO.keys():
            if col in excel_headers:
                col_indices[col] = excel_headers.index(col) + 1
                
# 2. Carregar dados em bloco (Dinâmico para ler toda a planilha real)
        print(f"[EXPORT] Mapeando espaços vazios e NFs existentes...", flush=True)
        ultima_linha_com_dados = sheet.range('A1048576').end('up').row
        max_rows = max(10000, ultima_linha_com_dados + 100) 
        
        dados_planilha = {}
        for col_name, col_idx in col_indices.items():
            col_data = sheet.range((data_start_row, col_idx), (max_rows, col_idx)).value
            
            # --- CORREÇÃO: Blindagem para colunas 100% vazias no Excel ---
            tamanho_esperado = max_rows - data_start_row + 1
            if col_data is None:
                col_data = [None] * tamanho_esperado
            elif not isinstance(col_data, list):
                col_data = [col_data] + [None] * (tamanho_esperado - 1)
                
            dados_planilha[col_name] = col_data
            
        # 3. Identificar Duplicatas já salvas na planilha
        dados_existentes = set()
        if 'NF' in col_indices and 'CNPJ Fornecedor' in col_indices:
            for nf, cnpj in zip(dados_planilha['NF'], dados_planilha['CNPJ Fornecedor']):
                if nf is not None and cnpj is not None:
                    try:
                        dados_existentes.add((int(float(nf)), int(float(cnpj))))
                    except:
                        pass
        
        print(f"[EXPORT] {len(dados_existentes)} notas mapeadas para validação anti-duplicidade.", flush=True)
                        
        # 4. Buscador de Buracos
        def linha_esta_livre(rel_idx):
            for col_name in col_indices.keys():
                val = dados_planilha[col_name][rel_idx]
                if val is not None and str(val).strip() != "":
                    return False
            return True

        # 5. Escrever Dados
        next_insert_row = data_start_row
        novos_adicionados = 0
        total_notas = len(lista_dados)
        print("-" * 70)

        for index, dicionario in enumerate(lista_dados, start=1):
            num_nota = formatar_valor_para_planilha('NF', dicionario.get(COLUNAS_MAPEAMENTO['NF']['dict_key']), int)
            cnpj = formatar_valor_para_planilha('CNPJ Fornecedor', dicionario.get(COLUNAS_MAPEAMENTO['CNPJ Fornecedor']['dict_key']), int)

            if num_nota is not None and cnpj is not None and (num_nota, cnpj) in dados_existentes:
                print(f"[{index}/{total_notas}] ⏭️ Ignorada (Duplicada): NF {num_nota}".ljust(70), flush=True)
                continue

            rel_idx = next_insert_row - data_start_row
            while rel_idx < len(dados_planilha[list(col_indices.keys())[0]]) and not linha_esta_livre(rel_idx):
                next_insert_row += 1
                rel_idx = next_insert_row - data_start_row

            print(f"[{index}/{total_notas}] ✍️ Gravando NF {num_nota} na Linha {next_insert_row}...".ljust(70), flush=True)

            for excel_col_name, col_info in COLUNAS_MAPEAMENTO.items():
                col_idx = col_indices.get(excel_col_name)
                if col_idx is not None:
                    valor_formatado = formatar_valor_para_planilha(
                        excel_col_name, dicionario.get(col_info['dict_key']), col_info['type']
                    )
                    sheet.range((next_insert_row, col_idx)).value = valor_formatado
                    dados_planilha[excel_col_name][rel_idx] = "PREENCHIDO"
            
            # Alimenta a memória em tempo de execução para evitar duplicados do mesmo lote
            if num_nota is not None and cnpj is not None:
                dados_existentes.add((num_nota, cnpj))

            novos_adicionados += 1
            next_insert_row += 1

        print("-" * 70)
        
        if novos_adicionados > 0:
            print(f"[EXPORT] Reativando cálculos automáticos e atualizando fórmulas da Tabela...", flush=True)
            app.calculation = 'automatic'  
            
            print(f"[EXPORT] Salvando arquivo...", flush=True)
            wb.save()
            print(f"[SUCESSO] Operação finalizada. {novos_adicionados} novas NFs salvas com velocidade e integridade ABSOLUTA.")
        else:
            print("[EXPORT] Processamento concluído. Nenhuma nova NF salva.")
            
    except Exception as e:
        print(f"[ERRO CRÍTICO] Falha ao processar com xlwings: {e}")
        raise e
    finally:
        try:
            app.screen_updating = True
            app.calculation = 'automatic'
        except:
            pass
        try:
            wb.close()
        except:
            pass
        app.quit()