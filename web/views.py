from django.shortcuts import render
from django.views.generic import FormView
from django.urls import reverse
from django.contrib import messages

from captcha.models import CaptchaStore
from captcha.helpers import captcha_image_url

from api import tasks, models
from .forms import ContactMeForm


class IndexView(FormView):
    template_name = 'web/index.html'
    form_class = ContactMeForm

    def get_success_url(self):
        return reverse('web:web-index')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cp_key = CaptchaStore.generate_key()
        context['captcha_img_url'] = captcha_image_url(cp_key)
        context['captcha_key'] = cp_key

        return context

    def form_valid(self, form):
        # contact form submitted, send the managers an email and redirect to homepage
        name = form.cleaned_data['name']
        email = form.cleaned_data['email']
        message = form.cleaned_data['message']

        tasks.email_managers('anonymous_contact.html', {
            'user_name': name,
            'user_email': email,
            'message': message
        })

        messages.info(self.request, "Contact email sent.")

        return super().form_valid(form)


def statistics(request):
    context = {
        'total_deals': models.Deal.objects.count(),
        'total_messages': models.LogChatMessage.objects.count()
    }

    return render(request, 'web/statistics.html', context)

