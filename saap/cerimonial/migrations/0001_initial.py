# -*- coding: utf-8 -*-
# Generated by Django 1.9.9 on 2016-09-02 13:22
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AssuntoProcesso',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='modified')),
                ('descricao', models.CharField(default='', max_length=254, verbose_name='Nome / Descrição')),
            ],
            options={
                'ordering': ('descricao',),
                'abstract': False,
                'verbose_name_plural': 'Assuntos de Processos',
                'verbose_name': 'Assunto de Processo',
            },
        ),
        migrations.CreateModel(
            name='ClassificacaoProcesso',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('descricao', models.CharField(default='', max_length=254, verbose_name='Nome / Descrição')),
            ],
            options={
                'ordering': ('descricao',),
                'abstract': False,
                'verbose_name_plural': 'Classificações de Processos',
                'verbose_name': 'Classificacao de Processo',
            },
        ),
        migrations.CreateModel(
            name='Contato',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('search', models.TextField(blank=True, default='')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='modified')),
                ('nome', models.CharField(max_length=100, verbose_name='Nome')),
                ('nome_social', models.CharField(blank=True, default='', max_length=100, verbose_name='Nome Social')),
                ('apelido', models.CharField(blank=True, default='', max_length=100, verbose_name='Apelido')),
                ('data_nascimento', models.DateField(blank=True, null=True, verbose_name='Data de Nascimento')),
                ('sexo', models.CharField(blank=True, choices=[('F', 'Feminino'), ('M', 'Masculino')], max_length=1, verbose_name='Sexo Biológico')),
                ('identidade_genero', models.CharField(blank=True, default='', max_length=100, verbose_name='Como se reconhece?')),
                ('tem_filhos', models.NullBooleanField(choices=[(None, '---------'), (True, 'Sim'), (False, 'Não')], default=None, verbose_name='Tem Filhos?')),
                ('quantos_filhos', models.PositiveSmallIntegerField(blank=True, default=0, verbose_name='Quantos Filhos?')),
                ('naturalidade', models.CharField(blank=True, max_length=50, verbose_name='Naturalidade')),
                ('nome_pai', models.CharField(blank=True, max_length=100, verbose_name='Nome do Pai')),
                ('nome_mae', models.CharField(blank=True, max_length=100, verbose_name='Nome da Mãe')),
                ('numero_sus', models.CharField(blank=True, max_length=100, verbose_name='Número do SUS')),
                ('cpf', models.CharField(blank=True, max_length=15, verbose_name='CPF')),
                ('titulo_eleitor', models.CharField(blank=True, max_length=15, verbose_name='Título de Eleitor')),
                ('rg', models.CharField(blank=True, max_length=30, verbose_name='RG')),
                ('rg_orgao_expedidor', models.CharField(blank=True, max_length=20, verbose_name='Órgão Expedidor')),
                ('rg_data_expedicao', models.DateField(blank=True, null=True, verbose_name='Data de Expedição')),
                ('ativo', models.BooleanField(choices=[(True, 'Sim'), (False, 'Não')], default=True, verbose_name='Ativo?')),
                ('profissao', models.CharField(blank=True, max_length=254, verbose_name='Profissão')),
                ('cargo', models.CharField(blank=True, default='', max_length=254, verbose_name='Cargo/Função')),
                ('observacoes', models.TextField(blank=True, default='', verbose_name='Outros observações sobre o Contato')),
            ],
            options={
                'permissions': (('print_impressoenderecamento', 'Pode Imprimir Impressos de Endereçamento'), ('print_rel_contato_agrupado_por_processo', 'Pode Imprimir Relatório de Contatos Agrupados por Processo')),
                'ordering': ['nome'],
                'verbose_name_plural': 'Contatos',
                'verbose_name': 'Contato',
            },
        ),
        migrations.CreateModel(
            name='Dependente',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='modified')),
                ('nome', models.CharField(max_length=100, verbose_name='Nome')),
                ('nome_social', models.CharField(blank=True, default='', max_length=100, verbose_name='Nome Social')),
                ('apelido', models.CharField(blank=True, default='', max_length=100, verbose_name='Apelido')),
                ('sexo', models.CharField(blank=True, choices=[('F', 'Feminino'), ('M', 'Masculino')], max_length=1, verbose_name='Sexo Biológico')),
                ('data_nascimento', models.DateField(blank=True, null=True, verbose_name='Data Nascimento')),
                ('identidade_genero', models.CharField(blank=True, default='', max_length=100, verbose_name='Como se reconhece?')),
            ],
            options={
                'verbose_name_plural': 'Dependentes',
                'verbose_name': 'Dependente',
            },
        ),
        migrations.CreateModel(
            name='Email',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='modified')),
                ('email', models.EmailField(max_length=254, verbose_name='Email')),
                ('preferencial', models.BooleanField(choices=[(True, 'Sim'), (False, 'Não')], default=True, verbose_name='Preferêncial?')),
                ('permissao', models.BooleanField(choices=[(True, 'Sim'), (False, 'Não')], default=True, help_text='Permite que nossa instituição envie informações         para este email?', verbose_name='Permissão:')),
            ],
            options={
                'verbose_name_plural': "Email's",
                'verbose_name': 'Email',
            },
        ),
        migrations.CreateModel(
            name='Endereco',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='modified')),
                ('uf', models.CharField(blank=True, choices=[('AC', 'Acre'), ('AL', 'Alagoas'), ('AP', 'Amapá'), ('AM', 'Amazonas'), ('BA', 'Bahia'), ('CE', 'Ceará'), ('DF', 'Distrito Federal'), ('ES', 'Espírito Santo'), ('GO', 'Goiás'), ('MA', 'Maranhão'), ('MT', 'Mato Grosso'), ('MS', 'Mato Grosso do Sul'), ('MG', 'Minas Gerais'), ('PR', 'Paraná'), ('PB', 'Paraíba'), ('PA', 'Pará'), ('PE', 'Pernambuco'), ('PI', 'Piauí'), ('RJ', 'Rio de Janeiro'), ('RN', 'Rio Grande do Norte'), ('RS', 'Rio Grande do Sul'), ('RO', 'Rondônia'), ('RR', 'Roraima'), ('SC', 'Santa Catarina'), ('SE', 'Sergipe'), ('SP', 'São Paulo'), ('TO', 'Tocantins'), ('EX', 'Exterior')], max_length=2, verbose_name='Estado')),
                ('cep', models.CharField(blank=True, default='', max_length=9, verbose_name='CEP')),
                ('endereco', models.CharField(blank=True, default='', help_text='O campo endereço também é um campo de busca, nele você pode digitar qualquer informação, inclusive digitar o cep para localizar o endereço, e vice-versa!', max_length=254, verbose_name='Endereço')),
                ('numero', models.CharField(blank=True, default='', max_length=50, verbose_name='Número')),
                ('complemento', models.CharField(blank=True, default='', max_length=254, verbose_name='Complemento')),
                ('ponto_referencia', models.CharField(blank=True, default='', max_length=254, verbose_name='Pontos de Referência')),
                ('observacoes', models.TextField(blank=True, default='', verbose_name='Outros observações sobre o Endereço')),
                ('preferencial', models.BooleanField(choices=[(True, 'Sim'), (False, 'Não')], default=True, verbose_name='Preferencial?')),
            ],
            options={
                'verbose_name_plural': 'Endereços',
                'verbose_name': 'Endereço',
            },
        ),
        migrations.CreateModel(
            name='EstadoCivil',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('descricao', models.CharField(default='', max_length=254, verbose_name='Nome / Descrição')),
            ],
            options={
                'ordering': ('descricao',),
                'abstract': False,
                'verbose_name_plural': 'Estados Civis',
                'verbose_name': 'Estado Civil',
            },
        ),
        migrations.CreateModel(
            name='FiliacaoPartidaria',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='modified')),
                ('data', models.DateField(verbose_name='Data de Filiação')),
                ('data_desfiliacao', models.DateField(blank=True, null=True, verbose_name='Data de Desfiliação')),
            ],
            options={
                'verbose_name_plural': 'Filiações Partidárias',
                'verbose_name': 'Filiação Partidária',
            },
        ),
        migrations.CreateModel(
            name='GrupoDeContatos',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='modified')),
                ('nome', models.CharField(max_length=100, unique=True, verbose_name='Nome do Grupo')),
            ],
            options={
                'ordering': ('nome',),
                'verbose_name_plural': 'Grupos de Contatos',
                'verbose_name': 'Grupo de Contatos',
            },
        ),
        migrations.CreateModel(
            name='LocalTrabalho',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='modified')),
                ('nome', models.CharField(max_length=254, verbose_name='Nome / Razão Social')),
                ('nome_social', models.CharField(blank=True, default='', max_length=254, verbose_name='Nome Fantasia')),
                ('uf', models.CharField(blank=True, choices=[('AC', 'Acre'), ('AL', 'Alagoas'), ('AP', 'Amapá'), ('AM', 'Amazonas'), ('BA', 'Bahia'), ('CE', 'Ceará'), ('DF', 'Distrito Federal'), ('ES', 'Espírito Santo'), ('GO', 'Goiás'), ('MA', 'Maranhão'), ('MT', 'Mato Grosso'), ('MS', 'Mato Grosso do Sul'), ('MG', 'Minas Gerais'), ('PR', 'Paraná'), ('PB', 'Paraíba'), ('PA', 'Pará'), ('PE', 'Pernambuco'), ('PI', 'Piauí'), ('RJ', 'Rio de Janeiro'), ('RN', 'Rio Grande do Norte'), ('RS', 'Rio Grande do Sul'), ('RO', 'Rondônia'), ('RR', 'Roraima'), ('SC', 'Santa Catarina'), ('SE', 'Sergipe'), ('SP', 'São Paulo'), ('TO', 'Tocantins'), ('EX', 'Exterior')], max_length=2, verbose_name='Estado')),
                ('cep', models.CharField(blank=True, default='', max_length=9, verbose_name='CEP')),
                ('endereco', models.CharField(blank=True, default='', help_text='O campo endereço também é um campo de busca. Nele você pode digitar qualquer informação, inclusive digitar o cep para localizar o endereço, e vice-versa!', max_length=254, verbose_name='Endereço')),
                ('numero', models.CharField(blank=True, default='', max_length=50, verbose_name='Número')),
                ('complemento', models.CharField(blank=True, default='', max_length=30, verbose_name='Complemento')),
                ('data_inicio', models.DateField(blank=True, null=True, verbose_name='Data de Início')),
                ('data_fim', models.DateField(blank=True, null=True, verbose_name='Data de Fim')),
                ('preferencial', models.BooleanField(choices=[(True, 'Sim'), (False, 'Não')], default=True, verbose_name='Preferencial?')),
                ('cargo', models.CharField(blank=True, default='', help_text='Ao definir um cargo e função aqui, o Cargo/Função preenchido na aba "Dados Básicos", será desconsiderado ao gerar impressos!', max_length=254, verbose_name='Cargo/Função')),
            ],
            options={
                'verbose_name_plural': 'Locais de Trabalho',
                'verbose_name': 'Local de Trabalho',
            },
        ),
        migrations.CreateModel(
            name='NivelInstrucao',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('descricao', models.CharField(default='', max_length=254, verbose_name='Nome / Descrição')),
            ],
            options={
                'ordering': ('descricao',),
                'abstract': False,
                'verbose_name_plural': 'Níveis de Instrução',
                'verbose_name': 'Nível de Instrução',
            },
        ),
        migrations.CreateModel(
            name='OperadoraTelefonia',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('descricao', models.CharField(default='', max_length=254, verbose_name='Nome / Descrição')),
            ],
            options={
                'ordering': ('descricao',),
                'abstract': False,
                'verbose_name_plural': 'Operadoras de Telefonia',
                'verbose_name': 'Operadora de Telefonia',
            },
        ),
        migrations.CreateModel(
            name='Parentesco',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('descricao', models.CharField(default='', max_length=254, verbose_name='Nome / Descrição')),
            ],
            options={
                'ordering': ('descricao',),
                'abstract': False,
                'verbose_name_plural': 'Parentescos',
                'verbose_name': 'Parentesco',
            },
        ),
        migrations.CreateModel(
            name='Processo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('search', models.TextField(blank=True, default='')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='modified')),
                ('titulo', models.CharField(max_length=9999, verbose_name='Título')),
                ('data', models.DateField(verbose_name='Data de Abertura')),
                ('descricao', models.TextField(blank=True, default='', verbose_name='Descrição do Processo')),
                ('observacoes', models.TextField(blank=True, default='', verbose_name='Outras observações sobre o Processo')),
                ('solucao', models.TextField(blank=True, default='', verbose_name='Solução do Processo')),
                ('importancia', models.CharField(blank=True, choices=[('B', 'Baixa'), ('M', 'Média'), ('A', 'Alta'), ('C', 'Crítica')], max_length=1, verbose_name='Importância')),
            ],
            options={
                'ordering': ('titulo',),
                'verbose_name_plural': 'Processos',
                'verbose_name': 'Processo',
            },
        ),
        migrations.CreateModel(
            name='PronomeTratamento',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome_por_extenso', models.CharField(default='', max_length=254, verbose_name='Nome Por Extenso')),
                ('abreviatura_singular_m', models.CharField(default='', max_length=254, verbose_name='Abreviatura Singular Masculino')),
                ('abreviatura_singular_f', models.CharField(default='', max_length=254, verbose_name='Abreviatura Singular Feminino')),
                ('abreviatura_plural_m', models.CharField(default='', max_length=254, verbose_name='Abreviatura Plural Masculino')),
                ('abreviatura_plural_f', models.CharField(default='', max_length=254, verbose_name='Abreviatura Plural Feminino')),
                ('vocativo_direto_singular_m', models.CharField(default='', max_length=254, verbose_name='Vocativo Direto Singular Masculino')),
                ('vocativo_direto_singular_f', models.CharField(default='', max_length=254, verbose_name='Vocativo Direto Singular Feminino')),
                ('vocativo_direto_plural_m', models.CharField(default='', max_length=254, verbose_name='Vocativo Direto Plural Masculino')),
                ('vocativo_direto_plural_f', models.CharField(default='', max_length=254, verbose_name='Vocativo Direto Plural Feminino')),
                ('vocativo_indireto_singular_m', models.CharField(default='', max_length=254, verbose_name='Vocativo Indireto Singular Masculino')),
                ('vocativo_indireto_singular_f', models.CharField(default='', max_length=254, verbose_name='Vocativo Indireto Singular Feminino')),
                ('vocativo_indireto_plural_m', models.CharField(default='', max_length=254, verbose_name='Vocativo Indireto Plural Masculino')),
                ('vocativo_indireto_plural_f', models.CharField(default='', max_length=254, verbose_name='Vocativo Indireto Plural Feminino')),
                ('enderecamento_singular_m', models.CharField(default='', max_length=254, verbose_name='Endereçamento Singular Masculino')),
                ('enderecamento_singular_f', models.CharField(default='', max_length=254, verbose_name='Endereçamento Singular Feminino')),
                ('enderecamento_plural_m', models.CharField(default='', max_length=254, verbose_name='Endereçamento Plural Masculino')),
                ('enderecamento_plural_f', models.CharField(default='', max_length=254, verbose_name='Endereçamento Plural Feminino')),
                ('prefixo_nome_singular_m', models.CharField(default='', max_length=254, verbose_name='Prefixo Singular Masculino')),
                ('prefixo_nome_singular_f', models.CharField(default='', max_length=254, verbose_name='Prefixo Singular Feminino')),
                ('prefixo_nome_plural_m', models.CharField(default='', max_length=254, verbose_name='Prefixo Plural Masculino')),
                ('prefixo_nome_plural_f', models.CharField(default='', max_length=254, verbose_name='Prefixo Plural Feminino')),
            ],
            options={
                'verbose_name_plural': 'Pronomes de tratamento',
                'verbose_name': 'Pronome de Tratamento',
            },
        ),
        migrations.CreateModel(
            name='StatusProcesso',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('descricao', models.CharField(default='', max_length=254, verbose_name='Nome / Descrição')),
            ],
            options={
                'ordering': ('descricao',),
                'abstract': False,
                'verbose_name_plural': 'Status de Processos',
                'verbose_name': 'Status de Processo',
            },
        ),
        migrations.CreateModel(
            name='Telefone',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='modified')),
                ('telefone', models.CharField(max_length=100, verbose_name='Número do Telefone')),
                ('proprio', models.NullBooleanField(choices=[(None, '---------'), (True, 'Sim'), (False, 'Não')], verbose_name='Próprio?')),
                ('de_quem_e', models.CharField(blank=True, help_text='Se não é próprio, de quem é?', max_length=40, verbose_name='De quem é?')),
                ('preferencial', models.BooleanField(choices=[(True, 'Sim'), (False, 'Não')], default=True, verbose_name='Preferêncial?')),
                ('permissao', models.BooleanField(choices=[(True, 'Sim'), (False, 'Não')], default=True, help_text='Permite que nossa instituição entre em contato         com você neste telefone?', verbose_name='Permissão:')),
                ('contato', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='telefone_set', to='cerimonial.Contato', verbose_name='Contato')),
            ],
            options={
                'verbose_name_plural': 'Telefones',
                'verbose_name': 'Telefone',
            },
        ),
        migrations.CreateModel(
            name='TipoAutoridade',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('descricao', models.CharField(default='', max_length=254, verbose_name='Nome / Descrição')),
                ('pronomes', models.ManyToManyField(related_name='tipoautoridade_set', to='cerimonial.PronomeTratamento')),
            ],
            options={
                'ordering': ('descricao',),
                'abstract': False,
                'verbose_name_plural': 'Tipos de Autoridade',
                'verbose_name': 'Tipo de Autoridade',
            },
        ),
        migrations.CreateModel(
            name='TipoEmail',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('descricao', models.CharField(default='', max_length=254, verbose_name='Nome / Descrição')),
            ],
            options={
                'ordering': ('descricao',),
                'abstract': False,
                'verbose_name_plural': 'Tipos de Email',
                'verbose_name': 'Tipo de Email',
            },
        ),
        migrations.CreateModel(
            name='TipoEndereco',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('descricao', models.CharField(default='', max_length=254, verbose_name='Nome / Descrição')),
            ],
            options={
                'ordering': ('descricao',),
                'abstract': False,
                'verbose_name_plural': 'Tipos de Endereço',
                'verbose_name': 'Tipo de Endereço',
            },
        ),
        migrations.CreateModel(
            name='TipoLocalTrabalho',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('descricao', models.CharField(default='', max_length=254, verbose_name='Nome / Descrição')),
            ],
            options={
                'ordering': ('descricao',),
                'abstract': False,
                'verbose_name_plural': 'Tipos de Local de Trabalho',
                'verbose_name': 'Tipo do Local de Trabalho',
            },
        ),
        migrations.CreateModel(
            name='TipoTelefone',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('descricao', models.CharField(default='', max_length=254, verbose_name='Nome / Descrição')),
            ],
            options={
                'ordering': ('descricao',),
                'abstract': False,
                'verbose_name_plural': 'Tipos de Telefone',
                'verbose_name': 'Tipo de Telefone',
            },
        ),
        migrations.CreateModel(
            name='TopicoProcesso',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('descricao', models.CharField(default='', max_length=254, verbose_name='Nome / Descrição')),
            ],
            options={
                'ordering': ('descricao',),
                'abstract': False,
                'verbose_name_plural': 'Tópicos de Processos',
                'verbose_name': 'Tópico de Processo',
            },
        ),
    ]
