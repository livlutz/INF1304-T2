from django.contrib import admin
from .models import Item, Reserva

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ['nome', 'estoque']
    search_fields = ['nome']

@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ['nome_cliente', 'item', 'quantidade', 'data_reserva']
    list_filter = ['data_reserva', 'item']
    search_fields = ['nome_cliente', 'item__nome']
    date_hierarchy = 'data_reserva'

