from math import floor

from braces.views import PermissionRequiredMixin
from compressor.utils.decorators import cached_property
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.forms.utils import ErrorList
from django.http.response import HttpResponse
from django.template.defaultfilters import lower
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

from saap.cerimonial.forms import ImpressoEnderecamentoContatoFilterSet,\
    ContatoAgrupadoPorProcessoFilterSet, ContatoAgrupadoPorGrupoFilterSet
from saap.cerimonial.models import Contato, Processo, GrupoDeContatos, Telefone
from saap.core.models import AreaTrabalho, Municipio
from saap.crud.base import make_pagination


class ImpressoEnderecamentoContatoView(PermissionRequiredMixin, FilterView):
    permission_required = 'cerimonial.print_impressoenderecamento'
    filterset_class = ImpressoEnderecamentoContatoFilterSet
    model = Contato
    template_name = "cerimonial/filter_impressoenderecamento_contato.html"
    container_field = 'workspace__operadores'
    """list_field_names = ['nome', 'data_nascimento']
    """

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

        if 'print' in request.GET and self.object_list.exists():
            if self.filterset.form.cleaned_data['impresso']:
                response = HttpResponse(content_type='application/pdf')
                response['Content-Disposition'] = \
                    'inline; filename="impresso_enderecamento.pdf"'
                self.build_pdf(response)
                return response
            else:
                self.filterset.form._errors['impresso'] = ErrorList([_(
                    'Selecione o tipo de impresso a ser usado!')])

        context = self.get_context_data(filter=self.filterset,
                                        object_list=self.object_list)

        if len(request.GET) and not len(self.filterset.form.errors)\
                and not self.object_list.exists():
            messages.error(request, _('Não existe Contatos com as '
                                      'condições definidas na busca!'))

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

        return context

    def build_pdf(self, response):

        cleaned_data = self.filterset.form.cleaned_data

        impresso = cleaned_data['impresso']

        fs = int(impresso.fontsize)
        if cleaned_data['fontsize']:
            fs = int(cleaned_data['fontsize'])

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

        endpref = contato.endereco_set.filter(
            preferencial=True).first()
        if endpref:
            endereco = endpref.endereco +\
                (' - ' + endpref.numero if endpref.numero else '') +\
                (' - ' + endpref.complemento if endpref.complemento else '')

            story.append(Paragraph(endereco, stylesheet['endereco_style']))

            b_m_uf = '%s - %s - %s' % (
                endpref.bairro,
                endpref.municipio.nome if endpref.municipio else '',
                endpref.uf)

            story.append(Paragraph(b_m_uf, stylesheet['endereco_style']))
            story.append(Paragraph(endpref.cep, stylesheet['endereco_style']))

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
        self.ctx_title = 'Título do contexto do Relatório'
        self.relat_title = 'Título do Relatório'
        self.nome_objeto = 'Nome do Objeto'

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
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = \
                'inline; filename="relatorio.pdf"'
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
                    Paragraph(p.data.strftime('%d/%m/%Y'), self.s_center),
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
                'data', 'titulo', 'contatos__nome')
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
             tit_relatorio += force_text(_('Agrupados'))
        else:
            tit_relatorio += force_text(_('Sem Agrupamento'))
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
                force_text(_('Sem Agrupamento')) + ' ' + lbl_group
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
            'processo_set__data',
            'nome',
            'endereco_set__bairro__nome',
            'endereco_set__endereco').distinct(
            'processo_set__' + self.agrupamento,
            'processo_set__data',
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

            endpref = contato.endereco_set.filter(
                preferencial=True).first()
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
        self.ctx_title = 'Relatório de Contatos Com Agrupamento Por Processos'
        self.relat_title = 'Relatório de Contatos e Processos'
        self.nome_objeto = 'Processo'


class RelatorioContatoAgrupadoPorGrupoView(RelatorioAgrupado):
    permission_required = 'cerimonial.print_rel_contato_agrupado_por_grupo'
    filterset_class = ContatoAgrupadoPorGrupoFilterSet
    model = Contato
    template_name = 'cerimonial/filter_contato_agrupado_por_grupo.html'
    container_field = 'workspace__operadores'

    def __init__(self):
        super().__init__()
        self.ctx_title = 'Relatório de Contatos Com Agrupamento Por Grupos'
        self.relat_title = 'Relatório de Contatos e Grupos'
        self.nome_objeto = 'Contato'

    def build_pdf(self, response):
        CONTATO = 0
        TELEFONES_PREFERENCIAL = 1

        CIDADE = 0
        ENDERECO = 1
        BAIRRO = 2
        NUMERO = 3
        GRUPO = 4
        ID = 5
        NOME = 6

        self.set_headings()
        self.set_styles()
        self.set_cabec(self.h5)
        estilo = self.h_style

        corpo_relatorio = []
        self.add_relat_title(corpo_relatorio)

        registros = self.get_data()
        for dados in registros:
            endereco = ','.join(dados[CONTATO][ENDERECO:NUMERO])

            item = [
                Paragraph(dados[CONTATO][CIDADE], estilo),
                Paragraph(dados[CONTATO][GRUPO], estilo),
                Paragraph(dados[CONTATO][NOME], estilo),
                Paragraph(endereco, estilo),
                Paragraph(dados[TELEFONES_PREFERENCIAL], estilo),
            ]
            corpo_relatorio.append(item)

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

        for i, value in enumerate(corpo_relatorio):
            if len(value) <= 1:
                style.add('SPAN', (0, i), (-1, i))

            if len(value) == 0:
                style.add('INNERGRID', (0, i), (-1, i), 0, colors.black),
                style.add('GRID', (0, i), (-1, i), -1, colors.white)
                style.add('LINEABOVE', (0, i), (-1, i), 0.1, colors.black)

            if len(value) == 1:
                style.add('LINEABOVE', (0, i), (-1, i), 0.1, colors.black)

        rowHeights = 20
        t = LongTable(corpo_relatorio, rowHeights=rowHeights, splitByRow=True)
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

        for i, value in enumerate(corpo_relatorio):
            if len(value) == 0:
                t._argH[i] = 7
                continue
            for cell in value:
                if isinstance(cell, list):
                    t._argH[i] = (rowHeights) * (
                        len(cell) - (0 if len(cell) > 1 else 0))
                    break

        elements = [t]

        doc = SimpleDocTemplate(
            response,
            pagesize=landscape(A4),
            rightMargin=1.25 * cm,
            leftMargin=1.25 * cm,
            topMargin=1.1 * cm,
            bottomMargin=0.8 * cm)
        doc.build(elements)

    def get_data(self):
        contatos = []
        consulta_agregada = self.object_list.order_by(
            'endereco_set__municipio__nome',
            'grupodecontatos_set__nome',
            'nome'
        )
        consulta_agregada = consulta_agregada.values_list(
            'endereco_set__municipio__nome',
            'endereco_set__endereco',
            'endereco_set__bairro__nome',
            'endereco_set__numero',
            'grupodecontatos_set__nome',
            'id',
            'nome',
        )
        for contato in consulta_agregada.all():
            telefones = self.get_telefone_preferencial(contato[-2])
            numero_fone = telefones[0].telefone if telefones else ''
            contatos.append((contato, numero_fone,))

        return contatos

    def get_telefone_preferencial(self, contato_id):
        return Telefone.objects.filter(
            contato__id=contato_id, preferencial=True)

    def set_cabec(self, h5):
        cabec = [Paragraph(_('Cidade'), h5)]
        cabec.append(Paragraph(_('Grupo'), h5))
        cabec.append(Paragraph(_('Nome'), h5))
        cabec.append(Paragraph(_('Endereço'), h5))
        cabec.append(Paragraph(_('Telefone'), h5))
        self.cabec = cabec

    def add_relat_title(self, corpo_relatorio):
        tit_relatorio = _(self.relat_title)
        tit_relatorio = force_text(tit_relatorio) + ' '
        tit_relatorio += force_text(_('Agrupados'))

        corpo_relatorio.append([Paragraph(tit_relatorio, self.h3)])

        corpo_relatorio.append(self.cabec)