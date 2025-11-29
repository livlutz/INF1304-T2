"""
Views principais do projeto Quitute nas Nuvens.
"""

from django.shortcuts import render, redirect
from django.views import View
from consumidor.models import Item, EmailSubscription
from consumidor.lambda_integration import subscribe_email_to_sns


class HomepageView(View):
    """
    View da página inicial que captura o e-mail do comprador.

    GET: Exibe o formulário para entrada de e-mail
    POST: Armazena o e-mail na sessão, inscreve no SNS e redireciona para lista de quitutes
    """

    template_name = 'items/homepage.html'

    def get(self, request):
        """Renderiza a página inicial."""
        return render(request, self.template_name)

    def post(self, request):
        """Processa o formulário de e-mail e inscreve no SNS via Lambda."""
        email = request.POST.get('email')

        if email:
            # Salvar email na sessão
            request.session['customer_email'] = email

            # Verificar se email já está inscrito (evitar chamadas desnecessárias)
            subscription, created = EmailSubscription.objects.get_or_create(
                email=email,
                defaults={'subscribed': False}
            )

            # Se é novo ou não está inscrito, chamar Lambda
            if created or not subscription.subscribed:
                print(f"📧 Inscrevendo email {email} no SNS via Lambda...")

                result = subscribe_email_to_sns(email)

                if result['success']:
                    # Atualizar status local
                    subscription.subscription_arn = result.get('subscription_arn')
                    subscription.subscribed = True
                    subscription.save()
                    print(f"✅ Email {email} inscrito com sucesso!")
                else:
                    print(f"⚠️ Falha ao inscrever {email}: {result['message']}")
                    # Não bloqueia o fluxo - usuário continua navegando
            else:
                print(f"ℹ️ Email {email} já está inscrito no SNS")

            return redirect('item_list')

        return render(request, self.template_name)


class SubscribeView(View):
    """
    Simple subscribe endpoint that accepts GET (query param `email`) or POST (form field `email`).
    Mirrors the logic used in `HomepageView.post` so external callers can hit `/subscribe/`.
    """

    def _subscribe_email(self, request, email: str):
        if not email:
            return None

        # Save email in session for user flow
        request.session['customer_email'] = email

        subscription, created = EmailSubscription.objects.get_or_create(
            email=email,
            defaults={'subscribed': False}
        )

        if created or not subscription.subscribed:
            result = subscribe_email_to_sns(email)
            if result.get('success'):
                subscription.subscription_arn = result.get('subscription_arn')
                subscription.subscribed = True
                subscription.save()
        return subscription

    def get(self, request):
        email = request.GET.get('email')
        self._subscribe_email(request, email)
        return redirect('item_list')

    def post(self, request):
        email = request.POST.get('email')
        self._subscribe_email(request, email)
        return redirect('item_list')

