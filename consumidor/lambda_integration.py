"""
Integração com AWS Lambda Functions
"""
import os
import json
import requests
import boto3

SUBSCRIBE_EMAIL_URL = os.getenv('SUBSCRIBE_EMAIL_URL', '')
SUBSCRIBE_EMAIL_QUEUE_URL = os.getenv('SUBSCRIBE_EMAIL_QUEUE_URL', '')
VERIFICA_DISPONIVEL_URL = os.getenv('VERIFICA_DISPONIVEL_URL', '')
VENDA_PRODUTOS_URL = os.getenv('VENDA_PRODUTOS_URL', '')
ENTREGA_PRODUTO_URL = os.getenv('ENTREGA_PRODUTO_URL', '')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
USE_SQS_TRIGGER = os.getenv('USE_SQS_TRIGGER', 'false').lower() == 'true'


def subscribe_email_to_sns(email):
    """
    Inscreve email no SNS via SQS (trigger) ou Function URL (HTTP direto)
    
    Args:
        email: Email do usuário a ser inscrito
        
    Returns:
        dict: {'success': bool, 'message': str}
    """
    if USE_SQS_TRIGGER:
        return subscribe_via_sqs(email)
    else:
        return subscribe_via_http(email)


def subscribe_via_sqs(email):
    """
    Envia mensagem para fila SQS que ativará o trigger da Lambda
    
    Args:
        email: Email do usuário a ser inscrito
        
    Returns:
        dict: {'success': bool, 'message': str}
    """
    if not SUBSCRIBE_EMAIL_QUEUE_URL:
        print("⚠️ SUBSCRIBE_EMAIL_QUEUE_URL não configurada no .env")
        return {
            'success': False,
            'message': 'SQS Queue URL não configurada'
        }
    
    try:
        sqs = boto3.client('sqs', region_name=AWS_REGION)
        
        message_body = json.dumps({'email': email})
        
        response = sqs.send_message(
            QueueUrl=SUBSCRIBE_EMAIL_QUEUE_URL,
            MessageBody=message_body
        )
        
        print(f"✅ Mensagem enviada para SQS: {response.get('MessageId')}")
        
        return {
            'success': True,
            'message': 'Email enviado para processamento via SQS',
            'message_id': response.get('MessageId')
        }
        
    except Exception as e:
        print(f"❌ Erro ao enviar mensagem SQS: {e}")
        return {
            'success': False,
            'message': f'Erro ao enviar para SQS: {str(e)}'
        }


def subscribe_via_http(email):
    """
    Chama Lambda subscribe_email via Function URL para inscrever email no SNS
    
    Args:
        email: Email do usuário a ser inscrito
        
    Returns:
        dict: {'success': bool, 'message': str}
    """
    if not SUBSCRIBE_EMAIL_URL:
        print("⚠️ SUBSCRIBE_EMAIL_URL não configurada no .env")
        return {
            'success': False,
            'message': 'Lambda URL não configurada'
        }
    
    try:
        # Function URL recebe payload direto (não precisa wrapper 'body')
        payload = {'email': email}
        
        response = requests.post(
            SUBSCRIBE_EMAIL_URL,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                'success': True,
                'message': data.get('message', 'Email inscrito com sucesso'),
                'subscription_arn': data.get('subscription_arn')
            }
        else:
            return {
                'success': False,
                'message': f'Erro HTTP {response.status_code}: {response.text}'
            }
            
    except requests.exceptions.Timeout:
        print(f"❌ Timeout ao chamar Lambda subscribe_email")
        return {
            'success': False,
            'message': 'Timeout na chamada da Lambda'
        }
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de rede ao chamar Lambda: {e}")
        return {
            'success': False,
            'message': f'Erro de rede: {str(e)}'
        }
    except Exception as e:
        print(f"❌ Erro inesperado ao chamar Lambda: {e}")
        return {
            'success': False,
            'message': str(e)
        }


def verifica_disponivel(produto_id, email):
    """
    Chama Lambda verifica_disponivel para verificar se produto está disponível
    
    Args:
        produto_id: ID do produto
        email: Email do cliente
        
    Returns:
        dict: {'success': bool, 'message': str, 'disponivel': bool}
    """
    if not VERIFICA_DISPONIVEL_URL:
        print("⚠️ VERIFICA_DISPONIVEL_URL não configurada no .env")
        return {
            'success': False,
            'message': 'Lambda URL não configurada',
            'disponivel': False
        }
    
    try:
        # Function URL recebe payload direto (não precisa wrapper 'body')
        payload = {
            'produto_id': produto_id,
            'email': email
        }
        
        response = requests.post(
            VERIFICA_DISPONIVEL_URL,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        data = response.json()
        
        if response.status_code == 200:
            return {
                'success': True,
                'message': data.get('message'),
                'disponivel': True,
                'produto': data.get('produto'),
                'quantidade_estoque': data.get('quantidade_estoque')
            }
        elif response.status_code == 404:
            return {
                'success': True,
                'message': data.get('message'),
                'disponivel': False,
                'produto': data.get('produto'),
                'interesse_registrado': data.get('interesse_registrado', False)
            }
        else:
            return {
                'success': False,
                'message': f'Erro HTTP {response.status_code}: {response.text}',
                'disponivel': False
            }
            
    except Exception as e:
        print(f"❌ Erro ao chamar Lambda verifica_disponivel: {e}")
        return {
            'success': False,
            'message': str(e),
            'disponivel': False
        }


def processar_venda(produto_id, quantidade, email):
    """
    Chama Lambda venda_produtos para processar uma venda
    
    Args:
        produto_id: ID do produto
        quantidade: Quantidade a vender
        email: Email do cliente
        
    Returns:
        dict: {'success': bool, 'message': str}
    """
    if not VENDA_PRODUTOS_URL:
        print("⚠️ VENDA_PRODUTOS_URL não configurada no .env")
        return {
            'success': False,
            'message': 'Lambda URL não configurada'
        }
    
    try:
        # Function URL recebe payload direto (não precisa wrapper 'body')
        payload = {
            'produto_id': produto_id,
            'quantidade': quantidade,
            'email': email
        }
        
        print(f"📤 Enviando para Lambda venda_produtos: {payload}")
        
        response = requests.post(
            VENDA_PRODUTOS_URL,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"📥 Resposta Lambda (status {response.status_code}): {response.text}")
        
        data = response.json()
        
        if response.status_code == 200:
            return {
                'success': True,
                'message': data.get('message'),
                'produto': data.get('produto'),
                'quantidade_vendida': data.get('quantidade_vendida'),
                'estoque_restante': data.get('estoque_restante'),
                'disponivel': data.get('disponivel')
            }
        else:
            return {
                'success': False,
                'message': data.get('message', f'Erro HTTP {response.status_code}')
            }
            
    except Exception as e:
        print(f"❌ Erro ao chamar Lambda venda_produtos: {e}")
        return {
            'success': False,
            'message': str(e)
        }


def entregar_produtos():
    """
    Chama Lambda entrega_produto para popular o banco com novos produtos
    
    Returns:
        dict: {'success': bool, 'message': str}
    """
    if not ENTREGA_PRODUTO_URL:
        print("⚠️ ENTREGA_PRODUTO_URL não configurada no .env")
        return {
            'success': False,
            'message': 'Lambda URL não configurada'
        }
    
    try:
        # Function URL recebe payload direto (vazio para esta Lambda)
        payload = {}
        
        response = requests.post(
            ENTREGA_PRODUTO_URL,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        data = response.json()
        
        if response.status_code == 200:
            return {
                'success': True,
                'message': data.get('mensagem'),
                'produtos_inseridos': data.get('produtos_inseridos'),
                'produtos_atualizados': data.get('produtos_atualizados'),
                'total_produtos': data.get('total_produtos')
            }
        else:
            return {
                'success': False,
                'message': f'Erro HTTP {response.status_code}: {response.text}'
            }
            
    except Exception as e:
        print(f"❌ Erro ao chamar Lambda entrega_produto: {e}")
        return {
            'success': False,
            'message': str(e)
        }
