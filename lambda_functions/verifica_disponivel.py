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
    Verifica se o item está disponível no estoque.
    Se disponível, envia email para o cliente ir buscar.
    Se não disponível, registra interesse e notificará quando chegar.
    """
    # Show the incoming event in the debug log
    print("Event received by Lambda function: " + json.dumps(event, indent=2))

    log = json.loads(event['body'])
    # Parse the event body to get the parameters
    produto_id = log.get('produto_id')
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

    try:
        # Connect to RDS MySQL
        connection = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )

        with connection.cursor() as cursor:
            # Busca o produto pelo ID e verifica disponibilidade
            cursor.execute(
                "SELECT id, nome, quantidade_estoque, disponivel FROM consumidor_item WHERE id = %s",
                (produto_id,)
            )
            result = cursor.fetchone()

            if result:
                produto_id_db, nome, quantidade, disponivel = result

                # Verifica se está disponível (em estoque e com quantidade > 0)
                if disponivel and quantidade > 0:
                    # Produto DISPONÍVEL - enviar email para o cliente ir buscar
                    message = f"Boa notícia! O produto '{nome}' está disponível na padaria! Temos {quantidade} unidades em estoque. Venha buscar o seu!"

                    # Connect to SNS
                    sns = boto3.client('sns')
                    alertTopic = 'ProdutoDisponivel'
                    try:
                        snsTopicArn = [t['TopicArn'] for t in sns.list_topics()['Topics']
                                      if t['TopicArn'].lower().endswith(':' + alertTopic.lower())][0]

                        # Send message to SNS
                        sns.publish(
                            TopicArn=snsTopicArn,
                            Message=message,
                            Subject='Produto Disponível na Padaria!',
                            MessageStructure='raw',
                            MessageAttributes={
                                'recipient': {
                                    'DataType': 'String',
                                    'StringValue': str(email)
                                }
                            }
                        )

                        return {
                            'statusCode': 200,
                            'body': json.dumps({
                                'message': f'{nome} está disponível! Email enviado para {email}.',
                                'produto': nome,
                                'quantidade_estoque': quantidade,
                                'disponivel': True
                            })
                        }

                    except boto3.exceptions.Boto3Error as e:
                        print(f"Error sending SNS message: {e}")
                        return {
                            'statusCode': 500,
                            'body': json.dumps(f"Error sending SNS message: {str(e)}")
                        }
                else:
                    # Produto NÃO DISPONÍVEL - registrar interesse
                    message = f"Desculpe, '{nome}' não está disponível no momento. Vamos te notificar quando chegar!"

                    # Registra o interesse do cliente (inserir na tabela de notificações)
                    cursor.execute(
                        """
                        INSERT INTO consumidor_notificacao (email_cliente, item_id, notificado)
                        VALUES (%s, %s, %s)
                        ON DUPLICATE KEY UPDATE notificado = FALSE
                        """,
                        (email, produto_id, False)
                    )
                    connection.commit()

                    return {
                        'statusCode': 404,
                        'body': json.dumps({
                            'message': message,
                            'produto': nome,
                            'disponivel': False,
                            'interesse_registrado': True
                        })
                    }
            else:
                return {
                    'statusCode': 404,
                    'body': json.dumps({
                        'message': f'Produto com ID {produto_id} não encontrado.',
                        'produto_id': produto_id
                    })
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
        'body': json.dumps('Function ran without errors.')
    }