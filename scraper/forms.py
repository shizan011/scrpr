from django import forms
from django.contrib.auth.forms import AuthenticationForm


class ScrapeForm(forms.Form):
    location = forms.CharField(
        label='Location', 
        max_length=100, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'locationInput'})
    )
    services = forms.CharField(
        label='Services', 
        max_length=100, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'servicesInput'})
    )
    email_providers = forms.CharField(
        label='Email Providers', 
        max_length=100, 
        initial='"@gmail.com" OR "@hotmail.com" OR "@yahoo.com" OR "@outlook.com"',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    # forms.py
class UserLoginForm(AuthenticationForm):
    username = forms.CharField(label='Username', widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label='Password', widget=forms.PasswordInput(attrs={'class': 'form-control'}))

