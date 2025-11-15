
import streamlit as st

#dicionario mapeando os nomes das guloseimas com numeros para serem escolhidos pelo usuario
guloseimas = {
    "pão francês": 1,
    "croissant": 2,
    "pao careca" : 3,
    "brioche": 4,
    "pao de queijo": 5,
    "joelho": 6,
    "coxinha": 7,
    "sonho": 8,
    "bolo de chocolate": 9,
    "bolo de cenoura": 10,
    "torta de limao": 11,
    "cookie de chocolate": 12,
    "brigadeiro gigante": 13,
    "cheesecake": 14,
    "muffin quentinho": 15,
    "empada": 16,
    "quiche": 17,
    "pão doce": 18,
    "torta de maçã": 19,
    "brownie": 20,

}

def verifica_disponibilidade(num_guloseima, email):
    """Verifica no banco de dados na AWS se a guloseima escolhida esta disponivel

    Args:
        num_guloseima (int): Número da guloseima escolhida pelo usuário
        email (str): Email do usuário para contato
    Returns:
        Envia um email para buscar a guloseima se estiver disponivel ou informa que nao esta disponivel e
        que o usuario sera notificado por email quando estiver em estoque
    """

    #TODO: Implementar a verificação de disponibilidade no banco de dados da AWS e chamar o email
    pass

# Streamlit interface
def main():
    st.title("🥐 Padaria - Sistema de Pedidos")
    st.write("Seja bem-vindo à padaria! Por favor, faça seu pedido:")

    # Criar lista de opções para o selectbox (nome da guloseima)
    guloseimas_nomes = list(guloseimas.keys())

    # Selectbox para escolher a guloseima
    guloseima_escolhida = st.selectbox(
        "Escolha sua guloseima:",
        guloseimas_nomes,
        index=0
    )

    # Mostrar o número da guloseima escolhida
    num_guloseima = guloseimas[guloseima_escolhida]
    st.info(f"Você selecionou: **{guloseima_escolhida}**")

    # Email input com placeholder
    email = st.text_input(
        "Digite seu email para contato:",
        help="Você receberá notificações sobre a disponibilidade do produto"
    )

    # Botão para confirmar a escolha
    if st.button("Verificar Disponibilidade"):
        with st.spinner("Verificando disponibilidade..."):
            verifica_disponibilidade(num_guloseima,email)
            #TODO: Adicionar feedback ao usuário sobre a disponibilidade quando a função estiver implementada

if __name__ == "__main__":
    main()