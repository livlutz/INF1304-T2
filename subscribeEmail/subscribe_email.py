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
    Subscribe a new user email to SNS topic when they register or make their first reservation.
    This function should be triggered when a new email is added to the database.
    """
    # Show the incoming event in the debug log
    print("Event received by Lambda function: " + json.dumps(event, indent=2))

    log = json.loads(event['body'])
    # Parse the event body to get the email
    email = log.get('email')

    if not email:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'email é obrigatório.',
                'email': email
            })
        }

    try:
        # Connect to SNS
        sns = boto3.client('sns')
        alertTopic = 'ProdutoDisponivel'

        try:
            # Get the SNS topic ARN
            snsTopicArn = [t['TopicArn'] for t in sns.list_topics()['Topics']
                          if t['TopicArn'].lower().endswith(':' + alertTopic.lower())][0]

            # Subscribe the email to the SNS topic
            response = sns.subscribe(
                TopicArn=snsTopicArn,
                Protocol='email',
                Endpoint=email,
                ReturnSubscriptionArn=True
            )

            subscription_arn = response.get('SubscriptionArn')

            # Connect to RDS MySQL to mark email as subscribed
            connection = pymysql.connect(
                host=host,
                user=user,
                password=password,
                database=database
            )

            with connection.cursor() as cursor:
                # Check if email already exists in subscriptions table
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

                # Insert or update subscription record
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

            connection.close()

            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': f'Email {email} subscrito com sucesso! Um email de confirmação foi enviado.',
                    'email': email,
                    'subscription_arn': subscription_arn,
                    'note': 'O usuário precisa confirmar a inscrição clicando no link enviado por email.'
                })
            }

        except IndexError:
            return {
                'statusCode': 404,
                'body': json.dumps({
                    'message': f'SNS Topic "{alertTopic}" não encontrado.',
                    'topic': alertTopic
                })
            }

        except boto3.exceptions.Boto3Error as e:
            print(f"Error subscribing to SNS: {e}")
            return {
                'statusCode': 500,
                'body': json.dumps(f"Error subscribing to SNS: {str(e)}")
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
