# -*- coding: utf-8 -*-
# Generated by Django 1.9.13 on 2018-09-26 16:34
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cerimonial', '0034_auto_20180926_1333'),
    ]

    operations = [
        migrations.AlterField(
            model_name='localtrabalho',
            name='numero',
            field=models.IntegerField(blank=True, default=0, verbose_name='Número'),
        ),
    ]
