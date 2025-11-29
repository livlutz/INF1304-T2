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
    Subscribe emails to SNS - suporta SQS Trigger e Function URL (HTTP)
    """
    print("Event received by Lambda function: " + json.dumps(event, indent=2))
    
    # Detectar origem do evento
    if 'Records' in event:
        # === TRIGGER SQS (caso queira usar no futuro) ===
        return process_sqs_messages(event)
    else:
        # === FUNCTION URL (HTTP) ou Teste Manual ===
        return process_http_request(event)


def process_http_request(event):
    """Processa requisição HTTP (Function URL ou Teste Console)"""
    try:
        # Parse body
        if 'body' in event:
            body = json.loads(event['body'])
        else:
            body = event
        
        email = body.get('email')
        
        if not email:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'message': 'email é obrigatório.',
                    'email': email
                })
            }
        
        # Subscribe to SNS
        result = subscribe_to_sns(email)
        
        if result['success']:
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'message': result['message'],
                    'email': email,
                    'subscription_arn': result.get('subscription_arn'),
                    'note': 'O usuário precisa confirmar a inscrição clicando no link enviado por email.'
                })
            }
        else:
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'message': result['message']
                })
            }
            
    except Exception as e:
        print(f"An error occurred: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e)})
        }


def process_sqs_messages(event):
    """Processa mensagens SQS (para usar com Trigger SQS no futuro)"""
    successful_messages = []
    failed_messages = []
    
    for record in event['Records']:
        try:
            message_body = json.loads(record['body'])
            email = message_body.get('email')
            
            if not email:
                print(f"❌ Email não encontrado na mensagem: {record['body']}")
                failed_messages.append(record['messageId'])
                continue
            
            print(f"📧 Processando email: {email}")
            
            result = subscribe_to_sns(email)
            
            if result['success']:
                successful_messages.append(record['messageId'])
                print(f"✅ Email {email} inscrito com sucesso")
            else:
                failed_messages.append(record['messageId'])
                print(f"❌ Falha ao inscrever {email}: {result['message']}")
                
        except Exception as e:
            print(f"❌ Erro ao processar mensagem {record['messageId']}: {e}")
            failed_messages.append(record['messageId'])
    
    if failed_messages:
        raise Exception(f"Failed to process {len(failed_messages)} messages")
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'total_messages': len(event['Records']),
            'successful': len(successful_messages),
            'failed': len(failed_messages)
        })
    }


def subscribe_to_sns(email):
    """
    Subscribe email to SNS topic and save to database
    
    Returns:
        dict: {'success': bool, 'message': str, 'subscription_arn': str}
    """
    try:
        # Connect to SNS
        sns = boto3.client('sns')
        alertTopic = 'EnviaEmail'
        
        # Get SNS topic ARN
        snsTopicArn = [t['TopicArn'] for t in sns.list_topics()['Topics']
                      if t['TopicArn'].lower().endswith(':' + alertTopic.lower())][0]
        
        # Subscribe email to SNS
        response = sns.subscribe(
            TopicArn=snsTopicArn,
            Protocol='email',
            Endpoint=email,
            ReturnSubscriptionArn=True
        )
        
        subscription_arn = response.get('SubscriptionArn')
        
        # Save to database
        connection = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        
        try:
            with connection.cursor() as cursor:
                # Create table if not exists
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS consumidor_emailsubscription (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        email VARCHAR(254) UNIQUE NOT NULL,
                        subscription_arn VARCHAR(255),
                        subscribed BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
                
                # Insert or update subscription
                cursor.execute(
                    """
                    INSERT INTO consumidor_emailsubscription (email, subscription_arn, subscribed)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        subscription_arn = %s,
                        subscribed = %s
                    """,
                    (email, subscription_arn, True, subscription_arn, True)
                )
                
                connection.commit()
        finally:
            connection.close()
        
        return {
            'success': True,
            'message': f'Email {email} subscrito com sucesso! Um email de confirmação foi enviado.',
            'subscription_arn': subscription_arn
        }
        
    except IndexError:
        return {
            'success': False,
            'message': f'SNS Topic "{alertTopic}" não encontrado'
        }
    except boto3.exceptions.Boto3Error as e:
        print(f"Error subscribing to SNS: {e}")
        return {
            'success': False,
            'message': f'Erro ao inscrever no SNS: {str(e)}'
        }
    except pymysql.MySQLError as e:
        print(f"Error connecting to MySQL: {e}")
        return {
            'success': False,
            'message': f'Erro de conexão MySQL: {str(e)}'
        }
    except Exception as e:
        print(f"An error occurred: {e}")
        return {
            'success': False,
            'message': f'Erro: {str(e)}'
        }
