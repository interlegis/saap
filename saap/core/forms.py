
from crispy_forms.bootstrap import FieldWithButtons, StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field
from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm, UserChangeForm as BaseUserChangeForm
from django.contrib.auth.tokens import default_token_generator
from django.forms.models import ModelForm
from django.utils.translation import ugettext_lazy as _
from django_filters.filterset import FilterSet
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

from image_cropping.widgets import ImageCropWidget, CropWidget
from saap.crispy_layout_mixin import to_row
from saap.core.models import * 
from saap.settings import SITE_DOMAIN, SITE_NAME

#import django_filter

from saap.core.models import Trecho, TipoLogradouro, User, OperadorAreaTrabalho,\
    ImpressoEnderecamento

class LoginForm(AuthenticationForm):

    username = forms.CharField(
        label="Username", max_length=254,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'name': 'username',
                'placeholder': _('Digite seu Endereço de email')}))
    password = forms.CharField(
        label="Password", max_length=30,
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'name': 'password',
                'placeholder': _('Digite sua Senha')}))

class NewPasswordForm(PasswordChangeForm):
    
    old_password = forms.CharField(
        label="Old password", max_length=30,
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'name': 'old_password',
                'placeholder': _('Digite sua senha antiga')}))
    
    new_password1 = forms.CharField(
        label="New password 1", max_length=30,
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'name': 'new_password1',
                'placeholder': _('Digite sua nova senha')}))

    new_password2 = forms.CharField(
        label="New password 2", max_length=30,
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'name': 'new_password2',
                'placeholder': _('Repita sua nova senha')}))

class ResetPasswordForm(PasswordResetForm):
    
    email = forms.CharField(
        label="Email", max_length=254,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'name': 'email',
                'placeholder': _('Digite seu Endereço de email')}))

    def save(self, subject_template_name='registration/password_reset_subject.txt',
             email_template_name='registration/password_reset_email.html',
             use_https=True, token_generator=default_token_generator,
             from_email=None, request=None, html_email_template_name=None,
             extra_email_context=None):

        email = self.cleaned_data["email"]
        for user in self.get_users(email):
            #if not domain_override:
            #current_site = get_current_site(request)
            #domain = current_site.domain
            context = {
                'email': user.email,
                'domain': SITE_DOMAIN,
                'site_name': SITE_NAME,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'user': user,
                'token': token_generator.make_token(user),
                'protocol': 'https' if use_https else 'http',
            }
            if extra_email_context is not None:
                context.update(extra_email_context)
            self.send_mail(subject_template_name, email_template_name,
                           context, from_email, user.email,
                           html_email_template_name=html_email_template_name)

class PasswordForm(SetPasswordForm):
    
    new_password1 = forms.CharField(
        label="New password 1", max_length=30,
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'name': 'new_password1',
                'placeholder': _('Digite sua nova senha')}))

    new_password2 = forms.CharField(
        label="New password 2", max_length=30,
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'name': 'new_password2',
                'placeholder': _('Repita sua nova senha')}))

class UserCreationForm(BaseUserCreationForm):

    class Meta(BaseUserCreationForm.Meta):
        model = User
        fields = ('email',)


class UserChangeForm(BaseUserChangeForm):

    class Meta(BaseUserChangeForm.Meta):
        model = User


class RegistrationForm(UserCreationForm):

    class Meta(UserCreationForm.Meta):
        fields = ('email', 'first_name', 'last_name')


class CustomImageCropWidget(ImageCropWidget):
    """
    Custom ImageCropWidget that doesn't show the initial value of the field.
    We use this trick, and place it right under the CropWidget so that
    it looks like the user is seeing the image and clearing the image.
    """
    template_with_initial = (
        # '%(initial_text)s: <a href="%(initial_url)s">%(initial)s</a> '
        '%(clear_template)s<br />%(input_text)s: %(input)s'
    )


class UserForm(UserChangeForm):
    # We don't have a password field
    password = None

    class Meta(UserChangeForm.Meta):
        model = User

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)

class OperadorAreaTrabalhoForm(ModelForm):

    class Meta:
        model = OperadorAreaTrabalho
        fields = ['user',
                  'grupos_associados',
                  'preferencial',
                  #'areatrabalho'
                  ]

    def __init__(self, *args, **kwargs):

        super(OperadorAreaTrabalhoForm, self).__init__(*args, **kwargs)
        self.fields[
            'grupos_associados'].widget = forms.CheckboxSelectMultiple()
        self.fields['grupos_associados'].queryset = self.fields[
            'grupos_associados'].queryset.order_by('name')

        self.fields['preferencial'].widget = forms.RadioSelect()
        self.fields['preferencial'].inline_class = True

        #self.fields['areatrabalho'].disabled = True

class ImpressoEnderecamentoForm(ModelForm):

    class Meta:
        model = ImpressoEnderecamento
        fields = ['nome',
                  'tipo',
                  'largura_pagina',
                  'altura_pagina',
                  'margem_esquerda',
                  'margem_superior',
                  'colunasfolha',
                  'linhasfolha',
                  'larguraetiqueta',
                  'alturaetiqueta',
                  'entre_colunas',
                  'entre_linhas',
                  'fontsize',
                  'rotate'
                  ]

    def __init__(self, *args, **kwargs):

        super(ImpressoEnderecamentoForm, self).__init__(*args, **kwargs)
        self.fields['rotate'].widget = forms.RadioSelect()
        self.fields['rotate'].inline_class = True


class ListWithSearchForm(forms.Form):
    q = forms.CharField(required=False, label='',
                        widget=forms.TextInput(
                            attrs={'type': 'search'}))

    o = forms.CharField(required=False, label='',
                        widget=forms.HiddenInput())

    class Meta:
        fields = ['q', 'o']

    def __init__(self, *args, **kwargs):
        super(ListWithSearchForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.form_class = 'form-inline'
        self.helper.form_method = 'GET'
        self.helper.layout = Layout(
            Field('o'),
            FieldWithButtons(
                Field('q',
                      placeholder=_('Filtrar Lista'),
                      css_class='input-lg'),
                StrictButton(
                    _('Filtrar'), css_class='btn-default btn-lg',
                    type='submit'))
        )

