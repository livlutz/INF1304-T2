# 🤖 Lambda Simulador de Vendedor - Setup Guide

## 📋 Visão Geral

Esta Lambda simula um fornecedor adicionando produtos aleatoriamente ao estoque da padaria. Ela:

- ✅ Adiciona de 1 a 10 produtos diferentes aleatoriamente
- ✅ Define quantidades aleatórias (2-15 unidades) para cada produto
- ✅ Atualiza o estoque no banco de dados RDS
- ✅ Detecta produtos que voltaram ao estoque
- ✅ **Aciona automaticamente** a Lambda de notificação de interessados
- ✅ Pode ser agendada para executar periodicamente

---

## 🚀 Parte 1: Deploy da Lambda

### Passo 1: Empacotar a Função

```bash
# Na raiz do projeto
cd lambda_builds

# Criar diretório para a função
mkdir simulador_vendedor
cd simulador_vendedor

# Instalar dependências
pip install pymysql boto3 -t .

# Copiar o código da função
cp ../../lambda_functions/simulador_vendedor.py lambda_function.py

# Criar arquivo ZIP
zip -r9 ../simulador_vendedor.zip .

cd ..
```

### Passo 2: Criar a Função Lambda na AWS

1. **Acessar AWS Console → Lambda**
   - URL: https://console.aws.amazon.com/lambda/

2. **Criar função:**
   - Clique em **"Create function"**
   - **Function name:** `simulador_vendedor`
   - **Runtime:** Python 3.11
   - **Architecture:** x86_64
   - **Permissions:** Use an existing role → `LambdaPadariaRole`
   - Clique em **"Create function"**

3. **Upload do código:**
   - Na seção **"Code source"**, clique em **"Upload from"** → **".zip file"**
   - Selecione `lambda_builds/simulador_vendedor.zip`
   - Clique em **"Save"**

4. **Configurar Handler:**
   - Na aba **"Code"**, em **"Runtime settings"**, clique em **"Edit"**
   - **Handler:** `lambda_function.lambda_handler`
   - Clique em **"Save"**

5. **Configurar Timeout e Memória:**
   - Vá em **"Configuration"** → **"General configuration"** → **"Edit"**
   - **Timeout:** 30 segundos
   - **Memory:** 256 MB
   - Clique em **"Save"**

6. **Adicionar Permissão para Invocar Outras Lambdas:**
   - Vá em **"Configuration"** → **"Permissions"**
   - Clique no **Role name** (LambdaPadariaRole)
   - Isso abrirá o IAM
   - Clique em **"Add permissions"** → **"Attach policies"**
   - Busque e selecione: `AWSLambdaRole` (ou crie inline policy abaixo)
   - Clique em **"Add permissions"**

   **OU criar Inline Policy:**
   - Clique em **"Add permissions"** → **"Create inline policy"**
   - Clique em **"JSON"** e cole:
   
   ```json
   {
       "Version": "2012-10-17",
       "Statement": [
           {
               "Effect": "Allow",
               "Action": [
                   "lambda:InvokeFunction"
               ],
               "Resource": [
                   "arn:aws:lambda:*:*:function:envia_email_interessados"
               ]
           }
       ]
   }
   ```
   
   - **Name:** `InvokeLambdaPolicy`
   - Clique em **"Create policy"**

---

## ⏰ Parte 2: Configurar Agendamento Automático (EventBridge)

### Opção A: Executar a Cada X Minutos/Horas

1. **No console da Lambda `simulador_vendedor`:**
   - Vá na aba **"Configuration"** → **"Triggers"**
   - Clique em **"Add trigger"**

2. **Configurar trigger:**
   - **Select a source:** EventBridge (CloudWatch Events)
   - **Rule:** Create a new rule
   - **Rule name:** `SimuladorVendedorAgendado`
   - **Rule description:** Simula entrega de produtos periodicamente
   - **Rule type:** Schedule expression

3. **Escolha a frequência:**

   **A cada 5 minutos:**
   ```
   rate(5 minutes)
   ```

   **A cada 15 minutos:**
   ```
   rate(15 minutes)
   ```

   **A cada 1 hora:**
   ```
   rate(1 hour)
   ```

   **A cada 3 horas:**
   ```
   rate(3 hours)
   ```

   **Todos os dias às 9h (horário UTC):**
   ```
   cron(0 9 * * ? *)
   ```

   **Todos os dias às 9h, 12h e 18h (horário UTC):**
   ```
   cron(0 9,12,18 * * ? *)
   ```

   **De segunda a sexta às 10h (horário UTC):**
   ```
   cron(0 10 ? * MON-FRI *)
   ```

4. **Clique em "Add"**

5. ✅ **Pronto!** A Lambda será executada automaticamente na frequência configurada.

### Opção B: Executar Manualmente com Diferentes Configurações

Você pode testar com diferentes números de produtos:

**Teste 1: Adicionar 3 produtos aleatórios**
```json
{
  "num_produtos": 3
}
```

**Teste 2: Adicionar 10 produtos aleatórios**
```json
{
  "num_produtos": 10
}
```

**Teste 3: Deixar escolher aleatoriamente (1-10)**
```json
{}
```

---

## 🧪 Parte 3: Testar a Função

### Teste Manual no Console

1. **Abrir a função no console Lambda**
2. **Ir na aba "Test"**
3. **Criar evento de teste:**
   - **Event name:** `TesteSimulacao`
   - **Event JSON:**
   ```json
   {
     "num_produtos": 5
   }
   ```
4. **Clicar em "Save"**
5. **Clicar em "Test"**

6. ✅ **Resultado esperado:**
```json
{
  "statusCode": 200,
  "body": {
    "mensagem": "Simulação de entrega concluída com sucesso!",
    "timestamp": "2025-11-26T20:30:00.123456",
    "produtos_adicionados": [
      {"nome": "pão francês", "quantidade": 8},
      {"nome": "croissant", "quantidade": 5},
      {"nome": "brownie", "quantidade": 12},
      {"nome": "coxinha", "quantidade": 7},
      {"nome": "bolo de chocolate", "quantidade": 4}
    ],
    "produtos_inseridos": 0,
    "produtos_atualizados": 5,
    "notificacoes_enviadas": 2,
    "total_produtos_diferentes": 5
  }
}
```

### Verificar no Banco de Dados

```bash
# No terminal local
python manage.py dbshell
```

```sql
-- Ver todos os produtos e quantidades
SELECT id, nome, quantidade_estoque, disponivel 
FROM consumidor_item 
ORDER BY id;

-- Ver logs de quando foi executado (pode adicionar tabela de logs)
SELECT * FROM consumidor_item WHERE quantidade_estoque > 0;
```

---

## 🔄 Parte 4: Fluxo Completo de Simulação

### Cenário de Teste Completo:

1. **Preparar ambiente:**
```sql
-- Zerar estoque de alguns produtos
UPDATE consumidor_item SET quantidade_estoque = 0, disponivel = 0 WHERE id IN (1, 5, 10);

-- Registrar interesse de clientes
INSERT INTO consumidor_notificacao (email_cliente, item_id, notificado)
VALUES 
  ('cliente1@email.com', 1, FALSE),
  ('cliente2@email.com', 5, FALSE),
  ('cliente3@email.com', 10, FALSE);
```

2. **Executar Lambda simulador_vendedor**
   - Pode ser via teste manual ou aguardar execução agendada

3. **Verificar resultados:**
```sql
-- Ver produtos que voltaram ao estoque
SELECT * FROM consumidor_item WHERE id IN (1, 5, 10);

-- Ver notificações enviadas
SELECT * FROM consumidor_notificacao WHERE notificado = TRUE;
```

4. **Verificar emails:**
   - Os clientes que registraram interesse devem receber email via SNS

---

## 📊 Parte 5: Monitoramento

### CloudWatch Logs

1. **Acessar AWS Console → CloudWatch**
2. **Ir em "Log groups"**
3. **Procurar:** `/aws/lambda/simulador_vendedor`
4. **Visualizar logs:**
   - Produtos adicionados em cada execução
   - Erros (se houver)
   - Notificações enviadas

### CloudWatch Metrics

1. **No console da Lambda, aba "Monitor"**
2. **Métricas importantes:**
   - **Invocations:** Quantas vezes foi executada
   - **Duration:** Tempo de execução
   - **Errors:** Erros ocorridos
   - **Throttles:** Execuções limitadas

### Logs Típicos de Sucesso:

```
Event received by Lambda function: {...}
Simulação de entrega iniciada em: 2025-11-26T20:30:00.123456
Adicionando 5 produtos diferentes ao estoque:
  - pão francês: +8 unidades
  - croissant: +5 unidades
  - brownie: +12 unidades
  - coxinha: +7 unidades
  - bolo de chocolate: +4 unidades
Encontrados 2 clientes interessados no produto ID 1
Lambda envia_email_interessados invocada para produto ID 1
Dados armazenados no RDS com sucesso! Inseridos: 0, Atualizados: 5
```

---

## 🎯 Casos de Uso

### Caso 1: Simulação Realista (Recomendado)
- **Frequência:** A cada 1-3 horas
- **Configuração:** `rate(2 hours)`
- **Produtos:** Aleatório (deixe o evento vazio `{}`)

### Caso 2: Demonstração Rápida
- **Frequência:** A cada 5 minutos
- **Configuração:** `rate(5 minutes)`
- **Produtos:** 3-5 produtos (`{"num_produtos": 3}`)

### Caso 3: Horário Comercial
- **Frequência:** 3x ao dia (manhã, tarde, noite)
- **Configuração:** `cron(0 9,14,18 * * ? *)`
- **Produtos:** Aleatório

### Caso 4: Dias Úteis Apenas
- **Frequência:** Seg-Sex às 10h
- **Configuração:** `cron(0 10 ? * MON-FRI *)`
- **Produtos:** 5-8 produtos

---

## 🛠️ Customizações Possíveis

### Ajustar Faixa de Quantidades

No arquivo `lambda_function.py`, linha ~44:
```python
quantidade_aleatoria = random.randint(2, 15)  # Ajuste aqui
```

Exemplo:
```python
quantidade_aleatoria = random.randint(5, 30)  # Mais produtos
```

### Ajustar Quantos Produtos Diferentes

No arquivo `lambda_function.py`, linha ~38:
```python
num_produtos = random.randint(1, 10)  # Ajuste aqui
```

Exemplo:
```python
num_produtos = random.randint(3, 8)  # Entre 3 e 8 produtos
```

### Adicionar Peso/Probabilidade por Produto

```python
# Produtos mais populares têm maior chance
PRODUTOS_POPULARES = [1, 2, 5, 7, 12]  # IDs

# Na função adicionar_produtos_aleatorios:
if random.random() < 0.7:  # 70% de chance
    # Adiciona produtos populares
    produtos_selecionados = [p for p in PRODUTOS_PADARIA if p['id'] in PRODUTOS_POPULARES]
else:
    # Adiciona produtos aleatórios
    produtos_selecionados = random.sample(PRODUTOS_PADARIA, num_produtos)
```

---

## 🐛 Troubleshooting

### Erro: "Unable to import module 'lambda_function'"
**Solução:** Verifique que o arquivo foi renomeado para `lambda_function.py` no ZIP

### Erro: "Task timed out after 3.00 seconds"
**Solução:** Aumente o timeout para 30 segundos nas configurações

### Erro: "Access Denied - InvokeFunction"
**Solução:** Adicione a permissão `lambda:InvokeFunction` na role IAM

### EventBridge não dispara a Lambda
**Solução:**
1. Verifique que o trigger está habilitado (enabled)
2. Verifique a expressão cron/rate
3. Aguarde o próximo horário agendado
4. Veja logs no CloudWatch Events

### Notificações não são enviadas
**Solução:**
1. Verifique que a Lambda `envia_email_interessados` existe
2. Verifique logs do CloudWatch
3. Teste manualmente a Lambda de emails

---

## 📈 Próximos Passos

1. **Adicionar variação por horário:**
   - Manhã: mais pães
   - Tarde: mais doces
   - Noite: menos produtos

2. **Implementar dias especiais:**
   - Finais de semana: mais bolos
   - Feriados: produtos especiais

3. **Dashboard de métricas:**
   - Quantos produtos foram adicionados
   - Frequência de notificações
   - Produtos mais/menos populares

4. **Integração com SQS:**
   - Fila de entregas pendentes
   - Processamento assíncrono

---

## ✅ Checklist de Configuração

- [ ] Lambda `simulador_vendedor` criada
- [ ] Código uploaded e handler configurado
- [ ] Timeout ajustado para 30s
- [ ] Permissão para invocar `envia_email_interessados` adicionada
- [ ] EventBridge trigger configurado com schedule
- [ ] Teste manual executado com sucesso
- [ ] Verificado produtos no banco de dados
- [ ] CloudWatch Logs configurado
- [ ] Notificações testadas end-to-end

---

**🎉 Pronto!** Seu simulador de vendedor está funcionando e adicionando produtos automaticamente! 🚀
