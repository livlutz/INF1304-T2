"""
Views do aplicativo Consumidor.

Este módulo contém as views responsáveis por gerenciar a experiência
do comprador ao visualizar e reservar quitutes.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView, DetailView
from django.urls import reverse_lazy
from .models import Item, Reserva, Notificacao
from .lambda_integration import processar_venda, entregar_produtos
import boto3
import os


def send_reservation_email(email, nome_cliente, item_nome, quantidade):
    """
    Envia email de confirmação de reserva via SNS
    """
    try:
        sns = boto3.client('sns', region_name=os.getenv('AWS_REGION', 'us-east-1'))
        alertTopic = 'EnviaEmail'
        snsTopicArn = [t['TopicArn'] for t in sns.list_topics()['Topics']
                      if t['TopicArn'].lower().endswith(':' + alertTopic.lower())][0]

        subject = f'Confirmação de Reserva - {item_nome}'
        message = f"""
Olá {nome_cliente},

Sua reserva foi confirmada com sucesso!

Detalhes da reserva:
- Produto: {item_nome}
- Quantidade: {quantidade}
- Email: {email}

Você pode retirar seu produto na padaria assim que estiver pronto.

Atenciosamente,
Quitute nas Nuvens
"""
        response = sns.publish(
            TopicArn=snsTopicArn,
            Message=message,
            Subject=subject
        )
        print(f"📧 Email de reserva enviado via SNS para {email}: {response}")
    except Exception as e:
        print(f"❌ Erro ao enviar email de reserva para {email}: {e}")


class SessionRequiredMixin:
    """
    Mixin que garante que o usuário tenha um e-mail na sessão.

    Redireciona para a homepage se o e-mail não estiver presente.
    """

    def dispatch(self, request, *args, **kwargs):
        """Verifica se o e-mail está na sessão antes de processar a requisição."""
        if 'customer_email' not in request.session:
            return redirect('homepage')
        return super().dispatch(request, *args, **kwargs)


class ItemListView(SessionRequiredMixin, ListView):
    """
    Exibe a lista de quitutes disponíveis para reserva.

    Atributos:
        model: Modelo Item
        template_name: Template de lista de itens
        context_object_name: Nome do contexto para os itens
    """

    model = Item
    template_name = 'items/list.html'
    context_object_name = 'items'

    def get_queryset(self):
        """Retorna todos os itens disponíveis."""
        return Item.objects.all()


class ItemDetailView(SessionRequiredMixin, DetailView):
    """
    Exibe os detalhes de um quitute específico.

    Permite ao usuário visualizar informações detalhadas e iniciar
    o processo de reserva.

    Atributos:
        model: Modelo Item
        template_name: Template de detalhes do item
        context_object_name: Nome do contexto para o item
    """

    model = Item
    template_name = 'items/detail.html'
    context_object_name = 'item'


class ItemReserveView(SessionRequiredMixin, View):
    """
    Processa a reserva de um quitute.

    POST: Cria uma nova reserva, atualiza o estoque e exibe confirmação
    GET: Redireciona para a página de detalhes do item
    """

    def post(self, request, pk):
        """
        Processa o formulário de reserva usando Lambda venda_produtos.

        Args:
            pk: ID do item a ser reservado

        Returns:
            Renderiza a página de sucesso ou redireciona para detalhes
        """
        item = get_object_or_404(Item, pk=pk)

        nome_cliente = request.POST.get('nome_cliente')
        quantidade = int(request.POST.get('quantidade', 1))
        email_cliente = request.session.get('customer_email')

        # Chama Lambda para processar a venda
        print(f"🔄 Chamando Lambda venda_produtos para item {pk}, quantidade {quantidade}")
        resultado = processar_venda(pk, quantidade, email_cliente)

        if resultado['success']:
            # Atualiza item local (sincroniza com banco)
            item.refresh_from_db()

            # Envia email de confirmação
            send_reservation_email(email_cliente, nome_cliente, item.nome, quantidade)

            # Renderiza página de sucesso
            return render(request, 'items/reservation_success.html', {
                'nome_cliente': nome_cliente,
                'item_nome': item.nome,
                'quantidade': quantidade,
                'email_cliente': email_cliente,
                'lambda_message': resultado.get('message')
            })
        else:
            # Se a Lambda falhou, mostra erro
            return render(request, 'items/reservation_error.html', {
                'item': item,
                'error_message': resultado.get('message')
            })

    def get(self, request, pk):
        """Redireciona GET requests para a página de detalhes."""
        return redirect('item_detail', pk=pk)


class ItemNotifyView(SessionRequiredMixin, View):
    """
    Registra o interesse do cliente em ser notificado quando o item voltar ao estoque.
    """

    def get(self, request, pk):
        """
        Registra a notificação para o item.

        Args:
            pk: ID do item

        Returns:
            Renderiza a página de confirmação de notificação
        """
        item = get_object_or_404(Item, pk=pk)
        email_cliente = request.session.get('customer_email')

        # Verifica se o email está inscrito no SNS
        from .models import EmailSubscription
        email_subscription = EmailSubscription.objects.filter(
            email=email_cliente,
            subscribed=True
        ).first()

        # Cria ou obtém a notificação existente
        notificacao, created = Notificacao.objects.get_or_create(
            email_cliente=email_cliente,
            item=item
        )

        return render(request, 'items/notify_success.html', {
            'item': item,
            'email_cliente': email_cliente,
            'already_registered': not created,
            'email_subscribed': email_subscription is not None
        })



class EntregarProdutosView(View):
    """
    View administrativa para chamar Lambda de entrega de produtos.
    Popula o banco com novos produtos da padaria.
    """

    def get(self, request):
        """Renderiza página com botão para entregar produtos."""
        return render(request, 'items/entregar_produtos.html')

    def post(self, request):
        """Chama Lambda para entregar produtos."""
        print("🚚 Chamando Lambda entrega_produto...")
        resultado = entregar_produtos()

        if resultado['success']:
            return render(request, 'items/entrega_sucesso.html', {
                'message': resultado.get('message'),
                'produtos_inseridos': resultado.get('produtos_inseridos'),
                'produtos_atualizados': resultado.get('produtos_atualizados'),
                'total_produtos': resultado.get('total_produtos')
            })
        else:
            return render(request, 'items/entrega_erro.html', {
                'error_message': resultado.get('message')
            })
