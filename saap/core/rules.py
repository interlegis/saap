
from django.utils.translation import ugettext_lazy as _

menu_dados_auxiliares = "menu_dados_auxiliares"
menu_tabelas_auxiliares = "menu_tabelas_auxiliares"
menu_area_trabalho = "menu_area_trabalho"
menu_contatos = "menu_contatos"
menu_grupocontatos = "menu_grupocontatos"
menu_processos = "menu_processos"
menu_impresso_enderecamento = "menu_impresso_enderecamento"
menu_relatorios = "menu_relatorios"

MENU_PERMS_FOR_USERS = (
    (menu_dados_auxiliares, _('Mostrar menu de Dados auxiliares')),
    (menu_tabelas_auxiliares, _('Mostrar menu de Tabelas auxiliares')),
    (menu_contatos, _('Mostrar menu de de Contatos')),
    (menu_grupocontatos, _('Mostrar menu de Grupos de Contatos')),
    (menu_processos, _('Mostrar menu de Processos')),
    (menu_area_trabalho, _('Mostrar menu de &Aacute;reas de trabalho')),
    (menu_impresso_enderecamento,
     _('Mostrar menu de Impressos de endereçamento')),
    (menu_relatorios,
     _('Mostrar Menu de Relatórios')),
)


search_trecho = 'search_trecho'

SEARCH_TRECHO = (
    (search_trecho, _('Consultar base de trechos')),
)


rules_patterns = []
