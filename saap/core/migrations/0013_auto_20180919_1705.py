# -*- coding: utf-8 -*-
# Generated by Django 1.9.13 on 2018-09-19 20:05
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_auto_20180918_1345'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='municipio',
            name='uf',
        ),
        migrations.AddField(
            model_name='bairro',
            name='estado',
            field=models.ForeignKey(default=21, on_delete=django.db.models.deletion.CASCADE, related_name='bairros_set', to='core.Estado', verbose_name='Estado'),
        ),
        migrations.AlterField(
            model_name='estado',
            name='nome',
            field=models.CharField(blank=True, max_length=50, verbose_name='Nome'),
        ),
        migrations.AlterField(
            model_name='estado',
            name='sigla',
            field=models.CharField(max_length=2, verbose_name='Sigla'),
        ),
        migrations.AlterField(
            model_name='municipio',
            name='estado',
            field=models.ForeignKey(default=4891, on_delete=django.db.models.deletion.CASCADE, related_name='municipios_set', to='core.Estado', verbose_name='Estado'),
        ),
        migrations.AlterField(
            model_name='municipio',
            name='nome',
            field=models.CharField(blank=True, max_length=50, verbose_name='Nome'),
        ),
    ]
