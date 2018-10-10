from math import floor

from braces.views import PermissionRequiredMixin
from compressor.utils.decorators import cached_property
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.forms.utils import ErrorList
from django.http.response import HttpResponse
from django.template.defaultfilters import lower
from django.template import Context, loader
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from django_filters.views import FilterView
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle,\
    StyleSheet1, _baseFontNameB
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.platypus.doctemplate import SimpleDocTemplate
from reportlab.platypus.frames import Frame
from reportlab.platypus.para import Paragraph
from reportlab.platypus.tables import TableStyle, LongTable
from reportlab.lib.units import mm

from saap.cerimonial.forms import ImpressoEnderecamentoContatoFilterSet,\
    ContatoAgrupadoPorProcessoFilterSet, ContatoAgrupadoPorGrupoFilterSet
from saap.cerimonial.models import Contato, Processo, Telefone, Email, GrupoDeContatos, Endereco
from saap.core.models import AreaTrabalho
from saap.crud.base import make_pagination


import time, datetime

class ImpressoEnderecamentoContatoView(PermissionRequiredMixin, FilterView):
    permission_required = 'cerimonial.print_impressoenderecamento'
    filterset_class = ImpressoEnderecamentoContatoFilterSet
    model = Contato
    template_name = "cerimonial/filter_impressoenderecamento_contato.html"
    container_field = 'workspace__operadores'

    paginate_by = 30

    @cached_property
    def is_contained(self):
        return True

    @property
    def verbose_name(self):
        return self.model._meta.verbose_name

    @property
    def verbose_name_plural(self):
        return self.model._meta.verbose_name_plural

    def get(self, request, *args, **kwargs):
        filterset_class = self.get_filterset_class()
        self.filterset = self.get_filterset(filterset_class)
        self.object_list = self.filterset.qs

        if len(request.GET) and not len(self.filterset.form.errors)\
                and not self.object_list.exists():
            messages.error(request, _('Não existe contato com as '
                                      'condições definidas na busca!'))

        if 'print' in request.GET and self.object_list.exists():
            if self.filterset.form.cleaned_data['impresso']:
                total_erros = self.validate_data()
                if(total_erros > 0):
                    messages.error(request, _('Existem %s contatos na busca que não tem endereço marcado para Contato.\
                             Revise-os na lista abaixo, antes de gerar o impresso.' % (total_erros)))
                else:
                    filename = str(self.filterset.form.cleaned_data['impresso']) + "_"\
                         + str(datetime.datetime.fromtimestamp(time.time()).strftime('%Y_%m_%d_%H_%M_%S'))
                    response = HttpResponse(content_type='application/pdf')
                    content = 'inline; filename="%s.pdf"' % filename
                    response['Content-Disposition'] = content
                    self.build_pdf(response)
                    return response
            else:
                self.filterset.form._errors['impresso'] = ErrorList([_(
                    'Selecione o tipo de impresso a ser usado!')])

        context = self.get_context_data(filter=self.filterset,
                                        object_list=self.object_list)

        return self.render_to_response(context)

    def get_filterset(self, filterset_class):
        kwargs = self.get_filterset_kwargs(filterset_class)
        try:
            kwargs['workspace'] = AreaTrabalho.objects.filter(
                operadores=self.request.user.pk)[0]
        except:
            raise PermissionDenied(_('Sem permissão de Acesso!'))

        return filterset_class(**kwargs)

    def get_queryset(self):
        qs = super().get_queryset()
        kwargs = {}
        if self.container_field:
            kwargs[self.container_field] = self.request.user.pk

        return qs.filter(**kwargs)

    def get_context_data(self, **kwargs):
        count = self.object_list.count()
        context = super(ImpressoEnderecamentoContatoView,
                        self).get_context_data(**kwargs)
        context['count'] = count

        context['title'] = _('Impressão de Etiquetas e Envelopes')
        paginator = context['paginator']
        page_obj = context['page_obj']

        context['page_range'] = make_pagination(
            page_obj.number, paginator.num_pages)

        qr = self.request.GET.copy()
        if 'page' in qr:
            del qr['page']
        context['filter_url'] = ('&' + qr.urlencode()) if len(qr) > 0 else ''

        for contato in context['page_obj']:            
            endpref = contato.endereco_set.filter(permite_contato=True).first()
            
            if endpref:
                contato.endereco = endpref.endereco if endpref.endereco else ''
                contato.municipio = '%s/%s' % (endpref.municipio.nome, endpref.estado.sigla)
            else:
                contato.endereco = ''
                contato.municipio = ''

            contato.grupo = contato.grupodecontatos_set.all()

        return context

    def build_pdf(self, response):

        cleaned_data = self.filterset.form.cleaned_data

        impresso = cleaned_data['impresso']

        fs = int(impresso.fontsize)

        stylesheet = StyleSheet1()
        stylesheet.add(ParagraphStyle(name='pronome_style',
                                      fontName="Helvetica",
                                      fontSize=fs * 0.8,
                                      leading=fs))
        stylesheet.add(ParagraphStyle(name='nome_style',
                                      fontName="Helvetica-Bold",
                                      fontSize=fs,
                                      leading=fs * 1.3))
        stylesheet.add(ParagraphStyle(name='endereco_style',
                                      fontName="Helvetica",
                                      fontSize=fs * 0.9,
                                      leading=fs))

        pagesize = (float(impresso.largura_pagina) * cm,
                    float(impresso.altura_pagina) * cm)

        ms = pagesize[1] - float(impresso.margem_superior) * cm
        me = float(impresso.margem_esquerda) * cm

        ae = float(impresso.alturaetiqueta) * cm
        le = float(impresso.larguraetiqueta) * cm

        el = float(impresso.entre_linhas) * cm
        ec = float(impresso.entre_colunas) * cm

        col = float(impresso.colunasfolha)
        row = float(impresso.linhasfolha)
        cr = int(col * row)

        p = canvas.Canvas(response, pagesize=pagesize)

        p.setTitle(str(self.filterset.form.cleaned_data['impresso']))

        if impresso.rotate:
            p.translate(pagesize[1], 0)
            p.rotate(90)

        i = -1
        for contato in self.object_list.all():
            i += 1
            if i != 0 and i % cr == 0:
                p.showPage()

                if impresso.rotate:
                    p.translate(pagesize[1], 0)
                    p.rotate(90)

            q = floor(i / col) % row
            r = i % int(col)

            l = me + r * ec + r * le
            b = ms - (q + 1) * ae - q * el

            f = Frame(l, b, le, ae,
                      leftPadding=fs / 3,
                      bottomPadding=fs / 3,
                      topPadding=fs / 3,
                      rightPadding=fs / 3,
                      showBoundary=0)
            # f.drawBoundary(p)
            f.addFromList(self.createParagraphs(contato, stylesheet), p)

        p.showPage()
        p.save()

    def createParagraphs(self, contato, stylesheet):

        cleaned_data = self.filterset.form.cleaned_data

        imprimir_cargo = (cleaned_data['imprimir_cargo'] == 'True')\
            if 'imprimir_cargo' in cleaned_data and\
            cleaned_data['imprimir_cargo'] else False

        local_cargo = cleaned_data['local_cargo']\
            if 'local_cargo' in cleaned_data and\
            cleaned_data['local_cargo'] else ''

        story = []

        linha_pronome = ''
        prefixo_nome = ''

        if contato.pronome_tratamento:
            if 'imprimir_pronome' in cleaned_data and\
                    cleaned_data['imprimir_pronome'] == 'True':
                linha_pronome = getattr(
                    contato.pronome_tratamento,
                    'enderecamento_singular_%s' % lower(
                        contato.sexo))
            prefixo_nome = getattr(
                contato.pronome_tratamento,
                'prefixo_nome_singular_%s' % lower(
                    contato.sexo))

        if local_cargo == ImpressoEnderecamentoContatoFilterSet.DEPOIS_PRONOME\
                and imprimir_cargo and (linha_pronome or contato.cargo):
            linha_pronome = '%s - %s' % (linha_pronome, contato.cargo)

        if linha_pronome:
            story.append(Paragraph(
                linha_pronome, stylesheet['pronome_style']))

        linha_nome = '%s %s' % (prefixo_nome, contato.nome)\
            if prefixo_nome else contato.nome

        if local_cargo == ImpressoEnderecamentoContatoFilterSet.LINHA_NOME\
                and imprimir_cargo:

            linha_nome = '%s %s' % (contato.cargo, linha_nome)
            linha_nome = linha_nome.strip()

        linha_nome = linha_nome.upper()\
            if 'nome_maiusculo' in cleaned_data and\
            cleaned_data['nome_maiusculo'] == 'True' else linha_nome

        story.append(Paragraph(linha_nome, stylesheet['nome_style']))

        if local_cargo == ImpressoEnderecamentoContatoFilterSet.DEPOIS_NOME\
                and imprimir_cargo and contato.cargo:
            story.append(
                Paragraph(contato.cargo, stylesheet['endereco_style']))

        endpref = contato.endereco_set.filter(permite_contato=True).first()

        endereco = endpref.endereco

        if(endpref.numero == None):
            endereco += ", S/N"
        else: 
            if(endpref.numero > 0):
                endereco += ", " + str(endpref.numero)
            else:
                endereco += ", S/N"
                
        if(endpref.complemento != '' and endpref.complemento != None):
           endereco += " - " + endpref.complemento

        municipio_uf = '%s/%s' % (endpref.municipio.nome, endpref.estado.sigla)

        cep = 'CEP %s' % endpref.cep

        bairro = endpref.bairro.nome if endpref.bairro else ''

        story.append(Paragraph(endereco, stylesheet['endereco_style']))
        story.append(Paragraph(bairro, stylesheet['endereco_style']))
        story.append(Paragraph(municipio_uf, stylesheet['endereco_style']))
        story.append(Paragraph(cep, stylesheet['endereco_style']))

        return story

    # obsoleto
    def drawText(self, p, x, y, contato):

        fs = int(self.impresso.fontsize)

        textobject = p.beginText()

        if contato.pronome_tratamento:
            textobject.setTextOrigin(x, y - fs * 0.8)
            textobject.setFont("Helvetica", fs * 0.8)
            textobject.textOut(
                getattr(contato.pronome_tratamento,
                        'enderecamento_singular_%s' % lower(contato.sexo)))
            textobject.moveCursor(0, fs)
        else:
            textobject.setTextOrigin(x, y - fs)

        textobject.setFont("Helvetica-Bold", fs)
        textobject.textOut(contato.nome)

        p.drawText(textobject)

    def validate_data(self):
        contatos = []
        consulta_agregada = self.object_list.order_by('nome',)
        consulta_agregada = consulta_agregada.values_list(
            'id',
        )

        total_erros = 0

        for contato in consulta_agregada.all():
            query = (Q(permite_contato=True))
            query.add(Q(contato__id=contato[0]), Q.AND)

            endereco = Endereco.objects.filter(query).count()

            if(endereco == 0):
                total_erros = total_erros + 1

        return total_erros



class RelatorioAgrupado(PermissionRequiredMixin, FilterView):
    permission_required = 'deve_ser_definida_na_heranca'
    filterset_class = None
    model = None
    template_name = 'deve_ser_definido_na_heranca'
    container_field = 'workspace_definido_na_heranca'

    paginate_by = 30
    
    def __init__(self):
        super().__init__()
        self.MAX_TITULO = 80
        self.ctx_title = 'Título do relatório'
        self.relat_title = 'Título do relatório'
        self.nome_objeto = 'Nome do Objeto'
        self.filename = 'Relatorio'

    @cached_property
    def is_contained(self):
        return True

    @property
    def verbose_name(self):
        return self.model._meta.verbose_name

    @property
    def verbose_name_plural(self):
        return self.model._meta.verbose_name_plural

    def get(self, request, *args, **kwargs):
        filterset_class = self.get_filterset_class()
        self.filterset = self.get_filterset(filterset_class)

        self.object_list = self.filterset.qs

        if 'print' in request.GET and self.object_list.exists():

            filename = str(self.filename) + "_" + str(datetime.datetime.fromtimestamp(time.time()).strftime('%Y_%m_%d_%H_%M_%S'))
            response = HttpResponse(content_type='application/pdf')
            content = 'attachment; filename="%s.pdf"' % filename
            response['Content-Disposition'] = content
            self.build_pdf(response)
            return response

        context = self.get_context_data(filter=self.filterset,
                                        object_list=self.object_list)

        if len(request.GET) and not len(self.filterset.form.errors)\
                and not self.object_list.exists():
            messages.error(request, _(
                'Não existe {} com as '
                'condições definidas na busca!'.format(self.nome_objeto)
            ))

        return self.render_to_response(context)

    def get_filterset(self, filterset_class):
        kwargs = self.get_filterset_kwargs(filterset_class)
        try:
            kwargs['workspace'] = AreaTrabalho.objects.filter(
                operadores=self.request.user.pk)[0]
        except:
            raise PermissionDenied(_('Sem permissão de Acesso!'))

        return filterset_class(**kwargs)

    def get_queryset(self):
        qs = super().get_queryset()
        kwargs = {}
        if self.container_field:
            kwargs[self.container_field] = self.request.user.pk

        return qs.filter(**kwargs)

    def get_context_data(self, **kwargs):
        count = self.object_list.count()
        context = super(RelatorioAgrupado, self).get_context_data(**kwargs)
        context['count'] = count

        context['title'] = _(self.ctx_title)
        paginator = context['paginator']
        page_obj = context['page_obj']

        context['page_range'] = make_pagination(
            page_obj.number, paginator.num_pages)

        qr = self.request.GET.copy()
        if 'page' in qr:
            del qr['page']
        context['filter_url'] = ('&' + qr.urlencode()) if len(qr) > 0 else ''

        return context

    def build_pdf(self, response):

        elements = []

        style = TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('LEADING', (0, 0), (-1, -1), 7),
            ('GRID', (0, 0), (-1, -1), 0.1, colors.black),
            ('INNERGRID', (0, 0), (-1, -1), 0.1, colors.black),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ])
        style.add('VALIGN', (0, 0), (-1, -1), 'MIDDLE')

        data = self.get_data()

        for i, value in enumerate(data):
            if len(value) <= 1:
                style.add('SPAN', (0, i), (-1, i))

            if len(value) == 0:
                style.add('INNERGRID', (0, i), (-1, i), 0, colors.black),
                style.add('GRID', (0, i), (-1, i), -1, colors.white)
                style.add('LINEABOVE', (0, i), (-1, i), 0.1, colors.black)

            if len(value) == 1:
                style.add('LINEABOVE', (0, i), (-1, i), 0.1, colors.black)

        rowHeights = 20
        t = LongTable(data, rowHeights=rowHeights, splitByRow=True)
        t.setStyle(style)
        if len(t._argW) == 5:
            t._argW[0] = 1.8 * cm
            t._argW[1] = 6 * cm
            t._argW[2] = 6.5 * cm
            t._argW[3] = 9.5 * cm
            t._argW[4] = 2.4 * cm
        elif len(t._argW) == 4:
            t._argW[0] = 2 * cm
            t._argW[1] = 10 * cm
            t._argW[2] = 11.5 * cm
            t._argW[3] = 3 * cm

        for i, value in enumerate(data):
            if len(value) == 0:
                t._argH[i] = 7
                continue
            for cell in value:
                if isinstance(cell, list):
                    t._argH[i] = (rowHeights) * (
                        len(cell) - (0 if len(cell) > 1 else 0))
                    break

        elements.append(t)

        doc = SimpleDocTemplate(
            response,
            pagesize=landscape(A4),
            title=self.relat_title,
            rightMargin=1.25 * cm,
            leftMargin=1.25 * cm,
            topMargin=1.1 * cm,
            bottomMargin=0.8 * cm)
        doc.build(elements)

    def get_data(self):
        self.set_headings()
        self.set_styles()

        cleaned_data = self.filterset.form.cleaned_data

        agrupamento = cleaned_data['agrupamento']
        agrupamento = '' if agrupamento == 'sem_agrupamento' else agrupamento
        self.agrupamento = agrupamento

        data = []
        self.set_cabec(self.h5)

        self.set_object_list()
        where = self.object_list.query.where

        for p in self.object_list.all():
            item = []

            self.set_label_agrupamento(p)

            if not data:
                self.add_relat_title(data)

            if not p or isinstance(p, str):
                self.add_group_title(data, p)
                contatos_query = self.build_query(p, where)
            else:
                if len(p.titulo) < self.MAX_TITULO:
                    paragrafo = str(p.titulo)
                    estilo = self.h_style
                else:
                    paragrafo = (
                        p.titulo[:self.MAX_TITULO] +
                        force_text(_(' (Continua...)'))
                    )
                    estilo = self.s_min

                item = [
                    Paragraph(p.data_abertura.strftime('%d/%m/%Y'), self.s_center),
                    Paragraph(paragrafo, estilo)
                ]

                contatos_query = p.contatos.all()

            self.set_body_data(where, contatos_query, data, item)

        return data

    def set_headings(self):
        self.h_style = getSampleStyleSheet()
        self.h3 = self.h_style["Heading3"]
        self.h3.fontName = _baseFontNameB
        self.h3.alignment = TA_CENTER

        self.h4 = self.h_style["Heading4"]
        self.h4.fontName = _baseFontNameB

        self.h5 = self.h_style["Heading5"]
        self.h5.fontName = _baseFontNameB
        self.h5.alignment = TA_CENTER

        self.h_style = self.h_style["BodyText"]
        self.h_style.wordWrap = None  # 'LTR'
        self.h_style.spaceBefore = 0
        self.h_style.fontSize = 8
        self.h_style.leading = 8

    def set_styles(self):
        self.s_min = getSampleStyleSheet()
        self.s_min = self.s_min["BodyText"]
        self.s_min.wordWrap = None  # 'LTR'
        self.s_min.spaceBefore = 0
        self.s_min.fontSize = 6
        self.s_min.leading = 8

        self.s_center = getSampleStyleSheet()
        self.s_center = self.s_center["BodyText"]
        self.s_center.wordWrap = None  # 'LTR'
        self.s_center.spaceBefore = 0
        self.s_center.alignment = TA_CENTER
        self.s_center.fontSize = 8
        self.s_center.leading = 8

        self.s_right = getSampleStyleSheet()
        self.s_right = self.s_right["BodyText"]
        self.s_right.wordWrap = None  # 'LTR'
        self.s_right.spaceBefore = 0
        self.s_right.alignment = TA_RIGHT
        self.s_right.fontSize = 8
        self.s_right.leading = 8

    def set_object_list(self):
        if not self.agrupamento:
            self.object_list = self.object_list.order_by(
                'data_abertura', 'titulo', 'contatos__nome')
        else:
            self.object_list = self.object_list.order_by(
                self.agrupamento).distinct(self.agrupamento).values_list(
                self.agrupamento, flat=True)

    def set_cabec(self, h5):
        cabec = [Paragraph(_('Data'), h5)]
        if self.agrupamento != 'titulo':
            cabec.append(Paragraph(_('Título'), h5))
        cabec.append(Paragraph(_('Nome'), h5))
        cabec.append(Paragraph(_('Endereço'), h5))
        cabec.append(Paragraph(_('Telefone'), h5))
        self.cabec = cabec

    def set_label_agrupamento(self, processo):
        label_agrupamento = ''
        if not processo or isinstance(processo, str):
            label_agrupamento = dict(
                self.filterset_class.AGRUPAMENTO_CHOICE)
            label_agrupamento = force_text(
                label_agrupamento[self.agrupamento])
        self.label_agrupamento = label_agrupamento

    def add_relat_title(self, data):
        tit_relatorio = _(self.relat_title)
        tit_relatorio = force_text(tit_relatorio) + ' '
        if self.label_agrupamento:
             tit_relatorio += force_text(_('(com agrupamento)'))
        else:
            tit_relatorio += force_text(_('(sem agrupamento)'))
        tit_relatorio +=  ' ' + self.label_agrupamento

        data.append([Paragraph(tit_relatorio, self.h3)])

        if not self.label_agrupamento:
            data.append(self.cabec)

    def add_group_title(self, corpo_relatorio, registro_principal):
        import pdb; pdb.set_trace()
        corpo_relatorio.append([])
        lbl_group = self.label_agrupamento
        if registro_principal:
            paragrafo =  lbl_group + ' - ' + str(registro_principal)
        else:
            paragrafo = (
                force_text(_('Sem agrupamento')) + ' ' + lbl_group
            )
        corpo_relatorio.append([Paragraph(paragrafo, self.h4)])

        corpo_relatorio.append(self.cabec)

    def build_query(self, processo, where):
        p_filter = (('processo_set__' + self.agrupamento, processo),)
        if not processo:
            p_filter = (
                (p_filter[0][0] + '__isnull', True),
                (p_filter[0][0] + '__exact', '')
            )

        q = Q()
        for filtro in p_filter:
            filtro_dict = {filtro[0]: filtro[1]}
            q = q | Q(**filtro_dict)

        contatos_query = Contato.objects.all()
        contatos_query.query.where = where.clone()
        contatos_query = contatos_query.filter(q)

        params = {self.container_field: self.request.user.pk}
        contatos_query = contatos_query.filter(**params)

        contatos_query = contatos_query.order_by(
            'processo_set__' + self.agrupamento,
            'processo_set__data_abertura',
            'nome',
            'endereco_set__bairro__nome',
            'endereco_set__endereco').distinct(
            'processo_set__' + self.agrupamento,
            'processo_set__data_abertura',
            'nome')
        return contatos_query

    def set_body_data(self, where, contatos_query, data, item):
        contatos = []
        enderecos = []
        telefones = []
        for contato in contatos_query:

            if self.agrupamento:
                contatos = []
                enderecos = []
                telefones = []
                item = []

            if contatos:
                contatos.append(Paragraph('--------------', self.s_center))
                enderecos.append(Paragraph('--------------', self.s_center))
                telefones.append(Paragraph('--------------', self.s_center))

            contatos.append(Paragraph(str(contato.nome), self.h_style))

            endpref = contato.endereco_set.filter(principal=True).first()
            endereco = ''
            if endpref:
                endereco = endpref.endereco + \
                           (' - ' + endpref.numero
                            if endpref.numero else '') + \
                           (' - ' + endpref.complemento
                            if endpref.complemento else '')

                endereco = '%s - %s - %s - %s' % (
                    endereco,
                    endpref.bairro if endpref.bairro else '',
                    endpref.municipio.nome
                    if endpref.municipio else '',
                    endpref.uf)

            enderecos.append(Paragraph(endereco, self.h_style))

            tels = '\n'.join(map(
                lambda x: str(x), list(contato.telefone_set.all())
            )) if contato.telefone_set.exists() else ''

            telefones.append((Paragraph(tels, self.s_center)))

            if self.agrupamento:
                params = {'contatos': contato,
                          self.container_field: self.request.user.pk}
                processos = Processo.objects.all()
                processos.query.where = where.clone()
                processos = processos.filter(**params)

                ps = None
                data_abertura = []
                titulo = []
                for ps in processos:

                    if data_abertura:
                        data_abertura.append(
                            Paragraph('--------------', self.s_center))
                        if self.agrupamento != 'titulo':
                            titulo.append(
                                Paragraph('--------------', self.s_center))

                    data_abertura.append(
                        Paragraph(
                            ps.data.strftime('%d/%m/%Y'), self.s_center))

                    if self.agrupamento != 'titulo':
                        if len(ps.titulo) < self.MAX_TITULO:
                            paragrafo = str(ps.titulo)
                            estilo = self.h_style
                        else:
                            paragrafo = (
                                ps.titulo[:self.MAX_TITULO] +
                                force_text(_(' (Continua...)'))
                            )
                            estilo = self.s_min
                        titulo.append(Paragraph(paragrafo, estilo))

                if not ps:
                    data_abertura.append(Paragraph('-----', self.s_center))
                    if self.agrupamento != 'titulo':
                        titulo.append(Paragraph('-----', self.s_center))

                if len(data_abertura) == 1:
                    item += data_abertura
                    if self.agrupamento != 'titulo':
                        item += titulo
                else:
                    item.append(data_abertura)
                    if self.agrupamento != 'titulo':
                        item.append(titulo)

                item.append(contatos[0])
                item.append(enderecos[0])
                item.append(telefones[0])

                data.append(item)

        if not self.agrupamento:
            if len(contatos) == 0:
                item.append('-----')
            else:
                item.append(contatos)
                item.append(enderecos)
                item.append(telefones)

            data.append(item)


class RelatorioContatoAgrupadoPorProcessoView(RelatorioAgrupado):
    permission_required = 'cerimonial.print_rel_contato_agrupado_por_processo'
    filterset_class = ContatoAgrupadoPorProcessoFilterSet
    model = Processo
    template_name = "cerimonial/filter_contato_agrupado_por_processo.html"
    container_field = 'workspace__operadores'

    def __init__(self):
        super().__init__()
        self.ctx_title = 'Relatório de Processos'
        self.relat_title = 'Relatório de Processos'
        self.nome_objeto = 'Processo'
        self.filename = 'Relatorio_Processos'


class RelatorioContatoAgrupadoPorGrupoView(RelatorioAgrupado):
    permission_required = 'cerimonial.print_rel_contato_agrupado_por_grupo'
    filterset_class = ContatoAgrupadoPorGrupoFilterSet
    model = Contato
    template_name = 'cerimonial/filter_contato_agrupado_por_grupo.html'
    container_field = 'workspace__operadores'

    def __init__(self):
        super().__init__()
        self.ctx_title = 'Relatório de Contatos'
        self.relat_title = 'Relatório de Contatos'
        self.nome_objeto = 'Contato'
        self.filename = 'Relatorio_Contatos'

    def get(self, request, *args, **kwargs):
        filterset_class = self.get_filterset_class()
        self.filterset = self.get_filterset(filterset_class)
        self.object_list = self.filterset.qs

        if len(request.GET) and not len(self.filterset.form.errors)\
                and not self.object_list.exists():
            messages.error(request, _('Não existe contato com as '
                                      'condições definidas na busca!'))
        
        if 'print' in request.GET and self.object_list.exists():
            if self.filterset.form.cleaned_data['formato'] == 'PDF':
                filename = str(self.filterset.form.cleaned_data['formato']) + "_Contatos_"\
                     + str(datetime.datetime.fromtimestamp(time.time()).strftime('%Y_%m_%d_%H_%M_%S'))
                response = HttpResponse(content_type='application/pdf')
                content = 'inline; filename="%s.pdf"' % filename
                #content = 'attachment; filename="%s.pdf"' % filename
                response['Content-Disposition'] = content
                self.build_pdf(response)
                return response
            elif self.filterset.form.cleaned_data['formato'] == 'TXT':
                total_erros = self.validate_data()
                if(total_erros > 0):
                    messages.error(request, _('Existem %s contatos na busca que não tem e-mail marcado para Contato.\
                             Revise-os na lista abaixo, antes de gerar a mala direta.' % (total_erros)))
                else:
                    filename = str(self.filterset.form.cleaned_data['formato']) + "_Contatos_"\
                         + str(datetime.datetime.fromtimestamp(time.time()).strftime('%Y_%m_%d_%H_%M_%S'))

                    response = HttpResponse(content_type='text/plain')
                    content = 'inline; filename="%s.txt"' % filename
                    #content = 'attachment; filename="%s.txt"' % filename
                    response['Content-Disposition'] = content
                    self.build_txt(response)
                    return response

        context = self.get_context_data(filter=self.filterset,
                                        object_list=self.object_list)
        
        return self.render_to_response(context)

    def get_filterset(self, filterset_class):
        kwargs = self.get_filterset_kwargs(filterset_class)
        try:
            kwargs['workspace'] = AreaTrabalho.objects.filter(
                operadores=self.request.user.pk)[0]
        except:
            raise PermissionDenied(_('Sem permissão de acesso!'))

        return filterset_class(**kwargs)

    def get_queryset(self):
        qs = super().get_queryset()
        kwargs = {}
        if self.container_field:
            kwargs[self.container_field] = self.request.user.pk

        return qs.filter(**kwargs)

    def get_context_data(self, **kwargs):
        count = self.object_list.count()
        context = super(RelatorioContatoAgrupadoPorGrupoView,
                        self).get_context_data(**kwargs)
        context['count'] = count

        context['title'] = _('Relatório de Contatos')
        paginator = context['paginator']
        page_obj = context['page_obj']

        context['page_range'] = make_pagination(
            page_obj.number, paginator.num_pages)

        qr = self.request.GET.copy()
        if 'page' in qr:
            del qr['page']
        context['filter_url'] = ('&' + qr.urlencode()) if len(qr) > 0 else ''

        for contato in context['page_obj']:            
            endpref = contato.endereco_set.filter(principal=True).first()
            grupo = contato.grupodecontatos_set.all()
            
            if endpref:
                contato.bairro = endpref.bairro.nome if endpref.bairro else ''
                contato.municipio = '%s/%s' % (endpref.municipio, endpref.estado.sigla) if endpref.municipio else ''
            else:
                contato.bairro = ''
                contato.municipio = ''

            contato.grupo = grupo
           
            telefone = contato.telefone_set.filter(principal=True).first()
            contato.telefone = telefone.telefone if telefone else ''
            
            email = contato.email_set.filter(permite_contato=True).first()
            contato.email = email.email if email else ''

        return context

    def build_txt(self, response):
        CONTATO = 0
        EMAILS = 3

        NOME = 1

        registros = self.get_data()

        csv_data = []

        for dados in registros:
            sem_email = False
            if(dados[EMAILS] != None):
                for email in dados[EMAILS]:
                    if email.permite_contato == True:
                        csv_data.append([dados[CONTATO][NOME], email])
                        sem_email = True

        t = loader.get_template('cerimonial/contato_email.txt')
        response.write(t.render({'data': csv_data}))
        return response

    def build_pdf(self, response):
        CONTATO = 0
        ENDERECOS = 1
        TELEFONES = 2
        EMAILS = 3
        GRUPOS = 4

        ID = 0
        NOME = 1
        NASCIMENTO = 2

        self.set_headings()
        self.set_styles()
        self.set_cabec(self.h5)

        if self.filterset.form.cleaned_data['orientacao'] == 'P':
            estilo = ParagraphStyle(
                name='Normal',
                fontSize=8,
            )   
        elif self.filterset.form.cleaned_data['orientacao'] == 'R':
            estilo = ParagraphStyle(
                name='Normal',
                fontSize=7,
            )   

        corpo_relatorio = []
        self.add_relat_title(corpo_relatorio)

        tipo_dado_contato = self.filterset.form.cleaned_data['tipo_dado_contato']

        registros = self.get_data()
        for dados in registros:

            enderecos = ''      
            municipios = ''

            if(dados[ENDERECOS] != None):

                for endereco in dados[ENDERECOS]:

                    if(endereco.endereco != '' and endereco.endereco != None):
                        
                        if ((tipo_dado_contato == 'P' and endereco.principal == True) or
                            (tipo_dado_contato == 'C' and endereco.permite_contato == True) or
                            (tipo_dado_contato == 'A')):

                            if(endereco.principal == True and endereco.permite_contato == False):
                                enderecos += "<b>Principal:</b> <br/>"
                            elif(endereco.principal == False and endereco.permite_contato == True):
                                enderecos += "<b>Para contato:</b> <br/>"
                            else:
                                enderecos += "<b>Ambos:</b> <br/>"

                            enderecos += endereco.endereco
    
                            if(endereco.numero == None):
                                enderecos += ", S/N"
                            else: 
                                if(endereco.numero > 0):
                                    enderecos += ", " + str(endereco.numero)
                                else:
                                    enderecos += ", S/N"
                
                            if(endereco.complemento != '' and endereco.complemento != None):
                                enderecos += " - " + endereco.complemento

                            if(endereco.bairro != '' and endereco.bairro != None):
                                enderecos += "<br/>" + endereco.bairro.nome
  
                            enderecos += "<br/>"

                            if(endereco.principal == True and endereco.permite_contato == False):
                                municipios += "<b>Principal:</b> <br/>"
                            elif(endereco.principal == False and endereco.permite_contato == True):
                                municipios += "<b>Para contato:</b> <br/>"
                            else:
                                municipios += "<b>Ambos:</b> <br/>"

                            if(endereco.municipio != '' and endereco.municipio != None):
                                municipios += '%s/%s' % (endereco.municipio.nome, endereco.estado.sigla)
     
                            if(endereco.cep != '' and endereco.cep != None):
                                municipios += "<br/>CEP " + endereco.cep

                            municipios += "<br/>"

            nascimento = ''

            if(dados[CONTATO][NASCIMENTO] != '' and dados[CONTATO][NASCIMENTO] != None):
                nascimento = dados[CONTATO][NASCIMENTO].strftime('%d/%m/%Y')

            telefones = ''

            if(dados[TELEFONES] != None):
                for telefone in dados[TELEFONES]:
                    if ((tipo_dado_contato == 'P' and telefone.principal == True) or
                            (tipo_dado_contato == 'C' and telefone.permite_contato == True) or
                            (tipo_dado_contato == 'A')):
 
                        if(telefone.principal == True and telefone.permite_contato == False):
                            telefones += "<b>Principal:</b> <br/>"
                        elif(telefone.principal == False and telefone.permite_contato == True):
                            telefones += "<b>Para contato:</b> <br/>"
                        else:
                            telefones += "<b>Ambos:</b> <br/>"

                        telefones += telefone.telefone + "<br/>"
             
            emails = ''

            if(dados[EMAILS] != None):
                for email in dados[EMAILS]:
                     if ((tipo_dado_contato == 'P' and email.principal == True) or
                            (tipo_dado_contato == 'C' and email.permite_contato == True) or
                            (tipo_dado_contato == 'A')):
                       
                        if(email.principal == True and email.permite_contato == False):
                            emails += "<b>Principal:</b> <br/>"
                        elif(email.principal == False and email.permite_contato == True):
                            emails += "<b>Para contato:</b> <br/>"
                        else:
                            emails += "<b>Ambos:</b> <br/>"

                        emails += email.email + "<br/>"

            grupos = ''

            if(dados[GRUPOS] != None):
                for grupo in dados[GRUPOS]:
                    grupos += grupo.nome + "<br/>"


            item = [
                Paragraph(dados[CONTATO][NOME], estilo),
                Paragraph(nascimento, estilo),
                Paragraph(enderecos, estilo),
                Paragraph(municipios, estilo),
                Paragraph(telefones, estilo),
                Paragraph(emails, estilo),
                Paragraph(grupos, estilo),
            ]
            corpo_relatorio.append(item)

        style = TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 6),
            ('LEADING', (0, 0), (-1, -1), 7),
            ('GRID', (0, 0), (-1, -1), 0.1, colors.black),
            ('INNERGRID', (0, 0), (-1, -1), 0.1, colors.black),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ])
        style.add('VALIGN', (0, 0), (-1, -1), 'MIDDLE')

        for i, value in enumerate(corpo_relatorio):
            if len(value) <= 1:
                style.add('SPAN', (0, i), (-1, i))

            if len(value) == 0:
                style.add('INNERGRID', (0, i), (-1, i), 0, colors.black),
                style.add('GRID', (0, i), (-1, i), -1, colors.white)
                style.add('LINEABOVE', (0, i), (-1, i), 0.1, colors.black)

            if len(value) == 1:
                style.add('LINEABOVE', (0, i), (-1, i), 0.1, colors.black)

        if self.filterset.form.cleaned_data['orientacao'] == 'P':
            if tipo_dado_contato == 'A':
                rowHeights = 80
            else:
                rowHeights = 40
        elif self.filterset.form.cleaned_data['orientacao'] == 'R':
            if tipo_dado_contato == 'A':
                rowHeights = 100
            else:
                rowHeights = 50

        t = LongTable(corpo_relatorio, rowHeights=None, splitByRow=True)
        #t = LongTable(corpo_relatorio, rowHeights=rowHeights, splitByRow=True)
        t.setStyle(style)
       
        if self.filterset.form.cleaned_data['orientacao'] == 'P':
            t._argW[0] = 5 * cm
            t._argW[1] = 2.5 * cm
            t._argW[2] = 5 * cm
            t._argW[3] = 3.5 * cm
            t._argW[4] = 3 * cm
            t._argW[5] = 5 * cm
            t._argW[6] = 3 * cm
        elif self.filterset.form.cleaned_data['orientacao'] == 'R':
            t._argW[0] = 3.3 * cm
            t._argW[1] = 2 * cm
            t._argW[2] = 3.3 * cm
            t._argW[3] = 3 * cm
            t._argW[4] = 2.3 * cm
            t._argW[5] = 3.3 * cm
            t._argW[6] = 2 * cm

        for i, value in enumerate(corpo_relatorio):
            if len(value) == 0:
                t._argH[i] = 7
                continue
            for cell in value:
                if isinstance(cell, list):
                    t._argH[i] = (height) * (
                        len(cell) - (0 if len(cell) > 1 else 0))
                    break

        elements = [t]

        if self.filterset.form.cleaned_data['orientacao'] == 'P':
            orientacao = landscape(A4)
        elif self.filterset.form.cleaned_data['orientacao'] == 'R':
            orientacao = A4

        doc = SimpleDocTemplate(
            response,
            title=self.relat_title,
            pagesize=orientacao,
            rightMargin=1.25 * cm,
            leftMargin=1.25 * cm,
            topMargin=1.1 * cm,
            bottomMargin=0.8 * cm)
        
        doc.build(elements, canvasmaker=NumberedCanvas)

    def get_data(self):
        contatos = []
        consulta_agregada = self.object_list.order_by('nome',)
        consulta_agregada = consulta_agregada.values_list(
            'id',
            'nome',
            'data_nascimento',
        )

        for contato in consulta_agregada.all():
            query = (Q(principal=True))
            query.add(Q(permite_contato=True), Q.OR)
            query.add(Q(contato__id=contato[0]), Q.AND)

            endereco = Endereco.objects.filter(query)
            telefone = Telefone.objects.filter(query)
            email = Email.objects.filter(query)
            grupos = GrupoDeContatos.objects.filter(contatos__id=contato[0])[:2]

            contatos.append((contato, endereco, telefone, email, grupos))

        return contatos

    def validate_data(self):
        contatos = []
        consulta_agregada = self.object_list.order_by('nome',)
        consulta_agregada = consulta_agregada.values_list(
            'id',
        )

        total_erros = 0

        for contato in consulta_agregada.all():
            query = (Q(permite_contato=True))
            query.add(Q(contato__id=contato[0]), Q.AND)

            email = Email.objects.filter(query).count()

            if(email == 0):
                total_erros = total_erros + 1

        return total_erros

    def set_cabec(self, h5):
        cabec = [Paragraph(_('Nome'), h5)]
        cabec.append(Paragraph(_('Nascimento'), h5))
        cabec.append(Paragraph(_('Endereço / Bairro'), h5))
        cabec.append(Paragraph(_('Cidade / CEP'), h5))
        cabec.append(Paragraph(_('Telefone'), h5))
        cabec.append(Paragraph(_('E-mail'), h5))
        cabec.append(Paragraph(_('Grupos'), h5))
        self.cabec = cabec

    def add_relat_title(self, corpo_relatorio):
        tit_relatorio = _(self.relat_title)
        tit_relatorio = force_text(tit_relatorio) + ' '

        corpo_relatorio.append([Paragraph(tit_relatorio, self.h3)])

        corpo_relatorio.append(self.cabec)

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        """add page info to each page (page x of y)"""
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.setFont("Helvetica", 7)
        self.drawRightString(25*mm, 10*mm,
            "Página %d de %d" % (self._pageNumber, page_count))
