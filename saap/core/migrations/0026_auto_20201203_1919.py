# -*- coding: utf-8 -*-
# Generated by Django 1.9.13 on 2020-12-03 22:19
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import smart_selects.db_fields


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0025_auto_20201105_1757'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bairro',
            name='estado',
            field=models.ForeignKey(default=21, on_delete=django.db.models.deletion.CASCADE, to='core.Estado', verbose_name='Estado'),
        ),
        migrations.AlterField(
            model_name='bairro',
            name='municipio',
            field=smart_selects.db_fields.ChainedForeignKey(auto_choose=True, chained_field='estado', chained_model_field='estado', default=4891, on_delete=django.db.models.deletion.CASCADE, to='core.Municipio', verbose_name='Município'),
        ),
        migrations.AlterField(
            model_name='distrito',
            name='estado',
            field=models.ForeignKey(default=21, on_delete=django.db.models.deletion.CASCADE, to='core.Estado', verbose_name='Estado'),
        ),
        migrations.AlterField(
            model_name='distrito',
            name='municipio',
            field=smart_selects.db_fields.ChainedForeignKey(auto_choose=True, chained_field='estado', chained_model_field='estado', default=4891, on_delete=django.db.models.deletion.CASCADE, to='core.Municipio', verbose_name='Município'),
        ),
        migrations.AlterField(
            model_name='municipio',
            name='estado',
            field=models.ForeignKey(default=21, on_delete=django.db.models.deletion.CASCADE, related_name='municipios_set', to='core.Estado', verbose_name='Estado'),
        ),
        migrations.AlterField(
            model_name='regiaomunicipal',
            name='estado',
            field=models.ForeignKey(default=21, on_delete=django.db.models.deletion.CASCADE, to='core.Estado', verbose_name='Estado'),
        ),
        migrations.AlterField(
            model_name='regiaomunicipal',
            name='municipio',
            field=smart_selects.db_fields.ChainedForeignKey(auto_choose=True, chained_field='estado', chained_model_field='estado', default=4891, on_delete=django.db.models.deletion.CASCADE, to='core.Municipio', verbose_name='Município'),
        ),
    ]
