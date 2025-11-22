"""
Views principais do projeto Quitute nas Nuvens.
"""

from django.shortcuts import render, redirect
from django.views import View
from consumidor.models import Item


class HomepageView(View):
    """
    View da página inicial que captura o e-mail do comprador.

    GET: Exibe o formulário para entrada de e-mail
    POST: Armazena o e-mail na sessão e redireciona para lista de quitutes
    """

    template_name = 'items/homepage.html'

    def get(self, request):
        """Renderiza a página inicial."""
        return render(request, self.template_name)

    def post(self, request):
        """Processa o formulário de e-mail e armazena na sessão."""
        email = request.POST.get('email')
        if email:
            request.session['customer_email'] = email
            return redirect('item_list')
        return render(request, self.template_name)

