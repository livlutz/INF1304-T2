from django.db import models

class Item(models.Model):
    nome = models.CharField(max_length=200)
    quantidade_estoque = models.IntegerField(default=0)
    disponivel = models.BooleanField(default=True)
    imagem = models.ImageField(upload_to='produtos/', null=True, blank=True)

    def __str__(self):
        return self.nome

class Reserva(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='reservas')
    nome_cliente = models.CharField(max_length=200, blank=True, null=True)
    email_cliente = models.EmailField()
    quantidade = models.IntegerField()
    confirmado = models.BooleanField(default=False)
    data_reserva = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nome_cliente or self.email_cliente} - {self.item.nome} ({self.quantidade})"

class Notificacao(models.Model):
    email_cliente = models.EmailField()
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='notificacoes')
    quantidade = models.IntegerField(default=1)  # Quantidade desejada para notificação
    notificado = models.BooleanField(default=False)
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.email_cliente} - {self.item.nome} ({self.quantidade})"


class EmailSubscription(models.Model):
    """
    Rastreia emails inscritos no SNS para notificações
    """
    email = models.EmailField(unique=True)
    subscription_arn = models.CharField(max_length=255, null=True, blank=True)
    subscribed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.email} - {'Inscrito' if self.subscribed else 'Pendente'}"

