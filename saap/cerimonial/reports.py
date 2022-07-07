from math import floor

from braces.views import PermissionRequiredMixin
from compressor.utils.decorators import cached_property
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Q, Prefetch
from django.forms.utils import ErrorList
from django.http.response import HttpResponse
from django.template.defaultfilters import lower
from django.template import Context, loader
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
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
    ProcessosFilterSet, ContatosFilterSet, ContatosExportaFilterSet, ProcessoIndividualFilterSet, ContatoIndividualFilterSet, \
    MalaDiretaFilterSet, AgendaFilterSet, EventoFilterSet
from saap.cerimonial.models import Contato, Processo, Telefone, Email, GrupoDeContatos, Endereco, \
                                   AssuntoProcesso, TopicoProcesso, LocalTrabalho, Dependente, FiliacaoPartidaria, \
                                   Bairro, Municipio, Estado, IMPORTANCIA_CHOICE, Evento
from saap.core.models import AreaTrabalho, OperadorAreaTrabalho
from saap.crud.base import make_pagination
from saap.utils import strip_tags, calcularIdade

import time, datetime, xlwt
import pdfkit 


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

    #permission_required = 'cerimonial.print_rel_processos'
    permission_required = 'core.menu_processos'
    filterset_class = ProcessosFilterSet
    model = Processo
    template_name = "cerimonial/filter_processos.html"
    container_field = 'workspace__operadores'

    paginate_by = 100

    def __init__(self):
        super().__init__()
        self.MAX_TITULO = 80
        self.ctx_title = 'Listagem de processos em PDF'
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
            kwargs['workspace'] = OperadorAreaTrabalho.objects.filter(user=self.request.user.pk, preferencial=True)[0].areatrabalho
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
        context = super(RelatorioProcessosView,
                        self).get_context_data(**kwargs)

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

        paragrafo = ""

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
        else:
            paragrafo = "Não consta"

        corpo_relatorio.append([Paragraph(paragrafo, self.h4)])

        corpo_relatorio.append(self.cabec)
    """
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
    """
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

                    if(ps.classificacao):
                        item.append(Paragraph(str(ps.classificacao), estilo))
                    else:
                        item.append(Paragraph("Não informada", estilo))

                    if(ps.status):
                        item.append(Paragraph(str(ps.status), estilo))
                    else:
                        item.append(Paragraph("Não informado", estilo))

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

    #permission_required = 'cerimonial.print_rel_processos'
    permission_required = 'core.menu_processos'
    filterset_class = ProcessoIndividualFilterSet
    model = Processo
    template_name = "cerimonial/filter_processo.html"
    container_field = 'workspace__operadores'

    paginate_by = 100

    def __init__(self):
        super().__init__()
        self.ctx_title = 'Relatório detalhado de um processo'
        self.relat_title = 'Detalhamento de Informações do Processo'
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
            kwargs['workspace'] = OperadorAreaTrabalho.objects.filter(user=self.request.user.pk, preferencial=True)[0].areatrabalho
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
        context = super(RelatorioProcessoIndividualView,
                        self).get_context_data(**kwargs)

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

        for processo in context['page_obj']:            
            processo.contatos_count = processo.contatos.count()

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
    """
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
    """
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
            primeiro = True
            for topico in topicos_set:
                if(primeiro):
                    primeiro = False
                else:
                    topicos += "<br/>"

                topicos += topico.descricao

            line.append(Paragraph(topicos, conteudo))
            data.append(line)

        assuntos_set = AssuntoProcesso.objects.filter(processo_set__id=p.id)
        if(assuntos_set):
            line = []
            line.append(Paragraph("Assuntos:", legenda))
            assuntos = ""
            primeiro = True
            for assunto in assuntos_set:
                if(primeiro):
                    primeiro = False
                else:
                    assuntos += "<br/>"

                assuntos += assunto.descricao
            
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

                contatos += strip_tags(contato.nome)
                contatos += "%s %s %s" % (endereco, municipio, telefone)

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

    #permission_required = 'cerimonial.print_rel_contatos'
    permission_required = 'core.menu_contatos'
    filterset_class = ContatoIndividualFilterSet
    model = Contato
    template_name = "cerimonial/filter_contato.html"
    container_field = 'workspace__operadores'

    paginate_by = 100

    def __init__(self):
        super().__init__()
        self.ctx_title = 'Relatório detalhado de um contato'
        self.relat_title = 'Detalhamento de Informações do Contato'
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
            kwargs['workspace'] = OperadorAreaTrabalho.objects.filter(user=self.request.user.pk, preferencial=True)[0].areatrabalho
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
        context['title'] = _(self.ctx_title)

        paginator = context['paginator']
        page_obj = context['page_obj']

        context['page_range'] = make_pagination(
            page_obj.number, paginator.num_pages)

        qr = self.request.GET.copy()
        if 'page' in qr:
            del qr['page']
        context['filter_url'] = ('&' + qr.urlencode()) if len(qr) > 0 else ''

        for contato in context['page_obj']:            

            enderecos = contato.endereco_set.all()
            contato.endereco = ''
            contato.municipio = ''          
            for endpref in enderecos:
                if endpref.permite_contato == True:
                    contato.endereco = endpref.endereco if endpref.endereco else ''
                    contato.municipio = '%s/%s' % (endpref.municipio.nome, endpref.estado.sigla)

            telefones = contato.telefone_set.all()
            contato.telefone = ''
            for telpref in telefones:
                if telpref.principal == True:
                    contato.telefone = telpref.telefone

            emails = contato.email_set.all()
            contato.email = ''
            for mailpref in emails:
                if mailpref.principal == True:
                    contato.email = mailpref.email


            contato.grupo = contato.grupodecontatos_set.all()

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

        contatos = self.object_list.all().filter(pk__in=self.filterset.form.cleaned_data['pk_selecionados'].split(','))

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
    """
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
    """
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
                line.append(Paragraph(str(p.quantos_filhos), conteudo))
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

        grupos_set = p.grupodecontatos_set.all()
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

        enderecos_set = p.endereco_set.all()
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

        telefones_set = p.telefone_set.all()
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

        emails_set = p.email_set.all()
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
            
        locais_trabalho_set = p.localtrabalho_set.all()
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

                if(trabalho.endereco):
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
    
                if(trabalho.cep):
                    locais_trabalho += '<br/>->CEP %s' % trabalho.cep

                if(trabalho.municipio):
                    locais_trabalho += '<br/>->Município: %s/%s' % (trabalho.municipio.nome, trabalho.estado.sigla)

                line = []
                line.append(Paragraph(legenda_trabalho, legenda))
                line.append(Paragraph(locais_trabalho, conteudo))
                data.append(line)

        dependentes_set = p.dependente_set.all()
        if(dependentes_set):
            line = []
            line.append(Paragraph("<br/>", conteudo))
            line.append(Paragraph("<br/>", conteudo))
            data.append(line)

            for dependente in dependentes_set:
                dependentes = ""

                dependentes += ("Nome: %s" % dependente.nome)
                dependentes += ("<br/>Parentesco: %s" % dependente.parentesco)

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

        partidos_set = p.filiacaopartidaria_set.all()
        if(partidos_set):
            line = []
            line.append(Paragraph("<br/>", conteudo))
            line.append(Paragraph("<br/>", conteudo))
            data.append(line)

            primeiro = True;
            partidos = ""
            for partido in partidos_set:

                if(primeiro):
                    primeiro = False
                else:
                    partidos += ("<br/>")

                partidos += "%s (%s)" % (partido.partido.nome, partido.partido.sigla)

                if(partido.data_desfiliacao):
                    partidos += (" (Filiado de %s a %s)" % ( partido.data_filiacao.strftime('%d/%m/%Y'), partido.data_desfiliacao.strftime('%d/%m/%Y') ) )
                else:
                    partidos += (" (Filiado em %s)" % partido.data_filiacao.strftime('%d/%m/%Y') )


            line = []
            line.append(Paragraph("Filiação partidária:", legenda))
            line.append(Paragraph(partidos, conteudo))
            data.append(line)

        processos_set = p.processo_set.all()
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

class ContatosExportaView(RelatorioProcessosView):
    #permission_required = 'cerimonial.print_rel_contatos'
    permission_required = 'core.menu_contatos'
    filterset_class = ContatosExportaFilterSet
    model = Contato
    template_name = 'cerimonial/filter_contatoexporta.html'
    container_field = 'workspace__operadores'

    def __init__(self):
        super().__init__()
        self.ctx_title = 'Exportação de contatos em planilha'
        self.relat_title = 'Exportação de Contatos'
        self.nome_objeto = 'Contato'
        self.filename = 'Exporta_Contatos'

    def get(self, request, *args, **kwargs):
        filterset_class = self.get_filterset_class()
        self.filterset = self.get_filterset(filterset_class)
        self.object_list = self.filterset.qs

        if len(request.GET) and not len(self.filterset.form.errors)\
                and not self.object_list.exists():
            messages.error(request, _('Não existe contato com as '
                                      'condições definidas na busca!'))
        if 'print' in request.GET and self.object_list.exists():

            if self.filterset.form.cleaned_data['opcao_exportacao'] == 'REL':
                filename = "Planilha_Contatos_"\
                     + str(datetime.datetime.fromtimestamp(time.time()).strftime('%Y_%m_%d_%H_%M_%S'))

                response = HttpResponse(content_type='application/ms-excel')
                content = 'attachment; filename="%s.xls"' % filename
                response['Content-Disposition'] = content
                self.build_xls(response)
                return response

            elif self.filterset.form.cleaned_data['opcao_exportacao'] == 'SAP':
                filename = "Exportacao_Contatos_"\
                     + str(datetime.datetime.fromtimestamp(time.time()).strftime('%Y_%m_%d_%H_%M_%S'))

                response = HttpResponse(content_type='application/ms-excel')
                content = 'attachment; filename="%s.xls"' % filename
                response['Content-Disposition'] = content
                self.build_xls_exportacao(response)
                return response


        context = self.get_context_data(filter=self.filterset,
                                        object_list=self.object_list)
        
        return self.render_to_response(context)

    def get_filterset(self, filterset_class):
        kwargs = self.get_filterset_kwargs(filterset_class)
        try:
            kwargs['workspace'] = OperadorAreaTrabalho.objects.filter(user=self.request.user.pk, preferencial=True)[0].areatrabalho
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
        context = super(ContatosExportaView,
                        self).get_context_data(**kwargs)

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

        for contato in context['page_obj']:            
            enderecos = contato.endereco_set.all()

            contato.endereco = ''
            contato.municipio = ''          
            for endpref in enderecos:
                if endpref.permite_contato == True:
                    contato.endereco = endpref.endereco if endpref.endereco else ''
                    contato.municipio = '%s/%s' % (endpref.municipio.nome, endpref.estado.sigla)

            if contato.sexo != '':
                if contato.sexo == 'M':
                    contato.sexo = 'Masculino'
                elif contato.sexo == 'F':
                    contato.sexo = 'Feminino'

            contato.grupo = contato.grupodecontatos_set.all()

        return context


    def build_xls_exportacao(self, response):

        CONTATO = 0
        ENDERECOS = 1
        TELEFONES = 2
        EMAILS = 3

        NOME = 1
        NASCIMENTO = 3
        SEXO = 6

        colunas = [
                    'nome',
                    'nascimento',
                    'sexo',
                    'logradouro1',
                    'numero1', 
                    'complemento1', 
                    'bairro1', 
                    'cep1',
                    'cidade1', 
                    'estado1', 
                    'logradouro2',
                    'numero2', 
                    'complemento2', 
                    'bairro2', 
                    'cep2',
                    'cidade2', 
                    'estado2',
                    'telefone1', 
                    'telefone2', 
                    'email1',
                    'email2', 
                    ]

        registros = self.object_list.order_by('nome',)

        wb = xlwt.Workbook(encoding='utf-8')
        ws = wb.add_sheet('Contatos')

        # Fonte do cabeçalho
        font_style = xlwt.XFStyle()
        font_style.font.bold = True

        lin_num = 0
        col_num = 0

        # Cria as colunas
        for coluna in colunas:
            ws.write(lin_num, col_num, colunas[col_num], font_style)
            col_num += 1

        # Fonte do corpo
        font_style = xlwt.XFStyle()


        # Cria os registros
        for dados in registros:
            col_num = 0
            lin_num += 1
            tam_linha = 1
              
            # Nome
            ws.write(lin_num, col_num, dados.nome, font_style)
            ws.col(col_num).width = 12000
            col_num += 1

            # Nascimento
            if(dados.data_nascimento != '' and dados.data_nascimento != None):
                nascimento = dados.data_nascimento.strftime('%d/%m/%Y')
            else:
                nascimento = ""
                
            ws.write(lin_num, col_num, nascimento, font_style)
            ws.col(col_num).width = 3000
            col_num += 1

            # Sexo
            if(dados.sexo != '' and dados.sexo != None):
                sexo = dados.sexo
            else:
                sexo = ''

            ws.write(lin_num, col_num, sexo, font_style)
            ws.col(col_num).width = 2000
            col_num += 1

            # Endereços
            endereco_logradouro = ['','']
            endereco_numero = ['','']
            endereco_complemento = ['','']
            endereco_bairro = ['','']
            endereco_cep = ['','']
            endereco_municipio = ['','']
            endereco_estado = ['','']

            if(dados.endereco_set.all().count() > 0):
                total_enderecos = 0
                for endereco in dados.endereco_set.all():

                    endereco_logradouro[total_enderecos] = endereco.endereco
                    endereco_numero[total_enderecos] = endereco.numero
                    endereco_complemento[total_enderecos] = endereco.complemento
                    endereco_bairro[total_enderecos] = endereco.bairro.nome
                    endereco_cep[total_enderecos] = endereco.cep
                    endereco_municipio[total_enderecos] = endereco.municipio.nome
                    endereco_estado[total_enderecos] = endereco.estado.sigla

                    total_enderecos += 1

                    if (total_enderecos >= 2):
                        break

            # Telefones 
            telefone_telefone = ['','']

            if(dados.telefone_set.all().count() > 0):
                total_telefones = 0
                for telefone in dados.telefone_set.all():  
                    telefone_telefone[total_telefones] = telefone.telefone

                    total_telefones += 1

                    if (total_telefones >= 2):
                        break

            # Emails 
            email_email = ['','']
            if(dados.email_set.all().count() > 0):
                total_emails = 0
                for email in dados.email_set.all():
                    email_email[total_emails] = email.email

                    total_emails += 1

                    if (total_emails >= 2):
                        break


            i = 0
            while i < 2:
                ws.write(lin_num, col_num, endereco_logradouro[i], font_style)
                ws.col(col_num).width = 11000
                col_num += 1

                ws.write(lin_num, col_num, endereco_numero[i], font_style)
                ws.col(col_num).width = 2500
                col_num += 1

                ws.write(lin_num, col_num, endereco_complemento[i], font_style)
                ws.col(col_num).width = 3500
                col_num += 1

                ws.write(lin_num, col_num, endereco_bairro[i], font_style)
                ws.col(col_num).width = 5000
                col_num += 1

                ws.write(lin_num, col_num, endereco_cep[i], font_style)
                ws.col(col_num).width = 4000
                col_num += 1

                ws.write(lin_num, col_num, endereco_municipio[i], font_style)
                ws.col(col_num).width = 6000
                col_num += 1

                ws.write(lin_num, col_num, endereco_estado[i], font_style)
                ws.col(col_num).width = 2000
                col_num += 1

                i += 1

            i = 0
            while i < 2:

                ws.write(lin_num, col_num, telefone_telefone[i], font_style)
                ws.col(col_num).width = 5000
                col_num += 1

                i += 1

            i = 0
            while i < 2:
 
                ws.write(lin_num, col_num, email_email[i], font_style)
                ws.col(col_num).width = 9000
                col_num += 1

                i += 1


        wb.save(response)

        return response

    def build_xls(self, response):

        col_codigo = -1
        col_status = -1
        col_nascimento = -1
        col_naturalidade = -1
        col_idade = -1
        col_sexo = -1
        col_estadocivil = -1
        col_filhos = -1
        col_enderecos = -1
        col_telefones = -1
        col_emails = -1
        col_grupos = -1
        col_nivelinstrucao = -1
        col_cargo = -1
        col_documentosp = -1
        col_documentose = -1
        
        campos_exportados = self.filterset.form.cleaned_data['campos_exportados']
        tipo_dado_contato = self.filterset.form.cleaned_data['tipo_dado_contato']

        colunas = ['Nome']
        col_nome = 0

        if campos_exportados:
            qtde_campos_adicionais = 0;
            for opcao in campos_exportados:
                if(opcao == 'COD'):
                   colunas = ['Código', 'Nome']
                   qtde_campos_adicionais += 1
                   col_codigo = 0 # Se não houver código, a primeira coluna será a do nome.
                   col_nome = 1   # Do contrário, a primeira será a do código
                elif(opcao == 'STA'):
                   colunas = colunas + ['Ativo?']
                   qtde_campos_adicionais += 1
                   col_status = qtde_campos_adicionais 
                elif(opcao == 'NAS'):
                   colunas = colunas + ['Nascimento']
                   qtde_campos_adicionais += 1
                   col_nascimento = qtde_campos_adicionais 
                elif(opcao == 'NAT'):
                    colunas = colunas + ['Naturalidade']
                    qtde_campos_adicionais += 1
                    col_naturalidade = qtde_campos_adicionais 
                elif(opcao == 'IDA'):
                    colunas = colunas + ['Idade']
                    qtde_campos_adicionais += 1
                    col_idade = qtde_campos_adicionais 
                elif(opcao == 'SEX'):
                    colunas = colunas + ['Sexo']
                    qtde_campos_adicionais += 1
                    col_sexo = qtde_campos_adicionais 
                elif(opcao == 'EST'):
                    colunas = colunas + ['Estado civil']
                    qtde_campos_adicionais += 1
                    col_estadocivil = qtde_campos_adicionais 
                elif(opcao == 'FIL'):
                    colunas = colunas + ['Filhos']
                    qtde_campos_adicionais += 1
                    col_filhos = qtde_campos_adicionais 
                elif(opcao == 'END'):
                    if(tipo_dado_contato == 'P'):
                        colunas = colunas + ['Endereço principal', 'Cidade (Principal)', 'CEP (Principal)']
                        qtde_campos_adicionais += 3
                        col_enderecos = qtde_campos_adicionais 
                    elif(tipo_dado_contato == 'C'):
                        colunas = colunas + ['Endereço para contato', 'Cidade (Contato)', 'CEP (Contato)']
                        qtde_campos_adicionais += 3
                        col_enderecos = qtde_campos_adicionais 
                    elif(tipo_dado_contato == 'T'):
                        colunas = colunas + ['Endereço principal', 'Cidade (Principal)', 'CEP (Principal)', 
                                             'Endereço para contato', 'Cidade (Contato)', 'CEP (Contato)',
                                             'Outros endereços', 'Cidade (Outros)', 'CEP (Outros)']
                        qtde_campos_adicionais += 9
                        col_enderecos = qtde_campos_adicionais 
                elif(opcao == 'TEL'):
                    if(tipo_dado_contato == 'P'):
                        colunas = colunas + ['Telefone principal']
                        qtde_campos_adicionais += 1
                        col_telefones = qtde_campos_adicionais 
                    elif(tipo_dado_contato == 'C'):
                        colunas = colunas + ['Telefone para contato']
                        qtde_campos_adicionais += 1
                        col_telefones = qtde_campos_adicionais 
                    elif(tipo_dado_contato == 'T'):
                        colunas = colunas + ['Telefone principal', 'Telefone para contato', 'Outros telefones']
                        qtde_campos_adicionais += 3
                        col_telefones = qtde_campos_adicionais 
                elif(opcao == 'EMA'):
                    if(tipo_dado_contato == 'P'):
                        colunas = colunas + ['E-mail principal']
                        qtde_campos_adicionais += 1
                        col_emails = qtde_campos_adicionais 
                    elif(tipo_dado_contato == 'C'):
                        colunas = colunas + ['E-mail para contato']
                        qtde_campos_adicionais += 1
                        col_emails = qtde_campos_adicionais 
                    elif(tipo_dado_contato == 'T'):
                        colunas = colunas + ['E-mail principal', 'E-mail para contato', 'Outros e-mails']
                        qtde_campos_adicionais += 3
                        col_emails = qtde_campos_adicionais 
                elif(opcao == 'GRU'):
                    colunas = colunas + ['Grupos']
                    qtde_campos_adicionais += 1
                    col_grupos = qtde_campos_adicionais 
                elif(opcao == 'NIV'):
                    colunas = colunas + ['Nível de instrução']
                    qtde_campos_adicionais += 1
                    col_nivelinstrucao = qtde_campos_adicionais 
                elif(opcao == 'AUT'):
                    colunas = colunas + ['Profissão', 'Cargo/Função', 'Tipo de autoridade']
                    qtde_campos_adicionais += 3
                    col_cargo = qtde_campos_adicionais 
                elif(opcao == 'DOC'):
                    colunas = colunas + ['CPF', 'RG', 'Órgão expedidor', 'Data de expedição', 'Título de eleitor', 'Número do SUS']
                    qtde_campos_adicionais += 6
                    col_documentosp = qtde_campos_adicionais 
                elif(opcao == 'DOE'):
                    colunas = colunas + ['CNPJ', 'IE']
                    qtde_campos_adicionais += 2
                    col_documentose = qtde_campos_adicionais 

        registros = self.object_list.order_by('nome',)

        wb = xlwt.Workbook(encoding='utf-8')
        ws = wb.add_sheet('Contatos')

        # Fonte do cabeçalho
        font_style = xlwt.XFStyle()
        font_style.font.bold = True

        lin_num = 0
        col_num = 0

        # Cria as colunas
        for coluna in colunas:
            ws.write(lin_num, col_num, colunas[col_num], font_style)
            col_num += 1

        # Fonte do corpo
        font_style = xlwt.XFStyle()

        # Cria os registros
        for dados in registros:
            col_num = 0
            lin_num += 1
            tam_linha = 1
              
            # Nome
            ws.write(lin_num, col_nome, dados.nome, font_style)
            ws.col(col_nome).width = 12000

            # Código 
            if(col_codigo != -1):
                ws.write(lin_num, col_codigo, dados.pk, font_style)
                ws.col(col_codigo).width = 2500
      
            # Status
            if(col_status != -1):
                if (dados.ativo == 1):
                    ativo = "Sim"
                else:
                    ativo = "Não"

                ws.write(lin_num, col_status, ativo, font_style)
                ws.col(col_status).width = 1700

            # Nascimento
            if(col_nascimento != -1):
                if(dados.data_nascimento != '' and dados.data_nascimento != None):
                    nascimento = dados.data_nascimento.strftime('%d/%m/%Y')
                else:
                    nascimento = ""
                    
                ws.write(lin_num, col_nascimento, nascimento, font_style)
                ws.col(col_nascimento).width = 2900

            # Naturalidade
            if(col_naturalidade != -1):
                if(dados.naturalidade != '' and dados.naturalidade != None):
                    naturalidade = dados.naturalidade.nome
                else:
                    naturalidade = ""

                ws.write(lin_num, col_naturalidade, naturalidade, font_style)
                ws.col(col_naturalidade).width = 7000

            # Idade
            if(col_idade != -1):
                if(dados.data_nascimento != '' and dados.data_nascimento != None):
                    idade = calcularIdade(dados.data_nascimento)
                else:
                    idade = ""
                    
                ws.write(lin_num, col_idade, idade, font_style)
                ws.col(col_idade).width = 1800

            # Sexo
            if(col_sexo != -1):
                if(dados.sexo != '' and dados.sexo != None):
                    if dados.sexo == 'M':
                        sexo = 'Masculino'
                    elif dados.sexo == 'F':
                        sexo = 'Feminino'
                else:
                    sexo = ''

                ws.write(lin_num, col_sexo, sexo, font_style)
                ws.col(col_sexo).width = 2600

            # Estado civil
            if(col_estadocivil != -1):
                if(dados.estado_civil != '' and dados.estado_civil != None):
                    estado_civil = dados.estado_civil.descricao
                else:
                    estado_civil = ""
                    
                ws.write(lin_num, col_estadocivil, estado_civil, font_style)
                ws.col(col_estadocivil).width = 3000

            # Filhos
            if(col_filhos != -1):
                if(dados.tem_filhos != '' and dados.tem_filhos != None):
                    filhos = "Sim (" + str(dados.quantos_filhos) + ")"
                else:
                    filhos = "Não"

                ws.write(lin_num, col_filhos, filhos, font_style)
                ws.col(col_filhos).width = 2200

            # Endereços
            if(col_enderecos != -1):

                endereco_principal = ''
                endereco_contato = ''
                outros_enderecos = ''
                municipio_principal = ''
                municipio_contato = ''
                municipio_outros = ''
                cep_principal = ''
                cep_contato = ''
                cep_outros = ''
                
                if(dados.endereco_set.all().count() > 0):
                    i = 0
                    primeiro_outros = True
                    for endereco in dados.endereco_set.all():

                        endereco_completo = endereco.endereco
    
                        if(endereco.numero == None):
                            endereco_completo += ", S/N"
                        else: 
                            if(endereco.numero > 0):
                                endereco_completo += ", " + str(endereco.numero)
                            else:
                                endereco_completo += ", S/N"
                
                        if(endereco.complemento != '' and endereco.complemento != None):
                            endereco_completo += " - " + endereco.complemento

                        if(endereco.bairro != '' and endereco.bairro != None):
                            endereco_completo += " - " + endereco.bairro.nome

                        if (endereco.principal == True):
                            endereco_principal = endereco_completo
                            municipio_principal = '%s/%s' % (endereco.municipio.nome, endereco.estado.sigla)
                            cep_principal = endereco.cep
                        elif (endereco.permite_contato == True):
                            endereco_contato = endereco_completo             
                            municipio_contato = '%s/%s' % (endereco.municipio.nome, endereco.estado.sigla)
                            cep_contato = endereco.cep
                        else:
                            i += 1
                            if (primeiro_outros == True):
                                primeiro_outros = False
                            else:
                                outros_enderecos += "\n"
                                municipio_outros += "\n"
                                cep_outros += "\n"

                            outros_enderecos += endereco_completo
                            municipio_outros = '%s/%s' % (endereco.municipio.nome, endereco.estado.sigla)
                            cep_outros = endereco.cep

                    if (tipo_dado_contato == 'P'):
                        ws.write(lin_num, col_enderecos-2, endereco_principal, font_style)
                        ws.write(lin_num, col_enderecos-1, municipio_principal, font_style)
                        ws.write(lin_num, col_enderecos, cep_principal, font_style)
                        ws.col(col_enderecos-2).width = 15000
                        ws.col(col_enderecos-1).width = 6000
                        ws.col(col_enderecos).width = 4000
                    elif (tipo_dado_contato == 'C'):
                        ws.write(lin_num, col_enderecos-2, endereco_contato, font_style)
                        ws.write(lin_num, col_enderecos-1, municipio_contato, font_style)
                        ws.write(lin_num, col_enderecos, cep_contato, font_style)
                        ws.col(col_enderecos-2).width = 15000
                        ws.col(col_enderecos-1).width = 6000
                        ws.col(col_enderecos).width = 4000
                    elif (tipo_dado_contato == 'T'):
                        ws.write(lin_num, col_enderecos-8, endereco_principal, font_style)
                        ws.write(lin_num, col_enderecos-7, municipio_principal, font_style)
                        ws.write(lin_num, col_enderecos-6, cep_principal, font_style)
                        ws.col(col_enderecos-8).width = 15000
                        ws.col(col_enderecos-7).width = 6000
                        ws.col(col_enderecos-6).width = 4000
                        ws.write(lin_num, col_enderecos-5, endereco_contato, font_style)
                        ws.write(lin_num, col_enderecos-4, municipio_contato, font_style)
                        ws.write(lin_num, col_enderecos-3, cep_contato, font_style)
                        ws.col(col_enderecos-5).width = 15000
                        ws.col(col_enderecos-4).width = 6000
                        ws.col(col_enderecos-3).width = 4000
                        ws.write(lin_num, col_enderecos-2, outros_enderecos, font_style)
                        ws.write(lin_num, col_enderecos-1, municipio_outros, font_style)
                        ws.write(lin_num, col_enderecos, cep_outros, font_style)
                        ws.col(col_enderecos-2).width = 15000
                        ws.col(col_enderecos-1).width = 6000
                        ws.col(col_enderecos).width = 4000
                    if(tam_linha < i):
                        tam_linha = i                
           
            # Telefones 
            if(col_telefones != -1):

                telefone_principal = ''
                telefone_contato = ''
                outros_telefones = ''

                if(dados.telefone_set.all().count() > 0):
                    i = 0
                    primeiro_outros = True
                    for telefone in dados.telefone_set.all():
                        if (telefone.principal == True):
                            telefone_principal = telefone.telefone
                        elif (telefone.permite_contato == True):
                            telefone_contato = telefone.telefone              
                        else:
                            i += 1
                            if (primeiro_outros == True):
                                primeiro_outros = False
                            else:
                                outros_telefones += "\n"

                            outros_telefones += telefone.telefone

                    if (tipo_dado_contato == 'P'):
                        ws.write(lin_num, col_telefones, telefone_principal, font_style)
                        ws.col(col_telefones).width = 5000
                    elif (tipo_dado_contato == 'C'):
                        ws.write(lin_num, col_telefones, telefone_contato, font_style)
                        ws.col(col_telefones).width = 5000
                    elif (tipo_dado_contato == 'T'):
                        ws.write(lin_num, (col_telefones-2), telefone_principal, font_style)
                        ws.write(lin_num, (col_telefones-1), telefone_contato, font_style)
                        ws.write(lin_num, col_telefones, outros_telefones, font_style)
                        ws.col(col_telefones-2).width = 5000
                        ws.col(col_telefones-1).width = 5000
                        ws.col(col_telefones).width = 5000
                    if(tam_linha < i):
                        tam_linha = i                

            # E-mails  
            if(col_emails != -1):

                email_principal = ''
                email_contato = ''
                outros_emails = ''

                if(dados.email_set.all().count() > 0):
                    i = 0
                    primeiro_outros = True
                    for email in dados.email_set.all():
                        if (email.principal == True):
                            email_principal = email.email                         
                        elif (email.permite_contato == True):
                            email_contato = email.email                         
                        else:
                            i += 1
                            if (primeiro_outros == True):
                                primeiro_outros = False
                            else:
                                outros_emails += "\n"

                            outros_emails += email.email

                    if (tipo_dado_contato == 'P'):
                        ws.write(lin_num, col_emails, email_principal, font_style)
                        ws.col(col_emails).width = 9000
                    elif (tipo_dado_contato == 'C'):
                        ws.write(lin_num, col_emails, email_contato, font_style)
                        ws.col(col_emails).width = 9000
                    elif (tipo_dado_contato == 'T'):
                        ws.write(lin_num, (col_emails-2), email_principal, font_style)
                        ws.write(lin_num, (col_emails-1), email_contato, font_style)
                        ws.write(lin_num, col_emails, outros_emails, font_style)
                        ws.col(col_emails-2).width = 9000
                        ws.col(col_emails-1).width = 9000
                        ws.col(col_emails).width = 9000
                    if(tam_linha < i):
                        tam_linha = i                

            # Grupos
            if(col_grupos != -1):
                grupos = ''
                if(dados.grupodecontatos_set.all().count() > 0):
                    i = 0
                    for grupo in dados.grupodecontatos_set.all():
                        grupos += grupo.nome
                        i += 1
                        if(i < dados.grupodecontatos_set.all().count()):
                            grupos += "\n"
                    if(tam_linha < i):
                        tam_linha = i                

                ws.write(lin_num, col_grupos, grupos, font_style)
                ws.col(col_grupos).width = 7000

            if(col_nivelinstrucao != -1):
                if(dados.nivel_instrucao != '' and dados.nivel_instrucao != None):
                    nivel_instrucao = dados.nivel_instrucao.descricao
                else:
                    nivel_instrucao = ""
                    
                ws.write(lin_num, col_nivelinstrucao, nivel_instrucao, font_style)
                ws.col(col_nivelinstrucao).width = 8000

            if(col_cargo != -1):
                if(dados.profissao != '' and dados.profissao != None):
                    profissao = dados.profissao
                else:
                    profissao = ""
 
                if(dados.cargo != '' and dados.cargo != None):
                    cargo = dados.cargo
                else:
                    cargo = ""
 
                if(dados.tipo_autoridade != '' and dados.tipo_autoridade != None):
                    tipo_autoridade = dados.tipo_autoridade.descricao
                else:
                    tipo_autoridade = ""
                    
                ws.write(lin_num, col_cargo-2, profissao, font_style)
                ws.write(lin_num, col_cargo-1, cargo, font_style)
                ws.write(lin_num, col_cargo, tipo_autoridade, font_style)
                ws.col(col_cargo-2).width = 8000
                ws.col(col_cargo-1).width = 8000
                ws.col(col_cargo).width = 8000

            if(col_documentosp != -1):
                if(dados.cpf != '' and dados.cpf != None):
                    cpf = dados.cpf
                else:
                    cpf = ""
 
                if(dados.rg != '' and dados.rg != None):
                    rg = dados.rg
                else:
                    rg = ""
 
                if(dados.rg_orgao_expedidor != '' and dados.rg_orgao_expedidor != None):
                    rg_orgao = dados.rg_orgao_expedidor
                else:
                    rg_orgao = ""
  
                if(dados.rg_data_expedicao != '' and dados.rg_data_expedicao != None):
                    rg_data = dados.rg_data_expedicao.strftime('%d/%m/%Y')
                else:
                    rg_data = ""
 
                if(dados.titulo_eleitor != '' and dados.titulo_eleitor != None):
                    titulo_eleitor = dados.titulo_eleitor
                else:
                    titulo_eleitor = ""

                if(dados.numero_sus != '' and dados.numero_sus != None):
                    numero_sus = dados.numero_sus
                else:
                    numero_sus = ""
                    
                ws.write(lin_num, col_documentosp-5, cpf, font_style)
                ws.write(lin_num, col_documentosp-4, rg, font_style)
                ws.write(lin_num, col_documentosp-3, rg_data, font_style)
                ws.write(lin_num, col_documentosp-2, rg_orgao, font_style)
                ws.write(lin_num, col_documentosp-1, titulo_eleitor, font_style)
                ws.write(lin_num, col_documentosp, numero_sus, font_style)
                ws.col(col_documentosp-5).width = 5000
                ws.col(col_documentosp-4).width = 5000
                ws.col(col_documentosp-3).width = 5000
                ws.col(col_documentosp-2).width = 5000
                ws.col(col_documentosp-1).width = 5000
                ws.col(col_documentosp).width = 5000

            if(col_documentose != -1):
                if(dados.cnpj != '' and dados.cnpj != None):
                    cnpj = dados.cnpj
                else:
                    cnpj = ""
 
                if(dados.ie != '' and dados.ie != None):
                    ie = dados.ie
                else:
                    ie = ""
                
                ws.write(lin_num, col_documentose-1, cnpj, font_style)
                ws.write(lin_num, col_documentose, ie, font_style)
                ws.col(col_documentose-1).width = 5000
                ws.col(col_documentose).width = 5000

            if(tam_linha > 1): 
                ws.row(lin_num).height = 250 * tam_linha

        wb.save(response)

        return response

#
#
#
#
#
#
#
#

class RelatorioContatosView(RelatorioProcessosView):
    #permission_required = 'cerimonial.print_rel_contatos'
    permission_required = 'core.menu_contatos'
    filterset_class = ContatosFilterSet
    model = Contato
    template_name = 'cerimonial/filter_contatos.html'
    container_field = 'workspace__operadores'

    def __init__(self):
        super().__init__()
        self.ctx_title = 'Listagem de contatos em PDF'
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
            filename = str("Contatos_") +\
                        str(datetime.datetime.fromtimestamp(time.time()).strftime('%Y_%m_%d_%H_%M_%S'))
            content = 'inline; filename="%s.pdf"' % filename
            content = 'attachment; filename="%s.pdf"' % filename
            response = HttpResponse(self.build_pdf())
            response['Content-Type'] = 'application/pdf'
            response['Content-Disposition'] = content
            return response
        
        context = self.get_context_data(filter=self.filterset,
                                        object_list=self.object_list)

        return self.render_to_response(context)

    def get_filterset(self, filterset_class):
        kwargs = self.get_filterset_kwargs(filterset_class)
        try:
            kwargs['workspace'] = OperadorAreaTrabalho.objects.filter(user=self.request.user.pk, preferencial=True)[0].areatrabalho
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
        context['title'] = _(self.ctx_title)

        paginator = context['paginator']
        page_obj = context['page_obj']

        context['page_range'] = make_pagination(
            page_obj.number, paginator.num_pages)

        qr = self.request.GET.copy()
        if 'page' in qr:
            del qr['page']
        context['filter_url'] = ('&' + qr.urlencode()) if len(qr) > 0 else ''

        for contato in context['page_obj']:            

            enderecos = contato.endereco_set.all()
            contato.endereco = ''
            contato.municipio = ''          
            for endpref in enderecos:
                if endpref.permite_contato == True:
                    contato.endereco = endpref.endereco if endpref.endereco else ''
                    contato.municipio = '%s/%s' % (endpref.municipio.nome, endpref.estado.sigla)

            telefones = contato.telefone_set.all()
            contato.telefone = ''
            for telpref in telefones:
                if telpref.principal == True:
                    contato.telefone = telpref.telefone

            emails = contato.email_set.all()
            contato.email = ''
            for mailpref in emails:
                if mailpref.principal == True:
                    contato.email = mailpref.email


            contato.grupo = contato.grupodecontatos_set.all()

        return context

    def build_pdf(self):


        if self.filterset.form.cleaned_data['orientacao'] == 'P':
            fonte_tamanho = '13px'
        elif self.filterset.form.cleaned_data['orientacao'] == 'R':
            fonte_tamanho = '11px'
 
        tipo_dado_contato = self.filterset.form.cleaned_data['tipo_dado_contato']

        html = "\
                <!DOCTYPE html>\
                <html>\
                <head>\
                    <meta charset='utf-8'>\
                    <style>\
                        body {\
                          font-family: 'Liberation Sans';\
                        }\
                        table, th, td {\
                          border: 1px solid black;\
                          border-collapse: collapse;\
                          vertical-align: top;\
                          padding: 5px;\
                        }\
                        th {\
                          font-size: 16px;}\
                        td {\
                          font-size: " + fonte_tamanho + ";\
                        } \
                    </style>\
                </head>\
                <body>\
                <center><h2>Relatório de Contatos</h2></center>\
              "

        tabela = "<table>\
                    <colgroup>\
                       <col span='1' style='width: 20%;'>\
                       <col span='1' style='width: 10%;'>\
                       <col span='1' style='width: 20%;'>\
                       <col span='1' style='width: 15%;'>\
                       <col span='1' style='width: 10%;'>\
                       <col span='1' style='width: 15%;'>\
                       <col span='1' style='width: 10%;'>\
                    </colgroup>\
                    <thead><tr>\
                        <th>Nome</th>\
                        <th>Nascimento</th>\
                        <th>Endereço / Bairro</th>\
                        <th>Cidade / CEP</th>\
                        <th>Telefone</th>\
                        <th>E-mail</th>\
                        <th>Grupos</th>\
                    </tr></thead>\
                    <tbody>"

        html += tabela 

        registros = self.object_list
        
        for dados in registros:
            enderecos = ''      
            municipios = ''

            if(dados.endereco_set.all().count() > 0):

                for endereco in dados.endereco_set.all():

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

            if(dados.data_nascimento != '' and dados.data_nascimento != None):
                nascimento = dados.data_nascimento.strftime('%d/%m/%Y')

            telefones = ''

            if(dados.telefone_set.all().count() > 0):
                for telefone in dados.telefone_set.all():
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

            if(dados.email_set.all().count() > 0):
                for email in dados.email_set.all():
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

            if(dados.grupodecontatos_set.all().count() > 0):
                for grupo in dados.grupodecontatos_set.all():
                    grupos += grupo.nome + "<br/>"

            html += "\
                    <tr class='page-break'>\
                        <td>" + dados.nome + "</td>\
                        <td>" + nascimento + "</td>\
                        <td>" + enderecos + "</td>\
                        <td>" + municipios + "</td>\
                        <td>" + telefones + "</td>\
                        <td>" + emails + "</td>\
                        <td>" + grupos + "</td>\
                    </tr>"

        html += "   </tbody>\
                    </table>\
                 </html>"

        if self.filterset.form.cleaned_data['orientacao'] == 'P':
            orientacao = 'landscape'
        elif self.filterset.form.cleaned_data['orientacao'] == 'R':
            orientacao = 'portrait'

        options = {
            'page-size': 'A4',
            'orientation': orientacao,
            'margin-top': '0.40in',
            'margin-right': '0.40in',
            'margin-bottom': '0.40in',
            'margin-left': '0.40in',
            'encoding': "UTF-8",
            'no-outline': None
        }

        return pdfkit.from_string(html, options=options) 


#
#
#
#
#
#
#
#

class RelatorioAgendaView(RelatorioProcessosView):
    #permission_required = 'cerimonial.print_rel_agenda'
    #permission_required = 'core.menu_agenda'
    permission_required = 'core.menu_contatos'
    filterset_class = AgendaFilterSet
    model = Evento
    template_name = 'cerimonial/filter_agenda.html'
    container_field = 'workspace__operadores'

    def __init__(self):
        super().__init__()
        self.ctx_title = 'Agenda em PDF'
        self.relat_title = 'Agenda do parlamentar '
        self.nome_objeto = 'Evento'
        self.filename = 'Relatorio_Agenda'

    def get(self, request, *args, **kwargs):
        filterset_class = self.get_filterset_class()
        self.filterset = self.get_filterset(filterset_class)
        self.object_list = self.filterset.qs

        if len(request.GET) and not len(self.filterset.form.errors)\
                and not self.object_list.exists():
            messages.error(request, _('Não existe agenda com as '
                                      'condições definidas na busca!'))
        
        if 'print' in request.GET and self.object_list.exists():
            filename = str("Agenda_") +\
                        str(datetime.datetime.fromtimestamp(time.time()).strftime('%Y_%m_%d_%H_%M_%S'))
            response = HttpResponse(content_type='application/pdf')
            content = 'inline; filename="%s.pdf"' % filename
            #content = 'attachment; filename="%s.pdf"' % filename
            response['Content-Disposition'] = content
            self.build_pdf(response)
            return response
        
        context = self.get_context_data(filter=self.filterset,
                                        object_list=self.object_list)

        return self.render_to_response(context)

    def get_filterset(self, filterset_class):
        kwargs = self.get_filterset_kwargs(filterset_class)
        try:
            kwargs['workspace'] = OperadorAreaTrabalho.objects.filter(user=self.request.user.pk, preferencial=True)[0].areatrabalho
        except:
            raise PermissionDenied(_('Sem permissão de acesso!'))

        self.relat_title += str(kwargs['workspace'])

        return filterset_class(**kwargs)

    def get_queryset(self):
        qs = super().get_queryset()
        kwargs = {}
        if self.container_field:
            kwargs[self.container_field] = self.request.user.pk

        return qs.filter(**kwargs)

    def get_context_data(self, **kwargs):
        count = self.object_list.count()
        context = super(RelatorioAgendaView,
                        self).get_context_data(**kwargs)

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

        for agenda in page_obj:
            fmt = "%d/%m/%Y às %H:%M"
            agenda.inicio = agenda.inicio.strftime(fmt)
            agenda.termino = agenda.termino.strftime(fmt)
            agenda.url = "/eventos/" + str(agenda.id) 

        return context

    def build_pdf(self, response):
        TITULO = 0
        DESCRICAO = 1
        LOCALIZACAO = 2
        BAIRRO = 3
        MUNICIPIO = 4
        INICIO = 5
        TERMINO = 6

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

        registros = self.get_data()
        for dados in registros:

            titulo = dados[TITULO]
            descricao = dados[DESCRICAO]

            if(dados[BAIRRO] != None):
                bairro = str(Bairro.objects.filter(pk=dados[BAIRRO])[0])
            else:
                bairro = ''

            if(dados[MUNICIPIO] != None):
                municipio = str(Municipio.objects.filter(pk=dados[MUNICIPIO])[0])
            else:
                municipio = ''

            localizacao = ''
            localizacao += dados[LOCALIZACAO]
            localizacao += "<br/><b>Bairro:</b> " + str(bairro)
            localizacao += "<br/><b>Município:</b> " + str(municipio)

            data_inicio = dados[INICIO].strftime('%d/%m/%Y')
            hora_inicio = dados[INICIO].strftime('%H:%M')
            data_termino = dados[TERMINO].strftime('%d/%m/%Y')
            hora_termino = dados[TERMINO].strftime('%H:%M')

            item = [
                Paragraph(dados[TITULO], estilo),
                Paragraph(dados[DESCRICAO], estilo),
                Paragraph(localizacao, estilo),
                Paragraph(data_inicio, estilo),
                Paragraph(hora_inicio, estilo),
                Paragraph(data_termino, estilo),
                Paragraph(hora_termino, estilo),
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
            rowHeights = 40
        elif self.filterset.form.cleaned_data['orientacao'] == 'R':
            rowHeights = 50

        t = LongTable(corpo_relatorio, rowHeights=None, splitByRow=True)
        #t = LongTable(corpo_relatorio, rowHeights=rowHeights, splitByRow=True)
        t.setStyle(style)
       
        if self.filterset.form.cleaned_data['orientacao'] == 'P':
            t._argW[0] = 5 * cm
            t._argW[1] = 7 * cm
            t._argW[2] = 5 * cm
            t._argW[3] = 2 * cm
            t._argW[4] = 2 * cm
            t._argW[5] = 2 * cm
            t._argW[6] = 2 * cm
        elif self.filterset.form.cleaned_data['orientacao'] == 'R':
            t._argW[0] = 3.5 * cm
            t._argW[1] = 4.5 * cm
            t._argW[2] = 4 * cm
            t._argW[3] = 2 * cm
            t._argW[4] = 2 * cm
            t._argW[5] = 2 * cm
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

        agrupamento = 'sem_agrupamento'

        agenda = []
        consulta_agregada = self.object_list.order_by('inicio')
        consulta_agregada = consulta_agregada.values_list(
            'titulo',
            'descricao',
            'localizacao',
            'bairro',
            'municipio',
            'inicio',
            'termino',
        )

        for evento in consulta_agregada.all():
            agenda.append(evento)

        return agenda

    def set_cabec(self, h5):
        cabec = [Paragraph(_('Título'), h5)]
        cabec.append(Paragraph(_('Descrição'), h5))
        cabec.append(Paragraph(_('Localização'), h5))
        cabec.append(Paragraph(_('Data de início'), h5))
        cabec.append(Paragraph(_('Hora de início'), h5))
        cabec.append(Paragraph(_('Data de término'), h5))
        cabec.append(Paragraph(_('Hora de término'), h5))
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
#
#

class RelatorioEventoView(PermissionRequiredMixin, FilterView):
    #permission_required = 'cerimonial.print_rel_agenda'
    #permission_required = 'core.menu_agenda'
    permission_required = 'core.menu_contatos'
    filterset_class = EventoFilterSet
    model = Evento
    template_name = "cerimonial/filter_evento.html"
    container_field = 'workspace__operadores'

    paginate_by = 100

    def __init__(self):
        super().__init__()
        self.ctx_title = 'Relatório detalhado de um evento'
        self.relat_title = 'Detalhamento de Informações do Evento'
        self.nome_objeto = 'Evento'
        self.filename = 'Detalhamento_Evento'

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
                messages.error(request, _('Não há Evento selecionado. Marque ao menos um contato para gerar o relatório'))
                
        context = self.get_context_data(filter=self.filterset,
                                        object_list=self.object_list)

        return self.render_to_response(context)

    def get_filterset(self, filterset_class):
        kwargs = self.get_filterset_kwargs(filterset_class)
        try:
            kwargs['workspace'] = OperadorAreaTrabalho.objects.filter(user=self.request.user.pk, preferencial=True)[0].areatrabalho
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
        context = super(RelatorioEventoView,
                        self).get_context_data(**kwargs)

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

        for agenda in page_obj:
            fmt = "%d/%m/%Y às %H:%M"
            agenda.inicio = agenda.inicio.strftime(fmt)
            agenda.termino = agenda.termino.strftime(fmt)
            agenda.url = "/eventos/" + str(agenda.id) 

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

        eventos = Evento.objects.filter(pk__in=self.filterset.form.cleaned_data['pk_selecionados'].split(','))

        for e in eventos:
            data = self.get_data(e)

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
    """
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

        eventos_query = Evento.objects.all()
        eventos_query.query.where = where.clone()
        eventos_query = eventos_query.filter(q)

        params = {self.container_field: self.request.user.pk}
        eventos_query = eventos_query.filter(**params)

        eventos_query = eventos_query.order_by(
           'inicio')
        return contatos_query
    """
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
        line.append(Paragraph("Título:", legenda))
        line.append(Paragraph(p.titulo, conteudo))
        data.append(line)
 
        if(p.descricao):
            line = []
            line.append(Paragraph("Descrição:", legenda))
            line.append(Paragraph(strip_tags(p.descricao), conteudo))
            data.append(line)

        if(p.localizacao):
            line = []
            line.append(Paragraph("Localização:", legenda))
            line.append(Paragraph(strip_tags(p.localizacao), conteudo))
            data.append(line)

        if(p.bairro):
            line = []
            line.append(Paragraph("Bairro:", legenda))
            line.append(Paragraph(p.bairro.nome, conteudo))
            data.append(line)

        if(p.municipio):
            line = []
            line.append(Paragraph("Município:", legenda))
            line.append(Paragraph(('%s/%s' % (p.municipio.nome, p.estado.sigla)), conteudo))
            data.append(line)

        line = []
        line.append(Paragraph("Início:", legenda))
        line.append(Paragraph(p.inicio.strftime('%d/%m/%Y às %H:%M'), conteudo))
        data.append(line)

        line = []
        line.append(Paragraph("Término:", legenda))
        line.append(Paragraph(p.termino.strftime('%d/%m/%Y às %H:%M'), conteudo))
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

class MalaDiretaView(RelatorioProcessosView):
    #permission_required = 'cerimonial.print_rel_contatos'
    permission_required = 'core.menu_contatos'
    filterset_class = MalaDiretaFilterSet
    model = Contato
    template_name = 'cerimonial/filter_contatoemail.html'
    container_field = 'workspace__operadores'

    def __init__(self):
        super().__init__()
        self.ctx_title = 'Exportação de e-mail'
        #self.relat_title = 'Mala Direta'
        self.nome_objeto = 'Contato'
        #self.filename = 'Mala_Direta'

    def get(self, request, *args, **kwargs):
        filterset_class = self.get_filterset_class()
        self.filterset = self.get_filterset(filterset_class)
        self.object_list = self.filterset.qs

        if len(request.GET) and not len(self.filterset.form.errors)\
                and not self.object_list.exists():
            messages.error(request, _('Não existe contato com as '
                                      'condições definidas na busca!'))
        
        if 'print' in request.GET and self.object_list.exists():
            erros_email = self.validate_data()
            if(self.filterset.form.cleaned_data['ocultar_sem_email'] != True and erros_email > 0):
                self.filterset.form._errors['ocultar_sem_email'] = ErrorList([_(
                    'ATENÇÃO! Marcando Sim, você vai remover do relatório %s contatos que não tem e-mail' % (erros_email))])

                messages.error(request, _('Existem %s contatos na busca que não tem e-mail marcado para Contato.\
                         <br>Revise-os antes de gerar a mala direta, ou se preferir, escolha Sim no campo "Ocultar sem e-mail"' % (erros_email)))
            else:
                filename = str("Contatos_")\
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
            kwargs['workspace'] = OperadorAreaTrabalho.objects.filter(user=self.request.user.pk, preferencial=True)[0].areatrabalho
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
        context = super(MalaDiretaView,
                        self).get_context_data(**kwargs)

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


        for contato in context['page_obj']:            
            
            if(contato.endereco_set.all().count() > 0):
                endpref = contato.endereco_set.all()[0]
            else:
                endpref = None

            if endpref:
                contato.bairro = endpref.bairro.nome if endpref.bairro else ''
                contato.municipio = '%s/%s' % (endpref.municipio, endpref.estado.sigla) if endpref.municipio else ''
            else:
                contato.bairro = ''
                contato.municipio = ''

            grupo = contato.grupodecontatos_set.all()
            contato.grupo = grupo
          
            if (contato.telefone_set.all().count() > 0): 
                telefone = contato.telefone_set.all()[0]
            else:
                telefone = None

            contato.telefone = telefone.telefone if telefone else ''

            if (contato.email_set.all().count() > 0): 
                email = contato.email_set.all()[0]
            else:
                email = None

            contato.email = email.email if email else ''

        return context

    def build_txt(self, response):

        registros = self.object_list.order_by('nome')

        csv_data = []

        for contato in registros:
            if contato.email_set.all().count() > 0:
                email = contato.email_set.all()[0]
                csv_data.append([contato.nome, email.email])

        t = loader.get_template('cerimonial/contato_email.txt')
        response.write(t.render({'data': csv_data}).encode("utf-8"))
        return response

    def validate_data(self):
        consulta_agregada = self.object_list.order_by('nome',)

        total_erros = 0

        for contato in consulta_agregada.all():
            if(contato.email_set.all().count() < 1):
                total_erros = total_erros + 1

        return total_erros

#
#
#
#
#
#
#
#

class ImpressoEnderecamentoView(PermissionRequiredMixin, FilterView):
#class ImpressoEnderecamentoView(RelatorioProcessosView):
    #permission_required = 'cerimonial.print_impressoenderecamento'
    permission_required = 'core.menu_contatos'
    filterset_class = ImpressoEnderecamentoFilterSet
    model = Contato
    template_name = "cerimonial/filter_impressoenderecamento_contato.html"
    container_field = 'workspace__operadores'

    paginate_by = 100

    def __init__(self):
        super().__init__()
        self.ctx_title = 'Impressão de Etiquetas e Envelopes'
        self.relat_title = 'Impressão de Etiquetas e Envelopes'
        self.nome_objeto = 'Contato'
        self.filename = 'Impresso_Enderecamento'

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

                erros_endereco = self.validate_endereco()
                erros_sexo = self.validate_sexo()
                contatos_nao_casados = self.validate_estado_civil()

                # Pessoas sem endereço cadastrado
                if(self.filterset.form.cleaned_data['ocultar_sem_endereco'] != True and erros_endereco > 0):
                    self.filterset.form._errors['ocultar_sem_endereco'] = ErrorList([_(
                        'ATENÇÃO! Marcando Sim, você vai remover do relatório %s contatos que não tem endereço' % (erros_endereco))])

                    messages.error(request, _('Existem %s contatos na busca que não tem endereço marcado para Contato.\
                             <br>Revise-os antes de gerar o impresso, ou se preferir, escolha Sim no campo "Ocultar sem endereço"' % (erros_endereco)))
                # Pessoas sem pronome cadastrado, usando a expressão "Para"
                elif(self.filterset.form.cleaned_data['imprimir_pronome'] == 'True' and self.filterset.form.cleaned_data['pronome_padrao'] != 'True' and erros_sexo > 0):
                    self.filterset.form._errors['pronome_padrao'] = ErrorList([_(
                        'ATENÇÃO! Marcando Sim, você vai utilizar a expressão "Para" em %s contatos que não tem pronome cadastrado' % (erros_sexo))])

                    messages.error(request, _('Existem %s contatos na busca que não tem sexo escolhido.\
                             <br>Revise-os para exibir o pronome corretamente, ou se preferir, escolha Sim no campo "Utilizar pronome padrão"' % (erros_sexo)))
                # Pessoas não casadas usando a expressão "e esposo" ou "e esposa"
                elif( (self.filterset.form.cleaned_data['pos_nome'] == 'EPO' and contatos_nao_casados > 0) or
                      (self.filterset.form.cleaned_data['pos_nome'] == 'EPA' and contatos_nao_casados > 0) ):
                    messages.error(request, _('Existem %s contatos na busca que não são casados, e por isso não podem usar a expressão pós-nome escolhida.\
                             <br>Escolha apenas contatos casados ou altere a expressão pós-nome escolhida' % (contatos_nao_casados)))
                # Comentado devido a casamento entre pessoas do mesmo sexo
                # elif( (self.filterset.form.cleaned_data['pos_nome'] == 'EPO' and erros_sexo[1] > 0) or
                #       (self.filterset.form.cleaned_data['pos_nome'] == 'EPA' and erros_sexo[2] > 0) ):
                #     messages.error(request, _('Existem contatos na busca que não podem usar a expressão pós-nome escolhida devido ao sexo.\
                #              <br>Escolha apenas contatos do mesmo sexo ou altere a expressão pós-nome escolhida'))
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
            kwargs['workspace'] = OperadorAreaTrabalho.objects.filter(user=self.request.user.pk, preferencial=True)[0].areatrabalho
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
        context['title'] = _(self.ctx_title)

        paginator = context['paginator']
        page_obj = context['page_obj']

        context['page_range'] = make_pagination(
            page_obj.number, paginator.num_pages)

        qr = self.request.GET.copy()
        if 'page' in qr:
            del qr['page']
        context['filter_url'] = ('&' + qr.urlencode()) if len(qr) > 0 else ''

        for contato in context['page_obj']:            
            if contato.endereco_set.all():
                endereco_atual = contato.endereco_set.all()[0]
                contato.endereco = endereco_atual.endereco if endereco_atual.endereco else ''
                contato.municipio = '%s/%s' % (endereco_atual.municipio.nome, endereco_atual.estado.sigla)
            else:
                contato.endereco = ''
                contato.municipio = ''

            if contato.sexo != '':
                if contato.sexo == 'M':
                    contato.sexo = 'Masculino'
                elif contato.sexo == 'F':
                    contato.sexo = 'Feminino'

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
            if contato.endereco_set.all().count() > 0:
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

        if 'imprimir_pronome' in cleaned_data and cleaned_data['imprimir_pronome'] == 'True':
            if contato.pronome_tratamento:
                if contato.sexo == '':
                    linha_pronome = "Para"
                else:
                    linha_pronome = getattr(
                        contato.pronome_tratamento,
                        'enderecamento_singular_%s' % lower(
                            contato.sexo))
                    prefixo_nome = getattr(
                        contato.pronome_tratamento,
                        'prefixo_nome_singular_%s' % lower(
                            contato.sexo))
            else:
                if contato.sexo == '':
                    linha_pronome = "Para"
                elif contato.sexo == 'M':
                    linha_pronome = "Ao Sr."
                elif contato.sexo == 'F':
                    linha_pronome = "À Sra."

        if local_cargo == ImpressoEnderecamentoFilterSet.DEPOIS_PRONOME\
                and imprimir_cargo and (linha_pronome or contato.cargo):
            linha_pronome = '%s %s' % (linha_pronome, contato.cargo)

        if linha_pronome:
            story.append(Paragraph(
                linha_pronome, stylesheet['pronome_style']))

        linha_nome = '%s %s' % (prefixo_nome, contato.nome)\
            if prefixo_nome else contato.nome

        if local_cargo == ImpressoEnderecamentoFilterSet.LINHA_NOME\
                and imprimir_cargo:

            linha_nome = '%s %s' % (contato.cargo, linha_nome)
            linha_nome = linha_nome.strip()

        pos_nome = ""

        if 'pos_nome' in cleaned_data and cleaned_data['pos_nome'] != 'N':
            if cleaned_data['pos_nome'] == 'FAM':
                pos_nome = " " + "e família"
            elif cleaned_data['pos_nome'] == 'EPO':
                pos_nome = " " + "e esposo"
            elif cleaned_data['pos_nome'] == 'EPA':
                pos_nome = " " + "e esposa"
            elif cleaned_data['pos_nome'] == 'CPO':
                pos_nome = " " + "e companheiro"
            elif cleaned_data['pos_nome'] == 'CPA':
                pos_nome = " " + "e companheira"

        if 'nome_maiusculo' in cleaned_data and cleaned_data['nome_maiusculo'] == 'True':
           linha_nome = linha_nome.upper()
           pos_nome = pos_nome.upper()
        else:
           linha_nome = linha_nome       

        linha_nome = linha_nome + pos_nome 

        story.append(Paragraph(linha_nome, stylesheet['nome_style']))

        if local_cargo == ImpressoEnderecamentoFilterSet.DEPOIS_NOME\
                and imprimir_cargo and contato.cargo:
            story.append(
                Paragraph(contato.cargo, stylesheet['endereco_style']))

        endpref = contato.endereco_set.all()[0]

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

    def validate_endereco(self):
        consulta_agregada = self.object_list.order_by('nome',)
    
        total_erros = 0

        for contato in consulta_agregada.all():
            if(contato.endereco_set.all().count() < 1):
                total_erros = total_erros + 1

        return total_erros

    def validate_sexo(self):
        consulta_agregada = self.object_list.order_by('nome')
        consulta_agregada = consulta_agregada.values_list('sexo',)

        total_erros = 0

        for contato_sexo in consulta_agregada.all():
            if(contato_sexo[0] == ''):
                total_erros = total_erros + 1

        return total_erros

    def validate_estado_civil(self):
        consulta_agregada = self.object_list.order_by('nome')
        consulta_agregada = consulta_agregada.values_list('estado_civil',)

        nao_casados = 0

        for estado_civil in consulta_agregada.all():
            if(estado_civil != '3'):
                nao_casados = nao_casados + 1

        return nao_casados

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

