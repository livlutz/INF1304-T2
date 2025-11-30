# INF1304-T2

![Python](https://img.shields.io/badge/Python-14354C?style=flat&logo=python&logoColor=white)
![HTML](https://img.shields.io/badge/HTML-e34c26?style=flat&logo=html5&logoColor=white)
![Django](https://img.shields.io/badge/Django-092E20?style=flat&logo=django&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=flat&logo=mysql&logoColor=white)
![AWS](https://img.shields.io/badge/Amazon_Web_Services-FF9900?style=for-the-badge&logo=amazonwebservices&logoColor=white)
![AmazonRDS](https://img.shields.io/badge/Amazon%20RDS-527FFF?style=for-the-badge&logo=amazon-rds&logoColor=white)

## 🍰 Projeto Quitute nas Nuvens

Aplicação para uma padraria inteligente usando a nuvem da Amazon (AWS). A aplicação funciona como um *marketplace* , com um fornecedor entregando produtos e a padraria se encarregando de vendê-los.

## 🤝 Membros da dupla

Lívia Lutz dos Santos - 2211055

Thiago Pereira Camerato - 2212580

## 📌 Objetivo

Desenvolver uma aplicação web para gerenciamento de reservas de quitutes em uma padaria virtual, integrando serviços da AWS (Lambda, RDS, SNS) para automatizar o controle de estoque e notificações aos clientes.

## 📋 Relatório de Implementação

### ✅ O que funciona

**Backend Django:**
- ✅ Sistema completo de modelos (Item, Reserva, Notificacao, EmailSubscription)
- ✅ Views para listagem, detalhamento e reserva de produtos
- ✅ Sistema de notificações por email via Amazon SNS
- ✅ Interface web responsiva com templates HTML/CSS
- ✅ Validação de disponibilidade de produtos

**Banco de Dados:**
- ✅ Integração com MySQL (RDS) e SQLite (desenvolvimento)
- ✅ Tabelas para itens, reservas, notificações e inscrições de email

**Integração AWS:**
- ✅ Amazon SNS para envio de notificações por email
- ✅ Tópicos SNS configurados (ProdutoDisponivel, EnviaEmail)
- ✅ Sistema de inscrição de emails no SNS

**Interface do Usuário:**
- ✅ Página inicial com captura de email
- ✅ Listagem de produtos disponíveis
- ✅ Página de detalhes do produto
- ✅ Formulários de reserva e notificação
- ✅ Páginas de confirmação de sucesso/erro
- ✅ Navegação responsiva com CSS

### ❌ O que não funciona
   - Conforme as especificações do trabalho no enunciado, não houve nenhuma funcionalidade que testamos e não funcionou

## ✅ Funcionalidades Implementadas

### Backend Django
- **Modelos de Dados**: Item, Reserva, Notificacao, EmailSubscription
- **Views**: ItemListView, ItemDetailView, ItemReserveView, ItemNotifyView
- **Integração AWS**: Chamadas para Lambda functions e SNS

### Banco de Dados
- **Esquema**: Tabelas criadas para itens, reservas e notificações
- **Integração**: Suporte a MySQL (RDS) e SQLite (desenvolvimento)

### Funções Lambda da AWS
- **simulador_vendedor**: Popula banco de dados com produtos
- **venda_de_produtos**: Atualiza estoque, envia emails para retirar produtos e registra usuários na espera caso o produto não esteja disponível para retirar
- **subscribe_email**: Gerencia inscrições SNS dos emails dos usuários

### Amazon SNS
- **Tópicos**: ProdutoDisponivel e EnviaEmail criados
- **Notificações**: Emails de confirmação de reserva enviados
- **Subscriptions**: Sistema de inscrição de emails

### Interface Web
- **Templates**: Páginas responsivas com CSS
- **Navegação**: Homepage, lista de produtos, detalhes, formulários
- **Feedback**: Páginas de sucesso/erro para operações

## 🔄 Funcionamento Atual do Sistema

### Fluxo Principal - Cliente

1. **Acesso Inicial:**
   - Cliente acessa `http://localhost:8000`
   - Informa seu email na página inicial
   - Email é armazenado na sessão

2. **Navegação de Produtos:**
   - Visualiza lista de produtos disponíveis
   - Pode ver detalhes de cada produto
   - Produtos indisponíveis são marcados como tal

3. **Reserva de Produtos:**
   - Para produtos disponíveis: Reserva imediata + email de confirmação
   - Para produtos indisponíveis: Opção de solicitar notificação
   - Sistema chama Lambda `venda_de_produtos` para processamento

4. **Notificações:**
   - **Funcionando**: Confirmação de reserva por email via SNS

### Fluxo Administrativo - Lambda Functions

**Entrega de Produtos (`simulador_vendedor`):**
- Popula banco de dados com produtos
- Chamada via interface administrativa em `/entregar-produtos/`

**Processamento de Vendas (`venda_de_produtos`):**
- Verifica disponibilidade e atualiza estoque
- Envia confirmação por email

**Subscrição de Emails (`subscribe_email`):**
- Gerencia inscrições no SNS para notificações

## 🔧 Instalação e Configuração

### Pré-requisitos
- Python 3.12+
- Conta AWS com acesso ao RDS, Lambda e SNS
- MySQL Workbench (opcional, para administração do banco)

### Passos de Instalação

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/livlutz/INF1304-T2.git
   cd INF1304-T2
   ```

2. **Configure ambiente virtual:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # ou
   venv\Scripts\activate     # Windows
   ```

3. **Instale dependências:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure variáveis de ambiente:**

   Crie um arquivo `.env` na raiz do projeto:
   ```env
   # Banco de dados RDS
   DB_HOST=seu-endpoint-rds.us-east-1.rds.amazonaws.com
   DB_USER=seu_usuario
   DB_PASSWORD=sua_senha
   DB_NAME=padaria-db
   DB_PORT=3306

   ```

5. **Execute migrações do Django:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Deploy das Lambda Functions:**

   No AWS Lambda Console, crie as seguintes funções:
   - `simulador_vendedor` → `vendaProduto/simulador_vendedor.py`
   - `venda_de_produtos` → `vendaProduto/venda_de_produtos.py`
   - `subscribe_email` → `subscribeEmail/subscribe_email.py`

   Configure as variáveis de ambiente em cada função.

7. **Configure SNS Topics:**

   No AWS SNS Console:
   - Crie tópico `ProdutoDisponivel`
   - Crie tópico `EnviaEmail`
   - Configure subscrições de email conforme necessário

### Inicialização da Aplicação

```bash
# Execute o script de inicialização, que também pode substituir os passos 2, 3 e 5
./run.sh

# Ou manualmente:
python manage.py runserver
```

Acesse: `http://localhost:8000`

## 📖 Instruções de Operação

### Operação Normal (Cliente)

1. **Acesse a aplicação** em `http://localhost:8000`
2. **Digite seu email** na página inicial
3. **Navegue pelos produtos** disponíveis
4. **Para produtos disponíveis**: Clique para reservar
5. **Para produtos indisponíveis**: Solicite notificação por email
6. **Aguarde confirmação** por email via SNS

### Testando Funcionalidades

#### Teste de Reserva
1. Acesse produto disponível
2. Faça reserva
3. Verifique se email de confirmação foi enviado
4. Confirme se estoque foi atualizado

#### Teste de Notificação
1. Solicite notificação para produto indisponível
2. Use função administrativa para "reabastecer"
3. Verifique se notificação foi enviada

### Monitoramento

- **Django Logs**: Visíveis no terminal onde o servidor roda
- **Lambda Logs**: CloudWatch Logs no AWS Console
- **RDS Queries**: MySQL Workbench ou `python manage.py dbshell`
- **SNS Messages**: AWS SNS Console → tópicos criados

## 📊 Diagramas

### Diagrama de Blocos da Arquitetura

![Diagrama de Blocos](diagramas/Diagrama_de_bloco.png)

### Diagramas UML de sequência

#### Verificação de Disponibilidade

![UML Verifica Disponibilidade](diagramas/UML_verifica_disponibilidade.png)

#### Venda de Produtos

![UML Venda de Produtos](diagramas/UML_venda_de_produtos.png)
