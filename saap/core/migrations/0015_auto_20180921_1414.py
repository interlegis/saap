# -*- coding: utf-8 -*-
# Generated by Django 1.9.13 on 2018-09-21 17:14
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_auto_20180921_1413'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bairro',
            name='municipio',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bairros_set', to='core.Municipio', verbose_name='Município'),
        ),
    ]
