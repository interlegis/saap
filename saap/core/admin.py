from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import ugettext_lazy as _
from image_cropping import ImageCroppingMixin

from saap.utils import register_all_models_in_admin

from saap.core.models import AuditLog

from .forms import UserChangeForm, UserCreationForm
from .models import User


"""
class BairroAdmin(admin.ModelAdmin):
    form = BairroForm
    raw_id_field = ('municipio','estado')
    
    #adiciona a url para pegar os municipios filtrados . Acessar url por http://dominio:porta/admin/app/modelo/get_estados/?estado=id_estado ex.: http://localhost:8000/admin/projeto/app/get_estados/?estado=1

    def get_urls(self, *args, **kwargs):
        urls = super(BairroAdmin, self).get_urls(*args, **kwargs)
        myurls = patterns('',
            (r'^get_municipios/$', views.get_municipios, {}, 'get_municipios'),
        )
        return myurls + urls
"""

# Register your models here.
class UserAdmin(BaseUserAdmin, ImageCroppingMixin, admin.ModelAdmin):
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {
         'fields': ('first_name', 'last_name', 'avatar', 'cropping')}),
        (_('Permissions'), {'fields': (
            'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    form = UserChangeForm
    add_form = UserCreationForm
    list_display = ('email', 'first_name', 'last_name', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('first_name',)
    filter_horizontal = ('groups', 'user_permissions',)

class ParlamentarAdmin(admin.ModelAdmin):
    list_display = ('nome')

admin.site.register(get_user_model(), UserAdmin)
#admin.site.register(get_user_model(), ParlamentarAdmin)

register_all_models_in_admin(__name__)

class AuditLogAdmin(admin.ModelAdmin):
    pass

    def has_add_permission(self, request):
        return False

    # def has_change_permission(self, request, obj=None):
    #     return False
    #
    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        pass

    def delete_model(self, request, obj):
        pass

    def save_related(self, request, form, formsets, change):
        pass


# Na linha acima register_all_models_in_admin registrou AuditLog
admin.site.unregister(AuditLog)
admin.site.register(AuditLog, AuditLogAdmin)

admin.site.site_title = 'Administração - SAAP'
admin.site.site_header = 'Administração - SAAP'
