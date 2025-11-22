import json
import boto3
import pymysql

# Cria cliente Lambda
lambda_client = boto3.client('lambda')

# RDS MySQL connection details
host = 'padaria-db.cyzbfkdaor1i.us-east-1.rds.amazonaws.com'
user = "padaria_livia"
password = "P$dAr1$12345"
database = "padaria-db"

# Produtos a cada entrega
PRODUTOS_PADARIA = [
    {"id": 1, "nome": "pão francês", "quantidade": 8},
    {"id": 2, "nome": "croissant", "quantidade": 5},
    {"id": 3, "nome": "pao careca", "quantidade": 7},
    {"id": 4, "nome": "brioche", "quantidade": 4},
    {"id": 5, "nome": "pao de queijo", "quantidade": 9},
    {"id": 6, "nome": "joelho", "quantidade": 6},
    {"id": 7, "nome": "coxinha", "quantidade": 8},
    {"id": 8, "nome": "sonho", "quantidade": 5},
    {"id": 9, "nome": "bolo de chocolate", "quantidade": 3},
    {"id": 10, "nome": "bolo de cenoura", "quantidade": 4},
    {"id": 11, "nome": "torta de limao", "quantidade": 2},
    {"id": 12, "nome": "cookie de chocolate", "quantidade": 9},
    {"id": 13, "nome": "brigadeiro gigante", "quantidade": 3},
    {"id": 14, "nome": "cheesecake", "quantidade": 2},
    {"id": 15, "nome": "muffin quentinho", "quantidade": 7},
    {"id": 16, "nome": "empada", "quantidade": 6},
    {"id": 17, "nome": "quiche", "quantidade": 3},
    {"id": 18, "nome": "pão doce", "quantidade": 8},
    {"id": 19, "nome": "torta de maçã", "quantidade": 4},
    {"id": 20, "nome": "brownie", "quantidade": 6},
]

def armazena_produtos_rds(produtos: list) -> dict:
    """
    Armazena os produtos no banco de dados RDS MySQL
    :param produtos: lista de produtos da padaria
    :returns: dicionário com contagem de produtos inseridos/atualizados
    """
    try:
        # Conecta com RDS MySQL
        connection = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )

        produtos_inseridos = 0
        produtos_atualizados = 0

        with connection.cursor() as cursor:
            # Armazena os produtos no banco de dados
            for produto in produtos:
                try:
                    cursor.execute(
                        """
                        INSERT INTO consumidor_item (id, nome, quantidade_estoque, disponivel)
                        VALUES (%s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            quantidade_estoque = quantidade_estoque + %s,
                            disponivel = %s
                        """,
                        (
                            produto['id'],
                            produto['nome'],
                            produto['quantidade'],
                            True,
                            produto['quantidade'],
                            True
                        )
                    )

                    if cursor.rowcount == 1:
                        produtos_inseridos += 1
                    else:
                        produtos_atualizados += 1

                except pymysql.MySQLError as e:
                    print(f"Erro ao inserir produto {produto['nome']}: {e}")
                    continue

            connection.commit()

        connection.close()
        print(f"Dados armazenados no RDS com sucesso! Inseridos: {produtos_inseridos}, Atualizados: {produtos_atualizados}")

        return {
            'inseridos': produtos_inseridos,
            'atualizados': produtos_atualizados
        }

    except Exception as e:
        print(e)
        print(f"Erro ao armazenar dados no RDS: {str(e)}")
        raise


def lambda_handler(event, context):
    """
    Recebe evento e popula o banco de dados com produtos da padaria
    """
    try:
        # Log do evento recebido
        print("Event received by Lambda function: " + json.dumps(event, indent=2))

        # Armazena produtos no RDS
        resultado = armazena_produtos_rds(PRODUTOS_PADARIA)

        response = {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "mensagem": "Produtos entregues com sucesso!",
                "produtos_inseridos": resultado['inseridos'],
                "produtos_atualizados": resultado['atualizados'],
                "total_produtos": len(PRODUTOS_PADARIA)
            })
        }

        return response

    except Exception as e:
        
        return {
            "statusCode": 400,
            "body": json.dumps({"error": str(e)})
        }