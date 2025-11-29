import json
import boto3
import pymysql
import os

# RDS MySQL connection details
host = os.getenv('DB_HOST')
user = os.getenv('DB_USER')
password = os.getenv('DB_PASSWORD')
database = os.getenv('DB_NAME')

def lambda_handler(event, context):
    """
    Envia email para clientes que estavam esperando por um produto que acabou de chegar.
    Esta função é chamada quando produtos são entregues/reabastecidos.
    """
    # Show the incoming event in the debug log
    print("Event received by Lambda function: " + json.dumps(event, indent=2))

    # Parse event - pode vir de HTTP (com body) ou de outra Lambda (direto)
    if "body" in event and event["body"] is not None:
        # Chamada via HTTP (Function URL)
        if isinstance(event["body"], str):
            log = json.loads(event["body"])
        else:
            log = event["body"]
    else:
        # Chamada direta (de outra Lambda ou teste console)
        log = event

    # Parse the event body to get the product ID
    produto_id = log.get('produto_id')

    if not produto_id:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'produto_id é obrigatório.',
                'produto_id': produto_id
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

        emails_enviados = 0
        produto_nome = None

        with connection.cursor() as cursor:
            # Busca informações do produto
            cursor.execute(
                "SELECT nome, quantidade_estoque, disponivel FROM consumidor_item WHERE id = %s",
                (produto_id,)
            )
            produto = cursor.fetchone()

            if not produto:
                return {
                    'statusCode': 404,
                    'body': json.dumps({
                        'message': f'Produto com ID {produto_id} não encontrado.'
                    })
                }

            produto_nome, quantidade, disponivel = produto

            # Verifica se o produto está disponível
            if not disponivel or quantidade <= 0:
                return {
                    'statusCode': 400,
                    'body': json.dumps({
                        'message': f'Produto {produto_nome} ainda não está disponível.',
                        'produto': produto_nome,
                        'quantidade_estoque': quantidade
                    })
                }

            # Busca todos os clientes que querem ser notificados sobre este produto
            cursor.execute(
                """
                SELECT email_cliente
                FROM consumidor_notificacao
                WHERE item_id = %s AND notificado = FALSE
                """,
                (produto_id,)
            )
            clientes = cursor.fetchall()

            if not clientes:
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'message': f'Nenhum cliente aguardando notificação para {produto_nome}.',
                        'emails_enviados': 0
                    })
                }

            # Connect to SNS
            sns = boto3.client('sns')
            alertTopic = 'ProdutoDisponivel'

            try:
                snsTopicArn = [t['TopicArn'] for t in sns.list_topics()['Topics']
                              if t['TopicArn'].lower().endswith(':' + alertTopic.lower())][0]

                # Envia email para cada cliente que solicitou notificação para este produto específico
                print(f"Found SNS topic ARN: {snsTopicArn}")
                for cliente in clientes:
                    email = cliente[0]

                    # Verifica se o email está inscrito no SNS
                    cursor.execute(
                        """
                        SELECT subscribed
                        FROM consumidor_emailsubscription
                        WHERE email = %s AND subscribed = TRUE
                        """,
                        (email,)
                    )
                    subscription = cursor.fetchone()

                    if not subscription:
                        print(f"Email {email} não está inscrito no SNS. Pulando...")
                        continue

                    message = f"Boa notícia! O produto '{produto_nome}' que você estava esperando acabou de chegar na padaria! Temos {quantidade} unidades disponíveis. Venha buscar o seu!"

                    try:
                        print(f"Publishing to SNS topic {snsTopicArn} for recipient {email}")
                        resp = sns.publish(
                            TopicArn=snsTopicArn,
                            Message=message,
                            Subject=f'{produto_nome} disponível na Padaria!'
                        )
                        print(f"SNS publish response: {resp}")

                        # Marca como notificado
                        cursor.execute(
                            """
                            UPDATE consumidor_notificacao
                            SET notificado = TRUE
                            WHERE item_id = %s AND email_cliente = %s
                            """,
                            (produto_id, email)
                        )

                        emails_enviados += 1
                        print(f"Email enviado (SNS) para {email}")

                    except Exception as e:
                        # Log full exception for CloudWatch
                        print(f"Error publishing to SNS for {email}: {type(e).__name__}: {e}")
                        # don't re-raise, continue with next recipient
                        continue

                # Commit DB changes after attempting all publishes
                connection.commit()

            except boto3.exceptions.Boto3Error as e:
                print(f"Error accessing SNS: {e}")
                return {
                    'statusCode': 500,
                    'body': json.dumps(f"Error accessing SNS: {str(e)}")
                }

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
            'message': f'Emails enviados com sucesso para clientes aguardando {produto_nome}!',
            'produto': produto_nome,
            'emails_enviados': emails_enviados,
            'quantidade_estoque': quantidade
        })
    }