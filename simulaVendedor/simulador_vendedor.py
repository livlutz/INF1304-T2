import json
import boto3
import pymysql
import random
import os
from datetime import datetime

# RDS MySQL connection details
host = os.getenv('DB_HOST')
user = os.getenv('DB_USER')
password = os.getenv('DB_PASSWORD')
database = os.getenv('DB_NAME')
# Cliente Lambda para chamar a função de envio de emails
lambda_client = boto3.client('lambda')

# Produtos da padaria com quantidades variáveis
PRODUTOS_PADARIA = [
    {"id": 1, "nome": "pão francês"},
    {"id": 2, "nome": "croissant"},
    {"id": 3, "nome": "pao careca"},
    {"id": 4, "nome": "brioche"},
    {"id": 5, "nome": "pao de queijo"},
    {"id": 6, "nome": "joelho"},
    {"id": 7, "nome": "coxinha"},
    {"id": 8, "nome": "sonho"},
    {"id": 9, "nome": "bolo de chocolate"},
    {"id": 10, "nome": "bolo de cenoura"},
    {"id": 11, "nome": "torta de limao"},
    {"id": 12, "nome": "cookie de chocolate"},
    {"id": 13, "nome": "brigadeiro gigante"},
    {"id": 14, "nome": "cheesecake"},
    {"id": 15, "nome": "muffin quentinho"},
    {"id": 16, "nome": "empada"},
    {"id": 17, "nome": "quiche"},
    {"id": 18, "nome": "pão doce"},
    {"id": 19, "nome": "torta de maçã"},
    {"id": 20, "nome": "brownie"},
]

def adicionar_produtos_aleatorios(num_produtos=None):
    """
    Adiciona produtos aleatórios ao estoque com quantidades aleatórias
    :param num_produtos: quantidade de produtos diferentes a adicionar (se None, escolhe aleatoriamente)
    :return: lista de produtos adicionados
    """
    if num_produtos is None:
        # Escolhe aleatoriamente quantos produtos diferentes adicionar (entre 1 e 10)
        num_produtos = random.randint(1, 10)
    
    # Seleciona produtos aleatórios
    produtos_selecionados = random.sample(PRODUTOS_PADARIA, min(num_produtos, len(PRODUTOS_PADARIA)))
    
    # Adiciona quantidade aleatória a cada produto
    produtos_para_adicionar = []
    for produto in produtos_selecionados:
        quantidade_aleatoria = random.randint(2, 15)  # Entre 2 e 15 unidades
        produtos_para_adicionar.append({
            'id': produto['id'],
            'nome': produto['nome'],
            'quantidade': quantidade_aleatoria
        })
    
    return produtos_para_adicionar


def verificar_e_notificar_interessados(produto_id, connection):
    """
    Verifica se há clientes interessados no produto e invoca Lambda de notificação
    :param produto_id: ID do produto que chegou
    :param connection: conexão com o banco de dados
    """
    try:
        with connection.cursor() as cursor:
            # Busca clientes interessados que ainda não foram notificados
            cursor.execute(
                """
                SELECT COUNT(*) as total
                FROM consumidor_notificacao 
                WHERE item_id = %s AND notificado = FALSE
                """,
                (produto_id,)
            )
            result = cursor.fetchone()
            
            if result and result[0] > 0:
                print(f"Encontrados {result[0]} clientes interessados no produto ID {produto_id}")
                
                # Invoca a Lambda de envio de emails
                try:
                    response = lambda_client.invoke(
                        FunctionName='envia_email_interessados',
                        InvocationType='Event',  # Assíncrono
                        Payload=json.dumps({
                            'produto_id': produto_id
                        })
                    )
                    print(f"Lambda envia_email_interessados invocada para produto ID {produto_id}")
                except Exception as e:
                    print(f"Erro ao invocar Lambda de emails: {e}")
                    
    except Exception as e:
        print(f"Erro ao verificar interessados: {e}")


def armazena_produtos_rds(produtos: list) -> dict:
    """
    Armazena os produtos no banco de dados RDS MySQL e notifica interessados
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
        produtos_com_interessados = []

        with connection.cursor() as cursor:
            # Armazena os produtos no banco de dados
            for produto in produtos:
                try:
                    # Verifica se o produto estava indisponível antes
                    cursor.execute(
                        "SELECT quantidade_estoque, disponivel FROM consumidor_item WHERE id = %s",
                        (produto['id'],)
                    )
                    resultado_anterior = cursor.fetchone()
                    estava_indisponivel = resultado_anterior and (resultado_anterior[0] == 0 or not resultado_anterior[1])
                    
                    # Insere ou atualiza o produto
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
                    
                    # Se estava indisponível e agora está disponível, marca para notificar
                    if estava_indisponivel:
                        produtos_com_interessados.append(produto['id'])

                except pymysql.MySQLError as e:
                    print(f"Erro ao inserir produto {produto['nome']}: {e}")
                    continue

            connection.commit()

        # Notifica interessados para produtos que voltaram ao estoque
        for produto_id in produtos_com_interessados:
            verificar_e_notificar_interessados(produto_id, connection)

        connection.close()
        print(f"Dados armazenados no RDS com sucesso! Inseridos: {produtos_inseridos}, Atualizados: {produtos_atualizados}")

        return {
            'inseridos': produtos_inseridos,
            'atualizados': produtos_atualizados,
            'notificacoes_enviadas': len(produtos_com_interessados)
        }

    except Exception as e:
        print(f"Erro ao armazenar dados no RDS: {str(e)}")
        raise


def lambda_handler(event, context):
    """
    Simula fornecedor adicionando produtos aleatoriamente ao estoque
    Pode ser acionado via EventBridge (CloudWatch Events) periodicamente
    """
    try:
        # Log do evento recebido
        print("Event received by Lambda function: " + json.dumps(event, indent=2))
        print(f"Simulação de entrega iniciada em: {datetime.now().isoformat()}")

        # Verifica se foi especificado quantos produtos adicionar
        num_produtos = event.get('num_produtos', None)
        
        # Gera produtos aleatórios
        produtos_para_adicionar = adicionar_produtos_aleatorios(num_produtos)
        
        print(f"Adicionando {len(produtos_para_adicionar)} produtos diferentes ao estoque:")
        for produto in produtos_para_adicionar:
            print(f"  - {produto['nome']}: +{produto['quantidade']} unidades")

        # Armazena produtos no RDS
        resultado = armazena_produtos_rds(produtos_para_adicionar)

        response = {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "mensagem": "Simulação de entrega concluída com sucesso!",
                "timestamp": datetime.now().isoformat(),
                "produtos_adicionados": [
                    {"nome": p['nome'], "quantidade": p['quantidade']} 
                    for p in produtos_para_adicionar
                ],
                "produtos_inseridos": resultado['inseridos'],
                "produtos_atualizados": resultado['atualizados'],
                "notificacoes_enviadas": resultado['notificacoes_enviadas'],
                "total_produtos_diferentes": len(produtos_para_adicionar)
            })
        }

        return response

    except Exception as e:
        print(f"Erro na simulação: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
        }
