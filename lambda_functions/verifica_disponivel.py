
"""Se o item estiver disponível, o usuário
deverá receber um e-mail informado que deve comparecer à padaria para efetivar a compra do item.
Se o item não estiver disponível no momento, quando o item chegar, esse cliente deverá ser
informado por e-mail."""

def lambda_handler(event,context):

    #ver se tem o produto no db