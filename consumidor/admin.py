from django.contrib import admin
from .models import Item, Reserva, Notificacao

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ['nome', 'quantidade_estoque', 'disponivel']
    search_fields = ['nome']
    list_filter = ['disponivel']

@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ['email_cliente', 'nome_cliente', 'item', 'quantidade', 'confirmado', 'data_reserva']
    list_filter = ['data_reserva', 'item', 'confirmado']
    search_fields = ['nome_cliente', 'email_cliente', 'item__nome']
    date_hierarchy = 'data_reserva'

@admin.register(Notificacao)
class NotificacaoAdmin(admin.ModelAdmin):
    list_display = ['email_cliente', 'item', 'notificado', 'data_criacao']
    list_filter = ['notificado', 'item']
    search_fields = ['email_cliente', 'item__nome']
    date_hierarchy = 'data_criacao'

