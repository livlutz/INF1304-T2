#!/bin/bash

# Script para atualizar o banco de dados para compatibilidade com as Lambda Functions
# Este script sincroniza o schema do banco de dados com os modelos Django

echo "=========================================="
echo "Atualizando Banco de Dados"
echo "=========================================="

# Ativa o ambiente virtual
source .venv/bin/activate

# Aplica as migrações
echo "Aplicando migrações..."
python manage.py migrate

echo ""
echo "=========================================="
echo "Banco de dados atualizado com sucesso!"
echo "=========================================="
echo ""
echo "Tabelas criadas/atualizadas:"
echo "  - consumidor_item: campos 'quantidade_estoque' e 'disponivel' adicionados"
echo "  - consumidor_reserva: campo 'confirmado' adicionado, 'nome_cliente' agora é opcional"
echo "  - consumidor_notificacao: tabela criada para gerenciar notificações de produtos"
echo ""
echo "Para popular o banco com produtos iniciais, execute:"
echo "  python manage.py shell"
echo "  >>> from lambda_functions.entrega_de_produtos import PRODUTOS_PADARIA"
echo "  >>> # Insira os produtos manualmente ou chame a lambda de entrega"
