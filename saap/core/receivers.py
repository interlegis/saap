import inspect
import logging

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core import serializers
from django.db.models.signals import post_delete, post_save, \
    post_migrate
from django.db.utils import DEFAULT_DB_ALIAS
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from saap.core.models import AuditLog

def audit_log_function(sender, **kwargs):
    try:
        if not (sender._meta.app_config.name.startswith('saap') or
                sender._meta.label == settings.AUTH_USER_MODEL):
            return
    except:
        # não é necessário usar logger, aqui é usada apenas para
        # eliminar um o if complexo
        return

    instance = kwargs.get('instance')
    if instance._meta.model == AuditLog:
        return

    logger = logging.getLogger(__name__)

    u = None
    pilha_de_execucao = inspect.stack()
    for i in pilha_de_execucao:
        if i.function == 'migrate':
            return
        r = i.frame.f_locals.get('request', None)
        try:
            if r.user._meta.label == settings.AUTH_USER_MODEL:
                u = r.user
                break
        except:
            # não é necessário usar logger, aqui é usada apenas para
            # eliminar um o if complexo
            pass

    operation = kwargs.get('operation')
    user = u
    model_name = instance.__class__.__name__
    app_name = instance._meta.app_label
    object_id = instance.id
    data = serializers.serialize('json', [instance])

    if len(data) > AuditLog.MAX_DATA_LENGTH:
        data = data[:AuditLog.MAX_DATA_LENGTH]

    if user:
        username = user
    else:
        username = ''

    AuditLog.objects.create(username=username,
                            operation=operation,
                            model_name=model_name,
                            app_name=app_name,
                            timestamp=timezone.now(),
                            object_id=object_id,
                            object=data)

@receiver(post_delete)
def audit_log_post_delete(sender, **kwargs):
    audit_log_function(sender, operation='D', **kwargs)


@receiver(post_save)
def audit_log_post_save(sender, **kwargs):
    operation = 'C' if kwargs.get('created') else 'U'
    audit_log_function(sender, operation=operation, **kwargs)
