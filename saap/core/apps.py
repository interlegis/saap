from django import apps
from django.utils.translation import ugettext_lazy as _


class AppConfig(apps.AppConfig):
    name = 'saap.core'
    label = 'core'
    verbose_name = _('Ajustes principais')

    def ready(self):
        from saap.core import receivers
