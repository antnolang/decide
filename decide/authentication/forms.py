from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser
# from django.contrib.auth.models import User


class SignUpForm(UserCreationForm):
    email = forms.EmailField(max_length=254, label='Main Email',
                             help_text='Required. Primary email')
    email1 = forms.EmailField(max_length=254,  label='GitHub email',
                              help_text='Required. Email for GitHub account')
    email2 = forms.EmailField(max_length=254, label='Facebook email',
                              help_text='Required. Email for Facebook account')

    class Meta:
        model = CustomUser
        fields = ('username', 'password1', 'password2',
                  'email', 'email1', 'email2',)
