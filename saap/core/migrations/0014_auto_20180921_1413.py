# -*- coding: utf-8 -*-
# Generated by Django 1.9.13 on 2018-09-21 17:13
from __future__ import unicode_literals

from django.db import migrations
import django.db.models.deletion
import smart_selects.db_fields


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_auto_20180919_1705'),
    ]

    #operations = [
    #    migrations.AlterField(
    #        model_name='bairro',
    #        name='municipio',
    #        field=smart_selects.db_fields.ChainedForeignKey(auto_choose=True, chained_field='estado', chained_model_field='estado', on_delete=django.db.models.deletion.CASCADE, to='core.Estado'),
    #    ),
    #]
