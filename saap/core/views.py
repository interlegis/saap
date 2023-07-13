
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth import get_user_model
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
from saap.crud.base_saap import CrudSaap, make_pagination
from saap.core.models import Partido, Filiacao

from saap.core.forms import OperadorAreaTrabalhoForm, ImpressoEnderecamentoForm,\
    ListWithSearchForm, UserForm, UserAdminForm
from saap.core.models import Cep, TipoLogradouro, Logradouro, RegiaoMunicipal,\
    Distrito, Bairro, Municipio, Estado, Trecho, AreaTrabalho, OperadorAreaTrabalho,\
    ImpressoEnderecamento, User, Parlamentar
from saap.core.rules import rules_patterns
from saap.core.serializers import TrechoSearchSerializer, TrechoSerializer
from saap.globalrules import globalrules
from saap.globalrules.crud_custom_saap import DetailMasterCrudSaap,\
    MasterDetailCrudSaapPermission
from saap.utils import normalize

from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

globalrules.rules.config_groups(rules_patterns)

class UserCrud(CrudSaap):
    help_text = 'usuario'
    model = get_user_model()

    class BaseMixin(CrudSaap.BaseMixin):
        list_field_names = ['email', 'first_name', 'last_name', 'groups', 'is_active']

    class DetailView(CrudSaap.DetailView):
        layout_key = 'UserDetail'

        def get_context_data(self, **kwargs):
            context = CrudSaap.DetailView.get_context_data(self, **kwargs)
            context['title'] = '{} <br><small>{}</small>'.format(
                self.object.get_full_name() or '...',
                self.object.email
            )
            return context

    class CreateView(CrudSaap.CreateView):
        form_class = UserAdminForm

        def form_valid(self, form):
            form.instance.event_agency = self.request.user.pk
            if form.is_valid():
                form.save()
                return HttpResponseRedirect(reverse('saap.core:user_list',))

    class UpdateView(CrudSaap.UpdateView):
        form_class = UserAdminForm

        def form_valid(self, form):
            form.instance.event_agency = self.request.user.pk
            if form.is_valid():
                form.save()
                return HttpResponseRedirect(reverse('saap.core:user_detail', kwargs={'pk': self.kwargs['pk']}))

    class ListView(CrudSaap.ListView):
        form_search_class = ListWithSearchForm
        paginate_by = 50

        def get(self, request, *args, **kwargs):
            return CrudSaap.ListView.get(
                self, request, *args, **kwargs)

        def get_context_data(self, **kwargs):
            context = CrudSaap.ListView.get_context_data(self, **kwargs)
            context['subnav_template_name'] = None
            context['title'] = _('Usuários')
            return context

        def hook_header_groups(self, *args, **kwargs):
            return 'Grupos'

        def hook_header_is_active(self, *args, **kwargs):
            return 'Ativo?'

        def get_queryset(self):
            qs = self.model.objects.all()
            q_param = self.request.GET.get('q', '')
            if q_param:
                q = Q(first_name__icontains=q_param)
                q |= Q(last_name__icontains=q_param)
                q |= Q(email__icontains=q_param)
                q |= Q(groups__name__icontains=q_param)
                qs = qs.filter(q)

            o_param = self.request.GET.get('o', '')
            ordering='first_name'
            if o_param:
                o_param = int(o_param)
                if abs(o_param) == 1:
                    ordering='email'
                elif abs(o_param) ==2:
                    ordering='first_name'
                elif abs(o_param) ==3:
                    ordering='last_name'
                elif abs(o_param) ==4:
                    ordering='groups__name'
                elif abs(o_param) ==5:
                    ordering='is_active'

                if int(o_param)<0:
                    ordering = '-' + ordering

            return qs.order_by(ordering)

class AreaTrabalhoCrud(DetailMasterCrudSaap):
    help_text = 'area_trabalho'
    model = AreaTrabalho
    model_set = 'operadorareatrabalho_set'

    class BaseMixin(DetailMasterCrudSaap.BaseMixin):
        list_field_names = ['nome', 'parlamentar', 'descricao']

#        def get_context_data(self, **kwargs):
#            context = super().get_context_data(**kwargs)
#            context['subnav_template_name'] = 'core/subnav_areatrabalho.yaml'
#            return context

    class DetailView(DetailMasterCrudSaap.DetailView):
#        layout_key = 'AreaTrabalhoDetail'
        list_field_names_set = ['user', 'grupos_associados']

    def change(request, workspace_id=None):
        workspaces = OperadorAreaTrabalho.objects.filter(user=request.user.pk)
        workspaces.update(preferencial=False)
        workspaces.filter(areatrabalho=workspace_id).update(preferencial=True)

        return HttpResponseRedirect(reverse('saap.cerimonial:contato_list'))

    class ListView(CrudSaap.ListView):
        form_search_class = ListWithSearchForm
        paginate_by = 50

        def get(self, request, *args, **kwargs):
            return CrudSaap.ListView.get(
                self, request, *args, **kwargs)

        def get_context_data(self, **kwargs):
            context = CrudSaap.ListView.get_context_data(self, **kwargs)
            context['subnav_template_name'] = None
            context['title'] = _('Áreas de Trabalho')
            return context

        def get_queryset(self):
            qs = self.model.objects.all()
            q_param = self.request.GET.get('q', '')
            if q_param:
                q = Q(nome__icontains=q_param)
                q |= Q(parlamentar__nome_parlamentar__icontains=q_param)
                q |= Q(descricao__icontains=q_param)
                qs = qs.filter(q)

            o_param = self.request.GET.get('o', '')
            ordering='nome'
            if o_param:
                o_param = int(o_param)
                if abs(o_param) == 1:
                    ordering='nome'
                elif abs(o_param) == 2:
                    ordering='parlamentar'
                elif abs(o_param) == 3:
                    ordering='descricao'

                if int(o_param)<0:
                    ordering = '-' + ordering

            return qs.order_by(ordering)

class OperadorAreaTrabalhoCrud(DetailMasterCrudSaap):
    parent_field = 'areatrabalho'
    model = OperadorAreaTrabalho
    help_path = 'operadorareatrabalho'

    class BaseMixin(DetailMasterCrudSaap.BaseMixin):

        list_field_names = ['user', 'areatrabalho', 'grupos_associados', 'preferencial']

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            #ontext['subnav_template_name'] = 'core/subnav_areatrabalho.yaml'
            return context

    class UpdateView(DetailMasterCrudSaap.UpdateView):
        form_class = OperadorAreaTrabalhoForm

        def form_valid(self, form):
            old = OperadorAreaTrabalho.objects.get(pk=self.object.pk)

            groups = list(old.grupos_associados.values_list('name', flat=True))
            globalrules.rules.groups_remove_user(old.user, groups)

            response = super().form_valid(form)

            groups = list(self.object.grupos_associados.values_list(
                'name', flat=True))
            globalrules.rules.groups_add_user(self.object.user, groups)

            return response

    class CreateView(DetailMasterCrudSaap.CreateView):
        form_class = OperadorAreaTrabalhoForm

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

    class DetailView(DetailMasterCrudSaap.DetailView):
        layout_key = 'OperadorAreaTrabalhoDetail'

        def get_context_data(self, **kwargs):
            context = CrudSaap.DetailView.get_context_data(self, **kwargs)
            context['title'] = '{} <br><small>{}</small>'.format(
                self.object.user,
                self.object.areatrabalho
            )
            return context

 
    class DeleteView(CrudSaap.DeleteView):

        def post(self, request, *args, **kwargs):

            self.object = self.get_object()
            groups = list(
                self.object.grupos_associados.values_list('name', flat=True))
            globalrules.rules.groups_remove_user(self.object.user, groups)

            return MasterDetailCrudPermission.DeleteView.post(
                self, request, *args, **kwargs)
    
    class ListView(CrudSaap.ListView):
        form_search_class = ListWithSearchForm
        paginate_by = 50

        def get(self, request, *args, **kwargs):
            return CrudSaap.ListView.get(
                self, request, *args, **kwargs)

        def get_context_data(self, **kwargs):
            context = CrudSaap.ListView.get_context_data(self, **kwargs)
            context['subnav_template_name'] = None
            context['title'] = _('Operadores das Áreas de Trabalho')
            return context

        def get_queryset(self):
            qs = self.model.objects.all()
            q_param = self.request.GET.get('q', '')
            if q_param:
                q = Q(user__first_name__icontains=q_param)
                q |= Q(user__email__icontains=q_param)
                q |= Q(areatrabalho__nome__icontains=q_param)
                qs = qs.filter(q)

            o_param = self.request.GET.get('o', '')
            ordering='user'
            if o_param:
                o_param = int(o_param)
                if abs(o_param) == 1:
                    ordering = 'user__first_name'
                elif abs(o_param) == 2:
                    ordering = 'areatrabalho__nome'
                elif abs(o_param) == 3:
                    ordering = 'grupos_associados'
                elif abs(o_param) == 4:
                    ordering = 'preferencial'

                if int(o_param)<0:
                    ordering = '-' + ordering

            return qs.order_by(ordering)

#-------------------------------------------------

TipoLogradouroCrud = DetailMasterCrudSaap.build(TipoLogradouro, None, 'tipo_logradouro')

class DistritoCrud(DetailMasterCrudSaap):
    help_text = 'distrito'
    model = Distrito

    class BaseMixin(DetailMasterCrudSaap.BaseMixin):
        list_field_names = ['nome', 'municipio', 'estado']

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
                q = Q(nome__icontains=q_param)
                q |= Q(municipio__nome__icontains=q_param)
                q |= Q(estado__nome__icontains=q_param)
                qs = qs.filter(q)

            o_param = self.request.GET.get('o', '')
            ordering='nome'
            if o_param:
                o_param = int(o_param)
                if abs(o_param) == 1:
                    ordering='nome'
                elif abs(o_param) == 2:
                    ordering='municipio'
                elif abs(o_param) == 3:
                    ordering='estado'

                if int(o_param)<0:
                    ordering = '-' + ordering

            return qs.order_by(ordering)


class RegiaoMunicipalCrud(DetailMasterCrudSaap):
    help_text = 'regiao_municipal'
    model = RegiaoMunicipal

    class BaseMixin(DetailMasterCrudSaap.BaseMixin):
        list_field_names = ['nome', 'municipio', 'estado']

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
                q = Q(nome__icontains=q_param)
                q |= Q(municipio__nome__icontains=q_param)
                q |= Q(estado__nome__icontains=q_param)
                qs = qs.filter(q)

            o_param = self.request.GET.get('o', '')
            ordering='nome'
            if o_param:
                o_param = int(o_param)
                if abs(o_param) == 1:
                    ordering='nome'
                elif abs(o_param) == 2:
                    ordering='municipio'
                elif abs(o_param) == 3:
                    ordering='estado'

                if int(o_param)<0:
                    ordering = '-' + ordering

            return qs.order_by(ordering)


class BairroCrud(DetailMasterCrudSaap):
    help_text = 'bairro'
    model = Bairro

    class BaseMixin(DetailMasterCrudSaap.BaseMixin):
        list_field_names = ['nome', 'municipio', 'estado']

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
                q = Q(nome__icontains=q_param)
                q |= Q(municipio__nome__icontains=q_param)
                q |= Q(estado__nome__icontains=q_param)
                qs = qs.filter(q)

            o_param = self.request.GET.get('o', '')
            ordering='nome'
            if o_param:
                o_param = int(o_param)
                if abs(o_param) == 1:
                    ordering='nome'
                elif abs(o_param) == 2:
                    ordering='municipio'
                elif abs(o_param) == 3:
                    ordering='estado'

                if int(o_param)<0:
                    ordering = '-' + ordering

            return qs.order_by(ordering)


class LogradouroCrud(DetailMasterCrudSaap):
    help_text = 'logradouro'
    model = Logradouro

    class BaseMixin(DetailMasterCrudSaap.BaseMixin):
        list_field_names = ['nome']

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
                q = Q(nome__icontains=q_param)
                qs = qs.filter(q)

            o_param = self.request.GET.get('o', '')
            ordering='nome'
            if o_param:
                o_param = int(o_param)
                if abs(o_param) == 1:
                    ordering='nome'

                if int(o_param)<0:
                    ordering = '-' + ordering

            return qs.order_by(ordering)


class MunicipioCrud(DetailMasterCrudSaap):
    help_text = 'municipio'
    model = Municipio

    class BaseMixin(DetailMasterCrudSaap.BaseMixin):
        list_field_names = ['nome', 'estado']

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
                q = Q(nome__icontains=q_param)
                q |= Q(estado__nome__icontains=q_param)
                q |= Q(estado__sigla=q_param)
                qs = qs.filter(q)

            o_param = self.request.GET.get('o', '')
            ordering='nome'
            if o_param:
                o_param = int(o_param)
                if abs(o_param) == 1:
                    ordering='nome'

                if int(o_param)<0:
                    ordering = '-' + ordering

            return qs.order_by(ordering)

class CepCrud(DetailMasterCrudSaap):
    help_text = 'cep'
    model = Cep

    class BaseMixin(DetailMasterCrudSaap.BaseMixin):
        list_field_names = ['numero']

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
                q = Q(numero__icontains=q_param)
                qs = qs.filter(q)

            o_param = self.request.GET.get('o', '')
            ordering='numero'
            if o_param:
                o_param = int(o_param)
                if abs(o_param) == 1:
                    ordering='numero'

                if int(o_param)<0:
                    ordering = '-' + ordering

            return qs.order_by(ordering)


EstadoCrud = DetailMasterCrudSaap.build(Estado, None, 'estado')

class TrechoCrud(DetailMasterCrudSaap):
    help_text = 'trecho'
    model = Trecho

    class BaseMixin(DetailMasterCrudSaap.BaseMixin):
        list_field_names = [
            ('tipo', 'logradouro'), 'bairro', 'municipio', 'cep', 'lado']

    class ListView(DetailMasterCrudSaap.ListView):
        form_search_class = ListWithSearchForm

        def get(self, request, *args, **kwargs):
            """trechos = Trecho.objects.all()
            for t in trechos:
                t.search = str(t)
                t.save(auto_update_search=False)"""
            return DetailMasterCrudSaap.ListView.get(
                self, request, *args, **kwargs)

        def get_context_data(self, **kwargs):
            context = DetailMasterCrudSaap.ListView.get_context_data(
                self, **kwargs)
            context['title'] = _("Base de CEPs e Endereços")
            return context

    class CreateView(DetailMasterCrudSaap.CreateView):

        def post(self, request, *args, **kwargs):
            response = super(DetailMasterCrudSaap.CreateView, self).post(
                self, request, *args, **kwargs)

            # FIXME: necessário enquanto o metodo save não tratar fields  m2m
            self.object.search = str(self.object)
            self.object.save(auto_update_search=False)

            return response

    class UpdateView(DetailMasterCrudSaap.UpdateView):

        def post(self, request, *args, **kwargs):
            response = super(DetailMasterCrudSaap.UpdateView, self).post(
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


#----------------------------------------------------

class ParlamentarCrud(CrudSaap):
    help_text = 'parlamentar'
    model = Parlamentar

    class BaseMixin(CrudSaap.BaseMixin):
        list_field_names = ['nome_parlamentar', 'nome_completo', 'ativo']

    class DetailView(CrudSaap.DetailView):
        layout_key = 'Parlamentar'

    class CreateView(CrudSaap.CreateView):
        layout_key = 'Parlamentar'

    class ListView(CrudSaap.ListView):
        form_search_class = ListWithSearchForm
        paginate_by = 50

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
                q = Q(nome_completo__icontains=q_param)
                q |= Q(nome_parlamentar__icontains=q_param)
                qs = qs.filter(q)

            o_param = self.request.GET.get('o', '')
            ordering='nome_parlamentar'
            if o_param:
                o_param = int(o_param)
                if abs(o_param) == 1:
                    ordering='nome_completo'
                elif abs(o_param) ==2:
                    ordering='nome_parlamentar'
                elif abs(o_param) ==3:
                    ordering='ativo'

                if int(o_param)<0:
                    ordering = '-' + ordering

            return qs.order_by(ordering)

class PartidoCrud(DetailMasterCrudSaap):
    help_text = 'partidos'
    model_set = 'filiacao_set'
    model = Partido

    def hook_header_data(self, *args, **kwargs):
        return 'Data de filiação'


    class BaseMixin(DetailMasterCrudSaap.BaseMixin):
        list_field_names = ['sigla', 'nome', 'data_criacao', 'data_extincao']

    class DetailView(DetailMasterCrudSaap.DetailView):
        list_field_names_set = ['parlamentar', 'data', 'data_desfiliacao']

    class CreateView(DetailMasterCrudSaap.CreateView):
        layout_key = 'Partido'

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
                q = Q(sigla__icontains=q_param)
                q |= Q(nome__icontains=q_param)
                qs = qs.filter(q)

            o_param = self.request.GET.get('o', '')
            ordering='sigla'
            if o_param:
                o_param = int(o_param)
                if abs(o_param) == 1:
                    ordering='sigla'
                elif abs(o_param) ==2:
                    ordering='nome'
                elif abs(o_param) ==3:
                    ordering='data_criacao'
                elif abs(o_param) ==4:
                    ordering='data_extincao'

                if int(o_param)<0:
                    ordering = '-' + ordering

            return qs.order_by(ordering)

class FiliacaoCrud(CrudSaap):
    model = Filiacao
    help_text = 'filiacao'

    class BaseMixin(CrudSaap.BaseMixin):

        list_field_names = ['parlamentar', 'partido', 'data', 'data_desfiliacao']

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            #context['subnav_template_name'] = 'core/subnav_areatrabalho.yaml'
            return context

    class CreateView(CrudSaap.CreateView):

        def form_valid(self, form):
            self.object = form.save(commit=False)
            oper = Filiacao.objects.filter(
                parlamentar_id=self.object.parlamentar_id,
                partido_id=self.object.partido_id
            ).first()

            if oper:
                form._errors['parlamentar'] = ErrorList([_(
                    'Este Parlamentar já está filiado '
                    'neste Partido.')])
                return self.form_invalid(form)

            response = super().form_valid(form)

            return response

    class DetailView(CrudSaap.DetailView):

        def get_context_data(self, **kwargs):
            context = CrudSaap.DetailView.get_context_data(self, **kwargs)
            context['title'] = '{} <br><small>{}</small>'.format(
                self.object.parlamentar or '...',
                self.object.partido
            )
            return context

    class ListView(CrudSaap.ListView):
        form_search_class = ListWithSearchForm
        paginate_by = 50

        def get(self, request, *args, **kwargs):
            return CrudSaap.ListView.get(
                self, request, *args, **kwargs)

        def get_context_data(self, **kwargs):
            context = CrudSaap.ListView.get_context_data(self, **kwargs)
            context['subnav_template_name'] = None
            return context

        def get_queryset(self):
            qs = self.model.objects.all()
            q_param = self.request.GET.get('q', '')
            if q_param:
                q = Q(parlamentar__nome_parlamentar__icontains=q_param)
                q |= Q(parlamentar__nome_completo__icontains=q_param)
                q |= Q(partido__sigla__icontains=q_param)
                q |= Q(partido__nome__icontains=q_param)
                qs = qs.filter(q)

            o_param = self.request.GET.get('o', '')
            ordering='parlamentar'
            if o_param:
                o_param = int(o_param)
                if abs(o_param) == 1:
                    ordering = 'parlamentar'
                elif abs(o_param) == 2:
                    ordering = 'partido'
                elif abs(o_param) == 3:
                    ordering = 'data'
                elif abs(o_param) == 4:
                    ordering = 'data_desfiliacao'

                if int(o_param)<0:
                    ordering = '-' + ordering

            return qs.order_by(ordering)




#-------------------------------------------------

class ImpressoEnderecamentoCrud(DetailMasterCrudSaap):
    model = ImpressoEnderecamento

    class UpdateView(DetailMasterCrudSaap.UpdateView):
        form_class = ImpressoEnderecamentoForm

    class CreateView(DetailMasterCrudSaap.CreateView):
        form_class = ImpressoEnderecamentoForm

#------------------------------------------------

class HelpTopicView(TemplateView):

    def get_template_names(self):

        topico = self.kwargs['topic']
        try:
            get_template('ajuda/%s.html' % topico)
        except TemplateDoesNotExist as e:
            raise Http404("Esse tópico de ajuda não existe. Acesse os tópicos pelo índice.")

        return ['ajuda/%s.html' % topico]
