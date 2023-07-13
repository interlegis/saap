
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
from django.contrib.auth import get_user_model, password_validation

from image_cropping.widgets import ImageCropWidget, CropWidget
from saap.crispy_layout_mixin import SaapFormHelper, SaapFormLayout, to_row
from saap.core.models import * 
from saap.settings import SITE_DOMAIN, SITE_NAME

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

class UserAdminForm(ModelForm):
    is_active = forms.TypedChoiceField(label=_('Usuário Ativo'),
                                       choices=YES_NO_CHOICES,
                                       coerce=lambda x: x == 'True')

    new_password1 = forms.CharField(
        label='Nova senha',
        max_length=50,
        strip=False,
        required=False,
        widget=forms.PasswordInput(),
        help_text='Deixe os campos em branco para não fazer alteração de senha')

    new_password2 = forms.CharField(
        label='Confirmar senha',
        max_length=50,
        strip=False,
        required=False,
        widget=forms.PasswordInput(),
        help_text='Deixe os campos em branco para não fazer alteração de senha')

    class Meta:
        model = get_user_model()
        fields = [
            get_user_model().USERNAME_FIELD,
            'first_name',
            'last_name',
            'is_active',
            'new_password1',
            'new_password2',
            'groups',
        ]

        if get_user_model().USERNAME_FIELD != 'email':
            fields.extend(['email'])

    def __init__(self, *args, **kwargs):

        self.user_session = kwargs.pop('user_session', None)
        self.granular = kwargs.pop('granular', None)
        self.instance = kwargs.get('instance', None)

        row_pwd = [
            ('username', 4),
            ('email', 6),
            ('is_active', 2),
            ('first_name', 6),
            ('last_name', 6),
            ('new_password1', 3 if self.instance and self.instance.pk else 6),
            ('new_password2', 3 if self.instance and self.instance.pk else 6),
        ]

        if self.instance and self.instance.pk:
            row_pwd += [
                (
                    FieldWithButtons(
                        'token',
                        StrictButton(
                            'Renovar',
                            id="renovar-token",
                            css_class="btn-outline-primary"),
                        css_class='' if self.instance and self.instance.pk else 'd-none'),
                    6
                )
            ]

        row_pwd += [

            ('groups', 12),

        ] + ([('user_permissions', 12)] if not self.granular is None else [])

        row_pwd = to_row(row_pwd)

        self.helper = SaapFormHelper()
        self.helper.layout = SaapFormLayout(row_pwd)
        super(UserAdminForm, self).__init__(*args, **kwargs)

        self.fields['groups'].widget = forms.CheckboxSelectMultiple()

        if not self.instance.pk:
            self.fields['groups'].choices = [
                (g.id, g) for g in Group.objects.exclude(
                    name__in=[]
                ).order_by('name')
            ]


    def save(self, commit=True):
        if self.cleaned_data['new_password1']:
            self.instance.set_password(self.cleaned_data['new_password1'])
        permissions = None
        votante = None
        operadorautor = None
        if self.instance.id:
            inst_old = get_user_model().objects.get(pk=self.instance.pk)
            if self.granular is None:
                permissions = list(inst_old.user_permissions.all())

        inst = super().save(commit)

        if permissions:
            inst.user_permissions.add(*permissions)

    def clean(self):
        data = super().clean()

        if self.errors:
            return data

        new_password1 = data.get('new_password1', '')
        new_password2 = data.get('new_password2', '')

        if new_password1 != new_password2:
            raise forms.ValidationError(
                _("As senhas informadas são diferentes"),
            )
        else:
            if new_password1 and new_password2:
                password_validation.validate_password(
                    new_password2, self.instance)

        """
        
        if 'email' in data and data['email']:
            duplicidade = get_user_model().objects.filter(email=data['email'])
            if self.instance.id:
                duplicidade = duplicidade.exclude(id=self.instance.id)

            if duplicidade.exists():
                raise forms.ValidationError(
                    "Email já cadastrado para: {}".format(
                        ', '.join(map(lambda x: str(x), duplicidade.all())),
                    )
                )"""

        return data


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
                  'areatrabalho'
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
                    _('Filtrar'), css_class='btn-lg btn-default btn-lrg',
                    type='submit'))
        )

