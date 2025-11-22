
"""Se o item estiver disponível, o usuário
deverá receber um e-mail informado que deve comparecer à padaria para efetivar a compra do item.
Se o item não estiver disponível no momento, quando o item chegar, esse cliente deverá ser
informado por e-mail."""

def lambda_handler(event,context):

    #conectar ao banco de dados AWS para verificar a disponibilidade do item
    #se disponível, enviar email para o usuário
    #se não disponível, enviar email informando que o usuário será notificado quando o item
    pass