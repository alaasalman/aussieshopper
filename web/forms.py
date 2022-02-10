from django import forms

from captcha.fields import CaptchaField


class ContactMeForm(forms.Form):
    """
    Form to handle the anonymous contact form on the homepage. The form class itself
    is only used to encapsulate the data but the markup is written explicitly for now.
    """
    name = forms.CharField(max_length=100, required=False)
    email = forms.EmailField(max_length=200, required=False)
    message = forms.CharField(widget=forms.Textarea(), required=False)
    captcha = CaptchaField()
