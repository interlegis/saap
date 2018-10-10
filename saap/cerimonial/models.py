from compressor.utils.decorators import cached_property
from django.db import models
from django.db.models.deletion import SET_NULL, PROTECT, CASCADE
from django.utils.translation import ugettext_lazy as _

from saap.core.models import Municipio, Estado, Partido
from saap.core.models import Trecho, Distrito, RegiaoMunicipal,\
    SaapAuditoriaModelMixin, SaapSearchMixin, AreaTrabalho, Bairro
from saap.utils import UF
from saap.utils import YES_NO_CHOICES, NONE_YES_NO_CHOICES,\
    get_settings_auth_user_model, validate_CPF, validate_CEP, validate_telefone

from smart_selects.db_fields import ChainedForeignKey

from exclusivebooleanfield.fields import ExclusiveBooleanField

FEMININO = 'F'
MASCULINO = 'M'
SEXO_CHOICE = ((FEMININO, _('Feminino')),
               (MASCULINO, _('Masculino')))


IMP_BAIXA = 'B'
IMP_MEDIA = 'M'
IMP_ALTA = 'A'
IMP_CRITICA = 'C'
IMPORTANCIA_CHOICE = (
    (IMP_BAIXA, _('Baixa')),
    (IMP_MEDIA, _('Média')),
    (IMP_ALTA, _('Alta')),
    (IMP_CRITICA, _('Crítica')),
)


class DescricaoAbstractModel(models.Model):
    descricao = models.CharField(
        default='', max_length=254, verbose_name=_('Nome / Descrição'))

    class Meta:
        abstract = True
        ordering = ('descricao',)

    def __str__(self):
        return self.descricao


class TipoTelefone(DescricaoAbstractModel):

    class Meta(DescricaoAbstractModel.Meta):
        verbose_name = _('Tipo de Telefone')
        verbose_name_plural = _('Tipos de telefone')


class TipoEndereco(DescricaoAbstractModel):

    class Meta(DescricaoAbstractModel.Meta):
        verbose_name = _('Tipo de Endereço')
        verbose_name_plural = _('Tipos de endereço')


class TipoEmail(DescricaoAbstractModel):

    class Meta(DescricaoAbstractModel.Meta):
        verbose_name = _('Tipo de Email')
        verbose_name_plural = _('Tipos de email')


class Parentesco(DescricaoAbstractModel):

    class Meta(DescricaoAbstractModel.Meta):
        verbose_name = _('Parentesco')
        verbose_name_plural = _('Parentescos')


class EstadoCivil(DescricaoAbstractModel):

    class Meta(DescricaoAbstractModel.Meta):
        verbose_name = _('Estado civil')
        verbose_name_plural = _('Estados civis')
        ordering = ['descricao']


class PronomeTratamento(models.Model):

    nome_por_extenso = models.CharField(
        default='', max_length=254, verbose_name=_('Nome por extenso'))

    abreviatura_singular_m = models.CharField(
        default='', max_length=254, blank=True, verbose_name=_(
            'Abreviatura no masculino singular'))

    abreviatura_singular_f = models.CharField(
        default='', max_length=254, blank=True, verbose_name=_(
            'Abreviatura no feminino singular'))

    abreviatura_plural_m = models.CharField(
        default='', max_length=254, blank=True, verbose_name=_(
            'Abreviatura no masculino plural'))

    abreviatura_plural_f = models.CharField(
        default='', max_length=254, blank=True, verbose_name=_(
            'Abreviatura no feminino plural'))

    vocativo_direto_singular_m = models.CharField(
        default='', max_length=254, blank=True, verbose_name=_(
            'Vocativo direto no masculino singular'))

    vocativo_direto_singular_f = models.CharField(
        default='', max_length=254, blank=True, verbose_name=_(
            'Vocativo direto no feminino singular'))

    vocativo_direto_plural_m = models.CharField(
        default='', max_length=254, blank=True, verbose_name=_(
            'Vocativo direto no masculino plural'))

    vocativo_direto_plural_f = models.CharField(
        default='', max_length=254, blank=True, verbose_name=_(
            'Vocativo direto no feminino plural'))

    vocativo_indireto_singular_m = models.CharField(
        default='', max_length=254, blank=True, verbose_name=_(
            'Vocativo indireto no masculino singular'))

    vocativo_indireto_singular_f = models.CharField(
        default='', max_length=254, blank=True, verbose_name=_(
            'Vocativo indireto no feminino singular'))

    vocativo_indireto_plural_m = models.CharField(
        default='', max_length=254, blank=True, verbose_name=_(
            'Vocativo indireto no masculino plural'))

    vocativo_indireto_plural_f = models.CharField(
        default='', max_length=254, blank=True, verbose_name=_(
            'Vocativo indireto no feminino plural'))

    enderecamento_singular_m = models.CharField(
        default='', max_length=254, blank=True, verbose_name=_(
            'Endereçamento no masculino singular'))

    enderecamento_singular_f = models.CharField(
        default='', max_length=254, blank=True, verbose_name=_(
            'Endereçamento no feminino singular'))

    enderecamento_plural_m = models.CharField(
        default='', max_length=254, blank=True, verbose_name=_(
            'Endereçamento no masculino plural'))

    enderecamento_plural_f = models.CharField(
        default='', max_length=254, blank=True, verbose_name=_(
            'Endereçamento no feminino plural'))

    prefixo_nome_singular_m = models.CharField(
        default='', max_length=254, blank=True, verbose_name=_(
            'Prefixo no masculino singular'))

    prefixo_nome_singular_f = models.CharField(
        default='', max_length=254, blank=True, verbose_name=_(
            'Prefixo no feminino singular'))

    prefixo_nome_plural_m = models.CharField(
        default='', max_length=254, blank=True, verbose_name=_(
            'Prefixo no masculino plural'))

    prefixo_nome_plural_f = models.CharField(
        default='', max_length=254, blank=True, verbose_name=_(
            'Prefixo no feminino plural'))

    class Meta:
        verbose_name = _('Pronome de tratamento')
        verbose_name_plural = _('Pronomes de tratamento')

    def __str__(self):
        return self.nome_por_extenso


class TipoAutoridade(DescricaoAbstractModel):

    pronomes = models.ManyToManyField(
        PronomeTratamento,
        related_name='tipoautoridade_set')

    class Meta(DescricaoAbstractModel.Meta):
        verbose_name = _('Tipo de autoridade')
        verbose_name_plural = _('Tipos de autoridade')


class TipoLocalTrabalho(DescricaoAbstractModel):

    class Meta(DescricaoAbstractModel.Meta):
        verbose_name = _('Tipo do local de trabalho')
        verbose_name_plural = _('Tipos de locais de trabalho')


class NivelInstrucao(DescricaoAbstractModel):

    class Meta(DescricaoAbstractModel.Meta):
        verbose_name = _('Nível de instrução')
        verbose_name_plural = _('Níveis de instrução')


class OperadoraTelefonia(DescricaoAbstractModel):

    class Meta(DescricaoAbstractModel.Meta):
        verbose_name = _('Operadora de telefonia')
        verbose_name_plural = _('Operadoras de telefonia')


class Contato(SaapSearchMixin, SaapAuditoriaModelMixin):

    nome = models.CharField(max_length=100, verbose_name=_('Nome'))

    nome_social = models.CharField(
        blank=True, default='', max_length=100, verbose_name=_('Nome social'))

    apelido = models.CharField(
        blank=True, default='', max_length=100, verbose_name=_('Apelido'))

    data_nascimento = models.DateField(
        blank=True, null=True, verbose_name=_('Data de nascimento')
    )

    sexo = models.CharField(
        max_length=1, blank=True,
        verbose_name=_('Sexo biológico'), choices=SEXO_CHOICE)

    identidade_genero = models.CharField(
        blank=True, default='',
        max_length=100, verbose_name=_('Gênero'))

    tem_filhos = models.NullBooleanField(
        choices=NONE_YES_NO_CHOICES,
        default=None, verbose_name=_('Tem filhos?'))

    quantos_filhos = models.PositiveSmallIntegerField(
        default=0, blank=True, verbose_name=_('Quantos filhos?'))

    estado_civil = models.ForeignKey(
        EstadoCivil,
        related_name='contato_set',
        blank=True, null=True, on_delete=SET_NULL,
        verbose_name=_('Estado civil'))

    nivel_instrucao = models.ForeignKey(
        NivelInstrucao,
        related_name='contato_set',
        blank=True, null=True, on_delete=SET_NULL,
        verbose_name=_('Nível de instrução'))

    estado = models.ForeignKey(
        Estado,
        blank=True, null=True, default=21,
        related_name='contato_set',
        verbose_name=_('Estado de nascimento'))

    naturalidade = ChainedForeignKey(
        Municipio,
        chained_field="estado",
        chained_model_field="estado",
        null=True, blank=True,
        show_all=False,
        auto_choose=True,
        sort=True,
        verbose_name=_('Cidade de nascimento'))

    nome_pai = models.CharField(
        max_length=100, blank=True, verbose_name=_('Nome do pai'))

    nome_mae = models.CharField(
        max_length=100, blank=True, verbose_name=_('Nome da mãe'))

    numero_sus = models.CharField(max_length=20, blank=True, default='', verbose_name=_('Número do SUS'))

    cpf = models.CharField(max_length=14, blank=True, verbose_name=_('CPF'), validators=[validate_CPF])

    titulo_eleitor = models.CharField(
        max_length=14,
        blank=True,
        verbose_name=_('Título de eleitor'))

    rg = models.CharField(max_length=10, blank=True, verbose_name=_('RG'))

    rg_orgao_expedidor = models.CharField(
        max_length=20, blank=True, verbose_name=_('Órgão expedidor'))

    rg_data_expedicao = models.DateField(
        blank=True, null=True, verbose_name=_('Data de expedição'))

    ativo = models.BooleanField(choices=YES_NO_CHOICES,
                                default=True, verbose_name=_('Ativo?'))

    workspace = models.ForeignKey(
        AreaTrabalho,
        verbose_name=_('Área de trabalho'),
        related_name='contato_set',
        blank=True, null=True, on_delete=PROTECT)

    perfil_user = models.ForeignKey(
        get_settings_auth_user_model(),
        verbose_name=_('Perfil do usuário'),
        related_name='contato_set',
        blank=True, null=True, on_delete=CASCADE)

    profissao = models.CharField(
        max_length=254, blank=True, verbose_name=_('Profissão'))

    tipo_autoridade = models.ForeignKey(
        TipoAutoridade,
        verbose_name=TipoAutoridade._meta.verbose_name,
        related_name='contato_set',
        blank=True, null=True, on_delete=SET_NULL)

    cargo = models.CharField(max_length=254, blank=True, default='',
                             verbose_name=_('Cargo/Função'))

    pronome_tratamento = models.ForeignKey(
        PronomeTratamento,
        verbose_name=PronomeTratamento._meta.verbose_name,
        related_name='contato_set',
        blank=True, null=True, on_delete=SET_NULL,
        help_text=_('O pronome de tratamento é opcional, mas será \
        obrigatório caso seja selecionado um tipo de autoridade.'))

    observacoes = models.TextField(
        blank=True, default='',
        verbose_name=_('Outras observações sobre o contato'))

    @cached_property
    def fields_search(self):
        return ['nome',
                'nome_social',
                'apelido']

    class Meta:
        verbose_name = _('Contato')
        verbose_name_plural = _('Contatos')
        ordering = ['nome']
        permissions = (
            ('print_impressoenderecamento',
             _('Pode imprimir impressos de endereçamento')),
            ('print_rel_contato_agrupado_por_processo',
             _('Pode imprimir relatório de contatos agrupados por processo')),
            ('print_rel_contato_agrupado_por_grupo',
             _('Pode imprimir relatório de contatos agrupados por grupo')),
        )
        unique_together = (
            ('nome', 'data_nascimento', 'workspace', 'perfil_user'),)

    def __str__(self):
        return self.nome


class PerfilManager(models.Manager):

    def for_user(self, user):
        return super(
            PerfilManager, self).get_queryset().get(
            perfil_user=user)


class Perfil(Contato):
    objects = PerfilManager()

    class Meta:
        verbose_name = _('Perfil')
        verbose_name_plural = _('Perfis')

        proxy = True


class Telefone(SaapAuditoriaModelMixin):

    contato = models.ForeignKey(
        Contato, on_delete=CASCADE,
        verbose_name=_('Contato'),
        related_name="telefone_set")

    operadora = models.ForeignKey(
        OperadoraTelefonia, on_delete=SET_NULL,
        related_name='telefone_set',
        blank=True, null=True,
        verbose_name=OperadoraTelefonia._meta.verbose_name)

    tipo = models.ForeignKey(
        TipoTelefone,
        blank=True, null=True,
        on_delete=SET_NULL,
        related_name='telefone_set',
        verbose_name='Tipo')

    telefone = models.CharField(max_length=15,
                                verbose_name='Telefone', validators=[validate_telefone])

    proprio = models.BooleanField(
        choices=YES_NO_CHOICES,
        blank=False, default=True, verbose_name=_('Próprio?'))

    whatsapp = models.BooleanField(
        choices=YES_NO_CHOICES,
        blank=False, default=False, verbose_name=_('Possui WhatsApp?'))

    de_quem_e = models.CharField(
        max_length=40, verbose_name='De quem é?', blank=True,
        help_text=_('Se não é próprio, de quem é?'))

#    principal = models.BooleanField(
#        choices=YES_NO_CHOICES,
#        blank=False, default=True, verbose_name=_('Principal?'))

#    permite_contato = models.BooleanField(
#        choices=YES_NO_CHOICES,
#        blank=False, default=True, verbose_name=_('Contato'),
#        help_text=_("Autorizado para contato do gabinete"))

    principal = ExclusiveBooleanField(
        on=('contato'),
        choices=YES_NO_CHOICES,
        blank=False, default=True, verbose_name=_('Principal?'),
        help_text=_("Se estiver 'Sim', após você salvar, este passa a ser o principal, alterando o atual"))

    permite_contato = ExclusiveBooleanField(
        on=('contato'),
        choices=YES_NO_CHOICES,
        blank=False, default=True, verbose_name=_('Contato'),
        help_text=_("Escolhido para contato do gabinete.\
                    Se estiver 'Sim', após você salvar, este passa a ser o escolhido, alterando o atual"))

    @property
    def numero_nome_contato(self):
        return str(self)

    class Meta:
        verbose_name = _('Telefone')
        verbose_name_plural = _('Telefones')

    def __str__(self):
        return self.telefone


class TelefonePerfil(Telefone):

    class Meta:
        proxy = True
        verbose_name = _('Telefone do perfil')
        verbose_name_plural = _('Telefones do perfil')


class Email(SaapAuditoriaModelMixin):

    contato = models.ForeignKey(
        Contato, on_delete=CASCADE,
        verbose_name=_('Contato'),
        related_name="email_set")

    tipo = models.ForeignKey(
        TipoEmail,
        blank=True, null=True,
        on_delete=SET_NULL,
        related_name='email_set',
        verbose_name='Tipo')

    email = models.EmailField(verbose_name='E-mail')

#    principal = models.BooleanField(
#        choices=YES_NO_CHOICES,
#        default=True, verbose_name=_('Principal?'))

#    permite_contato = models.BooleanField(
#        choices=YES_NO_CHOICES,
#        blank=False, default=True, verbose_name=_('Contato'),
#        help_text=_("Autorizado para contato do gabinete"))

    principal = ExclusiveBooleanField(
        on=('contato'),
        choices=YES_NO_CHOICES,
        blank=False, default=True, verbose_name=_('Principal?'),
        help_text=_("Se estiver 'Sim', após você salvar, este passa a ser o principal, alterando o atual"))

    permite_contato = ExclusiveBooleanField(
        on=('contato'),
        choices=YES_NO_CHOICES,
        blank=False, default=True, verbose_name=_('Contato'),
        help_text=_("Escolhido para contato do gabinete.\
                    Se estiver 'Sim', após você salvar, este passa a ser o escolhido, alterando o atual"))

    class Meta:
        verbose_name = _('E-mail')
        verbose_name_plural = _("E-mails")

    def __str__(self):
        return self.email


class EmailPerfil(Email):

    class Meta:
        proxy = True
        verbose_name = _('E-mail do perfil')
        verbose_name_plural = _("E-mails do perfil")


class Dependente(SaapAuditoriaModelMixin):

    parentesco = models.ForeignKey(Parentesco,
                                   on_delete=PROTECT,
                                   related_name='+',
                                   verbose_name=_('Parentesco'))
    contato = models.ForeignKey(Contato,
                                verbose_name=_('Contato'),
                                related_name='dependente_set',
                                on_delete=CASCADE)
    nome = models.CharField(max_length=100, verbose_name=_('Nome'))

    nome_social = models.CharField(
        blank=True, default='', max_length=100, verbose_name=_('Nome social'))

    apelido = models.CharField(
        blank=True, default='', max_length=100, verbose_name=_('Apelido'))
    sexo = models.CharField(
        blank=True, max_length=1, verbose_name=_('Sexo biológico'),
        choices=SEXO_CHOICE)

    data_nascimento = models.DateField(
        blank=True, null=True, verbose_name=_('Data de nascimento'))

    identidade_genero = models.CharField(
        blank=True, default='',
        max_length=100, verbose_name=_('Gênero'))

    nivel_instrucao = models.ForeignKey(
        NivelInstrucao,
        related_name='dependente_set',
        blank=True, null=True, on_delete=SET_NULL,
        verbose_name=_('Nivel de instrução'))

    class Meta:
        verbose_name = _('Dependente')
        verbose_name_plural = _('Dependentes')

    def __str__(self):
        return self.nome


class DependentePerfil(Dependente):

    class Meta:
        proxy = True
        verbose_name = _('Dependente do perfil')
        verbose_name_plural = _('Dependentes do perfil')

class LocalTrabalho(SaapAuditoriaModelMixin):
    contato = models.ForeignKey(Contato,
                                verbose_name=_('Contato'),
                                related_name='localtrabalho_set',
                                on_delete=CASCADE)
    nome = models.CharField(
        max_length=254, verbose_name=_('Nome / Razão social'))

    nome_social = models.CharField(
        blank=True, default='', max_length=254,
        verbose_name=_('Nome fantasia'))

    tipo = models.ForeignKey(
        TipoLocalTrabalho,
        related_name='localtrabalho_set',
        blank=True, null=True, on_delete=SET_NULL,
        verbose_name=_('Tipo do local de trabalho'))

    trecho = models.ForeignKey(
        Trecho,
        verbose_name=_('Trecho'),
        related_name='localtrabalho_set',
        blank=True, null=True, on_delete=SET_NULL)

    estado = models.ForeignKey(
        Estado,
        verbose_name=_('Estado'),
        related_name='localtrabalho_set',
        blank=False, null=False, default=21)

    municipio = ChainedForeignKey(
        Municipio,
        chained_field="estado",
        chained_model_field="estado",
        null=False, blank=False,
        default=4891,
        show_all=False,
        auto_choose=True,
        sort=True,
        verbose_name=_('Município'))

    cep = models.CharField(max_length=9, blank=False, default='',
                           verbose_name=_('CEP'), validators=[validate_CEP])

    endereco = models.CharField(
        max_length=35, blank=False, default='',
        verbose_name=_('Endereço'),
        help_text=_('O campo endereço também é um campo de busca. Nele '
                    'você pode digitar qualquer informação, inclusive '
                    'digitar o CEP para localizar o endereço, e vice-versa!'))

    numero = models.PositiveSmallIntegerField(blank=False, default=0,
                              verbose_name=_('Número'))

    bairro = ChainedForeignKey(
        Bairro,
        chained_field="municipio",
        chained_model_field="municipio",
        null=True, blank=True, default=5,
        show_all=False,
        auto_choose=False,
        sort=True,
        verbose_name=_('Bairro'))

    distrito = ChainedForeignKey(
        Distrito,
        chained_field="municipio",
        chained_model_field="municipio",
        null=True, blank=True,
        show_all=False,
        auto_choose=True,
        sort=True,
        verbose_name=_('Distrito'))

    regiao_municipal = ChainedForeignKey(
        RegiaoMunicipal,
        chained_field="municipio",
        chained_model_field="municipio",
        null=True, blank=True,
        show_all=False,
        auto_choose=True,
        sort=True,
        verbose_name=_('Região municipal'))

    complemento = models.CharField(max_length=6, blank=True, default='',
                                   verbose_name=_('Complemento'))

    data_inicio = models.DateField(
        blank=True, null=True, verbose_name=_('Data de início'))

    data_fim = models.DateField(
        blank=True, null=True, verbose_name=_('Data de fim'))

#    principal = models.BooleanField(
#        choices=YES_NO_CHOICES,
#        default=True, verbose_name=_('Principal?'))

    principal = ExclusiveBooleanField(
        on=('contato'),
        choices=YES_NO_CHOICES,
        blank=False, default=True, verbose_name=_('Principal?'),
        help_text=_("Se estiver 'Sim', após você salvar, este passa a ser o principal, alterando o atual"))

    cargo = models.CharField(
        max_length=254, blank=True, default='',
        verbose_name=_('Cargo/Função'),
        help_text=_('Ao definir um cargo e função aqui, o '
                    'Cargo/Função preenchido na aba "Dados básicos", '
                    'será desconsiderado ao gerar impressos!'))

    class Meta:
        verbose_name = _('Local de trabalho')
        verbose_name_plural = _('Locais de trabalho')

    def __str__(self):
        return self.nome


class LocalTrabalhoPerfil(LocalTrabalho):

    class Meta:
        proxy = True
        verbose_name = _('Local de trabalho do perfil')
        verbose_name_plural = _('Locais de trabalho do perfil')


class Endereco(SaapAuditoriaModelMixin):
    contato = models.ForeignKey(Contato,
                                verbose_name=_('Contato'),
                                related_name='endereco_set',
                                on_delete=CASCADE)

    tipo = models.ForeignKey(
        TipoEndereco,
        related_name='endereco_set',
        blank=True, null=True, on_delete=SET_NULL,
        verbose_name=_('Tipo do endereço'))

    trecho = models.ForeignKey(
        Trecho,
        verbose_name=_('Trecho'),
        related_name='endereco_set',
        blank=True, null=True, on_delete=SET_NULL)

    estado = models.ForeignKey(
        Estado,
        verbose_name=_('Estado'), 
        default=21,
        related_name='endereco_set',
        blank=False, null=False)

    municipio = ChainedForeignKey(
        Municipio,
        chained_field="estado",
        chained_model_field="estado",
        related_name='endereco_set',
        null=False, blank=False,
        show_all=False,
        auto_choose=True,
        sort=True,
        default=4891,
        verbose_name=_('Município'))

    bairro = ChainedForeignKey(
        Bairro,
        chained_field="municipio",
        chained_model_field="municipio",
        null=False, blank=False, default=5,
        show_all=False,
        auto_choose=True,
        sort=True,
        verbose_name=_('Bairro'))

    distrito = ChainedForeignKey(
        Distrito,
        chained_field="municipio",
        chained_model_field="municipio",
        null=True, blank=True,
        show_all=False,
        auto_choose=True,
        sort=True,
        related_name='endereco_set',
        verbose_name=_('Distrito'))

    regiao_municipal = ChainedForeignKey(
        RegiaoMunicipal,
        chained_field="municipio",
        chained_model_field="municipio",
        null=True, blank=True,
        show_all=False,
        auto_choose=True,
        related_name='endereco_set',
        sort=True,
        verbose_name=_('Região municipal'))

    cep = models.CharField(max_length=9, blank=False, null=False, default='',
                           verbose_name=_('CEP'), validators=[validate_CEP])

    endereco = models.CharField(
        max_length=35, blank=False, null=False, default='',
        verbose_name=_('Endereço'),
        help_text=_('O campo endereço também é um campo de busca, nele '
                    'você pode digitar qualquer informação, inclusive '
                    'digitar o CEP para localizar o endereço, e vice-versa!'))

    numero = models.PositiveSmallIntegerField(blank=False, default=0,
                              verbose_name=_('Número'))

    complemento = models.CharField(max_length=6, blank=True, default='',
                                   verbose_name=_('Complemento'))

    ponto_referencia = models.CharField(max_length=254, blank=True, default='',
                                        verbose_name=_('Pontos de referência'))

    observacoes = models.TextField(
        blank=True, default='',
        verbose_name=_('Outras observações sobre o endereço'))

#    principal = models.BooleanField(
#        choices=YES_NO_CHOICES,
#        default=True, verbose_name=_('Principal?'))

#    permite_contato = models.BooleanField(
#        choices=YES_NO_CHOICES,
#        blank=False, default=True, verbose_name=_('Contato'),
#        help_text=_("Autorizado para contato do gabinete"))

    principal = ExclusiveBooleanField(
        on=('contato'),
        choices=YES_NO_CHOICES,
        blank=False, default=True, verbose_name=_('Principal?'),
        help_text=_("Se estiver 'Sim', após você salvar, este passa a ser o principal, alterando o atual"))

    permite_contato = ExclusiveBooleanField(
        on=('contato'),
        choices=YES_NO_CHOICES,
        blank=False, default=True, verbose_name=_('Contato'),
        help_text=_("Escolhido para contato do gabinete.\
                    Se estiver 'Sim', após você salvar, este passa a ser o escolhido, alterando o atual"))

    @cached_property
    def fields_search_endereco(self):
        return ['endereco',
                'complemento',
                'observacoes',
                'ponto_referencia']

    class Meta:
        verbose_name = _('Endereço')
        verbose_name_plural = _('Endereços')

    def __str__(self):
        if(self.numero > 0):
            numero = (', ' + str(self.numero))
        else:
            numero = ', S/N'

        return self.endereco + numero


class EnderecoPerfil(Endereco):

    class Meta:
        proxy = True
        verbose_name = _('Endereço do perfil')
        verbose_name_plural = _('Endereços do perfil')

    def get_absolute_url(self):
        return reverse('view_mymodel', args=(self.pk,))


class FiliacaoPartidaria(SaapAuditoriaModelMixin):
    contato = models.ForeignKey(Contato,
                                verbose_name=_('Contato'),
                                related_name='filiacaopartidaria_set',
                                on_delete=CASCADE)

    data_filiacao = models.DateField(verbose_name=_('Data de filiação'), blank=False, null=False)

    partido = models.ForeignKey(Partido,
                                related_name='filiacaopartidaria_set',
                                verbose_name=Partido._meta.verbose_name)

    data_desfiliacao = models.DateField(blank=True, null=True, verbose_name=_('Data de desfiliação'))

    @property
    def contato_nome(self):
        return str(self.contato)

    class Meta:
        verbose_name = _('Filiação partidária')
        verbose_name_plural = _('Filiações partidárias')

    def __str__(self):
        return str(self.partido)

# -----------------------------------------------------------------
# -----------------------------------------------------------------
#  PROCESSOS
# -----------------------------------------------------------------
# -----------------------------------------------------------------

class StatusProcesso(DescricaoAbstractModel):

    class Meta(DescricaoAbstractModel.Meta):
        verbose_name = _('Status de processo')
        verbose_name_plural = _('Status de processos')

class ClassificacaoProcesso(DescricaoAbstractModel):

    class Meta(DescricaoAbstractModel.Meta):
        ordering = ('descricao',)
        verbose_name = _('Classificação de processo')
        verbose_name_plural = _('Classificações de processos')

    def __str__(self):
        return self.descricao

class TopicoProcesso(DescricaoAbstractModel):

    class Meta(DescricaoAbstractModel.Meta):
        verbose_name = _('Tópico de processo')
        verbose_name_plural = _('Tópicos de processos')


class AssuntoProcesso(DescricaoAbstractModel):

    class Meta(DescricaoAbstractModel.Meta):
        ordering = ('descricao',)
        verbose_name = _('Assunto de processo')
        verbose_name_plural = _('Assuntos de processos')

class Processo(SaapSearchMixin, SaapAuditoriaModelMixin):

    titulo = models.CharField(max_length=200, verbose_name=_('Título'))

    num_controle = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        verbose_name=_('Número de controle do gabinete')
    )

    materia_cam = models.CharField(
        max_length=14,
        blank=True,
        null=True,
        verbose_name=_('Número da matéria na Câmara')
    )

    link_cam = models.CharField(
        max_length=1000,
        blank=True,
        null=True,
        verbose_name=_('Link para acompanhamento na Câmara')
    )

    link_pref_orgao = models.CharField(
        max_length=1000,
        blank=True,
        null=True,
        verbose_name=_('Link para acompanhamento na prefeitura ou outro órgão')
    )

    proto_pref = models.CharField(
        max_length=12,
        blank=True,
        null=True,
        verbose_name=_('Protocolo da Prefeitura')
    )

    proto_orgao = models.CharField(
        max_length=12,
        blank=True,
        null=True,
        verbose_name=_('Protocolo do órgão')
    )

    oficio_cam = models.CharField(
        max_length=12,
        blank=True,
        null=True,
        verbose_name=_('Ofício enviado pela Câmara')
    )

    oficio_pref = models.CharField(
        max_length=12,
        blank=True,
        null=True,
        verbose_name=_('Ofício recebido da Prefeitura')
    )
 
    oficio_orgao = models.CharField(
        max_length=12,
        blank=True,
        null=True,
        verbose_name=_('Ofício recebido do órgão')
    )

    beneficiario = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('Beneficiário')
    )

    instituicao = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('Instituição envolvida')
    )

    orgao = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('Órgão demandado')
    )

    rua = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('Rua da solicitação')
    )

    bairro = models.ForeignKey(Bairro,
                               blank=True, null=True,
                               verbose_name=_('Bairro da solicitação'),
                               related_name='bairro_set',
                               on_delete=SET_NULL)
    
    urgente = models.BooleanField(
        choices=YES_NO_CHOICES,
        default=True, verbose_name=_('Urgente'))

    data_abertura = models.DateField(verbose_name=_('Data de abertura'))

    data_solucao = models.DateField(blank=True, null=True, verbose_name=_('Data da solução'))
    
    data_envio = models.DateField(blank=True, null=True, verbose_name=_('Data do envio'))
    
    data_protocolo = models.DateField(blank=True, null=True, verbose_name=_('Data do protocolo'))
    
    data_retorno = models.DateField(blank=True, null=True, verbose_name=_('Data do retorno'))

    historico = models.TextField(
        blank=True, default='',
        verbose_name=_('Histórico do processo'))

    observacoes = models.TextField(
        blank=True, default='',
        verbose_name=_('Outras observações sobre o processo'))

    solucao = models.TextField(
        blank=True, default='',
        verbose_name=_('Solução do processo'))

    contatos = models.ManyToManyField(Contato,
                                      blank=True,
                                      verbose_name=_(
                                          'Contatos interessados no processo'),
                                      related_name='processo_set',)

    status = models.ForeignKey(StatusProcesso,
                               blank=True, null=True,
                               verbose_name=_('Status'),
                               related_name='processo_set',
                               on_delete=SET_NULL)

    importancia = models.CharField(
        max_length=1, blank=True,
        verbose_name=_('Importância'), choices=IMPORTANCIA_CHOICE)

    topicos = models.ManyToManyField(
        TopicoProcesso, blank=True,
        related_name='processo_set',
        verbose_name=_('Tópicos'))

    classificacoes = models.ForeignKey(ClassificacaoProcesso,
                               blank=True, null=True,
                               verbose_name=_('Classificação'),
                               related_name='processo_set',
                               on_delete=SET_NULL)

    assuntos = models.ManyToManyField(
        AssuntoProcesso, blank=True,
        related_name='processo_set',
        verbose_name=_('Assuntos'),)

    workspace = models.ForeignKey(
        AreaTrabalho,
        verbose_name=_('Área de trabalho'),
        related_name='processo_set',
        on_delete=PROTECT)

    class Meta:
        verbose_name = _('Processo')
        verbose_name_plural = _('Processos')
        ordering = ('titulo', )

    def __str__(self):
        return str(self.titulo)

    @cached_property
    def fields_search(self):
        return ['titulo',
                'observacoes',
                'historico',
                'solucao']


class ProcessoContato(Processo):

    class Meta:
        proxy = True
        verbose_name = _('Processo do contato')
        verbose_name_plural = _('Processos do contato')


class GrupoDeContatos(SaapAuditoriaModelMixin):

    nome = models.CharField(max_length=100,
                            unique=True,
                            verbose_name=_('Nome do grupo'))

    contatos = models.ManyToManyField(Contato,
                                      blank=True,
                                      verbose_name=_(
                                          'Contatos do grupo'),
                                      related_name='grupodecontatos_set',)

    workspace = models.ForeignKey(
        AreaTrabalho,
        verbose_name=_('Área de trabalho'),
        related_name='grupodecontatos_set',
        on_delete=PROTECT)

    class Meta:
        verbose_name = _('Grupo de contatos')
        verbose_name_plural = _('Grupos de contatos')
        ordering = ('nome', )

    def __str__(self):
        return str(self.nome)

