from django.db.models.aggregates import Max
from django.db.models import Q, F, Func, Value
from django.utils.translation import ugettext_lazy as _
from django.views.generic.edit import FormView
from django.core.files.storage import FileSystemStorage
from django.db import transaction
from django.contrib.messages.views import SuccessMessageMixin
from django.http import Http404, HttpResponse, HttpResponseForbidden

from django.utils.safestring import mark_safe
from django.shortcuts import render
from django.views import generic
from django.shortcuts import redirect
from _functools import reduce
import datetime
from datetime import date, timedelta, datetime
import operator
import time, datetime

from saap.cerimonial.forms import LocalTrabalhoForm, EnderecoForm,\
    TipoAutoridadeForm, LocalTrabalhoPerfilForm,\
    ContatoFragmentPronomesForm, ContatoForm, ProcessoForm, \
    ContatoFragmentSearchForm, ProcessoContatoForm, ContatosImportaForm,\
    ListWithSearchProcessoForm, ListWithSearchContatoForm,\
    GrupoDeContatosForm, TelefoneForm, EmailForm, EventoForm
from saap.cerimonial.models import TipoTelefone, TipoEndereco,\
    TipoEmail, Parentesco, EstadoCivil, TipoAutoridade, TipoLocalTrabalho,\
    NivelInstrucao, Contato, Telefone, OperadoraTelefonia, Email,\
    PronomeTratamento, Dependente, LocalTrabalho, Endereco,\
    DependentePerfil, LocalTrabalhoPerfil,\
    EmailPerfil, TelefonePerfil, EnderecoPerfil, FiliacaoPartidaria,\
    StatusProcesso, ClassificacaoProcesso, TopicoProcesso, Processo,\
    AssuntoProcesso, ProcessoContato, GrupoDeContatos, Evento
from saap.cerimonial.rules import rules_patterns

from saap.cerimonial.utils import CalendarAgenda, CalendarAniversarios, \
    get_date, prev_month, prev_year, next_month, next_year, this_month

from saap.utils import normalize

from saap.core.forms import ListWithSearchForm
from saap.core.models import AreaTrabalho, OperadorAreaTrabalho,\
   Estado, Municipio, Bairro, User
from saap.crispy_layout_mixin import CrispyLayoutFormMixin

from saap.globalrules import globalrules

from saap.globalrules.crud_custom import DetailMasterCrud,\
    MasterDetailCrudPermission, PerfilAbstractCrud, PerfilDetailCrudPermission

from saap.globalrules.crud_custom_saap import DetailMasterCrudSaap,\
    MasterDetailCrudSaapPermission, PerfilAbstractCrudSaap, PerfilDetailCrudSaapPermission

from saap.crud.base_saap import CrudSaap, make_pagination

globalrules.rules.config_groups(rules_patterns)

# ---- Details Master Crud build ---------------------------
TipoTelefoneCrud = DetailMasterCrud.build(TipoTelefone, None, 'tipotelefone')
TipoEnderecoCrud = DetailMasterCrud.build(TipoEndereco, None, 'tipoendereco')
TipoEmailCrud = DetailMasterCrud.build(TipoEmail, None, 'tipoemail')
ParentescoCrud = DetailMasterCrud.build(Parentesco, None, 'parentesco')

TipoLocalTrabalhoCrud = DetailMasterCrud.build(
    TipoLocalTrabalho, None, 'tipolocaltrabalho')
StatusProcessoCrud = DetailMasterCrud.build(
    StatusProcesso, None, 'statusprocesso')
ClassificacaoProcessoCrud = DetailMasterCrud.build(
    ClassificacaoProcesso, None, 'classificacaoprocesso')




class TopicoProcessoCrud(CrudSaap):
    help_text = 'topicoprocesso'
    model = TopicoProcesso

    class BaseMixin(CrudSaap.BaseMixin):
        list_field_names = ['descricao']

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            return context

    class ListView(CrudSaap.ListView):
        form_search_class = ListWithSearchForm
        paginate_by = 30

        def get(self, request, *args, **kwargs):
            return CrudSaap.ListView.get(
                self, request, *args, **kwargs)

        def get_context_data(self, **kwargs):
            context = CrudSaap.ListView.get_context_data(self, **kwargs)
            return context

        def get_queryset(self):
            qs = self.model.objects.all()
            q_param = self.request.GET.get('q', '')
            if q_param:
                q = Q(descricao__icontains=q_param)
                qs = qs.filter(q)

            o_param = self.request.GET.get('o', '')
            ordering='descricao'
            if o_param:
                o_param = int(o_param)
                if abs(o_param) == 1:
                    ordering='descricao'

                if int(o_param)<0:
                    ordering = '-' + ordering

            return qs.order_by(ordering)



# ---- Details Master Crud herança ---------------------------
class OperadoraTelefoniaCrud(DetailMasterCrud):
    model_set = 'telefone_set'
    model = OperadoraTelefonia
    container_field_set = 'contato__workspace__operadores'

    class DetailView(DetailMasterCrud.DetailView):
        list_field_names_set = ['numero_nome_contato', ]


class NivelInstrucaoCrud(DetailMasterCrud):
    model_set = 'contato_set'
    model = NivelInstrucao
    container_field_set = 'workspace__operadores'


class EstadoCivilCrud(DetailMasterCrud):
    model_set = 'contato_set'
    model = EstadoCivil
    container_field_set = 'workspace__operadores'

##############################################

class PronomeTratamentoCrud(DetailMasterCrudSaap):
    help_text = 'pronometratamento'
    model = PronomeTratamento

    class BaseMixin(DetailMasterCrudSaap.BaseMixin):
        list_field_names = [
            'nome_por_extenso',
            ('abreviatura_singular_m', 'abreviatura_plural_m',),
            'vocativo_direto_singular_m',
            'vocativo_indireto_singular_m',
            ('prefixo_nome_singular_m', 'prefixo_nome_singular_f'),
            'enderecamento_singular_m', ]

    class ListView(DetailMasterCrudSaap.ListView):
        form_search_class = ListWithSearchForm
        paginate_by = 50

        def get(self, request, *args, **kwargs):
            return DetailMasterCrudSaap.ListView.get(
                self, request, *args, **kwargs)

        def get_context_data(self, **kwargs):
            context = DetailMasterCrudSaap.ListView.get_context_data(self, **kwargs)
            return context

        def get_queryset(self):
            qs = self.model.objects.all()
            q_param = self.request.GET.get('q', '')
            if q_param:
                q = Q(nome_por_extenso__icontains=q_param)
                q |= Q(abreviatura_singular_m__icontains=q_param)
                q |= Q(vocativo_direto_singular_m__icontains=q_param)
                q |= Q(vocativo_indireto_singular_m__icontains=q_param)
                q |= Q(prefixo_nome_singular_m__icontains=q_param)
                q |= Q(enderecamento_singular_m__icontains=q_param)
                qs = qs.filter(q)

            o_param = self.request.GET.get('o', '')
            ordering='nome_por_extenso'
            if o_param:
                o_param = int(o_param)
                if abs(o_param) == 1:
                    ordering='nome_por_extenso'
                elif abs(o_param) == 2:
                    ordering='abreviatura_singular_m'
                elif abs(o_param) == 3:
                    ordering='vocativo_direto_singular_m'
                elif abs(o_param) == 4:
                    ordering='vocativo_indireto_singular_m'
                elif abs(o_param) == 5:
                    ordering='prefixo_nome_singular_m'
                elif abs(o_param) == 6:
                    ordering='enderecamento_singular_m'

                if int(o_param)<0:
                    ordering = '-' + ordering

            return qs.order_by(ordering)

##################################################

class TipoAutoridadeCrud(DetailMasterCrudSaap):
    help_text = 'tipoautoriadade'
    model = TipoAutoridade

    class BaseMixin(DetailMasterCrudSaap.BaseMixin):
        list_field_names = ['descricao']
        form_class = TipoAutoridadeForm

    class ListView(DetailMasterCrudSaap.ListView):
        form_search_class = ListWithSearchForm
        paginate_by = 50

        def get(self, request, *args, **kwargs):
            return DetailMasterCrudSaap.ListView.get(
                self, request, *args, **kwargs)

        def get_context_data(self, **kwargs):
            context = DetailMasterCrudSaap.ListView.get_context_data(self, **kwargs)
            return context

        def get_queryset(self):
            qs = self.model.objects.all()
            q_param = self.request.GET.get('q', '')
            if q_param:
                q = Q(descricao__icontains=q_param)
                qs = qs.filter(q)

            o_param = self.request.GET.get('o', '')
            ordering='descricao'
            if o_param:
                o_param = int(o_param)
                if abs(o_param) == 1:
                    ordering='descricao'

                if int(o_param)<0:
                    ordering = '-' + ordering

            return qs.order_by(ordering)


# ---- Contato Master e Details ----------------------------

class ContatoCrud(DetailMasterCrud):
    model_set = None
    model = Contato
    container_field = 'workspace__operadores'

    class BaseMixin(DetailMasterCrud.BaseMixin):
        list_field_names = ['id', 'nome', 'data_nascimento', 'sexo', 'estado_civil']

        """def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)

            context['fluid'] = '-fluid'
            return context"""

        def get_initial(self):
            initial = {}

            try:
                initial['workspace'] = OperadorAreaTrabalho.objects.filter(user=self.request.user.pk, preferencial=True)[0].areatrabalho
            except:
                raise PermissionDenied(_('Sem permissão de acesso!'))

            return initial

    class ListView(DetailMasterCrud.ListView):
        form_search_class = ListWithSearchContatoForm

        def get(self, request, *args, **kwargs):
            return DetailMasterCrud.ListView.get(
                self, request, *args, **kwargs)

        def get_queryset(self):

            queryset = DetailMasterCrud.ListView.get_queryset(self)

            sexo = self.request.GET.get('sexo', '')
            pk = self.request.GET.get('pk', '')
            tem_filhos = self.request.GET.get('tem_filhos', '')
            ativo = self.request.GET.get('ativo', '')
            endereco = self.request.GET.get('endereco', '')
            num_endereco = self.request.GET.get('num_endereco', '')
            cep = self.request.GET.get('cep', '')
            telefone = self.request.GET.get('telefone', '')
            bairro = self.request.GET.getlist('bairro', '')
            municipio = self.request.GET.getlist('municipio', '')
            estado_civil = self.request.GET.get('estado_civil', '')
            nivel_instrucao = self.request.GET.get('nivel_instrucao', '')
            cargo = self.request.GET.get('cargo', '')
            dependente = self.request.GET.get('dependente', '')
            data_inicial = self.request.GET.get('data_inicial', '')
            data_final = self.request.GET.get('data_final', '')
            nasc_inicial = self.request.GET.get('nasc_inicial', '')
            nasc_final = self.request.GET.get('nasc_final', '')
            grupos = self.request.GET.getlist('grupos', '')
            dados_nulos = self.request.GET.getlist('dados_nulos', '')
            dados_nao_nulos = self.request.GET.getlist('dados_nao_nulos', '')
            tipo_autoridade = self.request.GET.getlist('tipo_autoridade', '')
            documentos = self.request.GET.get('documentos','')

            if sexo:
                queryset = queryset.filter(sexo=sexo)
 
            if pk:
                queryset = queryset.filter(pk=pk)

            if tem_filhos:
                if int(tem_filhos) > 1:
                    f = None
                    if int(tem_filhos) == 2:
                        f = True
                    elif int(tem_filhos) == 3:
                        f = False

                    queryset = queryset.filter(tem_filhos=f)

            if ativo:
                if int(ativo) > 1:
                    a = None
                    if int(ativo) == 2:
                        a = True
                    elif int(ativo) == 3:
                        a = False

                    queryset = queryset.filter(ativo=a)

            if endereco:
                query = normalize(endereco)

                query = query.split(' ')
                if query:
                    q = Q()
                    for item in query:
                        if not item:
                            continue
                        # Remove acentos dos campos que estão no banco
                        q = q & (Q(endereco_set__endereco__unaccent__icontains=item) | 
                                 Q(endereco_set__ponto_referencia__unaccent__icontains=item) |
                                 Q(endereco_set__complemento__unaccent__icontains=item))
                    if q:
                        queryset = queryset.filter(q)

            if dados_nulos:

                for opcao in dados_nulos:
                    if(opcao == 'DTN'):
                        queryset = queryset.exclude(data_nascimento__isnull=False)
                    elif(opcao == 'END'):
                        queryset = queryset.exclude(endereco_set__isnull=False)
                    elif(opcao == 'TEL'):
                        queryset = queryset.exclude(telefone_set__isnull=False)
                    elif(opcao == 'EML'):
                       queryset = queryset.exclude(email_set__isnull=False)
                    elif(opcao == 'SEX'):
                       queryset = queryset.filter(sexo='')
                    elif(opcao == 'ECV'):
                       queryset = queryset.exclude(estado_civil__isnull=False)
                    elif(opcao == 'GRP'):
                       queryset = queryset.exclude(grupodecontatos_set__isnull=False)
 
            if dados_nao_nulos:

                for opcao in dados_nao_nulos:
                    if(opcao == 'DTN'):
                        queryset = queryset.exclude(data_nascimento__isnull=True)
                    elif(opcao == 'END'):
                        queryset = queryset.exclude(endereco_set__isnull=True)
                    elif(opcao == 'TEL'):
                        queryset = queryset.exclude(telefone_set__isnull=True)
                    elif(opcao == 'EML'):
                       queryset = queryset.exclude(email_set__isnull=True)
                    elif(opcao == 'SEX'):
                       queryset = queryset.filter(Q(sexo='M') | Q(sexo='F'))
                    elif(opcao == 'ECV'):
                       queryset = queryset.exclude(estado_civil__isnull=True)
                    elif(opcao == 'GRP'):
                       queryset = queryset.exclude(grupodecontatos_set__isnull=True)
 
            if documentos:

                q = Q()
                q = q & (Q(rg=documentos) | 
                         Q(cpf=documentos) |
                         Q(cnpj=documentos) |
                         Q(ie=documentos))
               
                queryset = queryset.filter(q)

            if grupos:        
                queryset = queryset.filter(grupodecontatos_set__in=grupos).distinct()

            if bairro:
                queryset = queryset.filter(endereco_set__bairro__in=bairro).distinct()

            if municipio:
                queryset = queryset.filter(endereco_set__municipio__in=municipio).distinct()

            if cep:
                queryset = queryset.filter(endereco_set__cep=cep)

            if num_endereco:
                queryset = queryset.filter(endereco_set__numero=num_endereco)

            if telefone:
                queryset = queryset.filter(telefone_set__telefone=telefone)

            if estado_civil:
                queryset = queryset.filter(estado_civil=estado_civil)

            if nivel_instrucao:
                queryset = queryset.filter(nivel_instrucao=nivel_instrucao)
            
            if tipo_autoridade:
                if tipo_autoridade[0] != '':
                    queryset = queryset.filter(tipo_autoridade=tipo_autoridade[0])

            if cargo:
                query = normalize(cargo)

                query = query.split(' ')
                if query:
                    q = Q()
                    for item in query:
                        if not item:
                            continue
                        # Remove acentos dos campos que estão no banco
                        q = q & (Q(cargo__unaccent__icontains=item) |
                                 Q(profissao__unaccent__icontains=item))

                    if q:
                        queryset = queryset.filter(q)

            if dependente:
                query = normalize(dependente)

                query = query.split(' ')
                if query:
                    q = Q()
                    for item in query:
                        if not item:
                            continue
                        # Remove acentos dos campos que estão no banco
                        q = q & (Q(dependente_set__unaccent__icontains=item))

                    if q:
                        queryset = queryset.filter(q)

            if data_inicial and data_final:
                now = datetime.datetime.strptime(data_inicial, "%d/%m/%Y").date()
                then = datetime.datetime.strptime(data_final, "%d/%m/%Y").date()
                if now > then:
                    a = now
                    now = then
                    then = a

                # Build the list of month/day tuples.
                monthdays = [(now.month, now.day)]
                while now <= then:
                    monthdays.append((now.month, now.day))
                    now += timedelta(days=1)

                # Transform each into queryset keyword args.
                monthdays = (dict(zip(("data_nascimento__month",
                                       "data_nascimento__day"), t))
                             for t in monthdays)

                # Compose the djano.db.models.Q objects together for a single query.
                query = reduce(operator.or_, (Q(**d) for d in monthdays))

                # Run the query.
                queryset = queryset.extra(select={
                           'month': 'extract( month from data_nascimento )',
                           'day': 'extract( day from data_nascimento )', }
                           ).order_by('month', 'day', 'nome').filter(query)
 
            if nasc_inicial:
                data = datetime.datetime.strptime(nasc_inicial, "%d/%m/%Y").date()

                queryset = queryset.filter(data_nascimento__gte=data)

            if nasc_final:
                data = datetime.datetime.strptime(nasc_final, "%d/%m/%Y").date()

                queryset = queryset.filter(data_nascimento__lte=data)

            queryset = queryset.filter(workspace=OperadorAreaTrabalho.objects.filter(user=self.request.user.pk, preferencial=True)[0].areatrabalho)
            queryset = queryset.order_by('nome')

            return queryset

    class DetailView(DetailMasterCrud.DetailView):

        def get_object(self, queryset=None):

           if self.object.workspace == OperadorAreaTrabalho.objects.filter(user=self.request.user.pk, preferencial=True)[0].areatrabalho:
               return self.object
           else:
               raise Http404


    class CreateView(DetailMasterCrud.CreateView):
        form_class = ContatoForm
        layout_key = 'ContatoLayoutForForm'
        template_name = 'cerimonial/contato_form.html'

        def form_valid(self, form):
            response = super().form_valid(form)

            grupos = list(form.cleaned_data['grupodecontatos_set'])
            self.object.grupodecontatos_set.clear()
            if grupos:
                self.object.grupodecontatos_set.add(*grupos)

            return response

    class UpdateView(DetailMasterCrud.UpdateView):
        form_class = ContatoForm
        layout_key = 'ContatoLayoutForForm'
        template_name = 'cerimonial/contato_form.html'

        def get(self, request, *args, **kwargs):
            self.object = self.get_object()

            if self.object.workspace == OperadorAreaTrabalho.objects.filter(user=self.request.user.pk, preferencial=True)[0].areatrabalho:
                return super(DetailMasterCrud.UpdateView, self).get(request, *args, **kwargs)
            else:
                raise Http404


        def form_valid(self, form):
            
            response = super().form_valid(form)

            grupos = list(form.cleaned_data['grupodecontatos_set'])
            self.object.grupodecontatos_set.clear()
            if grupos:
                self.object.grupodecontatos_set.add(*grupos)

            return response

class PrincipalMixin:

    def post(self, request, *args, **kwargs):
        response = super(PrincipalMixin, self).post(
            self, request, *args, **kwargs)

        #if self.object.preferencial:
        #    query_filter = {self.crud.parent_field: self.object.contato}
        #    self.crud.model.objects.filter(**query_filter).exclude(
        #        pk=self.object.pk).update(preferencial=False)
        return response

class CalendarioView(generic.ListView):
    model = Evento
    template_name = 'cerimonial/calendario.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Agenda"

        d = get_date(self.request.GET.get('mes', None))

        workspace = OperadorAreaTrabalho.objects.filter(user=self.request.user.pk, preferencial=True)[0].areatrabalho
        eventos = Evento.objects.filter(inicio__year=d.year, inicio__month=d.month, workspace=workspace).order_by('inicio')
        cal = CalendarAgenda(d.year, d.month, eventos)

        # Call the formatmonth method, which returns our calendar as a table
        html_cal = cal.formatmonth(withyear=True)
        context['calendar'] = mark_safe(html_cal)
        context['prev_month'] = prev_month(d)
        context['next_month'] = next_month(d)
        context['prev_year'] = prev_year(d)
        context['next_year'] = next_year(d)
        context['this_month'] = this_month()
        return context

class AniversariosView(generic.ListView):
    model = Contato
    template_name = 'cerimonial/aniversarios.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Aniversários"

        d = get_date(self.request.GET.get('mes', None))

        workspace = OperadorAreaTrabalho.objects.filter(user=self.request.user.pk, preferencial=True)[0].areatrabalho
        contatos = Contato.objects.prefetch_related('email_set', 'telefone_set', 'endereco_set', 'endereco_set__estado', 'endereco_set__municipio', 'endereco_set__bairro').filter(                                                                            data_nascimento__month=d.month, workspace=workspace).order_by('data_nascimento')
        cal = CalendarAniversarios(d.year, d.month, contatos)

        # Call the formatmonth method, which returns our calendar as a table
        html_cal = cal.formatmonth(withyear=True)
        context['calendar'] = mark_safe(html_cal)
        context['prev_month'] = prev_month(d)
        context['next_month'] = next_month(d)
        context['prev_year'] = prev_year(d)
        context['next_year'] = next_year(d)
        context['this_month'] = this_month()
        return context

class ContatosImportaView(FormView):
    template_name = 'cerimonial/contato_importa.html'
    form_class = ContatosImportaForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Importação de Contatos"
        return context

    def get_initial(self):
            initial = {}

            try:
                initial['user'] = User.objects.filter(pk=self.request.user.pk)[0]
                initial['workspace'] = OperadorAreaTrabalho.objects.filter(user=self.request.user.pk, preferencial=True)[0].areatrabalho
            except:
                raise PermissionDenied(_('Sem permissão de acesso!'))

            return initial

class EventoCrud(DetailMasterCrud):
    model = Evento
    container_field_set = 'workspace__operadores'

    class BaseMixin(DetailMasterCrud.BaseMixin):
        list_field_names = ['titulo', ('bairro', 'municipio'), 'inicio', 'termino']
        layout_key = 'Evento'

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context['subnav_template_name'] = None
            return context


        def get_initial(self):
            initial = {}

            try:
                initial['workspace'] = OperadorAreaTrabalho.objects.filter(user=self.request.user.pk, preferencial=True)[0].areatrabalho
            except:
                raise PermissionDenied(_('Sem permissão de acesso!'))

            return initial


    class ListView(DetailMasterCrud.ListView):

        def get(self, request, *args, **kwargs):
            return DetailMasterCrud.ListView.get(
                self, request, *args, **kwargs)

        def get_queryset(self):
            queryset = DetailMasterCrud.ListView.get_queryset(self)

            queryset = queryset.filter(workspace=OperadorAreaTrabalho.objects.filter(user=self.request.user.pk, preferencial=True)[0].areatrabalho)
            queryset = queryset.order_by('inicio')

            return queryset

    class CreateView(DetailMasterCrud.CreateView):
        form_class = EventoForm
        layout_key = 'Evento'

    class DeleteView(DetailMasterCrud.DeleteView):
        form_class = EventoForm 
        layout_key = 'Evento'

        def get(self, request, *args, **kwargs):
            self.object = self.get_object()

            if self.object.workspace == OperadorAreaTrabalho.objects.filter(user=self.request.user.pk, preferencial=True)[0].areatrabalho:
                return super(DetailMasterCrud.DeleteView, self).get(request, *args, **kwargs)
            else:
               raise Http404


    class UpdateView(DetailMasterCrud.UpdateView):
        form_class = EventoForm 
        layout_key = 'Evento'

        def get(self, request, *args, **kwargs):
            self.object = self.get_object()

            if self.object.workspace == OperadorAreaTrabalho.objects.filter(user=self.request.user.pk, preferencial=True)[0].areatrabalho:
                return super(DetailMasterCrud.UpdateView, self).get(request, *args, **kwargs)
            else:
               raise Http404

    class DetailView(DetailMasterCrud.DetailView):

        def get_object(self, queryset=None):

           if self.object.workspace == OperadorAreaTrabalho.objects.filter(user=self.request.user.pk, preferencial=True)[0].areatrabalho:
               return self.object
           else:
               raise Http404


class FiliacaoPartidariaCrud(MasterDetailCrudPermission):
    model = FiliacaoPartidaria
    parent_field = 'contato'
    container_field = 'contato__workspace__operadores'


class DependenteCrud(MasterDetailCrudPermission):
    model = Dependente
    parent_field = 'contato'
    container_field = 'contato__workspace__operadores'

    class BaseMixin(MasterDetailCrudPermission.BaseMixin):
        list_field_names = ['nome', 'parentesco', 'data_nascimento', 'sexo']


class TelefoneCrud(MasterDetailCrudPermission):
    model = Telefone
    parent_field = 'contato'
    container_field = 'contato__workspace__operadores'

    class BaseMixin(MasterDetailCrudPermission.BaseMixin):
        list_field_names = ['telefone', 'tipo', 'operadora', 'principal', 'permite_contato', 'whatsapp']

    class CreateView(PrincipalMixin, MasterDetailCrudPermission.CreateView):
        form_class = TelefoneForm

    class UpdateView(PrincipalMixin, MasterDetailCrudPermission.UpdateView):
        form_class = TelefoneForm


class EmailCrud(MasterDetailCrudPermission):
    model = Email
    parent_field = 'contato'
    container_field = 'contato__workspace__operadores'

    class BaseMixin(MasterDetailCrudPermission.BaseMixin):
        list_field_names = ['email', 'tipo', 'principal', 'permite_contato']

    class CreateView(PrincipalMixin, MasterDetailCrudPermission.CreateView):
        form_class = EmailForm

    class UpdateView(PrincipalMixin, MasterDetailCrudPermission.UpdateView):
        form_class = EmailForm

class LocalTrabalhoCrud(MasterDetailCrudPermission):
    model = LocalTrabalho
    parent_field = 'contato'
    container_field = 'contato__workspace__operadores'

    class BaseMixin(MasterDetailCrudPermission.BaseMixin):
        list_field_names = ['nome', 'nome_fantasia', 'cargo', 'data_inicio']

    class CreateView(PrincipalMixin, MasterDetailCrudPermission.CreateView):
        form_class = LocalTrabalhoForm
        layout_key = 'LocalTrabalhoLayoutForForm'
        template_name = 'core/crispy_form_with_trecho_search.html'

    class UpdateView(PrincipalMixin, MasterDetailCrudPermission.UpdateView):
        form_class = LocalTrabalhoForm
        layout_key = 'LocalTrabalhoLayoutForForm'
        template_name = 'core/crispy_form_with_trecho_search.html'


# TODO: view está sem nenhum tipo de autenticação.
class ContatoFragmentFormPronomesView(FormView):
    form_class = ContatoFragmentPronomesForm
    template_name = 'crud/ajax_form.html'

    def get_initial(self):
        initial = FormView.get_initial(self)

        try:
            initial['instance'] = TipoAutoridade.objects.get(
                pk=self.kwargs['pk'])
        except:
            pass

        return initial

    def get(self, request, *args, **kwargs):

        return FormView.get(self, request, *args, **kwargs)

class EnderecoCrud(MasterDetailCrudPermission):
    model = Endereco
    parent_field = 'contato'
    container_field = 'contato__workspace__operadores'

    class BaseMixin(MasterDetailCrudPermission.BaseMixin):
        list_field_names = [('endereco', 'numero'), 'cep', 'bairro', 'municipio', 'principal', 'permite_contato']

    class CreateView(PrincipalMixin, MasterDetailCrudPermission.CreateView):
        form_class = EnderecoForm
        layout_key = 'EnderecoLayoutForForm'

    class UpdateView(PrincipalMixin, MasterDetailCrudPermission.UpdateView):
        form_class = EnderecoForm
        layout_key = 'EnderecoLayoutForForm'


# ---- Peril Master e Details ----------------------------
class PerfilCrud(PerfilAbstractCrud):
    pass


class EnderecoPerfilCrud(PerfilDetailCrudPermission):
    model = EnderecoPerfil
    parent_field = 'contato'

    class BaseMixin(PerfilDetailCrudPermission.BaseMixin):
        list_field_names = [('endereco', 'numero'), 'cep', 'bairro','municipio', 'principal', 'permite_contato']

#    class CreateView(PrincipalMixin, PerfilDetailCrudPermission.CreateView):
#        form_class = EnderecoForm
        #template_name = 'core/crispy_form_with_trecho_search.html'

#    class UpdateView(PrincipalMixin, PerfilDetailCrudPermission.UpdateView):
#        form_class = EnderecoForm
        #template_name = 'core/crispy_form_with_trecho_search.html'


class TelefonePerfilCrud(PerfilDetailCrudPermission):
    model = TelefonePerfil
    parent_field = 'contato'

    class BaseMixin(PerfilDetailCrudPermission.BaseMixin):
        list_field_names = ['telefone', 'tipo', 'operadora', 'principal', 'permite_contato', 'whatsapp']

    class UpdateView(PrincipalMixin, PerfilDetailCrudPermission.UpdateView):
        pass

    class CreateView(PrincipalMixin, PerfilDetailCrudPermission.CreateView):
        pass


class EmailPerfilCrud(PerfilDetailCrudPermission):
    model = EmailPerfil
    parent_field = 'contato'

    class BaseMixin(PerfilDetailCrudPermission.BaseMixin):
        list_field_names = ['email', 'tipo', 'principal', 'permite_contato']

    class UpdateView(PrincipalMixin, PerfilDetailCrudPermission.UpdateView):
        pass

    class CreateView(PrincipalMixin, PerfilDetailCrudPermission.CreateView):
        pass


class LocalTrabalhoPerfilCrud(PerfilDetailCrudPermission):
    model = LocalTrabalhoPerfil
    parent_field = 'contato'

    class BaseMixin(PerfilDetailCrudPermission.BaseMixin):
        list_field_names = ['nome', 'nome_fantasia', 'cargo', 'data_inicio']

    class CreateView(PrincipalMixin, PerfilDetailCrudPermission.CreateView):
        form_class = LocalTrabalhoPerfilForm
        template_name = 'cerimonial/crispy_form_with_trecho_search.html'

    class UpdateView(PrincipalMixin, PerfilDetailCrudPermission.UpdateView):
        form_class = LocalTrabalhoPerfilForm
        template_name = 'cerimonial/crispy_form_with_trecho_search.html'


class DependentePerfilCrud(PerfilDetailCrudPermission):
    model = DependentePerfil
    parent_field = 'contato'

# ---- Processo Master e Details ----------------------------


class AssuntoProcessoCrud(CrudSaap):
    help_text = 'assuntoprocesso'
    model = AssuntoProcesso
    model_set = 'processo_set'

    class BaseMixin(CrudSaap.BaseMixin):
        list_field_names = ['descricao']

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context['subnav_template_name'] = \
                'cerimonial/subnav_assuntoprocesso.yaml'
            return context

    class DetailView(CrudSaap.DetailView):
        list_field_names_set = ['titulo',
                                'contatos'
                                ]

    class ListView(CrudSaap.ListView):
        form_search_class = ListWithSearchForm
        paginate_by = 30

        def get(self, request, *args, **kwargs):
            return CrudSaap.ListView.get(
                self, request, *args, **kwargs)

        def get_context_data(self, **kwargs):
            context = CrudSaap.ListView.get_context_data(self, **kwargs)
            return context

        def get_queryset(self):
            qs = self.model.objects.all()
            q_param = self.request.GET.get('q', '')
            if q_param:
                q = Q(descricao__icontains=q_param)
                qs = qs.filter(q)

            o_param = self.request.GET.get('o', '')
            ordering='descricao'
            if o_param:
                o_param = int(o_param)
                if abs(o_param) == 1:
                    ordering='descricao'

                if int(o_param)<0:
                    ordering = '-' + ordering

            return qs.order_by(ordering)

class ProcessoMasterCrud(DetailMasterCrud):
    model = Processo
    container_field = 'workspace__operadores'

    class BaseMixin(DetailMasterCrud.BaseMixin):
        list_field_names = [ 'id', 'titulo', 'data_abertura', 'classificacao', 'status', 'topicos', 'assuntos' ]

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            #context['subnav_template_name'] = 'cerimonial/subnav_processo.yaml'
            context['subnav_template_name'] = None
            return context

        def get_form(self, form_class=None):
            try:
                form = super(CrispyLayoutFormMixin, self).get_form(form_class)
            except AttributeError as e:
                # simply return None if there is no get_form on super
                pass
            else:
                return form

        def get_form_kwargs(self):
            kwargs = super().get_form_kwargs()

            kwargs.update({'yaml_layout': self.get_layout()})
            return kwargs

        def get_initial(self):
            initial = {}

            try:
                initial['workspace'] = OperadorAreaTrabalho.objects.filter(user=self.request.user.pk, preferencial=True)[0].areatrabalho
            except:
                raise PermissionDenied(_('Sem permissão de acesso!'))

            return initial

    class ListView(DetailMasterCrud.ListView):
        form_search_class = ListWithSearchProcessoForm

        def get(self, request, *args, **kwargs):
            return DetailMasterCrud.ListView.get(
                self, request, *args, **kwargs)

        def get_queryset(self):
            queryset = DetailMasterCrud.ListView.get_queryset(self)

            pk = self.request.GET.get('pk', '')
            contatos = self.request.GET.get('contatos', '')
            numeros = self.request.GET.get('numeros', '')
            classificacoes = self.request.GET.getlist('classificacoes', '')
            status = self.request.GET.getlist('status', '')
            topicos = self.request.GET.getlist('topicos', '')
            assuntos = self.request.GET.getlist('assuntos', '')
            bairros = self.request.GET.getlist('bairros', '')
            importancias = self.request.GET.getlist('importancias', '')
            urgente = self.request.GET.get('urgente', '')
            endereco = self.request.GET.get('endereco', '')
            envolvidos = self.request.GET.get('envolvidos', '')
            data_envio_inicial = self.request.GET.get('data_envio_inicial', '')
            data_envio_final = self.request.GET.get('data_envio_final', '')
            data_protocolo_inicial = self.request.GET.get('data_protocolo_inicial', '')
            data_protocolo_final = self.request.GET.get('data_protocolo_final', '')
            data_abertura_inicial = self.request.GET.get('data_abertura_inicial', '')
            data_abertura_final = self.request.GET.get('data_abertura_final', '')
            data_retorno_inicial = self.request.GET.get('data_retorno_inicial', '')
            data_retorno_final = self.request.GET.get('data_retorno_final', '')
            data_solucao_inicial = self.request.GET.get('data_solucao_inicial', '')
            data_solucao_final = self.request.GET.get('data_solucao_final', '')

            if pk:
                queryset = queryset.filter(pk=pk)

            if urgente:
                if int(urgente) > 1:
                    f = None
                    if int(urgente) == 2:
                        f = True
                    elif int(urgente) == 3:
                        f = False

                    queryset = queryset.filter(urgente=f)

            if endereco:
                query = normalize(endereco)

                query = query.split(' ')
                if query:
                    q = Q()
                    for item in query:
                        if not item:
                            continue
                        # Remove acentos dos campos que estão no banco
                        q = q & Q(rua__unaccent__icontains=item)
                    if q:
                        queryset = queryset.filter(q)

            if envolvidos:
                query = normalize(envolvidos)

                query = query.split(' ')
                if query:
                    q = Q()
                    for item in query:
                        if not item:
                            continue
                        q = q & (Q(orgao__icontains=item) |
                                 Q(instituicao__icontains=item))
                    if q:
                        queryset = queryset.filter(q)



            if numeros:
                query = normalize(numeros)

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

            if bairros:
                queryset = queryset.filter(bairro__in=bairros).distinct()

            if classificacoes:
                queryset = queryset.filter(classificacao__in=classificacoes).distinct()

            if assuntos:
                queryset = queryset.filter(assuntos__in=assuntos).distinct()

            if status:
                queryset = queryset.filter(status__in=status).distinct()

            if topicos:
                queryset = queryset.filter(topicos__in=topicos).distinct()

            if importancias:
                queryset = queryset.filter(importancia__in=importancias).distinct()

            if contatos:
                query = normalize(contatos)

                query = query.split(' ')
                if query:
                    q = Q()
                    for item in query:
                        if not item:
                            continue
                        # Remove acentos dos campos que estão no banco
                        q = q & (Q(contatos__nome__unaccent__icontains=item) |
                                 Q(contatos__nome_social__unaccent__icontains=item) |
                                 Q(contatos__apelido__unaccent__icontains=item))

                    if q:
                        queryset = queryset.filter(q)
 
            if data_envio_inicial:
                data = datetime.datetime.strptime(data_envio_inicial, "%d/%m/%Y").date()

                queryset = queryset.filter(data_envio__gte=data)

            if data_envio_final:
                data = datetime.datetime.strptime(data_envio_final, "%d/%m/%Y").date()

                queryset = queryset.filter(data_envio__lte=data)

            if data_abertura_inicial:
                data = datetime.datetime.strptime(data_abertura_inicial, "%d/%m/%Y").date()

                queryset = queryset.filter(data_abertura__gte=data)

            if data_abertura_final:
                data = datetime.datetime.strptime(data_abertura_final, "%d/%m/%Y").date()

                queryset = queryset.filter(data_abertura__lte=data)

            if data_solucao_inicial:
                data = datetime.datetime.strptime(data_solucao_inicial, "%d/%m/%Y").date()

                queryset = queryset.filter(data_solucao__gte=data)

            if data_solucao_final:
                data = datetime.datetime.strptime(data_solucao_final, "%d/%m/%Y").date()

                queryset = queryset.filter(data_solucao__lte=data)

            if data_retorno_inicial:
                data = datetime.datetime.strptime(data_retorno_inicial, "%d/%m/%Y").date()

                queryset = queryset.filter(data_retorno__gte=data)

            if data_retorno_final:
                data = datetime.datetime.strptime(data_retorno_final, "%d/%m/%Y").date()

                queryset = queryset.filter(data_retorno__lte=data)

            if data_protocolo_inicial:
                data = datetime.datetime.strptime(data_protocolo_inicial, "%d/%m/%Y").date()

                queryset = queryset.filter(data_protocolo__gte=data)

            if data_protocolo_final:
                data = datetime.datetime.strptime(data_protocolo_final, "%d/%m/%Y").date()

                queryset = queryset.filter(data_protocolo__lte=data)

            queryset = queryset.filter(workspace=OperadorAreaTrabalho.objects.filter(user=self.request.user.pk, preferencial=True)[0].areatrabalho)
            queryset = queryset.order_by('titulo')

            return queryset

    class CreateView(DetailMasterCrud.CreateView):
        form_class = ProcessoForm
        layout_key = 'ProcessoLayoutForForm'

    class UpdateView(DetailMasterCrud.UpdateView):
        form_class = ProcessoForm
        layout_key = 'ProcessoLayoutForForm'

        def get(self, request, *args, **kwargs):
            self.object = self.get_object()

            if self.object.workspace == OperadorAreaTrabalho.objects.filter(user=self.request.user.pk, preferencial=True)[0].areatrabalho:
                return super(DetailMasterCrud.UpdateView, self).get(request, *args, **kwargs)
            else:
               raise Http404

    class DetailView(DetailMasterCrud.DetailView):

        def get_object(self, queryset=None):

           if self.object.workspace == OperadorAreaTrabalho.objects.filter(user=self.request.user.pk, preferencial=True)[0].areatrabalho:
               return self.object
           else:
               raise Http404


class ContatoFragmentFormSearchView(FormView):
    form_class = ContatoFragmentSearchForm
    template_name = 'crud/ajax_form.html'

    def get_initial(self):
        initial = FormView.get_initial(self)

        try:
            initial['workspace'] = OperadorAreaTrabalho.objects.filter(user=self.request.user.pk, preferencial=True)[0].areatrabalho
            initial['q'] = self.request.GET[
                'q'] if 'q' in self.request.GET else ''
            initial['pks_exclude'] = self.request.GET.getlist('pks_exclude[]')
        except:
            raise PermissionDenied(_('Sem permissão de acesso!'))

        return initial

    def get(self, request, *args, **kwargs):

        return FormView.get(self, request, *args, **kwargs)


class ProcessoContatoCrud(MasterDetailCrudPermission):
    parent_field = 'contatos'
    model = ProcessoContato
    help_path = 'processo'
    is_m2m = True
    container_field = 'contatos__workspace__operadores'

    class BaseMixin(MasterDetailCrudPermission.BaseMixin):
        list_field_names = [ 'id', 'titulo', 'data_abertura', 'classificacao', 'status', 'topicos','assuntos' ]

        def get_initial(self):
            initial = {}

            try:
                initial['workspace'] = OperadorAreaTrabalho.objects.filter(user=self.request.user.pk, preferencial=True)[0].areatrabalho
            except:
                raise PermissionDenied(_('Sem permissão de acesso!'))

            return initial

    class CreateView(MasterDetailCrudPermission.CreateView):
        layout_key = 'ProcessoLayoutForForm'
        form_class = ProcessoContatoForm
        template_name = 'cerimonial/processo_form.html'

        """def form_valid(self, form):
            response = MasterDetailCrudPermission.CreateView.form_valid(
                self, form)

            pk = self.kwargs['pk']
            self.object.contatos.add(Contato.objects.get(pk=pk))

            return response"""

    class UpdateView(MasterDetailCrudPermission.UpdateView):
        layout_key = 'ProcessoLayoutForForm'
        form_class = ProcessoContatoForm
        template_name = 'cerimonial/processo_form.html'

    class DetailView(MasterDetailCrudPermission.DetailView):
        layout_key = 'Processo'

    class ListView(MasterDetailCrudPermission.ListView):
        layout_key = 'ProcessoLayoutForForm'

        def get_queryset(self):
            qs = MasterDetailCrudPermission.ListView.get_queryset(self)
            qs = qs.annotate(pk_unico=Max('pk'))
            return qs

class GrupoDeContatosMasterCrud(DetailMasterCrudSaap):
    model = GrupoDeContatos
    container_field = 'workspace__operadores'
    model_set = 'contatos'

    class BaseMixin(DetailMasterCrudSaap.BaseMixin):
        list_field_names = ['nome']
        list_field_names_set = ['nome', 'telefone_set', 'email_set']
        layout_key = 'GrupoDeContatosLayoutForForm'

        def get_initial(self):
            initial = {}

            try:
                initial['workspace'] = OperadorAreaTrabalho.objects.filter(user=self.request.user.pk, preferencial=True)[0].areatrabalho
            except:
                raise PermissionDenied(_('Sem permissão de acesso!'))

            return initial

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context['subnav_template_name'] = None
            return context

        def get_form(self, form_class=None):
            try:
                form = super(CrispyLayoutFormMixin, self).get_form(form_class)
            except AttributeError as e:
                # simply return None if there is no get_form on super
                pass
            else:
                return form

        def get_form_kwargs(self):
            kwargs = super().get_form_kwargs()

            kwargs.update({'yaml_layout': self.get_layout()})
            return kwargs

    class ListView(DetailMasterCrudSaap.ListView):
        form_search_class = ListWithSearchForm
        paginate_by = 50

        def get(self, request, *args, **kwargs):
            return DetailMasterCrudSaap.ListView.get(
                self, request, *args, **kwargs)

        def get_context_data(self, **kwargs):
            context = DetailMasterCrudSaap.ListView.get_context_data(self, **kwargs)
            context['subnav_template_name'] = None
            return context

        def get_queryset(self):

            queryset = self.model.objects.all()

            q = Q(workspace=OperadorAreaTrabalho.objects.filter(user=self.request.user.pk, preferencial=True)[0].areatrabalho)

            q_param = self.request.GET.get('q', '')
            if q_param:
                q.add(Q(nome__icontains=q_param), Q.AND)

            queryset = queryset.filter(q)

            o_param = self.request.GET.get('o', '')
            ordering='nome'
            if o_param:
                o_param = int(o_param)
                if abs(o_param) == 1:
                    ordering='nome'

                if int(o_param)<0:
                    ordering = '-' + ordering


            return queryset.order_by(ordering)

    class CreateView(DetailMasterCrudSaap.CreateView):
        template_name = 'cerimonial/crispy_form_with_contato_search.html'
        form_class = GrupoDeContatosForm

    class UpdateView(DetailMasterCrudSaap.UpdateView):
        template_name = 'cerimonial/crispy_form_with_contato_search.html'
        form_class = GrupoDeContatosForm
