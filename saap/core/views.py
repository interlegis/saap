
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.forms.utils import ErrorList
from django.shortcuts import redirect
from django.http import Http404
from django.utils.translation import ugettext_lazy as _
from django_filters.views import FilterView
from django.views.generic.edit import FormView
from django.views.generic.base import TemplateView
from django.template import TemplateDoesNotExist
from django.template.loader import get_template
from rest_framework import viewsets, mixins
from rest_framework.authentication import SessionAuthentication,\
    BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from saap.crud.base import Crud, make_pagination
from saap.core.models import Partido, Filiacao

from saap.core.forms import OperadorAreaTrabalhoForm, ImpressoEnderecamentoForm,\
    ListWithSearchForm, UserForm
from saap.core.models import Cep, TipoLogradouro, Logradouro, RegiaoMunicipal,\
    Distrito, Bairro, Municipio, Estado, Trecho, AreaTrabalho, OperadorAreaTrabalho,\
    ImpressoEnderecamento, User, Parlamentar
from saap.core.rules import rules_patterns
from saap.core.serializers import TrechoSearchSerializer, TrechoSerializer
from saap.globalrules import globalrules
from saap.globalrules.crud_custom import DetailMasterCrud,\
    MasterDetailCrudPermission
from saap.utils import normalize

from django.http import HttpResponseRedirect

globalrules.rules.config_groups(rules_patterns)

CepCrud = DetailMasterCrud.build(Cep, None, 'cep')
RegiaoMunicipalCrud = DetailMasterCrud.build(
    RegiaoMunicipal, None,  'regiao_municipal')
DistritoCrud = DetailMasterCrud.build(Distrito, None, 'distrito')
MunicipioCrud = DetailMasterCrud.build(Municipio, None, 'municipio')
EstadoCrud = DetailMasterCrud.build(Estado, None, 'estado')
BairroCrud = DetailMasterCrud.build(Bairro, None, 'bairro')
TipoLogradouroCrud = DetailMasterCrud.build(TipoLogradouro, None, 'tipo_logradouro')
LogradouroCrud = DetailMasterCrud.build(Logradouro, None, 'logradouro')
ParlamentarCrud = DetailMasterCrud.build(Parlamentar, None, 'parlamentar')

#UserCrud = DetailMasterCrud.build(User, None, 'usuario')

class UserCrud(DetailMasterCrud):
    help_text = 'usuario'
    model = User

    class BaseMixin(DetailMasterCrud.BaseMixin):
         list_field_names = [
            ('first_name', 'last_name'), 'email', 'groups', 'is_active']

class TrechoCrud(DetailMasterCrud):
    help_text = 'trecho'
    model = Trecho

    class BaseMixin(DetailMasterCrud.BaseMixin):
        list_field_names = [
            ('tipo', 'logradouro'), 'bairro', 'municipio', 'cep', 'lado']

    class ListView(DetailMasterCrud.ListView):
        form_search_class = ListWithSearchForm

        def get(self, request, *args, **kwargs):
            """trechos = Trecho.objects.all()
            for t in trechos:
                t.search = str(t)
                t.save(auto_update_search=False)"""
            return DetailMasterCrud.ListView.get(
                self, request, *args, **kwargs)

        def get_context_data(self, **kwargs):
            context = DetailMasterCrud.ListView.get_context_data(
                self, **kwargs)
            context['title'] = _("Base de CEPs e Endereços")
            return context

    class CreateView(DetailMasterCrud.CreateView):

        def post(self, request, *args, **kwargs):
            response = super(DetailMasterCrud.CreateView, self).post(
                self, request, *args, **kwargs)

            # FIXME: necessário enquanto o metodo save não tratar fields  m2m
            self.object.search = str(self.object)
            self.object.save(auto_update_search=False)

            return response

    class UpdateView(DetailMasterCrud.UpdateView):

        def post(self, request, *args, **kwargs):
            response = super(DetailMasterCrud.UpdateView, self).post(
                self, request, *args, **kwargs)

            # FIXME: necessário enquanto o metodo save não tratar fields  m2m
            self.object.search = str(self.object)
            self.object.save(auto_update_search=False)

            return response

class TrechoSearchView(PermissionRequiredMixin, FilterView):
    template_name = 'search/search.html'
    #filterset_class = TrechoFilterSet
    permission_required = 'core.search_trecho'

    paginate_by = 20

    def get(self, request, *args, **kwargs):
        return SearchView.get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(TrechoSearchView,
                        self).get_context_data(**kwargs)
        context['title'] = _('Pesquisa de Endereços')
        paginator = context['paginator']
        page_obj = context['page_obj']

        context['page_range'] = make_pagination(
            page_obj.number, paginator.num_pages)

        qr = self.request.GET.copy()
        if 'page' in qr:
            del qr['page']
        context['filter_url'] = ('&' + qr.urlencode()) if len(qr) > 0 else ''

        return context


class TrechoJsonSearchView(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = TrechoSearchSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    page_size = 0

    def get_queryset(self, *args, **kwargs):
        request = self.request
        queryset = Trecho.objects.all()

        if request.GET.get('q') is not None:
            query = normalize(str(request.GET.get('q')))

            query = query.split(' ')
            if query:
                q = Q()
                for item in query:
                    if not item:
                        continue
                    q = q & Q(search__icontains=item)

                if q:
                    queryset = queryset.filter(q)

        return queryset


class TrechoJsonView(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = TrechoSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    queryset = Trecho.objects.all()


class AreaTrabalhoCrud(DetailMasterCrud):
    model = AreaTrabalho
    model_set = 'operadorareatrabalho_set'

    class BaseMixin(DetailMasterCrud.BaseMixin):
        
        list_field_names = ['nome', 'parlamentar', 'descricao']

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context['subnav_template_name'] = 'core/subnav_areatrabalho.yaml'
            return context

    class DetailView(DetailMasterCrud.DetailView):
        list_field_names_set = []

    def change(request, workspace_id=None):
        workspaces = OperadorAreaTrabalho.objects.filter(user=request.user.pk)
        workspaces.update(preferencial=False)
        workspaces.filter(areatrabalho=workspace_id).update(preferencial=True)

        return HttpResponseRedirect(reverse('saap.cerimonial:contato_list'))

class OperadorAreaTrabalhoCrud(MasterDetailCrudPermission):
    parent_field = 'areatrabalho'
    model = OperadorAreaTrabalho
    help_path = 'operadorareatrabalho'

    class BaseMixin(MasterDetailCrudPermission.BaseMixin):

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context[
                'subnav_template_name'] = 'core/subnav_areatrabalho.yaml'
            return context

    class UpdateView(MasterDetailCrudPermission.UpdateView):
        form_class = OperadorAreaTrabalhoForm

        # TODO tornar operador readonly na edição
        def form_valid(self, form):
            old = OperadorAreaTrabalho.objects.get(pk=self.object.pk)

            groups = list(old.grupos_associados.values_list('name', flat=True))
            globalrules.rules.groups_remove_user(old.user, groups)

            response = super().form_valid(form)

            groups = list(self.object.grupos_associados.values_list(
                'name', flat=True))
            globalrules.rules.groups_add_user(self.object.user, groups)

            return response

    class CreateView(MasterDetailCrudPermission.CreateView):
        form_class = OperadorAreaTrabalhoForm
        # TODO mostrar apenas usuários que não possuem grupo ou que são de
        # acesso social

        def form_valid(self, form):
            self.object = form.save(commit=False)
            oper = OperadorAreaTrabalho.objects.filter(
                user_id=self.object.user_id,
                areatrabalho_id=self.object.areatrabalho_id
            ).first()

            if oper:
                form._errors['user'] = ErrorList([_(
                    'Este Operador já está registrado '
                    'nesta Área de Trabalho.')])
                return self.form_invalid(form)

            response = super().form_valid(form)

            groups = list(self.object.grupos_associados.values_list(
                'name', flat=True))
            globalrules.rules.groups_add_user(self.object.user, groups)

            return response

    class DeleteView(MasterDetailCrudPermission.DeleteView):

        def post(self, request, *args, **kwargs):

            self.object = self.get_object()
            groups = list(
                self.object.grupos_associados.values_list('name', flat=True))
            globalrules.rules.groups_remove_user(self.object.user, groups)

            return MasterDetailCrudPermission.DeleteView.post(
                self, request, *args, **kwargs)

class PartidoCrud(DetailMasterCrud):
    help_text = 'partidos'
    model_set = 'filiacaopartidaria_set'
    model = Partido
    container_field_set = 'contato__workspace__operadores'
    # container_field = 'filiacoes_partidarias_set__contato__workspace__operadores'

    class DetailView(DetailMasterCrud.DetailView):
        list_field_names_set = ['contato_nome', ]

    class ListView(DetailMasterCrud.ListView):

        def get(self, request, *args, **kwargs):

            ws = AreaTrabalho.objects.filter(operadores=request.user).first()

            if ws and ws.parlamentar:
                filiacao_parlamentar = Filiacao.objects.filter(
                    parlamentar=ws.parlamentar)

                if filiacao_parlamentar.exists():
                    partido = filiacao_parlamentar.first().partido
                    return redirect(
                        reverse(
                            'saap.core:partido_detail',
                            args=(partido.pk,)))

            """else:
                self.kwargs['queryset_liberar_sem_container'] = True"""

            return DetailMasterCrud.ListView.get(
                self, request, *args, **kwargs)

        """def get_queryset(self):
            queryset = CrudListView.get_queryset(self)
            if not self.request.user.is_authenticated():
                return queryset

            if 'queryset_liberar_sem_container' in self.kwargs and\
                    self.kwargs['queryset_liberar_sem_container']:
                return queryset

            if self.container_field:
                params = {}
                params[self.container_field] = self.request.user.pk
                return queryset.filter(**params)

            return queryset"""


class ImpressoEnderecamentoCrud(DetailMasterCrud):
    model = ImpressoEnderecamento

    class UpdateView(DetailMasterCrud.UpdateView):
        form_class = ImpressoEnderecamentoForm

    class CreateView(DetailMasterCrud.CreateView):
        form_class = ImpressoEnderecamentoForm


class HelpTopicView(TemplateView):

    def get_template_names(self):

        topico = self.kwargs['topic']
        try:
            get_template('ajuda/%s.html' % topico)
        except TemplateDoesNotExist as e:
            raise Http404("Esse tópico de ajuda não existe. Acesse os tópicos pelo índice.")

        return ['ajuda/%s.html' % topico]
