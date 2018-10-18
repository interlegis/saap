from django.conf.urls import url, include
from django.contrib.auth import views as v_auth
from django.contrib.auth.decorators import permission_required, login_required
from django.views.generic.base import TemplateView

from saap.settings import EMAIL_SEND_USER, SITE_NAME
from saap.core.forms import LoginForm, NewPasswordForm, ResetPasswordForm, PasswordForm
from saap.core.views import CepCrud, RegiaoMunicipalCrud, DistritoCrud,\
    BairroCrud, MunicipioCrud, EstadoCrud, TipoLogradouroCrud, LogradouroCrud, TrechoCrud, \
    TrechoJsonSearchView, TrechoJsonView, AreaTrabalhoCrud,\
    OperadorAreaTrabalhoCrud, PartidoCrud, ImpressoEnderecamentoCrud

from .apps import AppConfig

from django.contrib import admin

app_name = AppConfig.name


urlpatterns = [

    url(r'^login/$', v_auth.login, {'template_name': 'core/login.html',
                                    'authentication_form': LoginForm,
                                    'extra_context': {'fluid': '-fluid'}
                                    }, name='login'),
    url(r'^logout/$', v_auth.logout, {'next_page': '/login'}, name='logout', ),

    url(r'^password_change/$', v_auth.password_change, {'template_name': 'core/password_change.html',
                                                        'password_change_form': NewPasswordForm,
                                                        'post_change_redirect': '/password_change/done',
                                                       }, name='password_change'),
    url(r'^password_change/done/$', v_auth.password_change_done, {'template_name': 'core/password_change_done.html'}, name='password_change_done'),


    url(r'^password_reset/$', v_auth.password_reset, {'template_name': 'core/password_reset.html',
                                                      'password_reset_form': ResetPasswordForm,
                                                      'email_template_name': 'core/password_reset_email.html',
                                                      'subject_template_name': 'core/password_reset_subject.txt',
                                                      'post_reset_redirect': '/password_reset/sent',
                                                      'from_email': EMAIL_SEND_USER,
                                                     }, name='password_reset'),
    url(r'^password_reset/sent/$', v_auth.password_reset_done, {'template_name': 'core/password_reset_sent.html'}, name='password_reset_sent'),

    url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        v_auth.password_reset_confirm, {'template_name':'core/password_reset_confirm.html',
                                        'set_password_form': PasswordForm,
                                        'post_reset_redirect': '/reset/done',
                                       }, name='password_reset_confirm'),
    url(r'^reset/done/$', v_auth.password_reset_complete, {'template_name':'core/password_reset_complete.html'}, name='password_reset_complete'),


#    url(r'^enderecos/', login_required(
#       TrechoSearchView.as_view()), name='search_view'),

    url(r'^areatrabalho/', include(AreaTrabalhoCrud.get_urls() +
                                   OperadorAreaTrabalhoCrud.get_urls())),

    url(r'^api/enderecos.json', TrechoJsonSearchView.as_view(
        {'get': 'list'}), name='trecho_search_rest_json'),
    url(r'^api/trecho.json/(?P<pk>[0-9]+)$', TrechoJsonView.as_view(
        {'get': 'retrieve'}), name='trecho_rest_json'),

    url(r'^sistema/core/cep/', include(CepCrud.get_urls())),
    url(r'^sistema/core/regiaomunicipal/',
        include(RegiaoMunicipalCrud.get_urls())),
    url(r'^sistema/core/distrito/', include(DistritoCrud.get_urls())),
    url(r'^sistema/core/municipio/', include(MunicipioCrud.get_urls())),
    url(r'^sistema/core/estado/', include(EstadoCrud.get_urls())),
    url(r'^sistema/core/bairro/', include(BairroCrud.get_urls())),
    url(r'^sistema/core/tipologradouro/',
        include(TipoLogradouroCrud.get_urls())),
    url(r'^sistema/core/logradouro/', include(LogradouroCrud.get_urls())),
    url(r'^sistema/core/trecho/', include(TrechoCrud.get_urls())),

    url(r'^sistema/core/impressoenderecamento/',
        include(ImpressoEnderecamentoCrud.get_urls())),

    url(r'^sistema/core/partido/', include(PartidoCrud.get_urls())),
    
    url(r'^sistema/$', permission_required(
        'core.menu_tabelas_auxiliares', login_url='saap.core:login')(
        TemplateView.as_view(template_name='saap_sistema.html')),
        name="tabelas_auxiliares"),

    url(r'^sistema$', permission_required(
        'core.menu_tabelas_auxiliares', login_url='saap.core:login')(
        TemplateView.as_view(template_name='saap_sistema.html')),
        name="tabelas_auxiliares"),

]
