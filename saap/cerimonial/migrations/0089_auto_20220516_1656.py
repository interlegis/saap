# -*- coding: utf-8 -*-
# Generated by Django 1.9.13 on 2022-05-16 19:56
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import smart_selects.db_fields


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0030_auto_20220516_1656'),
        ('cerimonial', '0088_auto_20220513_1132'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='evento',
            options={'ordering': ('inicio',), 'verbose_name': 'Evento', 'verbose_name_plural': 'Eventos'},
        ),
        migrations.RenameField(
            model_name='evento',
            old_name='description',
            new_name='descricao',
        ),
        migrations.RenameField(
            model_name='evento',
            old_name='start_time',
            new_name='inicio',
        ),
        migrations.RenameField(
            model_name='evento',
            old_name='location',
            new_name='localizacao',
        ),
        migrations.RenameField(
            model_name='evento',
            old_name='end_time',
            new_name='termino',
        ),
        migrations.RenameField(
            model_name='evento',
            old_name='title',
            new_name='titulo',
        ),
        migrations.AddField(
            model_name='evento',
            name='bairro',
            field=smart_selects.db_fields.ChainedForeignKey(blank=True, chained_field='municipio', chained_model_field='municipio', default=5, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.Bairro', verbose_name='Bairro'),
        ),
        migrations.AddField(
            model_name='evento',
            name='estado',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.Estado', verbose_name='Estado'),
        ),
        migrations.AddField(
            model_name='evento',
            name='municipio',
            field=smart_selects.db_fields.ChainedForeignKey(auto_choose=True, blank=True, chained_field='estado', chained_model_field='estado', null=True, on_delete=django.db.models.deletion.CASCADE, to='core.Municipio', verbose_name='Município'),
        ),
    ]
