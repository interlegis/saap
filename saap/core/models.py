
from compressor.utils.decorators import cached_property
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin, Group
from django.core.exceptions import PermissionDenied
from django.db import models
from django.db.models import permalink
from django.db.models.deletion import PROTECT, CASCADE
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from image_cropping import ImageCropField, ImageRatioField

from smart_selects.db_fields import ChainedForeignKey

from saap.core.rules import SEARCH_TRECHO
from saap.globalrules.globalrules import rules, GROUP_SOCIAL_USERS
from saap.utils import get_settings_auth_user_model, normalize
from saap.utils import YES_NO_CHOICES, restringe_tipos_de_arquivo_img

from .rules import MENU_PERMS_FOR_USERS


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self,
                     email, password, is_staff, is_superuser, **extra_fields):
        """
        Creates and saves a User with the given username, email and password.
        """
        now = timezone.now()
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email,
                          is_staff=is_staff,
                          is_active=True,
                          is_superuser=is_superuser,
                          date_joined=now, **extra_fields)
        user.set_password(password)
        try:
            user.save(using=self._db)
        except:
            user = self.model.objects.get_by_natural_key(email)

        rules.group_social_users_add_user(user)
        return user

    def create_user(self, email, password=None, **extra_fields):
        return self._create_user(email, password, False, False, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        return self._create_user(email, password, True, True, **extra_fields)

    class Meta:
        verbose_name = _('Usuário')
        verbose_name_plural = _('Usuários')


def sizeof_fmt(num, suffix='B'):
    """
    Shamelessly copied from StackOverflow:
    http://stackoverflow.com/questions/1094841/reusable-library-to-get-human-readable-version-of-file-size

    :param num:
    :param suffix:
    :return:
    """
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


def avatar_validation(image):
    if image:
        # 10 MB
        max_file_size = 10 * 1024 * 1024
        if image.size > max_file_size:
            raise forms.ValidationError(
                _('The maximum file size is {0}').format(sizeof_fmt(max_file_size)))


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(_('email address'), unique=True)

    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    last_name = models.CharField(_('last name'), max_length=30, blank=True)
    is_staff = models.BooleanField(
        _('staff status'), default=False,
        help_text=_('Designates whether the user can log into this admin '
                    'site.'))
    is_active = models.BooleanField(
        _('active'), default=True,
        help_text=_('Designates whether this user should be treated as '
                    'active. Unselect this instead of deleting accounts.'))
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    avatar = ImageCropField(
        _('profile picture'), upload_to="avatars/",
        validators=[avatar_validation], null=True, blank=True)
    cropping = ImageRatioField(
        'avatar', '70x70', help_text=_(
            'Note that the preview above will only be updated after '
            'you submit the form.'))

    objects = UserManager()

    USERNAME_FIELD = 'email'

    class Meta(AbstractBaseUser.Meta):
        abstract = False
        permissions = MENU_PERMS_FOR_USERS
        ordering = ['first_name']

    def __str__(self):
        return self.get_display_name()

    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        """
        return ' '.join([self.first_name, self.last_name]).strip()

    def get_short_name(self):
        """
        Returns the short name for the user.
        """
        return self.first_name

    def get_display_name(self):
        return self.get_full_name() or self.email

    @permalink
    def get_absolute_url(self):
        return 'users_profile', [self.pk], {}

    def delete(self, using=None, keep_parents=False):

        if self.groups.all().exclude(name=GROUP_SOCIAL_USERS).exists():
            raise PermissionDenied(
                _('Você não possui permissão para se autoremover do Portal!'))

        return AbstractBaseUser.delete(
            self, using=using, keep_parents=keep_parents)


class SaapSearchMixin(models.Model):

    search = models.TextField(blank=True, default='')

    class Meta:
        abstract = True

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None, auto_update_search=True):

        if auto_update_search and hasattr(self, 'fields_search'):
            search = ''
            for str_field in self.fields_search:
                fields = str_field.split('__')
                if len(fields) == 1:
                    try:
                        search += str(getattr(self, str_field)) + ' '
                    except:
                        pass
                else:
                    _self = self
                    print (str(fields))
                    for field in fields:
                        #print (field)
                        _self = getattr(_self, field)
                    search += str(_self) + ' '
            self.search = search
        self.search = normalize(self.search)

        return super(SaapSearchMixin, self).save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)


class SaapModelMixin(models.Model):
    # para migração
    """created = models.DateTimeField(
        verbose_name=_('created'),
        editable=True, auto_now_add=False)
    modified = models.DateTimeField(
        verbose_name=_('modified'), editable=True, auto_now=False)"""
    # para produção
    created = models.DateTimeField(
        verbose_name=_('created'),
        editable=False, auto_now_add=True)
    modified = models.DateTimeField(
        verbose_name=_('modified'), editable=False, auto_now=True)

    class Meta:
        abstract = True

    def clean(self):
        """
        Check for instances with null values in unique_together fields.
        """
        from django.core.exceptions import ValidationError

        super(SaapModelMixin, self).clean()

        for field_tuple in self._meta.unique_together[:]:
            unique_filter = {}
            unique_fields = []
            null_found = False
            for field_name in field_tuple:
                field_value = getattr(self, field_name)
                if getattr(self, field_name) is None:
                    unique_filter['%s__isnull' % field_name] = True
                    null_found = True
                else:
                    unique_filter['%s' % field_name] = field_value
                    unique_fields.append(field_name)
            if null_found:
                unique_queryset = self.__class__.objects.filter(
                    **unique_filter)
                if self.pk:
                    unique_queryset = unique_queryset.exclude(pk=self.pk)
                if unique_queryset.exists():
                    msg = self.unique_error_message(
                        self.__class__, tuple(unique_fields))
                    raise ValidationError(msg)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None, clean=True):
        if clean:
            self.clean()
        return models.Model.save(
            self,
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields)


class SaapAuditoriaModelMixin(SaapModelMixin):

    owner = models.ForeignKey(
        get_settings_auth_user_model(),
        verbose_name=_('owner'),
        related_name='+',
        on_delete=PROTECT)
    modifier = models.ForeignKey(
        get_settings_auth_user_model(),
        verbose_name=_('modifier'),
        related_name='+',
        on_delete=PROTECT)

    class Meta:
        abstract = True


class Estado(models.Model):

    REGIAO_CHOICES = (
        ('CO', 'Centro-Oeste'),
        ('NE', 'Nordeste'),
        ('NO', 'Norte'),
        ('SE', 'Sudeste'),
        ('SL', 'Sul'),
        ('EX', 'Exterior'),
    )

    nome = models.CharField(max_length=50, blank=True,
        verbose_name =_('Nome'))
    
    sigla = models.CharField(
        max_length=2, blank=False,
        verbose_name =_('Sigla'))
   
    regiao = models.CharField(
        max_length=2, blank=False, choices=REGIAO_CHOICES,
        verbose_name =_('Região geográfica'))

    class Meta:
        verbose_name = _('Estado')
        verbose_name_plural = _('Estados')
        ordering = ['nome']

    def __str__(self):
        return _('%(nome)s') % {
            'nome': self.nome
        }

class Municipio(models.Model):

    nome = models.CharField(max_length=50, blank=True,
        verbose_name =_('Nome'))
    
    estado = models.ForeignKey(
        Estado,
        blank=False, null=False, default=4891,
        related_name='municipios_set',
        verbose_name=_('Estado'))

    class Meta:
        verbose_name = _('Município')
        verbose_name_plural = _('Municípios')
        ordering = ['nome']

    def __str__(self):
        return self.nome


def get_foto_media_path(instance, subpath, filename):
    return './saap/parlamentar/%s/%s/%s' % (instance, subpath, filename)


def foto_upload_path(instance, filename):
    return get_foto_media_path(instance, 'foto', filename)


class NivelInstrucao(models.Model):
    descricao = models.CharField(
        max_length=50, verbose_name=_('Nível de instrução'))

    class Meta:
        verbose_name = _('Nível de instrução')
        verbose_name_plural = _('Níveis de instrução')
        ordering = ['descricao']

    def __str__(self):
        return self.descricao


class SituacaoMilitar(models.Model):
    descricao = models.CharField(
        max_length=50, verbose_name=_('Situação militar'))

    class Meta:
        verbose_name = _('Tipo de situação militar')
        verbose_name_plural = _('Tipos de situações militares')

    def __str__(self):
        return self.descricao


class Parlamentar(models.Model):
    FEMININO = 'F'
    MASCULINO = 'M'
    SEXO_CHOICE = ((FEMININO, _('Feminino')),
                   (MASCULINO, _('Masculino')))

    nome_completo = models.CharField(
        max_length=50, verbose_name=_('Nome completo'))
    nome_parlamentar = models.CharField(
        max_length=50,
        verbose_name=_('Nome do parlamentar'))
    ativo = models.BooleanField(verbose_name=_('Ativo na Casa?'))
    sexo = models.CharField(
        max_length=1, verbose_name=_('Sexo'), choices=SEXO_CHOICE)
    data_nascimento = models.DateField(
        blank=True, null=True, verbose_name=_('Data de nascimento'))
    profissao = models.CharField(
        max_length=50, blank=True, verbose_name=_('Profissão'))
    email = models.EmailField(
        max_length=100,
        blank=True,
        verbose_name=_('E-mail'))
    nivel_instrucao = models.ForeignKey(
        NivelInstrucao,
        blank=True,
        null=True,
        verbose_name=_('Nível de instrução'))
    situacao_militar = models.ForeignKey(
        SituacaoMilitar,
        blank=True,
        null=True,
        verbose_name=_('Situação militar'))    
    cpf = models.CharField(
        max_length=14, blank=True, verbose_name=_('CPF'))
    rg = models.CharField(
        max_length=15, blank=True, verbose_name=_('RG'))
    titulo_eleitor = models.CharField(
        max_length=15,
        blank=True,
        verbose_name=_('Título de eleitor'))
    numero_gab_parlamentar = models.CharField(
        max_length=10, blank=True, verbose_name=_('Nº do gabinete'))
    telefone = models.CharField(
        max_length=50, blank=True, verbose_name=_('Telefone'))
    fax = models.CharField(
        max_length=50, blank=True, verbose_name=_('Fax'))
    endereco_residencia = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Endereço residencial'))
    municipio_residencia = models.ForeignKey(
        Municipio, blank=True, null=True, verbose_name=_('Município'))
    cep_residencia = models.CharField(
        max_length=9, blank=True, verbose_name=_('CEP'))
    telefone_residencia = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Telefone residencial'))
    fax_residencia = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Fax residencial'))
    endereco_web = models.URLField(
        max_length=100, blank=True, verbose_name=_('HomePage'))
    locais_atuacao = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Locais de atuação'))
    biografia = models.TextField(
        blank=True, verbose_name=_('Biografia'))
    # XXX Esse atribuito foi colocado aqui para não atrapalhar a migração
    fotografia = models.ImageField(
        blank=True,
        null=True,
        upload_to=foto_upload_path,
        verbose_name=_('Fotografia'),
        validators=[restringe_tipos_de_arquivo_img])

    class Meta:
        verbose_name = _('Parlamentar')
        verbose_name_plural = _('Parlamentares')
        ordering = ['nome_parlamentar']

    def __str__(self):
        return self.nome_completo


class Partido(models.Model):
    sigla = models.CharField(max_length=9, verbose_name=_('Sigla'))
    nome = models.CharField(max_length=50, verbose_name=_('Nome'))
    data_criacao = models.DateField(
        blank=True, null=True, verbose_name=_('Data de criação'))
    data_extincao = models.DateField(
        blank=True, null=True, verbose_name=_('Data de extinção'))

    class Meta:
        verbose_name = _('Partido')
        verbose_name_plural = _('Partidos')
        ordering = ['sigla']

    def __str__(self):
        return _('%(sigla)s - %(nome)s') % {
            'sigla': self.sigla, 'nome': self.nome
        }
# - - - - - - - - - - - - - - - - - #
# FIM - Modelos importados do SAPL. #
# - - - - - - - - - - - - - - - - - #


class AreaTrabalho(SaapAuditoriaModelMixin):

    nome = models.CharField(max_length=100, blank=True, default='',
                            verbose_name=_('Nome'))

    descricao = models.CharField(
        default='', max_length=254, verbose_name=_('Descrição'))

    parlamentar = models.ForeignKey(
        Parlamentar,
        verbose_name=_('Parlamentar'),
        related_name='areatrabalho_set',
        blank=True, null=True, on_delete=CASCADE)

    operadores = models.ManyToManyField(
        get_settings_auth_user_model(),
        through='OperadorAreaTrabalho',
        through_fields=('areatrabalho', 'user'),
        symmetrical=False,
        related_name='areatrabalho_set')

    class Meta:
        verbose_name = _('Área de trabalho')
        verbose_name_plural = _('Áreas de trabalho')
        ordering = ['descricao']

    def __str__(self):
        return self.nome


class OperadorAreaTrabalho(SaapAuditoriaModelMixin):

    user = models.ForeignKey(
        get_settings_auth_user_model(),
        verbose_name=_('Operador da Área de Trabalho'),
        related_name='operadorareatrabalho_set',
        on_delete=CASCADE)

    areatrabalho = models.ForeignKey(
        AreaTrabalho,
        related_name='operadorareatrabalho_set',
        verbose_name=_('Área de trabalho'),
        on_delete=CASCADE)

    grupos_associados = models.ManyToManyField(
        Group,
        verbose_name=_('Grupos associados'),
        related_name='operadorareatrabalho_set')

    @property
    def user_name(self):
        return '%s - %s' % (
            self.user.get_display_name(),
            self.user.email)

    class Meta:
        verbose_name = _('Operador')
        verbose_name_plural = _('Operadores')
        ordering = ['user']

    def __str__(self):
        return self.user.get_display_name()


class Cep(models.Model):
    numero = models.CharField(max_length=9, verbose_name=_('CEP'), unique=True)

    class Meta:
        verbose_name = _('CEP')
        verbose_name_plural = _("CEPs")
        ordering = ('numero'),

    def __str__(self):
        return self.numero


class RegiaoMunicipal(models.Model):

    TIPO_CHOICES = [
        ('AU', _('Área urbana')),
        ('AR', _('Área rural')),
        ('UA', _('Área única'))]

    nome = models.CharField(
        max_length=254, verbose_name=_('Região municipal'))
    
    #municipio = models.ForeignKey(
    #    Municipio,
    #    blank=False, null=False, default=4891,
    #    related_name='regioes_municipais_set',
    #    verbose_name=_('Município'))

    estado = models.ForeignKey(
        Estado,
        blank=False, null=False, default=21,
        verbose_name=_('Estado'))

    municipio = ChainedForeignKey(
        Municipio,
        chained_field="estado",
        chained_model_field="estado",
        default=4891,
        show_all=False,
        auto_choose=True,
        sort=True,
        verbose_name=_('Município'))

    tipo = models.CharField(
        max_length=2,
        default='AU',
        choices=TIPO_CHOICES, verbose_name='Tipo da região')

    class Meta:
        verbose_name = _('Região municipal')
        verbose_name_plural = _('Regiões municipais')
        unique_together = (
            ('nome', 'municipio'),)

    def __str__(self):
        return '%s - %s' % (
            self.nome, self.get_tipo_display())


class Distrito(models.Model):
    nome = models.CharField(
        max_length=254,
        verbose_name=_('Nome do distrito'))

    estado = models.ForeignKey(
        Estado,
        blank=False, null=False, default=21,
        verbose_name=_('Estado'))

    municipio = ChainedForeignKey(
        Municipio,
        chained_field="estado",
        chained_model_field="estado",
        default=4891,
        show_all=False,
        auto_choose=True,
        sort=True,
        verbose_name=_('Município'))

    #municipio = models.ForeignKey(
    #    Municipio,
    #    blank=False, null=False, default=4891,
    #    related_name='distritos_set',
    #    verbose_name=_('Município'))

    class Meta:
        verbose_name = _('Distrito')
        verbose_name_plural = _("Distritos")
        unique_together = ('nome', 'municipio')

    def __str__(self):
        return self.nome


class Bairro(models.Model):

    nome = models.CharField(
        max_length=254,
        verbose_name=_('Nome'))

    estado = models.ForeignKey(
        Estado,
        blank=False, null=False, default=21,
        verbose_name=_('Estado'))

    municipio = ChainedForeignKey(
        Municipio,
        chained_field="estado",
        chained_model_field="estado",
        default=4891,
        show_all=False,
        auto_choose=True,
        sort=True,
        verbose_name=_('Município'))

    #codigo = models.PositiveIntegerField(
    #    default=0,
    #    verbose_name='Código',
    #    help_text=_('Código do bairro no Cadastro Oficial do município'))

    outros_nomes = models.TextField(
        blank=True,
        verbose_name=_('Outros nomes'),
        help_text=_('Ocorrências similares'))

    class Meta:
        unique_together=('nome', 'municipio')
        ordering = ('nome',)
        verbose_name = _('Bairro')
        verbose_name_plural = _("Bairros")

    def __str__(self):
        return self.nome


class TipoLogradouro(models.Model):
    nome = models.CharField(
        max_length=254,
        verbose_name=_('Tipo de logradouro'),
        unique=True)

    class Meta:
        verbose_name = _('Tipo de logradouro')
        verbose_name_plural = _("Tipos de logradouros")
        ordering = ('nome',)

    def __str__(self):
        return self.nome


class Logradouro(models.Model):
    nome = models.CharField(
        max_length=254,
        verbose_name=_('Logradouro'),
        unique=True)

    class Meta:
        verbose_name = _('Logradouro')
        verbose_name_plural = _("Logradouros")
        ordering = ('nome',)

    def __str__(self):
        return self.nome


class Trecho(SaapSearchMixin, SaapModelMixin):
    logradouro = models.ForeignKey(
        Logradouro,
        blank=True, null=True, default=None,
        related_name='trechos_set',
        verbose_name=_('Logradouro'))

    tipo = models.ForeignKey(
        TipoLogradouro,
        blank=True, null=True, default=None,
        related_name='trechos_set',
        verbose_name=_('Tipo de logradouro'))

    bairro = models.ForeignKey(
        Bairro,
        blank=True, null=True, default=None,
        related_name='trechos_set',
        verbose_name=_('Bairro'))

    distrito = models.ForeignKey(
        Distrito,
        blank=True, null=True, default=None,
        related_name='trechos_set',
        verbose_name=_('Distrito'))

    regiao_municipal = models.ForeignKey(
        RegiaoMunicipal,
        blank=True, null=True, default=None,
        related_name='trechos_set',
        verbose_name=_('Região municipal'))

    municipio = models.ForeignKey(
        Municipio,
        related_name='trechos_set',
        verbose_name=_('Município'))

    LADO_CHOICES = [
        ('NA', _('Não aplicável')),
        ('AL', _('Ambos os lados')),
        ('LE', _('Lado esquerdo')),
        ('LD', _('Lado direito'))]

    lado = models.CharField(
        max_length=2,
        default='AL',
        choices=LADO_CHOICES, verbose_name='Lado do logradouro')

    numero_inicial = models.PositiveIntegerField(
        blank=True, null=True, verbose_name='Número inicial')
    numero_final = models.PositiveIntegerField(
        blank=True, null=True, verbose_name='Número final')

    # http://mundogeo.com/blog/2006/03/01/eixo-de-logradouro-conceitos-e-beneficios-parte-1/
    # Pelo que vi, os correios afirmar não haver mais de um cep por trecho,
    # portanto essa relação poderia ser 1xN, mas pra evitar contratempos
    # futuros.
    cep = models.ManyToManyField(
        Cep,
        related_name='trechos_set',
        verbose_name=_('CEP'))

    @cached_property
    def fields_search(self):
        return [
            'tipo',
            'logradouro',
            'bairro',
            'distrito',
            'regiao_municipal',
            'municipio',
            'cep']


    class Meta:
        verbose_name = _('Trecho de logradouro')
        verbose_name_plural = _("Trechos de logradouro")
        ordering = [
            'municipio__nome',
            'regiao_municipal__nome',
            'distrito__nome',
            'bairro__nome',
            'tipo__nome',
            'logradouro__nome']
        unique_together = (
            ('municipio',
                'regiao_municipal',
                'distrito',
                'bairro',
                'logradouro',
                'tipo',
                'lado',
                'numero_inicial',
                'numero_final'),)

    def __str__(self):
        uf = str(self.municipio.estado.sigla) if self.municipio else ''
        municipio = str(self.municipio.nome) + '-' if self.municipio else ''
        tipo = str(self.tipo) + ' ' if self.tipo else ''
        logradouro = str(self.logradouro) + ' - ' if self.logradouro else ''
        bairro = self.bairro.nome + ' - ' if self.bairro else ''
        distrito = self.distrito.nome + ' - ' if self.distrito else ''
        rm = self.regiao_municipal.nome + \
            ' - ' if self.regiao_municipal else ''

        join_cep = ' - '.join(self.cep.values_list('numero', flat=True))
        join_cep = ' - ' + join_cep if join_cep else ''

        return '%s%s%s%s%s%s%s%s' % (
            tipo, logradouro, bairro, distrito, rm, municipio, uf, join_cep
        )


class ImpressoEnderecamento(models.Model):
    nome = models.CharField(max_length=254, verbose_name='Nome do Impresso')

    TIPO_CHOICES = [
        ('ET', _('Folha de etiquetas')),
        ('EV', _('Envelopes'))]

    tipo = models.CharField(
        max_length=2,
        default='ET',
        choices=TIPO_CHOICES, verbose_name='Tipo do impresso')

    largura_pagina = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name=_('Largura da página'),
        help_text=_('Em centímetros'))
    altura_pagina = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name=_('Altura da página'),
        help_text=_('Em centímetros'))

    margem_esquerda = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name=_('Margem esquerda'),
        help_text=_('Em centímetros'))
    margem_superior = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name=_('Margem superior'),
        help_text=_('Em centímetros'))

    colunasfolha = models.PositiveSmallIntegerField(
        verbose_name=_('Colunas'))
    linhasfolha = models.PositiveSmallIntegerField(
        verbose_name=_('Linhas'))

    larguraetiqueta = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name=_('Largura da etiqueta'),
        help_text=_('Em centímetros'))
    alturaetiqueta = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name=_('Altura da etiquta'),
        help_text=_('Em centímetros'))

    entre_colunas = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name=_('Distância entre colunas'),
        help_text=_('Em centímetros'))
    entre_linhas = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name=_('Distância entre linhas'),
        help_text=_('Em centímetros'))

    fontsize = models.DecimalField(
        max_digits=5, decimal_places=2,
        verbose_name=_('Tamanho da letra'),
        help_text=_('Em pixels'))

    rotate = models.BooleanField(
        default=False,
        choices=YES_NO_CHOICES,
        verbose_name=_('Rotacionar rexto'))

    class Meta:
        verbose_name = _('Impresso para endereçamento')
        verbose_name_plural = _("Impressos para endereçamento")

    def __str__(self):
        return self.nome

class Filiacao(models.Model):
    data = models.DateField(verbose_name=_('Data de filiação'))
    parlamentar = models.ForeignKey(Parlamentar)
    partido = models.ForeignKey(Partido, verbose_name=_('Partido'))
    data_desfiliacao = models.DateField(
        blank=True, null=True, verbose_name=_('Data de desfiliação'))

    class Meta:
        verbose_name = _('Filiação')
        verbose_name_plural = _('Filiações')
        # A ordenação descrescente por data é importante para listagem de
        # parlamentares e tela de Filiações do Parlamentar
        ordering = ('parlamentar', '-data', '-data_desfiliacao')

    def __str__(self):
        return _('%(parlamentar)s - %(partido)s') % {
            'parlamentar': self.parlamentar, 'partido': self.partido
        }
