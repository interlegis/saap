from _functools import reduce
from datetime import date, timedelta
import datetime
import operator

from crispy_forms.bootstrap import FieldWithButtons, StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Field, Layout, Fieldset, Div, BaseInput
from dateutil.relativedelta import relativedelta
from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple, AdminDateWidget
from django.db import models
from django.db.models import Q
#from django.forms.extras.widgets import SelectDateWidget
from django.forms.widgets import SelectDateWidget, DateInput

from django.forms.models import ModelForm, ModelMultipleChoiceField
from django.db.models import F
from django.utils.translation import ugettext_lazy as _
from django_filters.filters import ChoiceFilter, NumberFilter,\
    MethodFilter, ModelChoiceFilter, RangeFilter,\
    MultipleChoiceFilter, ModelMultipleChoiceFilter, BooleanFilter
from django_filters.filterset import FilterSet
from saap.crispy_layout_mixin import SaplFormLayout, to_row
from saap.core.models import Municipio

from saap import settings
from saap.cerimonial.models import LocalTrabalho, Endereco,\
    TipoAutoridade, PronomeTratamento, Contato, Perfil, Processo, Dependente,\
    IMPORTANCIA_CHOICE, AssuntoProcesso, ClassificacaoProcesso, StatusProcesso, ProcessoContato,\
    GrupoDeContatos, TopicoProcesso, Telefone, Email, EstadoCivil
from saap.core.forms import ListWithSearchForm
from saap.core.models import Trecho, ImpressoEnderecamento, Bairro, NivelInstrucao
from saap.utils import normalize, YES_NO_CHOICES, NONE_YES_NO_CHOICES


class ListTextWidget(forms.TextInput):

    def __init__(self, data_list, name, *args, **kwargs):
        super(ListTextWidget, self).__init__(*args, **kwargs)
        self._name = name
        self._list = data_list
        self.attrs.update({'list': 'list__%s' % self._name})

    def render(self, name, value, attrs=None):
        text_html = super(ListTextWidget, self).render(
            name, value, attrs=attrs)
        data_list = '<datalist id="list__%s">' % self._name
        for item in self._list:
            data_list += '<option value="%s">' % item
        data_list += '</datalist>'

        return (text_html + data_list)


class LocalTrabalhoPerfilForm(ModelForm):

    class Meta:
        model = LocalTrabalho
        fields = ['nome',
                  'nome_fantasia',
                  'data_inicio',
                  'data_fim',
                  'tipo',
                  'trecho',
                  'endereco',
                  'numero',
                  'complemento',
                  'distrito',
                  'regiao_municipal',
                  'cep',
                  'bairro',
                  'municipio',
                  'principal',
                  'cargo']

    def __init__(self, *args, **kwargs):

        instance = None
        super(LocalTrabalhoPerfilForm, self).__init__(*args, **kwargs)

        if isinstance(self.instance, LocalTrabalho):
            instance = self.instance

        self.fields['cep'].widget.attrs['class'] = 'cep'
        self.fields['endereco'].widget.attrs['autocomplete'] = 'on'
        self.fields['trecho'].queryset = Trecho.objects.all()
        self.fields['trecho'].widget = forms.HiddenInput()

        # Utilizando template bootstrap3 customizado
        self.fields['principal'].widget = forms.RadioSelect()
        self.fields['principal'].inline_class = True


class LocalTrabalhoForm(ModelForm):

    class Meta:
        model = LocalTrabalho
        fields = ['nome',
                  'nome_fantasia',
                  'data_inicio',
                  'data_fim',
                  'tipo',
                  'trecho',
                  'endereco',
                  'numero',
                  'complemento',
                  'distrito',
                  'regiao_municipal',
                  'cep',
                  'bairro',
                  'municipio',
                  'estado',
                  'principal',
                  'cargo']

    data_inicio = forms.DateField(
        required=False,
        label='Início',
        widget=DateInput(),
    )

    data_fim = forms.DateField(
        required=False,
        label='Fim',
        widget=DateInput(),
    )


    def __init__(self, *args, **kwargs):

        instance = None
        super(LocalTrabalhoForm, self).__init__(*args, **kwargs)

        if isinstance(self.instance, LocalTrabalho):
            instance = self.instance

        #if not instance:
        #    self.fields['cep'].initial = settings.INITIAL_VALUE_FORMS_CEP
        #    self.fields['municipio'].initial = Municipio.objects.get(
        #        pk=settings.INITIAL_VALUE_FORMS_MUNICIPIO)

        self.fields['cep'].widget.attrs['class'] = 'cep'
        self.fields['endereco'].widget.attrs['autocomplete'] = 'on'
        self.fields['trecho'].queryset = Trecho.objects.all()
        self.fields['trecho'].widget = forms.HiddenInput()

        # Utilizando template bootstrap3 customizado
        self.fields['principal'].widget = forms.RadioSelect()
        self.fields['principal'].inline_class = True


class ContatoForm(ModelForm):

    class Meta:
        model = Contato
        fields = ['nome',
                  'nome_social',
                  'apelido',
                  'data_nascimento',
                  'estado_civil',
                  'sexo',
                  'identidade_genero',
                  'nivel_instrucao',
                  'naturalidade',
                  'estado',
                  'tem_filhos',
                  'quantos_filhos',
                  'profissao',
                  'pronome_tratamento',
                  'tipo_autoridade',
                  'nome_pai',
                  'nome_mae',
                  'numero_sus',
                  'cpf',
                  'cnpj',
                  'ie',
                  'titulo_eleitor',
                  'rg',
                  'rg_orgao_expedidor',
                  'rg_data_expedicao',
                  'ativo',
                  'observacoes',
                  'cargo',
                  'grupodecontatos_set'
                  ]

    grupodecontatos_set = ModelMultipleChoiceField(
        queryset=GrupoDeContatos.objects.all(),
        required=False,
        label='',
        widget=FilteredSelectMultiple('grupodecontatos_set', False),
    )

    data_nascimento = forms.DateField(
        required=False,
        label='Data de nascimento',
        widget=DateInput(),
    )

    def __init__(self, *args, **kwargs):

        instance = None
        super(ContatoForm, self).__init__(*args, **kwargs)

        if isinstance(self.instance, Contato):
            instance = self.instance

        self.fields['cpf'].widget.attrs['class'] = 'cpf'
        self.fields['cnpj'].widget.attrs['class'] = 'cnpj'
        self.fields['numero_sus'].widget.attrs['class'] = 'numero_sus'
        self.fields['rg'].widget.attrs['class'] = 'rg'
        self.fields['titulo_eleitor'].widget.attrs['class'] = 'titulo_eleitor'

        if 'tipo_autoridade' in self.fields:
            self.fields['tipo_autoridade'].widget.attrs.update(
                {'onchange': 'atualizaPronomes(event)'})

        self.fields['pronome_tratamento'].widget = forms.RadioSelect()
        self.fields['pronome_tratamento'].queryset = \
            PronomeTratamento.objects.order_by(
                'prefixo_nome_singular_m', 'nome_por_extenso')

        if 'tipo_autoridade' in self.fields and\
                instance and instance.tipo_autoridade:
            pronomes_choice = instance.tipo_autoridade.pronomes.order_by(
                'nome_por_extenso', 'enderecamento_singular_m')
        else:
            pronomes_choice = self.fields['pronome_tratamento'].queryset

        self.fields['pronome_tratamento'].choices = [
            (p.pk, '%s ( "%s" ou "%s" )' % (
                p.nome_por_extenso,
                p.enderecamento_singular_m,
                p.enderecamento_singular_f,
                #p.vocativo_direto_singular_m,
                #p.vocativo_direto_singular_f
                ))
            for p in pronomes_choice]

        self.fields[
            'grupodecontatos_set'].widget = forms.CheckboxSelectMultiple()
        self.fields['grupodecontatos_set'].inline_class = True

        self.fields['grupodecontatos_set'].queryset = \
            GrupoDeContatos.objects.filter(workspace=self.initial['workspace'])

        if self.instance and self.instance.pk:
            self.fields['grupodecontatos_set'].initial = list(
                self.instance.grupodecontatos_set.all())

        self.fields['ativo'].widget = forms.RadioSelect()
        self.fields['ativo'].inline_class = True

    def clean(self):
        pronome = self.cleaned_data['pronome_tratamento']
        if 'tipo_autoridade' in self.cleaned_data:
            tipo_autoridade = self.cleaned_data['tipo_autoridade']

            if tipo_autoridade and not pronome:
                self._errors['pronome_tratamento'] = [
                    _('Tendo sido selecionado um tipo de autoridade, \
                    o campo pronome de tratamento se torna obrigatório.')]
       
        tem_filhos = self.cleaned_data['tem_filhos']
        
        quantos_filhos = self.cleaned_data['quantos_filhos']

        if quantos_filhos == None:
            self._errors['quantos_filhos'] = [_('O valor não pode estar vazio. Caso não tenha filhos, informe 0.')]
        else:
            if (tem_filhos == False or tem_filhos == None) and quantos_filhos > 0:
                self._errors['quantos_filhos'] = [_('Se o contato não tem filhos, informe 0 no campo "Quantos filhos?".')]
            elif tem_filhos == True and quantos_filhos < 1: 
                self._errors['quantos_filhos'] = [_('Se o contato tem filhos, informe mais que 0 no campo "Quantos filhos?".')]

        contato = Contato.objects.filter(workspace=self.initial['workspace'],nome=self.cleaned_data['nome'])

        if contato.count() > 0:
            # Inclusão - Se não tiver instância
            if self.instance.nome == '':
                self._errors['nome'] = [_('Já existe um contato com esse nome.')]
            # Edição - Se tiver instância, verifica o contato do banco. Se tiver e o nome for diferente do nome da instância, é porque o usuário está tentando alterar o nome para um já existente.
            elif contato != None and self.instance.nome != contato.first().nome:
                self._errors['nome'] = [_('Já existe um contato com esse nome.')]

class PerfilForm(ModelForm):

    class Meta:
        model = Contato
        fields = ['nome',
                  'nome_social',
                  'apelido',
                  'data_nascimento',
                  'estado_civil',
                  'sexo',
                  'identidade_genero',
                  'nivel_instrucao',
                  'naturalidade',
                  'estado',
                  'tem_filhos',
                  'quantos_filhos',
                  'profissao',
                  'tipo_autoridade',
                  'cargo',
                  'nome_pai',
                  'nome_mae',
                  'numero_sus',
                  'cpf',
                  'titulo_eleitor',
                  'rg',
                  'rg_orgao_expedidor',
                  'rg_data_expedicao']
       
    data_nascimento = forms.DateField(
        required=False,
        label='Data de nascimento',
        widget=DateInput(),
    )

    def __init__(self, *args, **kwargs):

        instance = None
        super(PerfilForm, self).__init__(*args, **kwargs)

        if isinstance(self.instance, Perfil):
            instance = self.instance

        self.fields['cpf'].widget.attrs['class'] = 'cpf'
        self.fields['numero_sus'].widget.attrs['class'] = 'numero_sus'
        self.fields['rg'].widget.attrs['class'] = 'rg'
        self.fields['titulo_eleitor'].widget.attrs['class'] = 'titulo_eleitor'

        #if 'tipo_autoridade' in self.fields:
        #    self.fields['tipo_autoridade'].widget.attrs.update(
        #        {'onchange': 'atualizaPronomes(event)'})

        #self.fields['pronome_tratamento'].widget = forms.RadioSelect()
        #self.fields['pronome_tratamento'].queryset = \
        #    PronomeTratamento.objects.order_by(
        #        'prefixo_nome_singular_m', 'nome_por_extenso')

        #if 'tipo_autoridade' in self.fields and\
        #        instance and instance.tipo_autoridade:
        #    pronomes_choice = instance.tipo_autoridade.pronomes.order_by(
        #        'prefixo_nome_singular_m', 'nome_por_extenso')
        #else:
        #    pronomes_choice = self.fields['pronome_tratamento'].queryset

        #self.fields['pronome_tratamento'].choices = [
        #    (p.pk, '%s, %s - %s - %s - %s - %s - %s - %s' % (
        #        p.prefixo_nome_singular_m,
        #        p.prefixo_nome_singular_f,
        #        p.nome_por_extenso,
        #        p.abreviatura_singular_m,
        #        p.abreviatura_plural_m,
        #        p.vocativo_direto_singular_m,
        #        p.vocativo_indireto_singular_m,
        #        p.enderecamento_singular_m))
        #    for p in pronomes_choice]

        #self.fields['pronome_tratamento'].help_text = ''

    def clean(self):
        #pronome = self.cleaned_data['pronome_tratamento']
        #if 'tipo_autoridade' in self.cleaned_data:
        #    tipo_autoridade = self.cleaned_data['tipo_autoridade']

        #    if tipo_autoridade and not pronome:
        #        self._errors['pronome_tratamento'] = [
        #            _('Tendo sido selecionado um tipo de autoridade, \
        #            o campo pronome de tratamento se torna obrigatório.')]
       
        tem_filhos = self.cleaned_data['tem_filhos']
        
        quantos_filhos = self.cleaned_data['quantos_filhos']

        if quantos_filhos == None:
            self._errors['quantos_filhos'] = [_('O valor não pode estar vazio. Caso não tenha filhos, informe 0.')]
        else:
            if (tem_filhos == False or tem_filhos == None) and quantos_filhos > 0:
                self._errors['quantos_filhos'] = [_('Se o contato não tem filhos, informe 0 no campo "Quantos filhos?".')]
            elif tem_filhos == True and quantos_filhos < 1: 
                self._errors['quantos_filhos'] = [_('Se o contato tem filhos, informe mais que 0 no campo "Quantos filhos?".')]

class ContatoFragmentPronomesForm(forms.Form):

    pronome_tratamento = forms.ModelChoiceField(
        label=Contato._meta.get_field('pronome_tratamento').verbose_name,
        queryset=PronomeTratamento.objects.all(),
        required=False)

    def __init__(self, *args, **kwargs):

        super(ContatoFragmentPronomesForm, self).__init__(
            *args, **kwargs)

        self.fields['pronome_tratamento'].widget = forms.RadioSelect()

        if 'instance' in self.initial:
            self.fields['pronome_tratamento'].queryset = self.initial[
                'instance'].pronomes.order_by(
                'nome_por_extenso')
        else:
            self.fields['pronome_tratamento'].queryset = \
                PronomeTratamento.objects.order_by(
                'nome_por_extenso')
     
        self.fields['pronome_tratamento'].choices = [
            (p.pk, '%s ( "%s" ou "%s" )' % (
                p.nome_por_extenso,
                p.enderecamento_singular_m,
                p.enderecamento_singular_f))
                #p.vocativo_direto_singular_m,
                #p.vocativo_direto_singular_f
            for p in self.fields['pronome_tratamento'].queryset]

        self.fields['pronome_tratamento'].help_text = _('O pronome de \
        tratamento é opcional, mas será \
        obrigatório caso seja selecionado um tipo de autoridade.')

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.disable_csrf = True

class EnderecoForm(ModelForm):

    class Meta:
        model = Endereco
        fields = ['tipo', 'id',
                  'trecho',
                  'endereco',
                  'numero',
                  'complemento',
                  'cep',
                  'estado',
                  'municipio',
                  'bairro',
                  'distrito',
                  'regiao_municipal',
                  'principal',
                  'permite_contato',
                  'observacoes',
                  'ponto_referencia']

    def __init__(self, *args, **kwargs):

        super(EnderecoForm, self).__init__(*args, **kwargs)

        self.fields['cep'].widget.attrs['class'] = 'cep'
        self.fields['endereco'].widget.attrs['autocomplete'] = 'on'

        self.fields['numero'].widget.attrs['class'] = 'numero_endereco'

        self.fields['trecho'].queryset = Trecho.objects.all()
        self.fields['trecho'].widget = forms.HiddenInput()

        # Utilizando template bootstrap3 customizado
        self.fields['principal'].widget = forms.RadioSelect()
        self.fields['principal'].inline_class = True

        self.fields['permite_contato'].widget = forms.RadioSelect()
        self.fields['permite_contato'].inline_class = True

    def clean(self):

        print('')

#       principais = Endereco.objects.filter(

#        pronome = self.cleaned_data['pronome_tratamento']
#        if 'tipo_autoridade' in self.cleaned_data:
#            tipo_autoridade = self.cleaned_data['tipo_autoridade']

#            if tipo_autoridade and not pronome:
#                self._errors['pronome_tratamento'] = [
#                    _('Tendo sido selecionado um tipo de autoridade, \
#                    o campo pronome de tratamento se torna obrigatório.')]

class TelefoneForm(ModelForm):

    class Meta:
        model = Telefone
        fields = ['telefone',
                  'tipo',
                  'operadora',
                  'whatsapp',
                  'ramal',
                  'principal',
                  'permite_contato',
                  'proprio',
                  'de_quem_e']

    def __init__(self, *args, **kwargs):

        super(TelefoneForm, self).__init__(*args, **kwargs)

        self.fields['whatsapp'].widget = forms.RadioSelect()
        self.fields['whatsapp'].inline_class = True
        
        self.fields['principal'].widget = forms.RadioSelect()
        self.fields['principal'].inline_class = True

        self.fields['proprio'].widget = forms.RadioSelect()
        self.fields['proprio'].inline_class = True

        self.fields['permite_contato'].widget = forms.RadioSelect()
        self.fields['permite_contato'].inline_class = True

class EmailForm(ModelForm):

    class Meta:
        model = Email
        fields = ['email',
                  'tipo',
                  'principal',
                  'permite_contato']

    def __init__(self, *args, **kwargs):

        super(EmailForm, self).__init__(*args, **kwargs)

        self.fields['principal'].widget = forms.RadioSelect()
        self.fields['principal'].inline_class = True

        self.fields['permite_contato'].widget = forms.RadioSelect()
        self.fields['permite_contato'].inline_class = True

class TipoAutoridadeForm(ModelForm):

    class Meta:
        model = TipoAutoridade
        fields = ['descricao',
                  'pronomes']

    def __init__(self, *args, **kwargs):

        super(TipoAutoridadeForm, self).__init__(*args, **kwargs)

        self.fields[
            'pronomes'].widget = forms.CheckboxSelectMultiple()

        self.fields['pronomes'].choices = [
            (p.pk, '%s, %s - %s - %s - %s - %s - %s - %s' % (
                p.prefixo_nome_singular_m,
                p.prefixo_nome_singular_f,
                p.nome_por_extenso,
                p.abreviatura_singular_m,
                p.abreviatura_plural_m,
                p.vocativo_direto_singular_m,
                p.vocativo_indireto_singular_m,
                p.enderecamento_singular_m))
            for p in self.fields[
                'pronomes'].queryset.order_by(
                'prefixo_nome_singular_m', 'nome_por_extenso')]
        """
        self.fields['pronomes'] = Field(
            'pronomes',
            template="cerimonial/layout/pronometratamento_checkbox.html")
        """


class ProcessoForm(ModelForm):
    q = forms.CharField(
        required=False,
        label='Busca por Contatos',
        widget=forms.TextInput(
            attrs={'type': 'search'}))

    class Meta:
        model = Processo
        fields = ['data_abertura',
                  'titulo',
                  'importancia',
                  'status',
                  'historico',
                  'num_controle',
                  'materia_cam',
                  'link_cam',
                  'link_pref_orgao',
                  'proto_pref',
                  'proto_orgao',
                  'oficio_cam',
                  'oficio_pref',
                  'oficio_orgao',
                  'instituicao',
                  'orgao',
                  'rua',
                  'bairro',
                  'urgente',
                  'data_solucao',
                  'data_envio',
                  'data_protocolo',
                  'data_retorno',
                  'importancia',
                  'classificacao',
                  'observacoes',
                  'solucao',
                  'q',
                  'contatos',
                  'topicos',
                  'assuntos']

    def __init__(self, *args, **kwargs):
        yaml_layout = kwargs.pop('yaml_layout')

        q_field = Div(
            FieldWithButtons(
                Field('q',
                      placeholder=_('Filtrar lista'),
                      autocomplete='off',
                      type='search',
                      onkeypress='atualizaContatos(event)'),
                StrictButton(
                    _('Filtrar'), css_class='btn-default',
                    type='button', onclick='atualizaContatos(event)')),
            Div(css_class='form-group-contato-search')
        )

        q = [_('Seleção de Contatos'),
             [(q_field, 5),
              (Div(Field('contatos'), css_class='form-group-contatos'), 7)]
             ]
        yaml_layout.append(q)

        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(*yaml_layout)

        #self.fields['data_abertura'] = forms.DateField(widget=SelectDateWidget(), label='Joining Date', initial=date.today())

        super(ProcessoForm, self).__init__(*args, **kwargs)

        if not self.instance.pk:
            self.fields['data_abertura'].initial = date.today()

        self.fields['q'].help_text = _('Digite parte do nome, nome social ou '
                                       'apelido do Contato que você procura.')

        self.fields['topicos'].widget = forms.SelectMultiple(
            attrs={'size': '8'})
        self.fields['topicos'].queryset = TopicoProcesso.objects.all()

        self.fields['assuntos'].widget = forms.SelectMultiple(
            attrs={'size': '8'})
        self.fields['assuntos'].queryset = AssuntoProcesso.objects.all()

        # Utilizando template bootstrap3 customizado
        self.fields['importancia'].widget = forms.RadioSelect()
        self.fields['importancia'].inline_class = True
        self.fields['importancia'].choices = IMPORTANCIA_CHOICE

        self.fields['urgente'].widget = forms.RadioSelect()
        self.fields['urgente'].inline_class = True

        self.fields['bairro'].queryset = Bairro.objects.filter(municipio=4891)

        self.fields['contatos'].widget = forms.CheckboxSelectMultiple()
        self.fields['contatos'].queryset = Contato.objects.all()
        self.fields['contatos'].choices = [
            (c.pk, c) for c in self.instance.contatos.order_by('nome')]\
            if self.instance.pk else []
        self.fields['contatos'].help_text = _(
            'Procure por Contatos na caixa de buscas e arraste '
            'para esta caixa os Contatos interessados neste Processo.')


class ProcessoContatoForm(ModelForm):

    class Meta:
        model = ProcessoContato
        fields = ['data_abertura',
                  'titulo',
                  'importancia',
                  'status',
                  'historico',
                  'classificacao',
                  'observacoes',
                  'solucao',
                  'link_cam',
                  'link_pref_orgao',
                  'num_controle',
                  'materia_cam',
                  'proto_pref',
                  'proto_orgao',
                  'oficio_cam',
                  'oficio_pref',
                  'oficio_orgao',
                  'instituicao',
                  'orgao',
                  'rua',
                  'bairro',
                  'urgente',
                  'data_solucao',
                  'data_envio',
                  'data_protocolo',
                  'data_retorno',
                  'topicos',
                  'assuntos']

    def __init__(self, *args, **kwargs):
        super(ProcessoContatoForm, self).__init__(*args, **kwargs)

        if not self.instance.pk:
            self.fields['data_abertura'].initial = date.today()

        self.fields['topicos'].widget = forms.SelectMultiple(
            attrs={'size': '8'})
        self.fields['topicos'].queryset = TopicoProcesso.objects.all()

        self.fields['assuntos'].widget = forms.SelectMultiple(
            attrs={'size': '8'})
        self.fields['assuntos'].queryset = AssuntoProcesso.objects.all()

        # Utilizando template bootstrap3 customizado
        self.fields['importancia'].widget = forms.RadioSelect()
        self.fields['importancia'].inline_class = True
        self.fields['importancia'].choices = IMPORTANCIA_CHOICE

        self.fields['bairro'].queryset = Bairro.objects.filter(municipio=4891)

        #self.fields['status'].widget = forms.RadioSelect()
        # self.fields['status'].inline_class = True
        self.fields['status'].choices = [
            (ass.pk, ass) for ass in StatusProcesso.objects.order_by('id')]

        #self.fields['classificacao'].widget = forms.CheckboxSelectMultiple()
        # self.fields['classificacao'].inline_class = True


class ContatoFragmentSearchForm(forms.Form):
    """q = forms.CharField(
        required=False,
        label='Busca por Contatos',
        widget=forms.TextInput(
            attrs={'type': 'search'}))"""

    contatos_search = forms.ModelChoiceField(
        label='',
        queryset=Contato.objects.all(),
        required=False)

    def __init__(self, *args, **kwargs):

        super(ContatoFragmentSearchForm, self).__init__(*args, **kwargs)

        """q_field = FieldWithButtons(
            Field('q',
                  placeholder=_('Filtrar lista'),
                  autocomplete='off'),
            StrictButton(
                _('Filtrar'), css_class='btn-default',
                type='button', onclick='atualizaContatos(event)'))"""

        self.fields['contatos_search'].widget = forms.CheckboxSelectMultiple()

        queryset = Contato.objects.filter(
            workspace=self.initial['workspace']).exclude(
            pk__in=self.initial['pks_exclude'])

        query = normalize(self.initial['q'])

        query = query.split(' ')
        if query:
            q = Q()
            for item in query:
                if not item:
                    continue
                q = q & Q(search__unaccent__icontains=item)

            if q:
                queryset = queryset.filter(q)

        queryset = queryset[:10]
        self.fields['contatos_search'].queryset = queryset

        self.fields['contatos_search'].choices = [(c.pk, c) for c in queryset]

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Field('contatos_search'),
                css_class='form-group-contatos-search'))
        self.helper.form_tag = False
        self.helper.disable_csrf = True

class GrupoDeContatosForm(ModelForm):
    q = forms.CharField(
        required=False,
        label='Busca por Contatos',
        widget=forms.TextInput(
            attrs={'type': 'search'}))

    class Meta:
        model = GrupoDeContatos
        fields = ['nome',
                  'q',
                  'contatos', ]

    def __init__(self, *args, **kwargs):
        yaml_layout = kwargs.pop('yaml_layout')

        q_field = Div(
            FieldWithButtons(
                Field('q',
                      placeholder=_('Filtrar lista'),
                      autocomplete='off',
                      type='search',
                      onkeypress='atualizaContatos(event)'),
                StrictButton(
                    _('Filtrar'), css_class='btn-default',
                    type='button', onclick='atualizaContatos(event)')),
            Div(css_class='form-group-contato-search')
        )

        q = [_('Seleção de Contatos'),
             [(q_field, 5),
              (Div(Field('contatos'), css_class='form-group-contatos'), 7)]
             ]
        yaml_layout.append(q)

        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(*yaml_layout)

        super(GrupoDeContatosForm, self).__init__(*args, **kwargs)

        self.fields['q'].help_text = _('Digite parte do nome, nome social ou '
                                       'apelido do contato que você procura.')

        self.fields['contatos'].widget = forms.CheckboxSelectMultiple()

        self.fields['contatos'].queryset = Contato.objects.all()

        self.fields['contatos'].choices = [
            (c.pk, c) for c in self.instance.contatos.order_by('nome')]\
            if self.instance.pk else []

        self.fields['contatos'].help_text = _(
            'Procure por contatos na caixa de buscas e arraste '
            'para esta caixa aqueles interessados neste processo.')


class RangeWidgetNumber(forms.MultiWidget):

    def __init__(self, attrs=None):
        widgets = (forms.NumberInput(
            attrs={'class': 'numberinput',
                   'placeholder': 'Mínimo'}),
                   forms.NumberInput(
            attrs={'class': 'numberinput',
                   'placeholder': 'Máximo'}))
        super(RangeWidgetNumber, self).__init__(widgets, attrs)

    def decompress(self, value):
        if value:
            return [value.start, value.stop]
        return [None, None]

    def format_output(self, rendered_widgets):
        html = '<div class="col-sm-6">%s</div><div class="col-sm-6">%s</div>'\
            % tuple(rendered_widgets)
        return '<div class="row">%s</div>' % html


class RangeWidgetOverride(forms.MultiWidget):

    def __init__(self, attrs=None):
        widgets = (forms.DateInput(format='%d/%m/%Y',
                                   attrs={'class': 'dateinput',
                                          'placeholder': 'Inicial'}),
                   forms.DateInput(format='%d/%m/%Y',
                                   attrs={'class': 'dateinput',
                                          'placeholder': 'Final'}))
        super(RangeWidgetOverride, self).__init__(widgets, attrs)

    def decompress(self, value):
        if value:
            return [value.start, value.stop]
        return [None, None]

    def format_output(self, rendered_widgets):
        html = '<div class="col-sm-6">%s</div><div class="col-sm-6">%s</div>'\
            % tuple(rendered_widgets)
        return '<div class="row">%s</div>' % html


class MethodRangeFilter(MethodFilter, RangeFilter):
    pass

class MethodChoiceFilter(MethodFilter, ChoiceFilter):
    pass

class MethodBooleanFilter(MethodFilter, BooleanFilter):
    pass

class MethodMultipleChoiceFilter(MethodFilter, MultipleChoiceFilter):
    pass

class MethodNumberFilter(MethodFilter, NumberFilter):
    pass

class MethodIntegerFilter(MethodFilter, NumberFilter):
    field_class = forms.IntegerField

class MethodModelChoiceFilter(MethodFilter, ModelChoiceFilter):
    pass

class MethodModelMultipleChoiceFilter(MethodFilter, ModelMultipleChoiceFilter):
    pass


class SubmitFilterPrint(BaseInput):

    input_type = 'submit'

    def __init__(self, *args, **kwargs):
        self.field_classes = 'btn'
        super(SubmitFilterPrint, self).__init__(*args, **kwargs)


def filter_impresso(queryset, value):
    return queryset

def filter_pk_selecionados(queryset, value):
    return queryset

class ImpressoEnderecamentoFilterSet(FilterSet):

    filter_overrides = {models.DateField: {
        'filter_class': MethodFilter,
        'extra': lambda f: {
            'label': 'Período de aniversário',
            'widget': RangeWidgetOverride}
    }}

    FEMININO = 'F'
    MASCULINO = 'M'
    AMBOS = ''
    SEXO_CHOICE = ((AMBOS, _('Ambos')),
                   (FEMININO, _('Feminino')),
                   (MASCULINO, _('Masculino')))

    DEPOIS_PRONOME = 'DP'
    LINHA_NOME = 'LN'
    DEPOIS_NOME = 'DN'
    LOCAL_CARGO_CHOICE = ((DEPOIS_PRONOME, _('Depois do pronome')),
                         (LINHA_NOME, _('Antes do nome')),
                         (DEPOIS_NOME, _('Entre o nome e o endereço')))

    BOTH_CHOICE = [(None, _('Ambos'))] + YES_NO_CHOICES

    NENHUMA = 'N'
    FAMILIA = 'FAM'
    ESPOSO = 'EPO'
    ESPOSA = 'EPA'
    COMPANHEIRO = 'CPO'
    COMPANHEIRA = 'CPA'

    POS_NOME_CHOICE = ((NENHUMA, _('Nenhuma')),
                         (FAMILIA, _('"e família"')),
                         (ESPOSO, _('"e esposo"')),
                         (ESPOSA, _('"e esposa"')),
                         (COMPANHEIRO, _('"e companheiro"')),
                         (COMPANHEIRA, _('"e companheira"')))

    pk = MethodIntegerFilter()
    
    search = MethodFilter()
    
    search_documentos = MethodFilter()

    sexo = ChoiceFilter(choices=SEXO_CHOICE)
    
    #sem_data = BooleanFilter()

    estado_civil = ModelChoiceFilter(
        required=False,
        queryset=EstadoCivil.objects.all())

    tem_filhos = BooleanFilter()

    ativo = BooleanFilter()

    idade = MethodRangeFilter(
        label=_('Idade entre:'),
        widget=RangeWidgetNumber)

    grupo = MethodModelMultipleChoiceFilter(
        required=False,
        label=_('Grupo de contatos:'),
        queryset=GrupoDeContatos.objects.all())
    
    search_endereco = MethodFilter()

    bairro = MethodModelMultipleChoiceFilter(
        required=False,
        label=_('Bairro de Novo Hamburgo'),
        queryset=Bairro.objects.filter(municipio=4891))

    cep = MethodFilter(label=_('CEP'))

    municipio = MethodModelMultipleChoiceFilter(
        required=False,
        label=_('Município do Rio Grande do Sul'),
        queryset=Municipio.objects.filter(estado=21))

    impresso = ModelChoiceFilter(
        required=False,
        queryset=ImpressoEnderecamento.objects.all(),
        action=filter_impresso,
        initial=2)

    imprimir_pronome = MethodChoiceFilter(
        choices=YES_NO_CHOICES, initial=False)

    pronome_padrao = MethodChoiceFilter(
        choices=YES_NO_CHOICES, initial=False)

    imprimir_cargo = MethodChoiceFilter(
        choices=YES_NO_CHOICES, initial=False)

    nome_maiusculo = MethodChoiceFilter(
        label=_('Nome maiúsculo'),
        choices=YES_NO_CHOICES, initial=False)

    ocultar_sem_endereco = MethodBooleanFilter()

    local_cargo = MethodChoiceFilter(
        label=_('Local para imprimir o cargo'),
        choices=LOCAL_CARGO_CHOICE)

    pos_nome = MethodChoiceFilter(
        label=_('Expressão pós-nome'),
        choices=POS_NOME_CHOICE)

    def filter_grupo(self, queryset, value):
        if value:
            queryset = queryset.filter(grupodecontatos_set__in=value)

        return queryset

    def filter_bairro(self, queryset, value):
        if value:
            queryset = queryset.filter(
                endereco_set__bairro__in=value,
                endereco_set__permite_contato=True)

        return queryset

    def filter_municipio(self, queryset, value):
        if value:
            queryset = queryset.filter(
                endereco_set__municipio__in=value,
                endereco_set__permite_contato=True)

        return queryset

    def filter_pk(self, queryset, value):
        queryset = queryset.filter(pk=value)
        return queryset

    def filter_local_cargo(self, queryset, value):
        return queryset

    def filter_imprimir_pronome(self, queryset, value):
        return queryset

    def filter_pronome_padrao(self, queryset, value):
        return queryset

    def filter_ocultar_sem_endereco(self, queryset, value):
        if(value == True):
            queryset = queryset.filter(
                    endereco_set__permite_contato=True)

        return queryset

    def filter_imprimir_cargo(self, queryset, value):
        return queryset

    def filter_nome_maiusculo(self, queryset, value):
        return queryset

    def filter_idade(self, queryset, value):
        idi = int(value.start) if value.start is not None else 0
        idf = int(value.stop) if value.stop is not None else 100
        
        if idi > idf:
            a = idi
            idi = idf
            idf = a

        # lim inicial-dt.mais antiga
        li = date.today() - relativedelta(years=idf + 1)
        # lim final - dt. mais nova
        lf = date.today() - relativedelta(years=idi)

        return queryset.filter(data_nascimento__gt=li,
                               data_nascimento__lte=lf)

    def filter_search(self, queryset, value):

        query = normalize(value)

        query = query.split(' ')
        if query:
            q = Q()
            for item in query:
                if not item:
                    continue
                q = q & Q(search__unaccent__icontains=item)

            if q:
                queryset = queryset.filter(q)
        return queryset

    def filter_sem_data(self, queryset, value):

        print(value)

        return queryset

    def filter_search_endereco(self, queryset, value):

        query = normalize(value)

        query = query.split(' ')
        if query:
            q = Q()
            for item in query:
                if not item:
                    continue
                q = q & (Q(endereco_set__endereco__unaccent__icontains=item) | 
                         Q(endereco_set__ponto_referencia__unaccent__icontains=item) |
                         Q(endereco_set__complemento__unaccent__icontains=item))
                q = q & Q(endereco_set__permite_contato=True)

            print(q)

            if q:
                queryset = queryset.filter(q)
        return queryset

    def filter_search_documentos(self, queryset, value):

        if value: 
            q = Q()
            q = q & (Q(cpf=value) | 
                     Q(rg=value) |
                     Q(cnpj=value) |
                     Q(ie=value))
            queryset = queryset.filter(q)

        return queryset

    def filter_cep(self, queryset, value):

        query = normalize(value.strip())
        
        q = Q()
        
        if query:
            q = q & Q(endereco_set__cep=value)
            q = q & Q(endereco_set__permite_contato=True)

        if q:
            queryset = queryset.filter(q)
        
        return queryset

    def filter_data_nascimento(self, queryset, value):

        if not value[0] and not value[1]:
            return queryset

        now = datetime.datetime.strptime(value[0], "%d/%m/%Y").date()
        then = datetime.datetime.strptime(value[1], "%d/%m/%Y").date()
        if now > then:
            a = now
            now = then
            then = a

        # Build the list of month/day tuples.
        monthdays = [(now.month, now.day)]
        while now <= then:
            monthdays.append((now.month, now.day))
            now += timedelta(days=1)

        # Tranform each into queryset keyword args.
        monthdays = (dict(zip(("data_nascimento__month",
                               "data_nascimento__day"), t))
                     for t in monthdays)

        # Compose the djano.db.models.Q objects together for a single query.
        query = reduce(operator.or_, (Q(**d) for d in monthdays))

        # Run the query.
        return queryset.extra(select={
            'month': 'extract( month from data_nascimento )',
            'day': 'extract( day from data_nascimento )', }
        ).order_by('month', 'day', 'nome').filter(query)

    class Meta:
        model = Contato
        fields = ['search',
                  'search_endereco',
                  'sexo',
                  'tem_filhos',
                  'data_nascimento',
                  'tipo_autoridade'
		  ]

    def __init__(self, data=None,
                 queryset=None, prefix=None, strict=None, **kwargs):

        workspace = kwargs.pop('workspace')

        super(ImpressoEnderecamentoFilterSet, self).__init__(
            data=data,
            queryset=queryset, prefix=prefix, strict=strict, **kwargs)

        col1 = to_row([
            ('pk', 2),
            ('search', 7),
            ('ativo', 3),
            ('sexo', 3),
            ('estado_civil', 3),
            ('tem_filhos', 3),
            ('search_documentos', 3),
            ('data_nascimento', 6),
            ('idade', 6),
            #('sem_data', 2),
            ('search_endereco', 6),
            ('cep', 3),
            ('ocultar_sem_endereco', 3),
            ('bairro', 6),
            ('municipio', 6),
            ('grupo', 6),
            ('tipo_autoridade', 6),
        ])

        col2 = to_row([
            ('impresso', 12),
            ('nome_maiusculo', 12),
            ('imprimir_pronome', 12),
            ('pronome_padrao', 12),
            ('pos_nome', 12),
            ('imprimir_cargo', 12),
            ('local_cargo', 12),
        ])

        row = to_row(
            [(Fieldset(
                _('Filtro de Contatos'),
                col1,
                to_row([(SubmitFilterPrint(
                    'filter',
                    value=_('Filtrar'), css_class='btn-default pull-right',
                    type='submit'), 12)])), 9),
             (Fieldset(
                 _('Impressão'),
                 col2,
                 to_row([(SubmitFilterPrint(
                     'print',
                     value=_('Imprimir'), css_class='btn-primary pull-right',
                     type='submit'), 12)])), 3)])

        self.form.helper = FormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            row,
        )

        self.form.fields['pk'].label = 'Código'

        self.form.fields['search'].label = 'Nome, nome social ou apelido'
       
        self.form.fields['search_endereco'].label = 'Endereço, complemento ou ponto de referência'

        self.form.fields['search_documentos'].label = 'RG, CPF, CNPJ ou IE'

        self.form.fields['data_nascimento'].label = 'Período de aniversário'
        
        #self.form.fields['sem_data'].label = 'Sem data'
        
        self.form.fields['ativo'].label = _('Ativo?')

        self.form.fields['cep'].widget.attrs['class'] = 'cep'
        
        self.form.fields['imprimir_pronome'].widget = forms.RadioSelect()
        self.form.fields['imprimir_pronome'].inline_class = True

        self.form.fields['pronome_padrao'].widget = forms.RadioSelect()
        self.form.fields['pronome_padrao'].inline_class = True
        self.form.fields['pronome_padrao'].label = _('<font color=red>Utilizar pronome padrão</font>')

        self.form.fields['ocultar_sem_endereco'].inline_class = True
        self.form.fields['ocultar_sem_endereco'].label = _('<font color=red>Ocultar sem endereço?</font>')

        self.form.fields['imprimir_cargo'].widget = forms.RadioSelect()
        self.form.fields['imprimir_cargo'].inline_class = True

        self.form.fields['nome_maiusculo'].widget = forms.RadioSelect()
        self.form.fields['nome_maiusculo'].inline_class = True

        self.form.fields['grupo'].queryset = GrupoDeContatos.objects.filter(
            workspace=workspace)

        self.form.fields['bairro'].queryset = Bairro.objects.filter(municipio=4891)
        
        self.form.fields['municipio'].queryset = Municipio.objects.filter(estado=21)

class ProcessoIndividualFilterSet(FilterSet):

    filter_overrides = {models.DateField: {
        'filter_class': MethodFilter,
        'extra': lambda f: {
            'label': '%s (%s)' % (f.verbose_name, _('período')),
            'widget': RangeWidgetOverride}
    }}

    pk = MethodIntegerFilter()

    search = MethodFilter()

    search_numeros = MethodFilter()
    
    search_contato = MethodFilter()

    dias_envio = MethodRangeFilter(
        label=_('Há quantos dias foi enviado?'),
        widget=RangeWidgetNumber)

    dias_retorno = MethodRangeFilter(
        label=_('Tempo entre envio e retorno'),
        widget=RangeWidgetNumber)

    dias_abertura = MethodRangeFilter(
        label=_('Tempo entre abertura e solução'),
        widget=RangeWidgetNumber)

    importancia = MethodMultipleChoiceFilter(
        required=False,
        label=_('Importância'),
        choices=IMPORTANCIA_CHOICE)

    status = MethodModelMultipleChoiceFilter(
        required=False,
        queryset=StatusProcesso.objects.all())

    classificacao = MethodModelMultipleChoiceFilter(
        required=False,
        label=_('Classificações'),
        queryset=ClassificacaoProcesso.objects.all())

    search_endereco = MethodFilter()
    
    search_envolvidos = MethodFilter()

    pk_selecionados = MethodFilter(
        required=False,
        action=filter_pk_selecionados,
        )

    bairro = MethodModelMultipleChoiceFilter(
        required=False,
        label=_('Bairro de Novo Hamburgo'),
        queryset=Bairro.objects.filter(municipio=4891))

    urgente = BooleanFilter()

    def filter_classificacao(self, queryset, value):
        if value:
            queryset = queryset.filter(classificacao__in=value)

        return queryset

    def filter_importancia(self, queryset, value):
        if value:
            queryset = queryset.filter(importancia__in=value)

        return queryset

    def filter_status(self, queryset, value):
        if value:
            queryset = queryset.filter(status__in=value)

        return queryset

    def filter_bairro(self, queryset, value):
        if value:
            queryset = queryset.filter(bairro__in=value)

        return queryset

    def filter_pk(self, queryset, value):
        queryset = queryset.filter(pk=value)
        return queryset

    def filter_data_abertura(self, queryset, value):

        if not value[0] and not value[1]:
            return queryset

        inicial = None
        final = None

        if(value[0] != ''):
            inicial = datetime.datetime.strptime(value[0], "%d/%m/%Y").date()
        if(value[1] != ''):
            final = datetime.datetime.strptime(value[1], "%d/%m/%Y").date()
   
        if(inicial != None and final != None):
            if inicial > final:
                inicial, final = final, inicial
            range_select = Q(data_abertura__range=[inicial, final])
        elif(inicial != None):
            range_select = Q(data_abertura__gte=inicial)
        elif(final != None):
            range_select = Q(data_abertura__lte=final)

        # Run the query.
        return queryset.filter(range_select)

    def filter_dias_envio(self, queryset, value):
        di = int(value.start) if value.start is not None else 0
        df = int(value.stop) if value.stop is not None else 5000

        if di > df:
            a = di
            di = df
            df = a

        # lim inicial-dt.mais antiga
        li = date.today() - relativedelta(days=df + 1)
        # lim final - dt. mais nova
        lf = date.today() - relativedelta(days=di)

        return queryset.filter(data_envio__gt=li,
                               data_envio__lte=lf)

    def filter_dias_retorno(self, queryset, value):
        di = int(value.start) if value.start is not None else 0
        df = int(value.stop) if value.stop is not None else 5000

        if di > df:
            a = di
            di = df
            df = a

        return queryset.extra(where = ["""DATE_PART('day', data_retorno::timestamp - data_envio::timestamp) >= %s AND\
                                       DATE_PART('day', data_retorno::timestamp - data_envio::timestamp) <= %s""" % (di, df)])

    def filter_dias_abertura(self, queryset, value):
        di = int(value.start) if value.start is not None else 0
        df = int(value.stop) if value.stop is not None else 5000

        if di > df:
            a = di
            di = df
            df = a

        return queryset.extra(where = ["""DATE_PART('day', data_solucao::timestamp - data_abertura::timestamp) >= %s AND\
                                       DATE_PART('day', data_solucao::timestamp - data_abertura::timestamp) <= %s""" % (di, df)])

    def filter_data_envio(self, queryset, value):

        if not value[0] and not value[1]:
            return queryset

        inicial = None
        final = None

        if(value[0] != ''):
            inicial = datetime.datetime.strptime(value[0], "%d/%m/%Y").date()
        if(value[1] != ''):
            final = datetime.datetime.strptime(value[1], "%d/%m/%Y").date()
   
        if(inicial != None and final != None):
            if inicial > final:
                inicial, final = final, inicial
            range_select = Q(data_envio__range=[inicial, final])
        elif(inicial != None):
            range_select = Q(data_envio__gte=inicial)
        elif(final != None):
            range_select = Q(data_envio__lte=final)

        # Run the query.
        return queryset.filter(range_select)

    def filter_data_protocolo(self, queryset, value):

        if not value[0] and not value[1]:
            return queryset

        inicial = None
        final = None

        if(value[0] != ''):
            inicial = datetime.datetime.strptime(value[0], "%d/%m/%Y").date()
        if(value[1] != ''):
            final = datetime.datetime.strptime(value[1], "%d/%m/%Y").date()
   
        if(inicial != None and final != None):
            if inicial > final:
                inicial, final = final, inicial
            range_select = Q(data_protocolo__range=[inicial, final])
        elif(inicial != None):
            range_select = Q(data_protocolo__gte=inicial)
        elif(final != None):
            range_select = Q(data_protocolo__lte=final)

        # Run the query.
        return queryset.filter(range_select)

    def filter_data_retorno(self, queryset, value):

        if not value[0] and not value[1]:
            return queryset

        inicial = None
        final = None

        if(value[0] != ''):
            inicial = datetime.datetime.strptime(value[0], "%d/%m/%Y").date()
        if(value[1] != ''):
            final = datetime.datetime.strptime(value[1], "%d/%m/%Y").date()
   
        if(inicial != None and final != None):
            if inicial > final:
                inicial, final = final, inicial
            range_select = Q(data_retorno__range=[inicial, final])
        elif(inicial != None):
            range_select = Q(data_retorno__gte=inicial)
        elif(final != None):
            range_select = Q(data_retorno__lte=final)

        # Run the query.
        return queryset.filter(range_select)

    def filter_data_solucao(self, queryset, value):

        if not value[0] and not value[1]:
            return queryset

        inicial = None
        final = None

        if(value[0] != ''):
            inicial = datetime.datetime.strptime(value[0], "%d/%m/%Y").date()
        if(value[1] != ''):
            final = datetime.datetime.strptime(value[1], "%d/%m/%Y").date()
   
        if(inicial != None and final != None):
            if inicial > final:
                inicial, final = final, inicial
            range_select = Q(data_solucao__range=[inicial, final])
        elif(inicial != None):
            range_select = Q(data_solucao__gte=inicial)
        elif(final != None):
            range_select = Q(data_solucao__lte=final)

        # Run the query.
        return queryset.filter(range_select)

    def filter_search_endereco(self, queryset, value):

        query = normalize(value)

        query = query.split(' ')
        if query:
            q = Q()
            for item in query:
                if not item:
                    continue
                q = q & Q(endereco__unaccent__icontains=item)

            if q:
                queryset = queryset.filter(q)
        return queryset

    def filter_contato(self, queryset, value):

        query = normalize(value)

        query = query.split(' ')
        if query:
            q = Q()
            for item in query:
                if not item:
                    continue
                q = q & (Q(contato_set__nome__unaccent__icontains=item) | 
                         Q(contato_set__nome_social__unaccent__icontains=item) |
                         Q(contato_set__apelido__unaccent__icontains=item))

            if q:
                queryset = queryset.filter(q)
        return queryset

    def filter_search(self, queryset, value):

        query = normalize(value)

        query = query.split(' ')
        if query:
            q = Q()
            for item in query:
                if not item:
                    continue
                q = q & Q(search__unaccent__icontains=item)

            if q:
                queryset = queryset.filter(q)
        return queryset

    def filter_search_numeros(self, queryset, value):

        query = normalize(value)

        if query:
            q = Q()
            for item in query:
                if not item:
                    continue
                q = q & (Q(materia_cam__icontains=item) | 
                         Q(oficio_cam__icontains=item) |
                         Q(oficio_pref__icontains=item) |
                         Q(oficio_orgao__icontains=item) |
                         Q(proto_pref__icontains=item) |
                         Q(proto_orgao__icontains=item))

            if q:
                queryset = queryset.filter(q)
        return queryset

    def filter_search_envolvidos(self, queryset, value):

        query = normalize(value)
        query = query.split(' ')

        if query:
            q = Q()
            for item in query:
                if not item:
                    continue
                q = q & (Q(orgao__unaccent__icontains=item) | 
                         Q(instituicao__unaccent__icontains=item))

            if q:
                queryset = queryset.filter(q)
        return queryset

    class Meta:
        model = Processo
        fields = ['search',
                  'search_contato',
                  'data_abertura',
                  'data_envio',
                  'data_retorno',
                  'data_envio',
                  'data_protocolo',
                  'data_solucao',
                  'dias_envio',
                  'dias_retorno',
                  'dias_abertura',
                  'bairro',
                  'search_numeros',
                  'search_endereco',
                  'search_envolvidos',
                  'topicos',
                  'importancia',
                  'classificacao',
                  'assuntos',
                  'urgente',
                  'status', ]

    def __init__(self, data=None,
                 queryset=None, prefix=None, strict=None, **kwargs):

        workspace = kwargs.pop('workspace')

        super(ProcessoIndividualFilterSet, self).__init__(
            data=data,
            queryset=queryset, prefix=prefix, strict=strict, **kwargs)

        c1_row1 = to_row([
            ('pk', 2),
            ('search', 6),
            ('search_contato', 4),
            ('search_numeros', 4),
            ('data_envio', 4),
            ('data_protocolo', 4),
            ('data_abertura', 4),
            ('data_retorno', 4),
            ('data_solucao', 4),
            ('dias_envio', 4),
            ('dias_retorno', 4),
            ('dias_abertura', 4),
            ('classificacao', 6),
            ('status', 6),
            ('topicos', 6),
            ('assuntos', 6),
            ('bairro', 6),
            ('importancia', 3),
            ('urgente', 3),
            ('search_endereco', 6),
            ('search_envolvidos', 6),
        ])

        c2_row1 = to_row([
            ('pk_selecionados', 12),])


        col1 = Fieldset(
            _('Busca por Processo'),
            c1_row1,
            to_row([
                (SubmitFilterPrint(
                    'filter',
                    value=_('Filtrar'),
                    css_class='btn-default pull-right',
                    type='submit'), 12)
            ]))

        col2 = Fieldset(
            _('Impressão'),
            c2_row1,
            to_row([(SubmitFilterPrint(
                'print',
                value=_('Imprimir'),
                css_class='btn-primary pull-right',
                type='submit'),12)
        ]))

        rows = to_row([
            (col1, 9),
            (col2, 3),
        ])

        self.form.helper = FormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            rows,
        )

        self.form.fields['pk'].label = _('Código')
        self.form.fields['pk_selecionados'].label = _('Códigos selecionados')
        self.form.fields['search'].label = _('Pesquisa por título, histórico, observações ou solução:')
        self.form.fields['search_contato'].label = _('Contatos interessados:')
        self.form.fields['search_numeros'].label = _('Matéria, protocolo ou ofício:')
        self.form.fields['search_endereco'].label = _('Endereço:')
        self.form.fields['search_envolvidos'].label = _('Órgão ou instituição:')
       
class ProcessosFilterSet(FilterSet):

    AGRUPADO_POR_NADA = 'sem_agrupamento'
#    AGRUPADO_POR_TITULO = 'titulo'
    AGRUPADO_POR_IMPORTANCIA = 'importancia'
    AGRUPADO_POR_TOPICO = 'topicos__descricao'
    AGRUPADO_POR_ASSUNTO = 'assuntos__descricao'
    AGRUPADO_POR_STATUS = 'status__descricao'
    AGRUPADO_POR_CLASSIFICACAO = 'classificacao__descricao'

    AGRUPAMENTO_CHOICE = (
        (AGRUPADO_POR_NADA, _('Sem agrupamento')),
#        (AGRUPADO_POR_TITULO, _('Por título')),
        (AGRUPADO_POR_IMPORTANCIA,
         _('Por importância')),
        (AGRUPADO_POR_TOPICO,
         _('Por tópico')),
        (AGRUPADO_POR_ASSUNTO,
         _('Por assunto')),
        (AGRUPADO_POR_STATUS,
         _('Por status')),
        (AGRUPADO_POR_CLASSIFICACAO,
         _('Por classificação')),
    )

    filter_overrides = {models.DateField: {
        'filter_class': MethodFilter,
        'extra': lambda f: {
            'label': '%s (%s)' % (f.verbose_name, _('período')),
            'widget': RangeWidgetOverride}
    }}

    search = MethodFilter()

    search_numeros = MethodFilter()
    
    search_contato = MethodFilter()

    dias_envio = MethodRangeFilter(
        label=_('Há quantos dias foi enviado?'),
        widget=RangeWidgetNumber)

    dias_retorno = MethodRangeFilter(
        label=_('Tempo entre envio e retorno'),
        widget=RangeWidgetNumber)

    dias_abertura = MethodRangeFilter(
        label=_('Tempo entre abertura e solução'),
        widget=RangeWidgetNumber)

    agrupamento = MethodChoiceFilter(
        required=False,
        choices=AGRUPAMENTO_CHOICE)

    importancia = MethodMultipleChoiceFilter(
        required=False,
        label=_('Importância'),
        choices=IMPORTANCIA_CHOICE)

    status = MethodModelMultipleChoiceFilter(
        required=False,
        queryset=StatusProcesso.objects.all())

    classificacao = MethodModelMultipleChoiceFilter(
        required=False,
        label=_('Classificações'),
        queryset=ClassificacaoProcesso.objects.all())

    search_endereco = MethodFilter()
    
    search_envolvidos = MethodFilter()

    bairro = MethodModelMultipleChoiceFilter(
        required=False,
        label=_('Bairro de Novo Hamburgo'),
        queryset=Bairro.objects.filter(municipio=4891))

    urgente = BooleanFilter()

    def filter_agrupamento(self, queryset, value):
        return queryset

    def filter_classificacao(self, queryset, value):
        if value:
            queryset = queryset.filter(classificacao__in=value)

        return queryset

    def filter_importancia(self, queryset, value):
        if value:
            queryset = queryset.filter(importancia__in=value)

        return queryset

    def filter_status(self, queryset, value):
        if value:
            queryset = queryset.filter(status__in=value)

        return queryset

    def filter_bairro(self, queryset, value):
        if value:
            queryset = queryset.filter(bairro__in=value)

        return queryset

    def filter_data_abertura(self, queryset, value):

        if not value[0] and not value[1]:
            return queryset

        inicial = None
        final = None

        if(value[0] != ''):
            inicial = datetime.datetime.strptime(value[0], "%d/%m/%Y").date()
        if(value[1] != ''):
            final = datetime.datetime.strptime(value[1], "%d/%m/%Y").date()
   
        if(inicial != None and final != None):
            if inicial > final:
                inicial, final = final, inicial
            range_select = Q(data_abertura__range=[inicial, final])
        elif(inicial != None):
            range_select = Q(data_abertura__gte=inicial)
        elif(final != None):
            range_select = Q(data_abertura__lte=final)

        # Run the query.
        return queryset.filter(range_select)

    def filter_dias_envio(self, queryset, value):
        di = int(value.start) if value.start is not None else 0
        df = int(value.stop) if value.stop is not None else 5000

        if di > df:
            a = di
            di = df
            df = a

        # lim inicial-dt.mais antiga
        li = date.today() - relativedelta(days=df + 1)
        # lim final - dt. mais nova
        lf = date.today() - relativedelta(days=di)

        return queryset.filter(data_envio__gt=li,
                               data_envio__lte=lf)

    def filter_dias_retorno(self, queryset, value):
        di = int(value.start) if value.start is not None else 0
        df = int(value.stop) if value.stop is not None else 5000

        if di > df:
            a = di
            di = df
            df = a

        return queryset.extra(where = ["""DATE_PART('day', data_retorno::timestamp - data_envio::timestamp) >= %s AND\
                                       DATE_PART('day', data_retorno::timestamp - data_envio::timestamp) <= %s""" % (di, df)])

    def filter_dias_abertura(self, queryset, value):
        di = int(value.start) if value.start is not None else 0
        df = int(value.stop) if value.stop is not None else 5000

        if di > df:
            a = di
            di = df
            df = a

        return queryset.extra(where = ["""DATE_PART('day', data_solucao::timestamp - data_abertura::timestamp) >= %s AND\
                                       DATE_PART('day', data_solucao::timestamp - data_abertura::timestamp) <= %s""" % (di, df)])

    def filter_data_envio(self, queryset, value):

        if not value[0] and not value[1]:
            return queryset

        inicial = None
        final = None

        if(value[0] != ''):
            inicial = datetime.datetime.strptime(value[0], "%d/%m/%Y").date()
        if(value[1] != ''):
            final = datetime.datetime.strptime(value[1], "%d/%m/%Y").date()
   
        if(inicial != None and final != None):
            if inicial > final:
                inicial, final = final, inicial
            range_select = Q(data_envio__range=[inicial, final])
        elif(inicial != None):
            range_select = Q(data_envio__gte=inicial)
        elif(final != None):
            range_select = Q(data_envio__lte=final)

        # Run the query.
        return queryset.filter(range_select)

    def filter_data_protocolo(self, queryset, value):

        if not value[0] and not value[1]:
            return queryset

        inicial = None
        final = None

        if(value[0] != ''):
            inicial = datetime.datetime.strptime(value[0], "%d/%m/%Y").date()
        if(value[1] != ''):
            final = datetime.datetime.strptime(value[1], "%d/%m/%Y").date()
   
        if(inicial != None and final != None):
            if inicial > final:
                inicial, final = final, inicial
            range_select = Q(data_protocolo__range=[inicial, final])
        elif(inicial != None):
            range_select = Q(data_protocolo__gte=inicial)
        elif(final != None):
            range_select = Q(data_protocolo__lte=final)

        # Run the query.
        return queryset.filter(range_select)

    def filter_data_retorno(self, queryset, value):

        if not value[0] and not value[1]:
            return queryset

        inicial = None
        final = None

        if(value[0] != ''):
            inicial = datetime.datetime.strptime(value[0], "%d/%m/%Y").date()
        if(value[1] != ''):
            final = datetime.datetime.strptime(value[1], "%d/%m/%Y").date()
   
        if(inicial != None and final != None):
            if inicial > final:
                inicial, final = final, inicial
            range_select = Q(data_retorno__range=[inicial, final])
        elif(inicial != None):
            range_select = Q(data_retorno__gte=inicial)
        elif(final != None):
            range_select = Q(data_retorno__lte=final)

        # Run the query.
        return queryset.filter(range_select)

    def filter_data_solucao(self, queryset, value):

        if not value[0] and not value[1]:
            return queryset

        inicial = None
        final = None

        if(value[0] != ''):
            inicial = datetime.datetime.strptime(value[0], "%d/%m/%Y").date()
        if(value[1] != ''):
            final = datetime.datetime.strptime(value[1], "%d/%m/%Y").date()
   
        if(inicial != None and final != None):
            if inicial > final:
                inicial, final = final, inicial
            range_select = Q(data_solucao__range=[inicial, final])
        elif(inicial != None):
            range_select = Q(data_solucao__gte=inicial)
        elif(final != None):
            range_select = Q(data_solucao__lte=final)

        # Run the query.
        return queryset.filter(range_select)

    def filter_search_endereco(self, queryset, value):

        query = normalize(value)

        query = query.split(' ')
        if query:
            q = Q()
            for item in query:
                if not item:
                    continue
                q = q & Q(endereco__unaccent__icontains=item)

            if q:
                queryset = queryset.filter(q)
        return queryset

    def filter_contato(self, queryset, value):

        query = normalize(value)

        query = query.split(' ')
        if query:
            q = Q()
            for item in query:
                if not item:
                    continue
                q = q & (Q(contato_set__nome__unaccent__icontains=item) | 
                         Q(contato_set__nome_social__unaccent__icontains=item) |
                         Q(contato_set__apelido__unaccent__icontains=item))

            if q:
                queryset = queryset.filter(q)
        return queryset

    def filter_search(self, queryset, value):

        query = normalize(value)

        query = query.split(' ')
        if query:
            q = Q()
            for item in query:
                if not item:
                    continue
                q = q & Q(search__unaccent__icontains=item)

            if q:
                queryset = queryset.filter(q)
        return queryset

    def filter_search_numeros(self, queryset, value):

        query = normalize(value)

        if query:
            q = Q()
            for item in query:
                if not item:
                    continue
                q = q & (Q(materia_cam__icontains=item) | 
                         Q(oficio_cam__icontains=item) |
                         Q(oficio_pref__icontains=item) |
                         Q(oficio_orgao__icontains=item) |
                         Q(proto_pref__icontains=item) |
                         Q(proto_orgao__icontains=item))

            if q:
                queryset = queryset.filter(q)
        return queryset

    def filter_search_envolvidos(self, queryset, value):

        query = normalize(value)
        query = query.split(' ')

        if query:
            q = Q()
            for item in query:
                if not item:
                    continue
                q = q & (Q(orgao__unaccent__icontains=item) | 
                         Q(instituicao__unaccent__icontains=item))

            if q:
                queryset = queryset.filter(q)
        return queryset

    class Meta:
        model = Processo
        fields = ['search',
                  'search_contato',
                  'data_abertura',
                  'data_envio',
                  'data_retorno',
                  'data_envio',
                  'data_protocolo',
                  'data_solucao',
                  'dias_envio',
                  'dias_retorno',
                  'dias_abertura',
                  'bairro',
                  'search_numeros',
                  'search_endereco',
                  'search_envolvidos',
                  'topicos',
                  'importancia',
                  'classificacao',
                  'assuntos',
                  'urgente',
                  'status', ]

    def __init__(self, data=None,
                 queryset=None, prefix=None, strict=None, **kwargs):

        workspace = kwargs.pop('workspace')

        super(ProcessosFilterSet, self).__init__(
            data=data,
            queryset=queryset, prefix=prefix, strict=strict, **kwargs)

        c1_row1 = to_row([
            ('search', 8),
            ('search_contato', 4),
            ('search_numeros', 4),
            ('data_envio', 4),
            ('data_protocolo', 4),
            ('data_abertura', 4),
            ('data_retorno', 4),
            ('data_solucao', 4),
            ('dias_envio', 4),
            ('dias_retorno', 4),
            ('dias_abertura', 4),
            ('classificacao', 6),
            ('status', 6),
            ('topicos', 6),
            ('assuntos', 6),
            ('bairro', 6),
            ('importancia', 3),
            ('urgente', 3),
            ('search_endereco', 6),
            ('search_envolvidos', 6),
        ])

        col1 = Fieldset(
            _('Filtro de Processos'),
            c1_row1,
            to_row([
                (SubmitFilterPrint(
                    'filter',
                    value=_('Filtrar'),
                    css_class='btn-default pull-right',
                    type='submit'), 12)
            ]))

        col2 = Fieldset(
            _('Impressão'),
            'agrupamento',

            SubmitFilterPrint(
                'print',
                value=_('Imprimir'),
                css_class='btn-primary pull-right',
                type='submit')
        )

        rows = to_row([
            (col1, 9),
            (col2, 3),
        ])

        self.form.helper = FormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            rows,
        )

        self.form.fields['search'].label = _('Pesquisa por título, histórico, observações ou solução')
        self.form.fields['search_contato'].label = _('Contatos interessados')
        self.form.fields['search_numeros'].label = _('Matéria, protocolo ou ofício')
        self.form.fields['search_endereco'].label = _('Endereço')
        self.form.fields['search_envolvidos'].label = _('Órgão ou instituição')
       
        self.form.fields['agrupamento'].label = _('Agrupamento')
        self.form.fields['agrupamento'].widget = forms.RadioSelect()

class ContatoIndividualFilterSet(FilterSet):

    filter_overrides = {models.DateField: {
        'filter_class': MethodFilter,
        'extra': lambda f: {
            'label': 'Período de aniversário',
            'widget': RangeWidgetOverride}
    }}

    FEMININO = 'F'
    MASCULINO = 'M'
    AMBOS = ''
    SEXO_CHOICE = ((AMBOS, _('Ambos')),
                   (FEMININO, _('Feminino')),
                   (MASCULINO, _('Masculino')))

    pk = MethodIntegerFilter()

    pk_selecionados = MethodFilter(
        required=False,
        action=filter_pk_selecionados,
        )

    search = MethodFilter()
    
    sexo = ChoiceFilter(choices=SEXO_CHOICE)

    estado_civil = ModelChoiceFilter(
        required=False,
        queryset=EstadoCivil.objects.all())

    tem_filhos = BooleanFilter()

    ativo = BooleanFilter()

    idade = MethodRangeFilter(
        label=_('Idade entre:'),
        widget=RangeWidgetNumber)

    grupo = MethodModelMultipleChoiceFilter(
        required=False,
        label=_('Grupo de contatos:'),
        queryset=GrupoDeContatos.objects.all())
    
    search_endereco = MethodFilter()

    bairro = MethodModelMultipleChoiceFilter(
        required=False,
        label=_('Bairro de Novo Hamburgo'),
        queryset=Bairro.objects.filter(municipio=4891))

    cep = MethodFilter(label=_('CEP'))
    
    telefone = MethodFilter(label=_('Telefone'))

    municipio = MethodModelChoiceFilter(
        required=False,
        label=_('Município do RS'),
        queryset=Bairro.objects.filter(estado=21))

    def filter_grupo(self, queryset, value):
        if value:
            queryset = queryset.filter(grupodecontatos_set__in=value)

        return queryset

    def filter_bairro(self, queryset, value):
        if value:
            queryset = queryset.filter(
                endereco_set__bairro__in=value)

        return queryset

    def filter_pk(self, queryset, value):
        queryset = queryset.filter(pk=value)
        return queryset

    def filter_municipio(self, queryset, value):
        queryset = queryset.filter(
                endereco_set__municipio=value)
        return queryset

    def filter_orientacao(self, queryset, value):
        return queryset

    def filter_formato(self, queryset, value):
        return queryset

    def filter_tipo_dado_contato(self, queryset, value):
        return queryset

    def filter_idade(self, queryset, value):
        idi = int(value.start) if value.start is not None else 0
        idf = int(value.stop) if value.stop is not None else 100

        if idi > idf:
            a = idi
            idi = idf
            idf = a

        # lim inicial-dt.mais antiga
        li = date.today() - relativedelta(years=idf + 1)
        # lim final - dt. mais nova
        lf = date.today() - relativedelta(years=idi)

        return queryset.filter(data_nascimento__gt=li,
                               data_nascimento__lte=lf)

    def filter_search(self, queryset, value):

        query = normalize(value)

        query = query.split(' ')
        if query:
            q = Q()
            for item in query:
                if not item:
                    continue
                q = q & Q(search__unaccent__icontains=item)

            if q:
                queryset = queryset.filter(q)
        return queryset

    def filter_search_endereco(self, queryset, value):

        query = normalize(value)

        query = query.split(' ')
        if query:
            q = Q()
            for item in query:
                if not item:
                    continue
                q = q & (Q(endereco_set__endereco__unaccent__icontains=item) | 
                         Q(endereco_set__ponto_referencia__unaccent__icontains=item) |
                         Q(endereco_set__complemento__unaccent__icontains=item))

            if q:
                queryset = queryset.filter(q)
        return queryset

    def filter_cep(self, queryset, value):

        query = normalize(value.strip())
        
        q = Q()
        
        if query:
            q = q & Q(endereco_set__cep=value)

        if q:
            queryset = queryset.filter(q)
        
        return queryset

    def filter_telefone(self, queryset, value):

        query = normalize(value.strip())
        
        q = Q()
       
        if query:
            q = q & Q(telefone_set__telefone=value)

        if q:
            queryset = queryset.filter(q)
        
        return queryset

    def filter_data_nascimento(self, queryset, value):

        if not value[0] or not value[1]:
            return queryset

        now = datetime.datetime.strptime(value[0], "%d/%m/%Y").date()
        then = datetime.datetime.strptime(value[1], "%d/%m/%Y").date()
        if now > then:
            a = now
            now = then
            then = a

        # Build the list of month/day tuples.
        monthdays = [(now.month, now.day)]
        while now <= then:
            monthdays.append((now.month, now.day))
            now += timedelta(days=1)

        # Tranform each into queryset keyword args.
        monthdays = (dict(zip(("data_nascimento__month",
                               "data_nascimento__day"), t))
                     for t in monthdays)

        # Compose the djano.db.models.Q objects together for a single query.
        query = reduce(operator.or_, (Q(**d) for d in monthdays))

        # Run the query.
        return queryset.extra(select={
            'month': 'extract( month from data_nascimento )',
            'day': 'extract( day from data_nascimento )', }
        ).order_by('month', 'day', 'nome').filter(query)

    class Meta:
        model = Contato
        fields = ['search',
                  'search_endereco',
                  'sexo',
                  'tem_filhos',
                  'data_nascimento',
                  'tipo_autoridade']

    def __init__(self, data=None,
                 queryset=None, prefix=None, strict=None, **kwargs):

        workspace = kwargs.pop('workspace')
 
        super(ContatoIndividualFilterSet, self).__init__(
            data=data,
            queryset=queryset, prefix=prefix, strict=strict, **kwargs)

        col1 = to_row([
            ('pk', 2),
            ('search', 10),
            ('sexo', 3),
            ('estado_civil', 3),
            ('tem_filhos', 3),
            ('ativo', 3),
            ('data_nascimento', 6),
            ('idade', 6),
            ('search_endereco', 12),
            ('cep', 4),
            ('telefone', 4),
            ('municipio', 4),
            ('bairro', 6),
            ('grupo', 6),
            ('tipo_autoridade', 6),
        ])

        col2 = to_row([
            ('pk_selecionados', 12),
        ])

        row = to_row(
            [(Fieldset(
                _('Busca por Contato'),
                col1,
                to_row([(SubmitFilterPrint(
                    'filter',
                    value=_('Filtrar'), css_class='btn-default pull-right',
                    type='submit'), 12)])), 9),
             (Fieldset(
                 _('Impressão'),
                 col2,
                 to_row([(SubmitFilterPrint(
                     'print',
                     value=_('Imprimir'), css_class='btn-primary pull-right',
                     type='submit'), 12)])), 3)])

        self.form.helper = FormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            row,
        )

        self.form.fields['pk'].label = _('Código')
        self.form.fields['pk_selecionados'].label = _('Códigos selecionados')
        self.form.fields['search'].label = 'Nome, nome social ou apelido'
        self.form.fields['search_endereco'].label = 'Endereço, complemento ou ponto de referência'
        self.form.fields['data_nascimento'].label = 'Período de aniversário'
        self.form.fields['tem_filhos'].label = _('Tem filhos?')
        self.form.fields['ativo'].label = _('Ativo?')
        self.form.fields['cep'].widget.attrs['class'] = 'cep'

        self.form.fields['grupo'].queryset = GrupoDeContatos.objects.filter(workspace=workspace)

        self.form.fields['bairro'].queryset = Bairro.objects.filter(municipio=4891)
        self.form.fields['municipio'].queryset = Municipio.objects.filter(estado=21)

class ContatosFilterSet(FilterSet):

    filter_overrides = {models.DateField: {
        'filter_class': MethodFilter,
        'extra': lambda f: {
            'label': 'Período de aniversário',
            'widget': RangeWidgetOverride}
    }}

    FEMININO = 'F'
    MASCULINO = 'M'
    AMBOS = ''
    SEXO_CHOICE = ((AMBOS, _('Ambos')),
                   (FEMININO, _('Feminino')),
                   (MASCULINO, _('Masculino')))

    BOTH_CHOICE = [(None, _('Ambos'))] + YES_NO_CHOICES

    RETRATO = 'R'
    PAISAGEM = 'P'
    ORIENTACAO_CHOICE = ((PAISAGEM, _('Paisagem')),
                         (RETRATO, _('Retrato')))

    PDF = 'PDF'
    TXT = 'TXT'
    FORMATO_CHOICE = ((PDF, _('PDF')),
                      (TXT, _('Mala direta')))

    PRINCIPAL = 'P'
    CONTATO = 'C'
    AMBOS = 'A'
    TIPO_DADO_CONTATO_CHOICE = ((PRINCIPAL, _('Apenas o principal')),
                      (CONTATO, _('Apenas o escolhido pra contato')),
                      (AMBOS, _('Ambos')))

    search = MethodFilter()
    
    sexo = ChoiceFilter(choices=SEXO_CHOICE)

    estado_civil = ModelChoiceFilter(
        required=False,
        queryset=EstadoCivil.objects.all())

    tem_filhos = BooleanFilter()

    ativo = BooleanFilter()

    ocultar_sem_email = MethodBooleanFilter()

    idade = MethodRangeFilter(
        label=_('Idade entre'),
        widget=RangeWidgetNumber)

    formato = MethodChoiceFilter(
        label=_('Formato'),
        choices=FORMATO_CHOICE, initial=PDF)
    
    orientacao = MethodChoiceFilter(
        label=_('Orientação'),
        choices=ORIENTACAO_CHOICE, initial=PAISAGEM)

    tipo_dado_contato = MethodChoiceFilter(
        label=_('Endereço, telefone e e-mail'),
        choices=TIPO_DADO_CONTATO_CHOICE, initial=PRINCIPAL)

    grupo = MethodModelMultipleChoiceFilter(
        required=False,
        label=_('Grupo de contatos:'),
        queryset=GrupoDeContatos.objects.all())
    
    search_endereco = MethodFilter()

    bairro = MethodModelMultipleChoiceFilter(
        required=False,
        label=_('Bairro de Novo Hamburgo'),
        queryset=Bairro.objects.filter(municipio=4891))

    cep = MethodFilter(label=_('CEP'))

    municipio = MethodModelChoiceFilter(
        required=False,
        label=_('Município do RS'),
        queryset=Bairro.objects.filter(estado=21))

    def filter_grupo(self, queryset, value):
        if value:
            queryset = queryset.filter(grupodecontatos_set__in=value)

        return queryset

    def filter_ocultar_sem_email(self, queryset, value):
        if(value == True):
            queryset = queryset.filter(
                    email_set__permite_contato=True)

        return queryset

    def filter_bairro(self, queryset, value):
        if value:
            queryset = queryset.filter(
                endereco_set__bairro__in=value)

        return queryset

    def filter_municipio(self, queryset, value):
        queryset = queryset.filter(
                endereco_set__municipio=value)
        return queryset

    def filter_orientacao(self, queryset, value):
        return queryset

    def filter_formato(self, queryset, value):
        return queryset

    def filter_tipo_dado_contato(self, queryset, value):
        return queryset

    def filter_idade(self, queryset, value):
        idi = int(value.start) if value.start is not None else 0
        idf = int(value.stop) if value.stop is not None else 100

        if idi > idf:
            a = idi
            idi = idf
            idf = a

        # lim inicial-dt.mais antiga
        li = date.today() - relativedelta(years=idf + 1)
        # lim final - dt. mais nova
        lf = date.today() - relativedelta(years=idi)

        return queryset.filter(data_nascimento__gt=li,
                               data_nascimento__lte=lf)

    def filter_search(self, queryset, value):

        query = normalize(value)

        query = query.split(' ')
        if query:
            q = Q()
            for item in query:
                if not item:
                    continue
                q = q & Q(search__unaccent__icontains=item)

            if q:
                queryset = queryset.filter(q)
        return queryset

    def filter_search_endereco(self, queryset, value):

        query = normalize(value)

        query = query.split(' ')
        if query:
            q = Q()
            for item in query:
                if not item:
                    continue
                q = q & (Q(endereco_set__endereco__unaccent__icontains=item) | 
                         Q(endereco_set__ponto_referencia__unaccent__icontains=item) |
                         Q(endereco_set__complemento__unaccent__icontains=item))

            if q:
                queryset = queryset.filter(q)
        return queryset

    def filter_cep(self, queryset, value):

        query = normalize(value.strip())
        
        q = Q()
        
        if query:
            q = q & Q(endereco_set__cep=value)

        if q:
            queryset = queryset.filter(q)
        
        return queryset

    def filter_data_nascimento(self, queryset, value):

        if not value[0] or not value[1]:
            return queryset

        now = datetime.datetime.strptime(value[0], "%d/%m/%Y").date()
        then = datetime.datetime.strptime(value[1], "%d/%m/%Y").date()
        if now > then:
            a = now
            now = then
            then = a

        # Build the list of month/day tuples.
        monthdays = [(now.month, now.day)]
        while now <= then:
            monthdays.append((now.month, now.day))
            now += timedelta(days=1)

        # Tranform each into queryset keyword args.
        monthdays = (dict(zip(("data_nascimento__month",
                               "data_nascimento__day"), t))
                     for t in monthdays)

        # Compose the djano.db.models.Q objects together for a single query.
        query = reduce(operator.or_, (Q(**d) for d in monthdays))

        # Run the query.
        return queryset.extra(select={
            'month': 'extract( month from data_nascimento )',
            'day': 'extract( day from data_nascimento )', }
        ).order_by('month', 'day', 'nome').filter(query)

    class Meta:
        model = Contato
        fields = ['search',
                  'search_endereco',
                  'sexo',
                  'tem_filhos',
                  'data_nascimento',
                  'tipo_autoridade']

    def __init__(self, data=None,
                 queryset=None, prefix=None, strict=None, **kwargs):

        workspace = kwargs.pop('workspace')
 
        super(ContatosFilterSet, self).__init__(
            data=data,
            queryset=queryset, prefix=prefix, strict=strict, **kwargs)

        col1 = to_row([
            ('search', 12),
            ('sexo', 3),
            ('estado_civil', 3),
            ('tem_filhos', 3),
            ('ativo', 3),
            ('data_nascimento', 6),
            ('idade', 6),
            ('search_endereco', 9),
            ('ocultar_sem_email', 3),
            ('cep', 6),
            ('municipio', 6),
            ('bairro', 6),
            ('grupo', 6),
            ('tipo_autoridade', 6),
        ])

        col2 = to_row([
            ('formato', 12),
            ('orientacao', 12),
            ('tipo_dado_contato', 12),
        ])

        row = to_row(
            [(Fieldset(
                _('Filtro de Contatos'),
                col1,
                to_row([(SubmitFilterPrint(
                    'filter',
                    value=_('Filtrar'), css_class='btn-default pull-right',
                    type='submit'), 12)])), 9),
             (Fieldset(
                 _('Impressão'),
                 col2,
                 to_row([(SubmitFilterPrint(
                     'print',
                     value=_('Gerar'), css_class='btn-primary pull-right',
                     type='submit'), 12)])), 3)])

        self.form.helper = FormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            row,
        )

        self.form.fields['search'].label = 'Nome, nome social ou apelido'
        self.form.fields['search_endereco'].label = 'Endereço, complemento ou ponto de referência'
        self.form.fields['data_nascimento'].label = 'Período de aniversário'
        self.form.fields['tem_filhos'].label = _('Tem filhos?')
        self.form.fields['ativo'].label = _('Ativo?')
        self.form.fields['cep'].widget.attrs['class'] = 'cep'

        self.form.fields['ocultar_sem_email'].inline_class = True
        self.form.fields['ocultar_sem_email'].label = _('<font color=red>Ocultar sem e-mail?</font>')

        self.form.fields['grupo'].queryset = GrupoDeContatos.objects.filter(workspace=workspace)
        self.form.fields['bairro'].queryset = Bairro.objects.filter(municipio=4891)
        self.form.fields['municipio'].queryset = Municipio.objects.filter(estado=21)

class ListWithSearchProcessoForm(ListWithSearchForm):

    pk = forms.IntegerField(
        label=_('Código'),
        required=False)

    numeros = forms.CharField(
        required=False,
        label=_('Matéria, protocolo ou ofício'))

    contatos = forms.CharField(
        required=False,
        label=_('Contatos interessados'))

    data_envio_inicial = forms.DateField(
        required=False,
        label=_('Envio (I)'))
 
    data_envio_final = forms.DateField(
        required=False,
        label=_('Envio (F)'))

    data_protocolo_inicial = forms.DateField(
        required=False,
        label=_('Protocolo (I)'))
 
    data_protocolo_final = forms.DateField(
        required=False,
        label=_('Protocolo (F)'))

    data_abertura_inicial = forms.DateField(
        required=False,
        label=_('Abertura (I)'))
 
    data_abertura_final = forms.DateField(
        required=False,
        label=_('Abertura (F)'))

    data_retorno_inicial = forms.DateField(
        required=False,
        label=_('Retorno (I)'))
 
    data_retorno_final = forms.DateField(
        required=False,
        label=_('Retorno (F)'))

    data_solucao_inicial = forms.DateField(
        required=False,
        label=_('Solução (I)'))
 
    data_solucao_final = forms.DateField(
        required=False,
        label=_('Solução (F)'))

    topicos = forms.ModelMultipleChoiceField(
        required=False,
        label=_('Tópico'),
        queryset=TopicoProcesso.objects.all())

    assuntos = forms.ModelMultipleChoiceField(
        required=False,
        label=_('Assunto'),
        queryset=AssuntoProcesso.objects.all())

    importancias = forms.MultipleChoiceField(
        required=False,
        label=_('Importância'),
        choices=IMPORTANCIA_CHOICE)

    status = forms.ModelMultipleChoiceField(
        required=False,
        queryset=StatusProcesso.objects.all())

    classificacoes = forms.ModelMultipleChoiceField(
        required=False,
        label=_('Classificação'),
        queryset=ClassificacaoProcesso.objects.all())

    endereco = forms.CharField(
        required=False,
        label=_('Endereço'))
   
    envolvidos = forms.CharField(
        required=False,
        label=_('Órgão ou instituição'))

    bairros = forms.ModelMultipleChoiceField(
        required=False,
        label=_('Bairro de Novo Hamburgo'),
        queryset=Bairro.objects.filter(municipio=4891))

    urgente = forms.NullBooleanField(
        required=False,
        label=_('Urgente?'))

    class Meta(ListWithSearchForm.Meta):
        fields = ['q',
                  'o',
                  'pk'
                  'contatos',
                  'numeros',
                  'classificacoes',
                  'status',
                  'topicos',
                  'assuntos',
                  'bairros',
                  'importancias',
                  'urgente',
                  'endereco',
                  'envolvidos',
                  'data_envio_inicial',
                  'data_envio_final',
                  'data_protocolo_inicial',
                  'data_protocolo_final',
                  'data_abertura_inicial',
                  'data_abertura_final',
                  'data_retorno_inicial',
                  'data_retorno_final',
                  'data_solucao_inicial',
                  'data_solucao_final',
                 ]
        pass

    def __init__(self, *args, **kwargs):
        super(ListWithSearchProcessoForm, self).__init__(*args, **kwargs)

        col1 = to_row([
            ('pk', 2),
            ('q', 6),
            ('contatos', 4),
            ('numeros', 6),
            ('data_envio_inicial', 3),
            ('data_envio_final', 3),
            ('data_protocolo_inicial', 3),
            ('data_protocolo_final', 3),
            ('data_abertura_inicial', 3),
            ('data_abertura_final', 3),
            ('data_retorno_inicial', 3),
            ('data_retorno_final', 3),
            ('data_solucao_inicial', 3),
            ('data_solucao_final', 3),
            ('classificacoes', 6),
            ('status', 6),
            ('topicos', 6),
            ('assuntos', 6),
            ('bairros', 6),
            ('importancias', 3),
            ('urgente', 3),
            ('endereco', 5),
            ('envolvidos', 5),
            #('o', 4),
        ])

        row = to_row(
            [(Fieldset(
                _(''),
                col1,
                to_row([(SubmitFilterPrint(
                    'filter',
                    value=_('Filtrar'), css_class='btn-default pull-right',
                    type='submit'), 12)])
            ), 12),
            ])

        #self.helper.form. = FormHelper()
        #self.helper.form.form_method = 'GET'
        self.helper.layout = Layout(
            row,
        )

        #workspace = kwargs.pop('workspace')

        self.fields['q'].label = _('Título, histórico, observações ou solução')

class ListWithSearchContatoForm(ListWithSearchForm):
    
    FEMININO = 'F'
    MASCULINO = 'M'
    INDIFERENTE = ''
    SEXO_CHOICE = ((INDIFERENTE, _('Indiferente')),
                   (FEMININO, _('Feminino')),
                   (MASCULINO, _('Masculino')))

    filter_overrides = {models.DateField: {
        'filter_class': MethodFilter,
        'extra': lambda f: {
            'label': 'Período de aniversário',
            'widget': RangeWidgetOverride}
    }}

    pk = forms.IntegerField(
                   label=_('Código'),
                   required=False
                   )
    
    sexo = forms.ChoiceField(
                   choices=SEXO_CHOICE,
                   required=False
                   )

    tem_filhos = forms.NullBooleanField(
        required=False,
        label=_('Tem filhos?'))

    ativo = forms.NullBooleanField(
        required=False,
        label=_('Ativo?'))

    data_inicial = forms.DateField(
        required=False,
        label=_('Aniversário (Início)'))
 
    data_final = forms.DateField(
        required=False,
        label=_('Aniversário (Fim)'))

    nasc_inicial = forms.DateField(
        required=False,
        label=_('Nascimento (Início)'))
 
    nasc_final = forms.DateField(
        required=False,
        label=_('Nascimento (Fim)'))

    endereco = forms.CharField(
        required=False,
        label=_('Endereço'))

    bairro = forms.ModelMultipleChoiceField(
        required=False,
        label=_('Bairro de Novo Hamburgo'),
        queryset=Bairro.objects.filter(municipio=4891))

    cep = forms.CharField(
        required=False,
        label=_('CEP'))

    telefone = forms.CharField(
        required=False,
        label=_('Telefone'))

    municipio = forms.ModelMultipleChoiceField(
        required=False,
        label=_('Município do Rio Grande do Sul'),
        queryset=Municipio.objects.filter(estado=21))

    grupos = forms.ModelMultipleChoiceField(
        required=False,
        label=_('Grupos de contatos:'),
        queryset=GrupoDeContatos.objects.all())

    estado_civil = forms.ModelChoiceField(
        required=False,
        label=_('Estado civil'),
        queryset=EstadoCivil.objects.all())

    nivel_instrucao = forms.ModelChoiceField(
        required=False,
        label=_('Nível de instrução'),
        queryset=NivelInstrucao.objects.all())

    profissao = forms.CharField(
        required=False,
        label=_('Profissão'))

    dependente = forms.CharField(
        required=False,
        label=_('Dependente'))

    documentos = forms.CharField(
        required=False,
        label=_('RG, CPF, CNPJ e IE'))

    class Meta(ListWithSearchForm.Meta):
        fields = ['q',
                  'o',
                  'pk'
                  'sexo',
                  'tem_filhos',
                  'ativo',
                  'endereco',
                  'cep',
                  'telefone',
                  'bairro',
                  'municipio',
                  'estado_civil',
                  'nivel_instrucao',
                  'profissao',
                  'dependente',
                  'documentos',
                  'data_inicial',
                  'data_final',
                  'nasc_inicial',
                  'nasc_final',
                  'grupos',
                 ]
        pass

    def __init__(self, *args, **kwargs):
        super(ListWithSearchContatoForm, self).__init__(*args, **kwargs)

        col1 = to_row([
            ('pk', 2),
            ('q', 7),
            ('ativo', 3),
            ('sexo', 3),
            ('estado_civil', 3),
            ('tem_filhos', 3),
            ('documentos', 3),
            ('data_inicial', 3),
            ('data_final', 3),
            ('nasc_inicial', 3),
            ('nasc_final', 3),
            ('endereco', 6),
            ('cep', 3),
            ('telefone', 3),
            ('bairro', 6),
            ('municipio', 6),
            ('nivel_instrucao', 4),
            ('profissao', 4),
            ('dependente', 4),
            ('grupos', 6),
        ])

        row = to_row(
            [(Fieldset(
                _(''),
                col1,
                to_row([(SubmitFilterPrint(
                    'filter',
                    value=_('Filtrar'), css_class='btn-default pull-right',
                    type='submit'), 12)])
            ), 12),
            ])

        #self.helper.form. = FormHelper()
        #self.helper.form.form_method = 'GET'
        self.helper.layout = Layout(
            row,
        )

        workspace = kwargs['initial']['workspace']

        self.fields['q'].label = _('Nome, nome social ou apelido')
        self.fields['cep'].widget.attrs['class'] = 'cep'
        self.fields['grupos'].queryset = GrupoDeContatos.objects.filter(workspace=workspace)
