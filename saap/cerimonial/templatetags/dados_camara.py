from django import template
from saap import settings
register = template.Library()

@register.simple_tag() 
def nome_camara(): 
    return settings.DADOS_NOME

@register.simple_tag() 
def endereco_camara(): 
    return settings.DADOS_ENDERECO

@register.simple_tag() 
def municipio_camara(): 
    return settings.DADOS_MUNICIPIO

@register.simple_tag() 
def uf_camara(): 
    return settings.DADOS_UF

@register.simple_tag() 
def cep_camara(): 
    return settings.DADOS_CEP

@register.simple_tag() 
def email_camara(): 
    return settings.DADOS_EMAIL

@register.simple_tag() 
def telefone_camara(): 
    return settings.DADOS_TELEFONE

@register.simple_tag() 
def site_camara(): 
    return settings.DADOS_SITE

@register.simple_tag() 
def versao_atual(): 
    return settings.VERSION

@register.simple_tag() 
def brasao_sistema():
    if settings.BRASAO_PROPRIO == 'True':
        return 'img/brasao-camara.png'
    else:
        return 'img/brasao-republica.png'

@register.simple_tag() 
def nome_sistema(): 
    return settings.SITE_NAME
