# 🚀 Passo a Passo - Integração do Projeto Quitute nas Nuvens

## 📋 Pré-requisitos

- Conta AWS ativa
- Python 3.11+ instalado
- Git instalado
- Acesso ao terminal/linha de comando

---

## 🔧 PARTE 1: Configuração Inicial Local

### Passo 1: Clonar o Repositório

```bash
git clone https://github.com/livlutz/INF1304-T2.git
cd INF1304-T2
```

### Passo 2: Criar Ambiente Virtual Python

```bash
# Linux/Mac
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### Passo 3: Instalar Dependências

```bash
pip install -r requirements.txt
```

---

## ☁️ PARTE 2: Configuração AWS

### Passo 4: Criar Banco de Dados RDS MySQL

1. **Acessar AWS Console → RDS**
   - URL: https://console.aws.amazon.com/rds/

2. **Criar banco de dados:**
   - Clique em **"Create database"**
   - Escolha **"Standard create"**
   - **Engine type:** MySQL
   - **Version:** MySQL 8.0.x (ou mais recente)
   - **Templates:** Free tier (para teste) ou Production (para produção)

3. **Settings:**
   - **DB instance identifier:** `padaria-db`
   - **Master username:** `padaria_livia` (ou outro de sua preferência)
   - **Master password:** Crie uma senha forte e **anote-a**

4. **Instance configuration:**
   - **DB instance class:** db.t3.micro (Free tier eligible)
   - **Storage type:** General Purpose SSD (gp2)
   - **Allocated storage:** 20 GB

5. **Connectivity:**
   - **Public access:** Yes (para desenvolvimento)
   - **VPC security group:** Create new
   - **Security group name:** `padaria-db-sg`
   - **VPC:** Default VPC

6. **Additional configuration:**
   - **Initial database name:** `padaria-db`
   - Desmarque "Enable automated backups" (para desenvolvimento)

7. **Clique em "Create database"**
   - ⏳ Aguarde 5-10 minutos até o status ficar "Available"

8. **Anotar o Endpoint:**
   - Após criação, clique no banco de dados
   - Na aba "Connectivity & security", copie o **Endpoint**
   - Exemplo: `padaria-db.cyzbfkdaor1i.us-east-1.rds.amazonaws.com`

9. **Configurar Security Group:**
   - Clique no security group vinculado ao RDS
   - Vá em **"Inbound rules"** → **"Edit inbound rules"**
   - **Add rule:**
     - Type: MySQL/Aurora
     - Protocol: TCP
     - Port: 3306
     - Source: **0.0.0.0/0** (para desenvolvimento - em produção, restringir IPs)
   - Salve as regras

### Passo 5: Configurar Amazon SNS (Notificações por Email)

1. **Acessar AWS Console → SNS**
   - URL: https://console.aws.amazon.com/sns/

2. **Criar Tópico SNS:**
   - Clique em **"Topics"** → **"Create topic"**
   - **Type:** Standard
   - **Name:** `ProdutoDisponivel`
   - **Display name:** Padaria - Produto Disponível
   - Clique em **"Create topic"**

3. **Anotar o ARN do Tópico:**
   - Copie o **ARN** exibido
   - Exemplo: `arn:aws:sns:us-east-1:123456789012:ProdutoDisponivel`

4. **Criar Subscription (Inscrição de Email):**
   - No tópico criado, clique em **"Create subscription"**
   - **Protocol:** Email
   - **Endpoint:** Seu email (ex: `seuemail@exemplo.com`)
   - Clique em **"Create subscription"**

5. **Confirmar Subscription:**
   - Verifique sua caixa de entrada
   - Abra o email da AWS SNS
   - Clique em **"Confirm subscription"**
   - ✅ Status deve mudar para "Confirmed"

### Passo 6: Criar Função IAM para Lambda

1. **Acessar AWS Console → IAM**
   - URL: https://console.aws.amazon.com/iam/

2. **Criar Role:**
   - Vá em **"Roles"** → **"Create role"**
   - **Trusted entity type:** AWS service
   - **Use case:** Lambda
   - Clique em **"Next"**

3. **Adicionar Permissions:**
   - Busque e selecione as seguintes policies:
     - ✅ `AWSLambdaBasicExecutionRole`
     - ✅ `AmazonSNSFullAccess`
     - ✅ `AWSLambdaVPCAccessExecutionRole` (se usar VPC)
   - Clique em **"Next"**

4. **Nome e Criação:**
   - **Role name:** `LambdaPadariaRole`
   - **Description:** Role para funções Lambda da padaria
   - Clique em **"Create role"**

5. **Adicionar Permissões Inline para RDS:**
   - Abra a role criada
   - Vá em **"Add permissions"** → **"Create inline policy"**
   - Clique em **"JSON"** e cole:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "rds-db:connect"
            ],
            "Resource": "*"
        }
    ]
}
```

   - Clique em **"Review policy"**
   - **Name:** `RDSConnectPolicy`
   - Clique em **"Create policy"**

---

## 🔑 PARTE 3: Configuração de Variáveis de Ambiente

### Passo 7: Criar Arquivo .env Local

1. **Na raiz do projeto**, crie um arquivo `.env`:

```bash
touch .env  # Linux/Mac
# ou
type nul > .env  # Windows
```

2. **Abra o arquivo `.env` e adicione:**

```env
# Configurações do RDS MySQL
DB_HOST=seu-endpoint-rds.us-east-1.rds.amazonaws.com
DB_USER=padaria_livia
DB_PASSWORD=sua_senha_forte
DB_NAME=padaria-db
DB_PORT=3306

# AWS Credentials (opcional - se não estiver usando AWS CLI configurado)
AWS_ACCESS_KEY_ID=sua_access_key
AWS_SECRET_ACCESS_KEY=sua_secret_key
AWS_DEFAULT_REGION=us-east-1
```

3. **Substitua os valores:**
   - `DB_HOST`: Endpoint do RDS copiado no Passo 4
   - `DB_PASSWORD`: Senha definida na criação do RDS
   - AWS credentials (se necessário)

### Passo 8: Executar Migrações do Django

```bash
# Com o ambiente virtual ativado
python manage.py migrate

# Verificar se as tabelas foram criadas
python manage.py dbshell
# No shell MySQL:
SHOW TABLES;
# Deve mostrar: consumidor_item, consumidor_reserva, consumidor_notificacao
# Digite 'exit' para sair
```

---

## λ PARTE 4: Deploy das Funções Lambda

### Passo 9: Preparar Pacotes Lambda

Cada função Lambda precisa ser empacotada com suas dependências.

#### 9.1: Criar Diretório de Build

```bash
mkdir lambda_builds
cd lambda_builds
```

#### 9.2: Empacotar Função `entrega_de_produtos`

```bash
# Criar diretório para a função
mkdir entrega_de_produtos
cd entrega_de_produtos

# Instalar dependências
pip install pymysql boto3 -t .

# Copiar o código da função
cp ../../lambda_functions/entrega_de_produtos.py .

# Criar arquivo ZIP
zip -r9 ../entrega_de_produtos.zip .

cd ..
```

#### 9.3: Empacotar Função `verifica_disponivel`

```bash
mkdir verifica_disponivel
cd verifica_disponivel

pip install pymysql boto3 -t .
cp ../../lambda_functions/verifica_disponivel.py lambda_function.py

zip -r9 ../verifica_disponivel.zip .
cd ..
```

#### 9.4: Empacotar Função `envia_email_interessados`

```bash
mkdir envia_email_interessados
cd envia_email_interessados

pip install pymysql boto3 -t .
cp ../../lambda_functions/envia_email_interessados.py lambda_function.py

zip -r9 ../envia_email_interessados.zip .
cd ..
```

#### 9.5: Empacotar Função `venda_de_produtos`

```bash
mkdir venda_de_produtos
cd venda_de_produtos

pip install pymysql boto3 -t .
cp ../../lambda_functions/venda_de_produtos.py lambda_function.py

zip -r9 ../venda_de_produtos.zip .
cd ..
```

### Passo 10: Fazer Upload das Funções Lambda

#### 10.1: Criar Função `entrega_de_produtos`

1. **Acessar AWS Console → Lambda**
   - URL: https://console.aws.amazon.com/lambda/

2. **Clique em "Create function"**
   - **Function name:** `entrega_de_produtos`
   - **Runtime:** Python 3.11
   - **Architecture:** x86_64
   - **Permissions:** Use an existing role → `LambdaPadariaRole`
   - Clique em **"Create function"**

3. **Upload do Código:**
   - Na seção **"Code source"**, clique em **"Upload from"** → **".zip file"**
   - Selecione `lambda_builds/entrega_de_produtos.zip`
   - Clique em **"Save"**

4. **Configurar Handler:**
   - Na aba **"Code"**, em **"Runtime settings"**, clique em **"Edit"**
   - **Handler:** `entrega_de_produtos.lambda_handler`
   - Clique em **"Save"**

5. **Configurar Variáveis de Ambiente:**
   - Vá na aba **"Configuration"** → **"Environment variables"**
   - Clique em **"Edit"** → **"Add environment variable"**
   - Adicione (se necessário - o código já tem hardcoded, mas é recomendado usar variáveis):
     ```
     DB_HOST = seu-endpoint-rds.us-east-1.rds.amazonaws.com
     DB_USER = padaria_livia
     DB_PASSWORD = sua_senha
     DB_NAME = padaria-db
     ```

6. **Aumentar Timeout:**
   - Ainda em **"Configuration"** → **"General configuration"** → **"Edit"**
   - **Timeout:** 30 segundos
   - **Memory:** 256 MB
   - Clique em **"Save"**

#### 10.2: Criar Função `verifica_disponivel`

Repita os mesmos passos da seção 10.1, mas com:
- **Function name:** `verifica_disponivel`
- **Handler:** `lambda_function.lambda_handler`
- **ZIP file:** `verifica_disponivel.zip`

#### 10.3: Criar Função `envia_email_interessados`

Repita os mesmos passos da seção 10.1, mas com:
- **Function name:** `envia_email_interessados`
- **Handler:** `lambda_function.lambda_handler`
- **ZIP file:** `envia_email_interessados.zip`

#### 10.4: Criar Função `venda_de_produtos`

Repita os mesmos passos da seção 10.1, mas com:
- **Function name:** `venda_de_produtos`
- **Handler:** `lambda_function.lambda_handler`
- **ZIP file:** `venda_de_produtos.zip`

### Passo 11: Criar Function URLs (Opcional - para chamar via HTTP)

Para cada função Lambda criada:

1. Abra a função no console Lambda
2. Vá em **"Configuration"** → **"Function URL"**
3. Clique em **"Create function URL"**
4. **Auth type:** NONE (para teste - em produção use AWS_IAM)
5. **CORS:** Marque "Configure cross-origin resource sharing (CORS)"
6. Clique em **"Save"**
7. **Copie a Function URL** gerada (ex: `https://abc123.lambda-url.us-east-1.on.aws/`)

---

## 🧪 PARTE 5: Testar a Integração

### Passo 12: Testar Função `entrega_de_produtos`

1. **No Console Lambda**, abra a função `entrega_de_produtos`
2. Vá na aba **"Test"**
3. Clique em **"Create new event"**
   - **Event name:** `TesteEntrega`
   - **Event JSON:**
   ```json
   {}
   ```
4. Clique em **"Save"**
5. Clique em **"Test"**
6. ✅ **Resultado esperado:**
   ```json
   {
     "statusCode": 200,
     "body": "{\"mensagem\": \"Produtos entregues com sucesso!\", ...}"
   }
   ```

7. **Verificar no Banco de Dados:**
   ```bash
   # No terminal local com .env configurado
   python manage.py dbshell
   ```
   ```sql
   SELECT * FROM consumidor_item LIMIT 5;
   -- Deve listar os produtos inseridos
   ```

### Passo 13: Testar Função `verifica_disponivel`

1. **No Console Lambda**, abra a função `verifica_disponivel`
2. **Event JSON:**
   ```json
   {
     "body": "{\"produto_id\": 1, \"email\": \"seuemail@exemplo.com\"}"
   }
   ```
3. Clique em **"Test"**
4. ✅ **Resultado esperado (produto disponível):**
   ```json
   {
     "statusCode": 200,
     "body": "{\"message\": \"pão francês está disponível! Email enviado...\"}"
   }
   ```
5. **Verifique seu email** - deve receber notificação via SNS

### Passo 14: Iniciar Aplicação Django

```bash
# Volte para o diretório raiz do projeto
cd /home/ubuntu/INF1304-T2

# Ative o ambiente virtual (se não estiver ativo)
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Inicie o servidor
python manage.py runserver

# Ou use o script bash:
./run.sh
```

### Passo 15: Testar Interface Web

1. **Abra o navegador:**
   - `http://localhost:8000` ou `http://127.0.0.1:8000`

2. **Fluxo de teste:**
   - Digite seu email
   - Navegue pelos produtos
   - Clique em um produto disponível
   - Preencha nome e quantidade
   - Clique em "Reservar"
   - ✅ Verifique seu email para confirmação

3. **Testar produto indisponível:**
   - No banco de dados, altere a quantidade de um produto para 0:
   ```sql
   UPDATE consumidor_item SET quantidade_estoque = 0 WHERE id = 5;
   ```
   - Tente reservar este produto
   - ✅ Deve registrar interesse e notificar quando chegar

---

## 🔄 PARTE 6: Fluxo Completo de Operação

### Cenário 1: Cliente Reserva Produto Disponível

1. **Cliente acessa aplicação** → Informa email
2. **Seleciona produto disponível** → Faz reserva
3. **Lambda `verifica_disponivel`** → Verifica estoque
4. **SNS** → Envia email imediato
5. **Cliente vai à padaria** → Retira produto
6. **Lambda `venda_de_produtos`** → Atualiza estoque

### Cenário 2: Cliente Quer Produto Indisponível

1. **Cliente acessa aplicação** → Informa email
2. **Seleciona produto indisponível** → Tenta reservar
3. **Lambda `verifica_disponivel`** → Detecta indisponibilidade
4. **Banco de Dados** → Registra interesse (tabela `consumidor_notificacao`)
5. **Fornecedor entrega produtos** → Lambda `entrega_de_produtos`
6. **Lambda `envia_email_interessados`** → Notifica clientes da fila
7. **Cliente recebe email** → Vai à padaria retirar

### Testar Fluxo Completo:

```bash
# 1. Popular banco com produtos
# Execute Lambda entrega_de_produtos no console AWS

# 2. Zerar estoque de um produto
python manage.py dbshell
UPDATE consumidor_item SET quantidade_estoque = 0, disponivel = 0 WHERE id = 3;
exit

# 3. Registrar interesse (via aplicação web ou Lambda)
# Acesse a aplicação e tente reservar o produto ID 3

# 4. Verificar interesse registrado
python manage.py dbshell
SELECT * FROM consumidor_notificacao WHERE item_id = 3;

# 5. Simular chegada do produto
# Execute novamente Lambda entrega_de_produtos

# 6. Verificar notificações enviadas
SELECT * FROM consumidor_notificacao WHERE item_id = 3 AND notificado = 1;

# 7. Verificar email recebido
```

---

## 🐛 Troubleshooting

### Problema: Erro de conexão com RDS

**Solução:**
```bash
# Verifique:
1. Security Group permite conexões na porta 3306
2. RDS está com "Public accessibility" habilitado
3. Credenciais no .env estão corretas
4. VPC e subnet do RDS permitem conexões externas

# Teste conexão manual:
mysql -h seu-endpoint-rds.us-east-1.rds.amazonaws.com -u padaria_livia -p
```

### Problema: Lambda não consegue acessar RDS

**Solução:**
```bash
# Verifique:
1. Lambda tem a role LambdaPadariaRole
2. Security Group do RDS permite conexões da Lambda
3. Se Lambda estiver em VPC, configure VPC endpoints
4. Timeout da Lambda está adequado (mínimo 30s)
```

### Problema: Emails SNS não chegam

**Solução:**
```bash
# Verifique:
1. Subscription está "Confirmed" no SNS
2. Email não está na caixa de spam
3. Lambda tem permissão SNS na role IAM
4. ARN do tópico está correto no código Lambda
```

### Problema: Erro ao instalar mysqlclient

**Solução:**
```bash
# Ubuntu/Debian:
sudo apt-get install python3-dev default-libmysqlclient-dev build-essential

# Mac:
brew install mysql-client
export PATH="/usr/local/opt/mysql-client/bin:$PATH"

# Windows:
# Baixe e instale MySQL Connector C:
https://dev.mysql.com/downloads/connector/c/
```

---

## 📚 Recursos Adicionais

### Documentação AWS

- **RDS:** https://docs.aws.amazon.com/rds/
- **Lambda:** https://docs.aws.amazon.com/lambda/
- **SNS:** https://docs.aws.amazon.com/sns/
- **IAM:** https://docs.aws.amazon.com/iam/

### Monitoramento

**CloudWatch Logs:**
- Console AWS → CloudWatch → Log groups
- Procure por `/aws/lambda/nome-da-funcao`
- Visualize logs de execução e erros

**Métricas Lambda:**
- Console Lambda → Aba "Monitor"
- Verifique: Invocations, Duration, Errors, Throttles

---

## ✅ Checklist Final

- [ ] RDS MySQL criado e disponível
- [ ] Security Group do RDS configurado (porta 3306)
- [ ] Tópico SNS criado (`ProdutoDisponivel`)
- [ ] Email subscrito e confirmado no SNS
- [ ] Role IAM `LambdaPadariaRole` criada
- [ ] 4 funções Lambda criadas e com código deployed
- [ ] Arquivo `.env` configurado localmente
- [ ] Migrações Django executadas com sucesso
- [ ] Tabelas criadas no RDS (consumidor_item, consumidor_reserva, consumidor_notificacao)
- [ ] Teste de entrega de produtos executado
- [ ] Teste de verificação de disponibilidade executado
- [ ] Email de notificação recebido
- [ ] Aplicação Django rodando em localhost:8000
- [ ] Fluxo completo testado (reserva → email → venda)

---

## 🎯 Próximos Passos (Melhorias)

1. **Segurança:**
   - Usar AWS Secrets Manager para credenciais
   - Restringir Security Groups por IP
   - Adicionar autenticação na aplicação Django

2. **Monitoramento:**
   - Configurar CloudWatch Alarms
   - Criar Dashboard de métricas
   - Implementar logs estruturados

3. **Escalabilidade:**
   - Usar RDS Multi-AZ
   - Implementar cache com ElastiCache
   - Deploy da aplicação Django no Elastic Beanstalk ou ECS

4. **CI/CD:**
   - Configurar GitHub Actions
   - Automatizar deploy de funções Lambda
   - Testes automatizados

---

**🎉 Parabéns!** Sua aplicação Quitute nas Nuvens está totalmente integrada com AWS!
