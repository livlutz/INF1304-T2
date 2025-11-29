import json
import boto3
import pymysql
import os

# Cria cliente Lambda
lambda_client = boto3.client('lambda')

# RDS MySQL connection details
host = os.getenv('DB_HOST')
user = os.getenv('DB_USER')
password = os.getenv('DB_PASSWORD')
database = os.getenv('DB_NAME')

def lambda_handler(event, context):
    """
    Processa a venda de um produto: diminui o estoque e registra a venda.
    """
    # Show the incoming event in the debug log
    print("Event received by Lambda function: " + json.dumps(event, indent=2))

    # Parse the event body to get the parameters
    if 'body' not in event or event['body'] is None:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'Body é obrigatório. Envie um POST request com JSON contendo produto_id, quantidade e email.'
            })
        }

    if "body" in event:
        log = json.loads(event["body"])
    else:
        log = event
    produto_id = log.get('produto_id')
    quantidade = log.get('quantidade', 1)  # Default 1 unidade
    email = log.get('email')

    if not produto_id or not email:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'produto_id e email são obrigatórios.',
                'produto_id': produto_id,
                'email': email
            })
        }

    if quantidade <= 0:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'quantidade deve ser maior que 0.',
                'quantidade': quantidade
            })
        }

    try:
        # Connect to RDS MySQL
        connection = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )

        with connection.cursor() as cursor:
            # Busca o produto e verifica estoque
            cursor.execute(
                "SELECT id, nome, quantidade_estoque, disponivel FROM consumidor_item WHERE id = %s",
                (produto_id,)
            )
            result = cursor.fetchone()

            if not result:
                return {
                    'statusCode': 404,
                    'body': json.dumps({
                        'message': f'Produto com ID {produto_id} não encontrado.'
                    })
                }

            produto_id_db, nome, quantidade_estoque, disponivel = result

            # Verifica se tem estoque suficiente
            if quantidade_estoque < quantidade:
                return {
                    'statusCode': 400,
                    'body': json.dumps({
                        'message': f'Estoque insuficiente. Apenas {quantidade_estoque} unidades disponíveis.',
                        'produto': nome,
                        'quantidade_solicitada': quantidade,
                        'quantidade_disponivel': quantidade_estoque
                    })
                }

            # Atualiza o estoque (diminui a quantidade)
            nova_quantidade = quantidade_estoque - quantidade
            novo_status_disponivel = nova_quantidade > 0

            cursor.execute(
                """
                UPDATE consumidor_item
                SET quantidade_estoque = %s, disponivel = %s
                WHERE id = %s
                """,
                (nova_quantidade, novo_status_disponivel, produto_id)
            )

            # Registra a reserva/venda
            cursor.execute(
                """
                INSERT INTO consumidor_reserva (item_id, email_cliente, quantidade, confirmado)
                VALUES (%s, %s, %s, %s)
                """,
                (produto_id, email, quantidade, True)
            )

            connection.commit()

            print(f"Venda processada: {quantidade}x {nome} para {email}")

            # Envia email de retirada via SNS
            try:
                sns = boto3.client('sns', region_name=os.getenv('AWS_REGION', 'us-east-1'))
                alertTopic = 'EnviaEmail'
                snsTopicArn = [t['TopicArn'] for t in sns.list_topics()['Topics']
                              if t['TopicArn'].lower().endswith(':' + alertTopic.lower())][0]

                subject = f'Seu pedido está pronto para retirada - {nome}'
                message = f"""
Olá,

Seu pedido foi confirmado com sucesso!

Detalhes do pedido:
- Produto: {nome}
- Quantidade: {quantidade}
- Estoque restante: {nova_quantidade}

Você pode retirar seu produto na padaria agora mesmo.

Atenciosamente,
Quitute nas Nuvens
"""
                response = sns.publish(
                    TopicArn=snsTopicArn,
                    Message=message,
                    Subject=subject
                )
                print(f"📧 Email de retirada enviado via SNS para {email}: {response}")
            except Exception as e:
                print(f"❌ Erro ao enviar email de retirada para {email}: {e}")



    except pymysql.MySQLError as e:
        print(f"Error connecting to MySQL: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"MySQL connection error: {str(e)}")
        }
    except KeyError as e:
        print(f"Key error: {e}")
        return {
            'statusCode': 400,
            'body': json.dumps(f"Missing parameter: {str(e)}")
        }
    except Exception as e:
        print(f"An error occurred: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error: {str(e)}")
        }
    finally:
        connection.close()

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': f'Venda processada com sucesso!',
            'produto': nome,
            'quantidade_vendida': quantidade,
            'estoque_restante': nova_quantidade,
            'disponivel': novo_status_disponivel,
            'email': email
        })
    }