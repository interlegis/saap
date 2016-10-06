from django.test import TestCase
from saap.cerimonial.reports import RelatorioContatoAgrupadoPorGrupoView


class ReportContatosPorGrupoNavTest(TestCase):
    def setUp(self):
        self.response = self.client.get('/reports/cerimonial/contatos_por_grupo')

    def test_get(self):
        '''GET / must return status code 200.'''
        self.assertEqual(200, self.response.status_code)

    def test_template(self):
        '''Must use index.html.'''
        self.assertTemplateUsed(self.response, 'cerimonial/filter_contato_agrupado_por_grupo.html')