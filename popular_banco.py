import database as db
import uuid
from datetime import datetime

db.init_db()

# Notas com campo de envio_pgto como DATA (YYYY-MM-DD)
dados_ficticios = [
    {
        "num_nota": "1001",
        "razao_fornecedor": "Tech Solutions LTDA",
        "cnpj_fornecedor": "12.345.678/0001-90",
        "emp_tomador": "Minha Empresa S.A.",
        "cnpj_tomador": "98.765.432/0001-00",
        "data_emissao": "2026-01-10",
        "data_vencimento": "2026-02-10",
        "valor_nf": 5400.00,
        "num_requisicao": "RC-001",
        "id_contrato": "CTR-99",
        "num_pedido": "PED-500",
        "envio_pgto": "2026-01-15", # Data preenchida
        "observacao": "Serviços de TI."
    },
    {
        "num_nota": "2045",
        "razao_fornecedor": "Papelaria Silva",
        "cnpj_fornecedor": "55.444.333/0001-11",
        "emp_tomador": "Minha Empresa S.A.",
        "cnpj_tomador": "98.765.432/0001-00",
        "data_emissao": "2026-01-12",
        "data_vencimento": "2026-01-20",
        "valor_nf": 235.50,
        "num_requisicao": "RC-040",
        "id_contrato": "",
        "num_pedido": "",
        "envio_pgto": "1900-01-01", # Data padrão (Pendente)
        "observacao": "Materiais."
    }
]

print("Inserindo dados novos...")
for nf in dados_ficticios:
    nf['id'] = str(uuid.uuid4())
    nf['responsavel'] = "Script Teste"
    nf['data_registro'] = datetime.now()
    db.salvar_nota(nf)
    print(f"Nota {nf['num_nota']} inserida.")