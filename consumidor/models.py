from django.db import models

class Item(models.Model):
    nome = models.CharField(max_length=200)
    estoque = models.IntegerField(default=0)
    
    def __str__(self):
        return self.nome

class Reserva(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='reservas')
    nome_cliente = models.CharField(max_length=200)
    email_cliente = models.EmailField()
    quantidade = models.IntegerField()
    data_reserva = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.nome_cliente} - {self.item.nome} ({self.quantidade})"

