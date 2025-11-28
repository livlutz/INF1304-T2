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
        Processa o formulário de reserva.
        
        Args:
            pk: ID do item a ser reservado
            
        Returns:
            Renderiza a página de sucesso ou redireciona para detalhes
        """
        item = get_object_or_404(Item, pk=pk)
        
        nome_cliente = request.POST.get('nome_cliente')
        quantidade = int(request.POST.get('quantidade', 1))
        email_cliente = request.session.get('customer_email')
        
        if item.quantidade_estoque >= quantidade:
            # Cria a reserva
            Reserva.objects.create(
                item=item,
                nome_cliente=nome_cliente,
                email_cliente=email_cliente,
                quantidade=quantidade,
                confirmado=True
            )
            
            # Atualiza o estoque
            item.quantidade_estoque -= quantidade
            item.disponivel = item.quantidade_estoque > 0
            item.save()
            
            # Renderiza página de sucesso
            return render(request, 'items/reservation_success.html', {
                'nome_cliente': nome_cliente,
                'item_nome': item.nome,
                'quantidade': quantidade,
                'email_cliente': email_cliente
            })
        
        # Se não houver estoque suficiente, redireciona
        return redirect('item_detail', pk=pk)
    
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
        
        # Cria ou obtém a notificação existente
        notificacao, created = Notificacao.objects.get_or_create(
            email_cliente=email_cliente,
            item=item
        )
        
        return render(request, 'items/notify_success.html', {
            'item': item,
            'email_cliente': email_cliente,
            'already_registered': not created
        })

