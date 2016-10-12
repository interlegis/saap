from django.test import TestCase
from django.utils.datetime_safe import date

from saap.cerimonial.models import Processo, StatusProcesso, Contato, SEXO_CHOICE
from django.shortcuts import resolve_url as r

from saap.core.models import AreaTrabalho, User, Bairro


class ProcessoModelTest(TestCase):
    def setUp(self):
        status_processo = StatusProcesso.objects.create(
            descricao='Status do processo'
        )

        user = User.objects.create(
            email='test@test.org',
            first_name='',
            last_name='',
        )

        workspace = AreaTrabalho.objects.create(
            nome='Área de trabalho',
            owner=user,
            modifier=user,
        )

        contato = Contato.objects.create(
            nome='Contato 1',
            sexo='M',
            naturalidade='Brasileiro',
            nome_pai='',
            nome_mae='',
            # numero_sus='',
            # cpf='',
            # titulo_eleitor="",
            # rg='',
            # rg_orgao_expedidor=''
            workspace=workspace,
            modifier=user,
            owner=user,
            # profissao='',
        )

        bairro = Bairro.objects.create(nome='Bairro')

        self.processo = Processo.objects.create(
            titulo='Título do processo',
            data=date(2016, 10, 10),
            protocolo='10004D',
            proto_cam='99.999999.9999',
            proto_pref='XX999FQG9',
            instituicao='Instituição',
            rua='Rua',
            orgao='Órgão',
            bairro=bairro,
            status=status_processo,
            urgente=True,
            data_solucao=date(2016, 10, 12),
            importancia='M',
            workspace=workspace,
            owner=user,
            modifier=user,
        )
        self.processo.contatos.add(contato)

    def test_create(self):
        self.assertTrue(Processo.objects.exists())

    def test_descricao_blank(self):
        field = Processo._meta.get_field('descricao')
        self.assertTrue(field.blank)

    def test_descricao_default_to_empty_string(self):
        self.assertEqual('', self.processo.descricao)

    def test_observacoes_blank(self):
        field = Processo._meta.get_field('observacoes')
        self.assertTrue(field.blank)

    def test_observacoes_default_to_empty_string(self):
        self.assertEqual('', self.processo.observacoes)

    def test_solucao_blank(self):
        field = Processo._meta.get_field('solucao')
        self.assertTrue(field.blank)

    def test_solucao_default_to_empty_string(self):
        self.assertEqual('', self.processo.solucao)

    def test_contatos_blank(self):
        field = Processo._meta.get_field('contatos')
        self.assertTrue(field.blank)

    def test_status_blank_and_null(self):
        field = Processo._meta.get_field('status')
        self.assertTrue(field.blank)
        self.assertTrue(field.null)

    def test_protocolo_null(self):
        field = Processo._meta.get_field('protocolo')
        self.assertTrue(field.blank)
        self.assertTrue(field.null)

    def test_date_value(self):
        self.assertEqual(date(2016, 10, 10), self.processo.data)

    def test_protocolo_value(self):
        self.assertEqual('10004D', self.processo.protocolo)

    def test_proto_cam_value(self):
        self.assertEqual('99.999999.9999', self.processo.proto_cam)

    def test_proto_pref_value(self):
        self.assertEqual('XX999FQG9', self.processo.proto_pref)

    def test_insticuicao_value(self):
        self.assertEqual('Instituição', self.processo.instituicao)

    def test_rua_value(self):
        self.assertEqual('Rua', self.processo.rua)

    def test_orgao_value(self):
        self.assertEqual('Órgão', self.processo.orgao)

    def test_bairro_value(self):
        self.assertEqual('Bairro', self.processo.bairro.nome)

    def test_status_value(self):
        self.assertEqual('Status do processo', self.processo.status.descricao)

    def test_urgente_value(self):
        self.assertTrue(self.processo.urgente)

    def test_data_solucao_value(self):
        self.assertEqual(date(2016, 10, 12), self.processo.data_solucao)

    def test_importancia_blank(self):
        field = Processo._meta.get_field('importancia')
        self.assertTrue(field.blank)

    def test_topicos_blank(self):
        field = Processo._meta.get_field('topicos')
        self.assertTrue(field.blank)

    def test_classificacoes_blank(self):
        field = Processo._meta.get_field('classificacoes')
        self.assertTrue(field.blank)

    def test_assuntos_blank(self):
        field = Processo._meta.get_field('assuntos')
        self.assertTrue(field.blank)