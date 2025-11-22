from django import forms
from .models import Item

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['nome', 'estoque']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'w-full p-2 border rounded mb-4', 'placeholder': 'Nome do item'}),
            'estoque': forms.NumberInput(attrs={'class': 'w-full p-2 border rounded mb-4', 'placeholder': 'Quantidade em estoque'}),
        }
        labels = {
            'nome': 'Nome do Item',
            'estoque': 'Quantidade em Estoque',
        }
