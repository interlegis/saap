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
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle,\
    StyleSheet1, _baseFontNameB
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.platypus import PageBreak
from reportlab.platypus.doctemplate import SimpleDocTemplate
from reportlab.platypus.frames import Frame
from reportlab.platypus.para import Paragraph
from reportlab.platypus.tables import TableStyle, LongTable
from reportlab.lib.units import mm

from saap.cerimonial.forms import ImpressoEnderecamentoFilterSet,\
    ProcessosFilterSet, ContatosFilterSet, ProcessoIndividualFilterSet, ContatoIndividualFilterSet
from saap.cerimonial.models import Contato, Processo, Telefone, Email, GrupoDeContatos, Endereco, AssuntoProcesso, TopicoProcesso, LocalTrabalho, Dependente, FiliacaoPartidaria, IMPORTANCIA_CHOICE
from saap.core.models import AreaTrabalho
from saap.crud.base import make_pagination
from saap.utils import strip_tags

import time, datetime

#
#
#
#
#
#
#
#
#
#

class RelatorioProcessosView(PermissionRequiredMixin, FilterView):
    #permission_required = 'deve_ser_definida_na_heranca'
    #filterset_class = None
    #model = None
    #template_name = 'deve_ser_definido_na_heranca'
    #container_field = 'workspace_definido_na_heranca'

    #def __init__(self):
    #        self.ctx_title = 'Título do relatório'
    #    self.relat_title = 'Título do relatório'
    #    self.nome_objeto = 'Nome do Objeto'
    #    self.filename = 'Relatorio'

    permission_required = 'cerimonial.print_rel_processo'
    filterset_class = ProcessosFilterSet
    model = Processo
    template_name = "cerimonial/filter_processos.html"
    container_field = 'workspace__operadores'

    paginate_by = 30

    def __init__(self):
        super().__init__()
        self.MAX_TITULO = 80
        self.ctx_title = 'Relatório de Processos'
        self.relat_title = 'Relatório de Processos'
        self.nome_objeto = 'Processo'
        self.filename = 'Relatorio_Processos'

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
            #content = 'attachment; filename="%s.pdf"' % filename
            content = 'inline; filename="%s.pdf"' % filename
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
        context = super(RelatorioProcessosView, self).get_context_data(**kwargs)
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
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ])
        style.add('VALIGN', (0, 0), (-1, -1), 'TOP')

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

#        rowHeights = 100

        t = LongTable(data, rowHeights=None, splitByRow=True)
#        t = LongTable(data, rowHeights=rowHeights, splitByRow=True)

        t.setStyle(style)

        #if len(t._argW) == 5:
        #    t._argW[0] = 1.8 * cm
        #    t._argW[1] = 6 * cm
        #    t._argW[2] = 6.5 * cm
        #    t._argW[3] = 9.5 * cm
        #    t._argW[4] = 2.4 * cm
        #elif len(t._argW) == 6:
        t._argW[0] = 5 * cm
        t._argW[1] = 2 * cm
        t._argW[2] = 4 * cm
        t._argW[3] = 4 * cm
        t._argW[4] = 6 * cm
        t._argW[5] = 7 * cm

        #for i, value in enumerate(data):
        #    if len(value) == 0:
        #        t._argH[i] = 7
        #        continue
        #    for cell in value:
        #        if isinstance(cell, list):
        #            t._argH[i] = (rowHeights) * (
        #                len(cell) - (0 if len(cell) > 1 else 0))
        #            break

        elements.append(t)

        doc = SimpleDocTemplate(
            response,
            title=self.relat_title,
            pagesize=landscape(A4),
            rightMargin=1.25 * cm,
            leftMargin=1.25 * cm,
            topMargin=1.1 * cm,
            bottomMargin=0.8 * cm)
        
        doc.build(elements, canvasmaker=NumberedCanvas)

    def get_data(self):
        self.set_headings()
        self.set_styles()

        cleaned_data = self.filterset.form.cleaned_data

        agrupamento = cleaned_data['agrupamento']
        agrupamento = '' if agrupamento == 'sem_agrupamento' else agrupamento
        self.agrupamento = agrupamento

        self.set_cabec(self.h5)

        self.set_object_list()
        where = self.object_list.query.where
 
        return self.set_body_data(where)
#       self.set_body_data(where, contatos_query, data, item)

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
                'data_abertura', 'titulo')
        else:
            self.object_list = self.object_list.order_by(
                self.agrupamento).distinct(self.agrupamento).values_list(
                self.agrupamento, flat=True)

    def set_cabec(self, h5):
        cabec = [Paragraph(_('Título'), h5)]
        cabec.append(Paragraph(_('Datas'), h5))
        cabec.append(Paragraph(_('Classificação'), h5))
        cabec.append(Paragraph(_('Status'), h5))
        cabec.append(Paragraph(_('Tópicos e assuntos'), h5))
        cabec.append(Paragraph(_('Contatos interessados'), h5))
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
             tit_relatorio += force_text(_('com agrupamento'))
             tit_relatorio +=  ' - ' + self.label_agrupamento
        else:
             tit_relatorio += force_text(_('sem agrupamento'))

        data.append([Paragraph(tit_relatorio, self.h3)])

        if not self.label_agrupamento:
            data.append(self.cabec)

    def add_group_title(self, corpo_relatorio, registro_principal):
        #import pdb; pdb.set_trace()
        corpo_relatorio.append([])
        #lbl_group = self.label_agrupamento

        if registro_principal:
            if(self.agrupamento == 'importancia'):
                if(registro_principal == 'B'):
                    opcao = 0
                elif(registro_principal == 'M'):
                    opcao = 1
                elif(registro_principal == 'A'):
                    opcao = 2
                elif(registro_principal == 'C'):
                    opcao = 3             
                paragrafo=IMPORTANCIA_CHOICE[opcao][1]
            else:
                paragrafo = str(registro_principal)
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

    def set_body_data(self, where):

        data = []

        for p in self.object_list:
            self.set_label_agrupamento(p)

            if not data:
                self.add_relat_title(data)

            if not p or isinstance(p, str):
                self.add_group_title(data, p)

            if self.agrupamento != '':
                params = {self.container_field: self.request.user.pk, self.agrupamento: p}
                processos = Processo.objects.all()
                processos.query.where = where.clone()
                processos = processos.filter(**params)

                for ps in processos:
                    item = []
                    titulo = ''

                    #estilo = self.s_center
                    if len(ps.titulo) < self.MAX_TITULO:
                        titulo = "<b>%s</b>" % str(ps.titulo)
                    else:
                        titulo = "<b>%s</b>" % (
                            ps.titulo[:self.MAX_TITULO] +
                            force_text(_(' (Continua...)'))
                        )
                        #estilo = self.s_min
                        
                    estilo = self.h_style

                    titulo += "<br/>"

                    if(ps.importancia):
                        if(ps.importancia == 'B'):
                            opcao = 0
                        elif(ps.importancia == 'M'):
                            opcao = 1
                        elif(ps.importancia == 'A'):
                            opcao = 2
                        elif(ps.importancia == 'C'):
                            opcao = 3             

                        titulo += "<br/>Importância: <b>%s</b>" % IMPORTANCIA_CHOICE[opcao][1]

                    if(ps.urgente == True):
                         titulo += "<br/>Urgente? <b>Sim</b>"
                    elif(ps.urgente == False):
                         titulo += "<br/>Urgente? <b>Não</b>"

                    item.append(Paragraph(titulo, estilo))

                    datas = "<b>Abertura:</b><br/>%s" % ps.data_abertura.strftime('%d/%m/%Y')
                    datas += "<br/><b>Envio:</b><br/>%s" % ps.data_envio.strftime('%d/%m/%Y') if ps.data_envio else ''
                    datas += "<br/><b>Protocolo:</b><br/>%s" % ps.data_protocolo.strftime('%d/%m/%Y') if ps.data_protocolo else ''
                    datas += "<br/><b>Retorno:</b><br/>%s" % ps.data_retorno.strftime('%d/%m/%Y') if ps.data_retorno else ''
                    datas += "<br/><b>Solução:</b><br/>%s" % ps.data_solucao.strftime('%d/%m/%Y') if ps.data_solucao else ''

                    item.append(Paragraph(datas, estilo))

                    item.append(Paragraph(str(ps.classificacao), estilo))
                    item.append(Paragraph(str(ps.status), estilo))

                    assuntos_set = AssuntoProcesso.objects.filter(processo_set__id=ps.id)
                    topicos_set = TopicoProcesso.objects.filter(processo_set__id=ps.id)

                    topicos = ''
                    if(topicos_set):
                        topicos += "<b>Tópicos:</b>"
                        for topico in topicos_set:
                            topicos += "<br/> %s" % str(topico.descricao)

                    assuntos = ''
                    if(assuntos_set):
                        assuntos += "<b>Assuntos:</b>"
                        for assunto in assuntos_set:
                            assuntos += "<br/> %s" % str(assunto.descricao)

                    topicos_assuntos = "%s <br/>-----<br/> %s" % (topicos,assuntos)

                    item.append(Paragraph(topicos_assuntos, estilo))

                    contatos = ''
                    for contato in ps.contatos.all():
                        endpref = contato.endereco_set.filter(permite_contato=True).first()
                        endereco = ''
                        municipio = ''
                        if endpref:
                            endereco = "<br/>-> %s" % endpref.endereco
                            if(endpref.numero == None):
                                endereco += ", S/N"
                            else: 
                                if(endpref.numero > 0):
                                    endereco += ", " + str(endpref.numero)
                                else:
                                    endereco += ", S/N"
            
                            if(endpref.complemento != '' and endpref.complemento != None):
                                endereco += " - " + endpref.complemento
  
                            endereco += ' - %s' % endpref.bairro.nome if endpref.bairro else ''
            
                            municipio = '<br/>-> %s/%s' % (endpref.municipio.nome, endpref.estado.sigla)
                            municipio += ' - CEP %s' % endpref.cep

                        telpref = contato.telefone_set.filter(permite_contato=True).first()
                        telefone = ''
                        if telpref:
                            telefone += "<br/>-> %s" % telpref.telefone

                        if(contatos != ''):
                            contatos += "-----<br/>"

                        contatos += "<b> %s </b>" % contato.nome
                        contatos += " %s %s %s <br/>" % (endereco, municipio, telefone)

                    item.append(Paragraph(contatos, estilo))
                
                    data.append(item)
            else:
                item = []
                titulo = ''
                #estilo = self.s_center

                if len(p.titulo) < self.MAX_TITULO:
                    titulo = str(p.titulo)
                else:
                    titulo = (
                        p.titulo[:self.MAX_TITULO] +
                        force_text(_(' (Continua...)'))
                    )
                   # estilo = self.s_min
                
                estilo = self.h_style

                item.append(Paragraph(titulo, estilo))

                datas = "<b>Abertura:</b><br/>%s" % p.data_abertura.strftime('%d/%m/%Y')
                datas += "<br/><b>Envio:</b><br/>%s" % p.data_envio.strftime('%d/%m/%Y') if p.data_envio else ''
                datas += "<br/><b>Protocolo:</b><br/>%s" % p.data_protocolo.strftime('%d/%m/%Y') if p.data_protocolo else ''
                datas += "<br/><b>Retorno:</b><br/>%s" % p.data_retorno.strftime('%d/%m/%Y') if p.data_retorno else ''
                datas += "<br/><b>Solução:</b><br/>%s" % p.data_solucao.strftime('%d/%m/%Y') if p.data_solucao else ''

                item.append(Paragraph(datas, estilo))

                classificacao = str(p.classificacao) if p.classificacao else ''
                item.append(Paragraph(classificacao, estilo))

                status = str(p.status) if p.status else ''
                item.append(Paragraph(status, estilo))

                assuntos_set = AssuntoProcesso.objects.filter(processo_set__id=p.id)
                topicos_set = TopicoProcesso.objects.filter(processo_set__id=p.id)

                topicos = ''
                if(topicos_set):
                    topicos += "<b>Tópicos:</b>"
                    for topico in topicos_set:
                        topicos += "<br/> %s" % str(topico.descricao)

                assuntos = ''
                if(assuntos_set):
                    assuntos += "<b>Assuntos:</b>"
                    for assunto in assuntos_set:
                        assuntos += "<br/> %s" % str(assunto.descricao)

                topicos_assuntos = "%s <br/>-----<br/> %s" % (topicos,assuntos)

                item.append(Paragraph(topicos_assuntos, estilo))

                contatos = ''
                for contato in p.contatos.all():
                    endpref = contato.endereco_set.filter(permite_contato=True).first()
                    endereco = ''
                    municipio = ''
                    if endpref:
                        endereco = "<br/>-> %s" % endpref.endereco
                        if(endpref.numero == None):
                            endereco += ", S/N"
                        else: 
                            if(endpref.numero > 0):
                                endereco += ", " + str(endpref.numero)
                            else:
                                endereco += ", S/N"
            
                        if(endpref.complemento != '' and endpref.complemento != None):
                            endereco += " - " + endpref.complemento
  
                        endereco += ' - %s' % endpref.bairro.nome if endpref.bairro else ''
            
                        municipio = '<br/>-> %s/%s' % (endpref.municipio.nome, endpref.estado.sigla)
                        municipio += ' - CEP %s' % endpref.cep

                    telpref = contato.telefone_set.filter(permite_contato=True).first()
                    telefone = ''
                    if telpref:
                        telefone += "<br/>-> %s" % telpref.telefone

                    if(contatos != ''):
                        contatos += "-----<br/>"

                    contatos += "<b> %s </b>" % contato.nome
                    contatos += " %s %s %s <br/>" % (endereco, municipio, telefone)

                item.append(Paragraph(contatos, estilo))
    
                data.append(item)

        return data

#
#
#
#
#
#
#
#
#
#

class RelatorioProcessoIndividualView(PermissionRequiredMixin, FilterView):

    permission_required = 'cerimonial.print_processo'
    filterset_class = ProcessoIndividualFilterSet
    model = Processo
    template_name = "cerimonial/filter_processo.html"
    container_field = 'workspace__operadores'

    paginate_by = 30

    def __init__(self):
        super().__init__()
        self.ctx_title = 'Detalhamento de Processo'
        self.relat_title = 'Detalhamento de Processo'
        self.nome_objeto = 'Processo'
        self.filename = 'Detalhamento_Processo'

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
            messages.error(request, _(
                'Não existe {} com as '
                'condições definidas na busca!'.format(self.nome_objeto)
            ))

        if 'print' in request.GET and self.object_list.exists():
            if self.filterset.form.cleaned_data['pk_selecionados']:
                filename = str(self.filename) + "_" + str(datetime.datetime.fromtimestamp(time.time()).strftime('%Y_%m_%d_%H_%M_%S'))
                response = HttpResponse(content_type='application/pdf')
                content = 'inline; filename="%s.pdf"' % filename
                response['Content-Disposition'] = content
                self.build_pdf(response)
                return response
            else:
                messages.error(request, _('Não há Processo selecionado. Marque ao menos um processo para gerar o relatório'))
                
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
        context = super(RelatorioProcessoIndividualView, self).get_context_data(**kwargs)
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
            #('GRID', (0, 0), (-1, -1), 0.1, colors.black),
            #('INNERGRID', (0, 0), (-1, -1), 0.1, colors.black),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ])
        style.add('VALIGN', (0, 0), (-1, -1), 'TOP')

        processos = Processo.objects.filter(pk__in=self.filterset.form.cleaned_data['pk_selecionados'].split(','))

        for p in processos:
            data = self.get_data(p)

            for i, value in enumerate(data):
                if len(value) <= 1:
                    style.add('SPAN', (0, i), (-1, i))

            t = LongTable(data, rowHeights=None, splitByRow=True)
            #t = LongTable(data, rowHeights=rowHeights, splitByRow=True)

            t.setStyle(style)

            t._argW[0] = 3 * cm
            t._argW[1] = 15 * cm

            elements.append(t)

            elements.append(PageBreak())

        doc = SimpleDocTemplate(
            response,
            pagesize=A4,
            title=self.relat_title,
            rightMargin=1.25 * cm,
            leftMargin=1.25 * cm,
            topMargin=1.1 * cm,
            bottomMargin=0.8 * cm)
 
        doc.build(elements)

    def get_data(self, processo):
        self.set_headings()
        self.set_styles()

        cleaned_data = self.filterset.form.cleaned_data

        #where = self.object_list.query.where
 
        return self.set_body_data(processo)

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
        self.h_style.fontName = _baseFontNameB

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

        self.s_left = getSampleStyleSheet()
        self.s_left = self.s_left["BodyText"]
        self.s_left.wordWrap = None  # 'LTR'
        self.s_left.spaceBefore = 0
        self.s_left.alignment = TA_LEFT
        self.s_left.fontSize = 8
        self.s_left.leading = 8

        self.s_right = getSampleStyleSheet()
        self.s_right = self.s_right["BodyText"]
        self.s_right.wordWrap = None  # 'LTR'
        self.s_right.spaceBefore = 0
        self.s_right.alignment = TA_RIGHT
        self.s_right.fontSize = 8
        self.s_right.leading = 8

    def add_relat_title(self, data):
        tit_relatorio = _(self.relat_title)
        tit_relatorio = force_text(tit_relatorio) + ' '

        data.append([Paragraph(tit_relatorio, self.h3)])

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

    def set_body_data(self, p):

        legenda = self.h_style
        conteudo = self.s_left

        data = []

        self.add_relat_title(data)
        
        line = []
        line.append(Paragraph("<br/>", conteudo))
        line.append(Paragraph("<br/>", conteudo))
        data.append(line)
        
        line = []
        line.append(Paragraph("Código:", legenda))
        line.append(Paragraph(str(p.id), conteudo))
        data.append(line)

        line = []
        line.append(Paragraph("Título:", legenda))
        line.append(Paragraph(p.titulo, conteudo))
        data.append(line)
        
        if(p.importancia):
            if(p.importancia == 'B'):
                opcao = 0
            elif(p.importancia == 'M'):
                opcao = 1
            elif(p.importancia == 'A'):
                opcao = 2
            elif(p.importancia == 'C'):
                opcao = 3             

        line = []
        line.append(Paragraph("Importância:", legenda))
        line.append(Paragraph(IMPORTANCIA_CHOICE[opcao][1], conteudo))
        data.append(line)

        line = []
        line.append(Paragraph("Urgente?", legenda))
        if(p.urgente == True):
            line.append(Paragraph("Sim", conteudo))
        elif(p.urgente == False):
            line.append(Paragraph("Não", conteudo))
        data.append(line)
        
        line = []
        line.append(Paragraph("Data de abertura:", legenda))
        line.append(Paragraph(p.data_abertura.strftime('%d/%m/%Y'), conteudo))
        data.append(line)

        topicos_set = TopicoProcesso.objects.filter(processo_set__id=p.id)
        if(topicos_set):
            line = []
            line.append(Paragraph("Tópicos:", legenda))
            topicos = ""
            for topico in topicos_set:
                topicos += topico.descricao + "<br/>"

            line.append(Paragraph(topicos, conteudo))
            data.append(line)

        assuntos_set = AssuntoProcesso.objects.filter(processo_set__id=p.id)
        if(assuntos_set):
            line = []
            line.append(Paragraph("Assuntos:", legenda))
            assuntos = ""
            for assunto in assuntos_set:
                assuntos += assunto.descricao + "<br/>"
            
            line.append(Paragraph(assuntos, conteudo))
            data.append(line)

        if(p.num_controle):
            line = []
            line.append(Paragraph("Número de controle do gabinete:", legenda))
            line.append(Paragraph(p.num_controle, conteudo))
            data.append(line)

        if(p.classificacao):
            line = []
            line.append(Paragraph("Classificação:", legenda))
            line.append(Paragraph(p.classificacao.descricao, conteudo))
            data.append(line)

        if(p.status):
            line = []
            line.append(Paragraph("Status:", legenda))
            line.append(Paragraph(p.status.descricao, conteudo))
            data.append(line)

        if(p.historico):
            line = []
            line.append(Paragraph("Histórico:", legenda))
            line.append(Paragraph(strip_tags(p.historico), conteudo))
            data.append(line)

        if(p.observacoes):
            line = []
            line.append(Paragraph("Observações:", legenda))
            line.append(Paragraph(strip_tags(p.observacoes), conteudo))
            data.append(line)

        if(p.rua):
            line = []
            line.append(Paragraph("Rua da solicitação:", legenda))
            line.append(Paragraph(p.rua, conteudo))
            data.append(line)

        if(p.bairro):
            line = []
            line.append(Paragraph("Bairro:", legenda))
            line.append(Paragraph(p.bairro.nome, conteudo))
            data.append(line)

        if(p.instituicao):
            line = []
            line.append(Paragraph("Instituição envolvida:", legenda))
            line.append(Paragraph(p.instituicao, conteudo))
            data.append(line)

        if(p.orgao):
            line = []
            line.append(Paragraph("Órgão demandado:", legenda))
            line.append(Paragraph(p.orgao, conteudo))
            data.append(line)

        if(p.materia_cam):
            line = []
            line.append(Paragraph("Matéria na Câmara:", legenda))
            line.append(Paragraph(p.materia_cam, conteudo))
            data.append(line)

        if(p.oficio_cam):
            line = []
            line.append(Paragraph("Ofício enviado pela Câmara:", legenda))
            line.append(Paragraph(p.oficio_cam, conteudo))
            data.append(line)

        if(p.data_envio):
            line = []
            line.append(Paragraph("Data de envio:", legenda))
            line.append(Paragraph(p.data_envio.strftime('%d/%m/%Y'), conteudo))
            data.append(line)

        if(p.proto_pref):
            line = []
            line.append(Paragraph("Protocolo da Prefeitura:", legenda))
            line.append(Paragraph(p.proto_pref, conteudo))
            data.append(line)

        if(p.proto_orgao):
            line = []
            line.append(Paragraph("Protocolo do Órgão:", legenda))
            line.append(Paragraph(p.proto_orgao, conteudo))
            data.append(line)

        if(p.data_protocolo):
            line = []
            line.append(Paragraph("Data de protocolo:", legenda))
            line.append(Paragraph(p.data_protocolo.strftime('%d/%m/%Y'), conteudo))
            data.append(line)

        if(p.oficio_pref):
            line = []
            line.append(Paragraph("Ofício da Prefeitura:", legenda))
            line.append(Paragraph(p.oficio_pref, conteudo))
            data.append(line)

        if(p.oficio_orgao):
            line = []
            line.append(Paragraph("Ofício do Órgão:", legenda))
            line.append(Paragraph(p.oficio_orgao, conteudo))
            data.append(line)

        if(p.link_cam):
            line = []
            line.append(Paragraph("Link na Câmara:", legenda))
            line.append(Paragraph(p.link_cam, conteudo))
            data.append(line)

        if(p.link_pref_orgao):
            line = []
            line.append(Paragraph("Link na Prefeitura/Órgão:", legenda))
            line.append(Paragraph(p.link_pref_orgao, conteudo))
            data.append(line)

        if(p.data_retorno):
            line = []
            line.append(Paragraph("Data de retorno:", legenda))
            line.append(Paragraph(p.data_retorno.strftime('%d/%m/%Y'), conteudo))
            data.append(line)

        if(p.solucao):
            line = []
            line.append(Paragraph("Solução:", legenda))
            line.append(Paragraph(strip_tags(p.solucao), conteudo))
            data.append(line)

        if(p.data_solucao):
            line = []
            line.append(Paragraph("Data da solução:", legenda))
            line.append(Paragraph(p.data_solucao.strftime('%d/%m/%Y'), conteudo))
            data.append(line)

        if(p.contatos):
            line = []
            line.append(Paragraph("Contatos:", legenda))
            contatos = ""
            for contato in p.contatos.all():
                endpref = contato.endereco_set.filter(permite_contato=True).first()
                endereco = ''
                municipio = ''
                if endpref:
                    endereco = "<br/>-> %s" % endpref.endereco
                    if(endpref.numero == None):
                        endereco += ", S/N"
                    else: 
                        if(endpref.numero > 0):
                            endereco += ", " + str(endpref.numero)
                        else:
                            endereco += ", S/N"
            
                    if(endpref.complemento != '' and endpref.complemento != None):
                        endereco += " - " + endpref.complemento
  
                    endereco += ' - %s' % endpref.bairro.nome if endpref.bairro else ''
            
                    municipio = '<br/>-> %s/%s' % (endpref.municipio.nome, endpref.estado.sigla)
                    municipio += ' - CEP %s' % endpref.cep

                telpref = contato.telefone_set.filter(permite_contato=True).first()
                telefone = ''
                if telpref:
                    telefone += "<br/>-> %s" % telpref.telefone

                if(contatos != ''):
                    contatos += "<br/>-----<br/>"

                #print(contato.nome)
                contatos += strip_tags(contato.nome)
                contatos += "%s %s %s" % (endereco, municipio, telefone)
                #contatos += "%s" % "Teste"

            line.append(Paragraph(contatos, conteudo))
            data.append(line)

        return data

#
#
#
#
#
#
#
#
#
#

class RelatorioContatoIndividualView(PermissionRequiredMixin, FilterView):

    permission_required = 'cerimonial.print_contato'
    filterset_class = ContatoIndividualFilterSet
    model = Contato
    template_name = "cerimonial/filter_contato.html"
    container_field = 'workspace__operadores'

    paginate_by = 30

    def __init__(self):
        super().__init__()
        self.ctx_title = 'Detalhamento de Contato'
        self.relat_title = 'Detalhamento de Contato'
        self.nome_objeto = 'Contato'
        self.filename = 'Detalhamento_Contato'

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
            messages.error(request, _(
                'Não existe {} com as '
                'condições definidas na busca!'.format(self.nome_objeto)
            ))

        if 'print' in request.GET and self.object_list.exists():
            if self.filterset.form.cleaned_data['pk_selecionados']:
                filename = str(self.filename) + "_" + str(datetime.datetime.fromtimestamp(time.time()).strftime('%Y_%m_%d_%H_%M_%S'))
                response = HttpResponse(content_type='application/pdf')
                content = 'inline; filename="%s.pdf"' % filename
                response['Content-Disposition'] = content
                self.build_pdf(response)
                return response
            else:
                messages.error(request, _('Não há Contato selecionado. Marque ao menos um contato para gerar o relatório'))
                
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
        context = super(RelatorioContatoIndividualView,
                        self).get_context_data(**kwargs)
        context['count'] = count

        context['title'] = _('Detalhamento de Contato')
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

    def build_pdf(self, response):

        elements = []

        style = TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('LEADING', (0, 0), (-1, -1), 7),
            #('GRID', (0, 0), (-1, -1), 0.1, colors.black),
            #('INNERGRID', (0, 0), (-1, -1), 0.1, colors.black),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ])
        style.add('VALIGN', (0, 0), (-1, -1), 'TOP')

        contatos = Contato.objects.filter(pk__in=self.filterset.form.cleaned_data['pk_selecionados'].split(','))

        for c in contatos:
            data = self.get_data(c)

            for i, value in enumerate(data):
                if len(value) <= 1:
                    style.add('SPAN', (0, i), (-1, i))

            t = LongTable(data, rowHeights=None, splitByRow=True)
            #t = LongTable(data, rowHeights=rowHeights, splitByRow=True)

            t.setStyle(style)

            t._argW[0] = 3 * cm
            t._argW[1] = 15 * cm

            elements.append(t)

            elements.append(PageBreak())

        doc = SimpleDocTemplate(
            response,
            pagesize=A4,
            title=self.relat_title,
            rightMargin=1.25 * cm,
            leftMargin=1.25 * cm,
            topMargin=1.1 * cm,
            bottomMargin=0.8 * cm)
 
        doc.build(elements)

    def get_data(self, processo):
        self.set_headings()
        self.set_styles()

        cleaned_data = self.filterset.form.cleaned_data

        #where = self.object_list.query.where
 
        return self.set_body_data(processo)

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
        self.h_style.fontName = _baseFontNameB

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

        self.s_left = getSampleStyleSheet()
        self.s_left = self.s_left["BodyText"]
        self.s_left.wordWrap = None  # 'LTR'
        self.s_left.spaceBefore = 0
        self.s_left.alignment = TA_LEFT
        self.s_left.fontSize = 8
        self.s_left.leading = 8

        self.s_right = getSampleStyleSheet()
        self.s_right = self.s_right["BodyText"]
        self.s_right.wordWrap = None  # 'LTR'
        self.s_right.spaceBefore = 0
        self.s_right.alignment = TA_RIGHT
        self.s_right.fontSize = 8
        self.s_right.leading = 8

    def add_relat_title(self, data):
        tit_relatorio = _(self.relat_title)
        tit_relatorio = force_text(tit_relatorio) + ' '

        data.append([Paragraph(tit_relatorio, self.h3)])

    def build_query(self, contato, where):
        p_filter = (('contato_set__' + self.agrupamento, contato),)
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
#            'processo_set__' + self.agrupamento,
#            'processo_set__data_abertura',
#            'nome',
#            'endereco_set__bairro__nome',
#            'endereco_set__endereco').distinct(
#            'processo_set__' + self.agrupamento,
#            'processo_set__data_abertura',
           'nome')
        return contatos_query

    def set_body_data(self, p):

        legenda = self.h_style
        conteudo = self.s_left

        data = []

        self.add_relat_title(data)
        
        line = []
        line.append(Paragraph("<br/>", conteudo))
        line.append(Paragraph("<br/>", conteudo))
        data.append(line)
 
        line = []
        line.append(Paragraph("Código:", legenda))
        line.append(Paragraph(str(p.id), conteudo))
        data.append(line)
       
        line = []
        line.append(Paragraph("Nome:", legenda))
        line.append(Paragraph(p.nome, conteudo))
        data.append(line)
 
        line = []
        line.append(Paragraph("Ativo?", legenda))
        if(p.ativo == True):
            line.append(Paragraph("Sim", conteudo))
        elif(p.ativo == False):
            line.append(Paragraph("Não", conteudo))
        data.append(line)
       
        if(p.data_nascimento):
            line = []
            line.append(Paragraph("Nascimento:", legenda))
            line.append(Paragraph(p.data_nascimento.strftime('%d/%m/%Y'), conteudo))
            data.append(line)

        if(p.naturalidade):
            line = []
            line.append(Paragraph("Naturalidade:", legenda))
            line.append(Paragraph('%s/%s' % (p.naturalidade.nome, p.estado.sigla), conteudo))
            data.append(line)
        elif(p.estado):
            line = []
            line.append(Paragraph("Estado de nascimento:", legenda))
            line.append(Paragraph(p.estado.nome, conteudo))
            data.append(line)

        if(p.sexo):
            line = []
            line.append(Paragraph("Sexo:", legenda))

            if(p.sexo == 'M'):
                sexo = 'Masculino'
            elif(p.sexo == 'F'):
                sexo = 'Feminino'

            line.append(Paragraph(sexo, conteudo))
            data.append(line)

        if(p.identidade_genero):
            line = []
            line.append(Paragraph("Gênero:", legenda))
            line.append(Paragraph(p.identidade_genero, conteudo))
            data.append(line)

        if(p.nome_social):
            line = []
            line.append(Paragraph("Nome social:", legenda))
            line.append(Paragraph(p.nome_social, conteudo))
            data.append(line)

        if(p.apelido):
            line = []
            line.append(Paragraph("Apelido:", legenda))
            line.append(Paragraph(p.apelido, conteudo))
            data.append(line)

        if(p.estado_civil):
            line = []
            line.append(Paragraph("Estado civil:", legenda))
            line.append(Paragraph(p.estado_civil.descricao, conteudo))
            data.append(line)

        if(p.tem_filhos):
            line = []
            line.append(Paragraph("Tem filhos?", legenda))
            if(p.tem_filhos == True):
                line.append(Paragraph("Sim", conteudo))
            elif(p.tem_filhos == False):
                line.append(Paragraph("Não", conteudo))
            data.append(line)

            if(p.quantos_filhos > 0):
                line = []
                line.append(Paragraph("Quantos filhos?", legenda))
                line.append(Paragraph(p.quantos_filhos, conteudo))
                data.append(line)

        if(p.nome_pai):
            line = []
            line.append(Paragraph("Nome do pai:", legenda))
            line.append(Paragraph(p.nome_pai, conteudo))
            data.append(line)

        if(p.nome_mae):
            line = []
            line.append(Paragraph("Nome da mãe:", legenda))
            line.append(Paragraph(p.nome_mae, conteudo))
            data.append(line)

        if(p.nivel_instrucao):
            line = []
            line.append(Paragraph("Nível de instrução:", legenda))
            line.append(Paragraph(p.nivel_instrucao.descricao, conteudo))
            data.append(line)

        if(p.profissao):
            line = []
            line.append(Paragraph("Profissão:", legenda))
            line.append(Paragraph(p.profissao, conteudo))
            data.append(line)

        if(p.cargo):
            line = []
            line.append(Paragraph("Cargo ou função:", legenda))
            line.append(Paragraph(p.cargo, conteudo))
            data.append(line)

        if(p.tipo_autoridade):
            line = []
            line.append(Paragraph("Autoridade:", legenda))
            line.append(Paragraph(p.tipo_autoridade.descricao, conteudo))
            data.append(line)

        grupos_set = GrupoDeContatos.objects.filter(contatos__id=p.id)
        if(grupos_set):
            line = []
            line.append(Paragraph("Grupos:", legenda))
            grupos = ""
            for grupo in grupos_set:
                if(grupos != ""):
                    grupos += "<br/>"
                grupos += grupo.nome

            line.append(Paragraph(grupos, conteudo))
            data.append(line)

        if(p.observacoes):
            line = []
            line.append(Paragraph("Observações:", legenda))
            line.append(Paragraph(strip_tags(p.observacoes), conteudo))
            data.append(line)

        enderecos_set = Endereco.objects.filter(contato__id=p.id).order_by('principal', 'permite_contato')
        if(enderecos_set):
            line = []
            line.append(Paragraph("<br/>", conteudo))
            line.append(Paragraph("<br/>", conteudo))
            data.append(line)

            for endereco in enderecos_set:
                enderecos = ""
                legenda_endereco = "Endereço"
                if(endereco.principal == True and endereco.permite_contato == False):
                    legenda_endereco += " <br/>principal:"
                elif(endereco.principal == False and endereco.permite_contato == True):
                    legenda_endereco += " <br/>para contato:"
                elif(endereco.principal == True and endereco.permite_contato == True):
                    legenda_endereco += " <br/>principal<br/> e de contato:"
                else:
                    legenda_endereco += ":"

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

                if(endereco.ponto_referencia != '' and endereco.ponto_referencia != None):
                    enderecos += "<br/>Ponto de referência: " + endereco.ponto_referencia

                if(endereco.bairro != '' and endereco.bairro != None):
                    enderecos += "<br/>Bairro: " + endereco.bairro.nome
 
                if(endereco.distrito != '' and endereco.distrito != None):
                    enderecos += "<br/>Distrito: " + endereco.distrito.nome
 
                if(endereco.cep != '' and endereco.cep != None):
                    enderecos += "<br/>CEP " + endereco.cep

                if(endereco.municipio != '' and endereco.municipio != None):
                    enderecos += '<br/>%s/%s' % (endereco.municipio.nome, endereco.estado.sigla)

                line = []
                line.append(Paragraph(legenda_endereco, legenda))
                line.append(Paragraph(enderecos, conteudo))
                data.append(line)

        telefones_set = Telefone.objects.filter(contato__id=p.id).order_by('principal', 'permite_contato')
        if(telefones_set):
            line = []
            line.append(Paragraph("<br/>", conteudo))
            line.append(Paragraph("<br/>", conteudo))
            data.append(line)

            for telefone in telefones_set:
                telefones = ""
                legenda_telefone = "Telefone"
                if(telefone.principal == True and telefone.permite_contato == False):
                    legenda_telefone += " <br/>principal:"
                elif(telefone.principal == False and telefone.permite_contato == True):
                    legenda_telefone += " <br/>para contato:"
                elif(telefone.principal == True and telefone.permite_contato == True):
                    legenda_telefone += " <br/>principal<br/> e de contato:"
                else:
                    legenda_telefone += ":"

                telefones += telefone.telefone

                if(telefone.operadora):
                    telefones += ("<br/>Operadora: %s" % telefone.operadora)
 
                if(telefone.tipo):
                    telefones += ("<br/>Tipo: %s" % telefone.tipo)

                if(telefone.whatsapp):
                    telefones += ("<br/>WhatsApp? %s" % telefone.whatsapp)

                if(telefone.proprio):
                    if(telefone.proprio == True):
                        telefones += "<br/>Pertence ao contato"
                    elif(telefone.proprio == False):
                        de_quem_e = ""
                        if(telefone.de_quem_e):
                            de_quem_e += telefone.de_quem_e

                        telefones += "<br/>Não pertence ao contato (Pertence a %s)" % de_quem_e

                line = []
                line.append(Paragraph(legenda_telefone, legenda))
                line.append(Paragraph(telefones, conteudo))
                data.append(line)

        emails_set = Email.objects.filter(contato__id=p.id).order_by('principal', 'permite_contato')
        if(emails_set):
            line = []
            line.append(Paragraph("<br/>", conteudo))
            line.append(Paragraph("<br/>", conteudo))
            data.append(line)

            for email in emails_set:
                emails = ""
                legenda_email = "E-mail"
                if(email.principal == True and email.permite_contato == False):
                    legenda_email += " <br/>principal:"
                elif(email.principal == False and email.permite_contato == True):
                    legenda_email += " <br/>para contato:"
                elif(email.principal == True and email.permite_contato == True):
                    legenda_email += " <br/>principal<br/> e de contato:"
                else:
                    legenda_email += ":"

                emails += email.email

                if(email.tipo):
                    emails += ("<br/>Tipo: %s" % email.tipo)

                line = []
                line.append(Paragraph(legenda_email, legenda))
                line.append(Paragraph(emails, conteudo))
                data.append(line)
            
        locais_trabalho_set = LocalTrabalho.objects.filter(contato__id=p.id).order_by('principal')
        if(locais_trabalho_set):
            line = []
            line.append(Paragraph("<br/>", conteudo))
            line.append(Paragraph("<br/>", conteudo))
            data.append(line)

            for trabalho in locais_trabalho_set:
                locais_trabalho = ""
                legenda_trabalho = "Local de trabalho"
                if(trabalho.principal == True):
                    legenda_trabalho += " <br/>principal:"
                else:
                    legenda_trabalho += ":"

                locais_trabalho += ("Razão social: %s" % trabalho.nome)

                if(trabalho.nome_fantasia):
                    locais_trabalho += ("<br/>Nome fantasia: %s" % trabalho.nome_fantasia)
 
                if(trabalho.data_inicio):
                    locais_trabalho += ("<br/>Início: %s" % trabalho.data_inicio.strftime('%d/%m/%Y'))

                if(trabalho.data_fim):
                    locais_trabalho += ("<br/>Fim: %s" % trabalho.data_fim.strftime('%d/%m/%Y'))

                if(trabalho.cargo):
                    locais_trabalho += ("<br/>Cargo/função: %s" % trabalho.cargo)

                locais_trabalho += ("<br/>->Endereço: %s" % trabalho.endereco)
                if(trabalho.numero == None):
                    locais_trabalho += ", S/N"
                else: 
                    if(trabalho.numero > 0):
                        locais_trabalho += ", " + str(trabalho.numero)
                    else:
                        locais_trabalho += ", S/N"
            
                if(trabalho.complemento != '' and trabalho.complemento != None):
                    locais_trabalho += " - " + trabalho.complemento
 
                if(trabalho.bairro): 
                    locais_trabalho += ' - Bairro %s' % trabalho.bairro.nome
            
                locais_trabalho += '<br/>->CEP %s' % trabalho.cep

                locais_trabalho += '<br/>->Município: %s/%s' % (trabalho.municipio.nome, trabalho.estado.sigla)

                line = []
                line.append(Paragraph(legenda_trabalho, legenda))
                line.append(Paragraph(locais_trabalho, conteudo))
                data.append(line)

        dependentes_set = Dependente.objects.filter(contato__id=p.id)
        if(dependentes_set):
            line = []
            line.append(Paragraph("<br/>", conteudo))
            line.append(Paragraph("<br/>", conteudo))
            data.append(line)

            for dependente in dependentes_set:
                dependentes = ""

                dependentes += ("Nome: %s" % dependente.nome)
                dependentes += ("Parentesco: %s" % dependente.parentesco)

                if(dependente.data_nascimento):
                    dependentes += ("<br/>Data de nascimento: %s" % dependente.data_nascimento.strftime('%d/%m/%Y'))

                if(dependente.sexo):
                    if(p.sexo == 'M'):
                        dependentes += ("<br/>Sexo: Masculino")
                    elif(p.sexo == 'F'):
                        dependentes += ("<br/>Sexo: Feminino")

                if(dependente.identidade_genero):
                    dependentes += ("<br/>Gênero: %s" % dependente.identidade_genero)

                if(dependente.nome_social):
                    dependentes += ("<br/>Nome social: %s" % dependente.nome_social)

                if(dependente.apelido):
                    dependentes += ("<br/>Apelido: %s" % dependente.apelido)

                if(dependente.nivel_instrucao):
                    dependentes += ("<br/>Nível de instrução: %s" % dependente.nivel_instrucao.descricao)

                line = []
                line.append(Paragraph("Dependente:", legenda))
                line.append(Paragraph(dependentes, conteudo))
                data.append(line)

        partidos_set = FiliacaoPartidaria.objects.filter(contato__id=p.id).order_by('partido')
        if(partidos_set):
            line = []
            line.append(Paragraph("<br/>", conteudo))
            line.append(Paragraph("<br/>", conteudo))
            data.append(line)

            partidos = ""
            for partido in partidos_set:
                partidos += "%s (%s)" % (partido.partido.nome, partido.partido.sigla)

                if(partido.data_desfiliacao):
                    partidos += (" (Filiado de %s a %s)" % ( partido.data_filiacao.strftime('%d/%m/%Y'), partido.data_desfiliacao.strftime('%d/%m/%Y') ) )
                else:
                    partidos += (" (Filiado em %s)" % partido.data_filiacao.strftime('%d/%m/%Y') )

            line = []
            line.append(Paragraph("Filiação partidária:", legenda))
            line.append(Paragraph(partidos, conteudo))
            data.append(line)

        processos_set = Processo.objects.filter(contatos__id=p.id)
        if(processos_set):
            line = []
            line.append(Paragraph("<br/>", conteudo))
            line.append(Paragraph("<br/>", conteudo))
            data.append(line)

            processos = ""
            for processo in processos_set:
                if(processos != ""):
                    processos += "<br/>"
                processos += "#%s %s" % (processo.id, processo.titulo)

            line = []
            line.append(Paragraph("Processos vinculados:", legenda))
            line.append(Paragraph(processos, conteudo))
            data.append(line)

        return data

#
#
#
#
#
#
#
#
#
#


class RelatorioContatosView(RelatorioProcessosView):
    permission_required = 'cerimonial.print_rel_contatos'
    filterset_class = ContatosFilterSet
    model = Contato
    template_name = 'cerimonial/filter_contatos.html'
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
                    self.filterset.form._errors['ocultar_sem_email'] = ErrorList([_(
                        'ATENÇÃO! Marcando Sim, você vai remover do relatório %s contatos que não tem e-mail' % (total_erros))])

                    messages.error(request, _('Existem %s contatos na busca que não tem e-mail marcado para Contato.\
                             <br>Revise-os antes de gerar a mala direta, ou se preferir, escolha Sim no campo "Ocultar sem e-mail"' % (total_erros)))
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
        context = super(RelatorioContatosView,
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
                            elif(endereco.principal == True and endereco.permite_contato == True):
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
        style.add('VALIGN', (0, 0), (-1, -1), 'TOP')

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

        #for i, value in enumerate(corpo_relatorio):
        #    if len(value) == 0:
        #        t._argH[i] = 7
        #        continue
        #    for cell in value:
        #        if isinstance(cell, list):
        #            t._argH[i] = (height) * (
        #                len(cell) - (0 if len(cell) > 1 else 0))
        #            break

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

#
#
#
#
#
#
#
#

#class ImpressoEnderecamentoView(PermissionRequiredMixin, FilterView):
class ImpressoEnderecamentoView(RelatorioProcessosView):
    permission_required = 'cerimonial.print_impressoenderecamento'
    filterset_class = ImpressoEnderecamentoFilterSet
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
                    self.filterset.form._errors['ocultar_sem_endereco'] = ErrorList([_(
                        'ATENÇÃO! Marcando Sim, você vai remover do relatório %s contatos que não tem endereço' % (total_erros))])

                    messages.error(request, _('Existem %s contatos na busca que não tem endereço marcado para Contato.\
                             <br>Revise-os antes de gerar o impresso, ou se preferir, escolha Sim no campo "Ocultar sem endereço"' % (total_erros)))
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
        context = super(ImpressoEnderecamentoView,
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

        if local_cargo == ImpressoEnderecamentoFilterSet.DEPOIS_PRONOME\
                and imprimir_cargo and (linha_pronome or contato.cargo):
            linha_pronome = '%s - %s' % (linha_pronome, contato.cargo)

        if linha_pronome:
            story.append(Paragraph(
                linha_pronome, stylesheet['pronome_style']))

        linha_nome = '%s %s' % (prefixo_nome, contato.nome)\
            if prefixo_nome else contato.nome

        if local_cargo == ImpressoEnderecamentoFilterSet.LINHA_NOME\
                and imprimir_cargo:

            linha_nome = '%s %s' % (contato.cargo, linha_nome)
            linha_nome = linha_nome.strip()

        linha_nome = linha_nome.upper()\
            if 'nome_maiusculo' in cleaned_data and\
            cleaned_data['nome_maiusculo'] == 'True' else linha_nome

        story.append(Paragraph(linha_nome, stylesheet['nome_style']))

        if local_cargo == ImpressoEnderecamentoFilterSet.DEPOIS_NOME\
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

