# -*- coding: utf-8 -*-
# Generated by Django 1.9.13 on 2022-05-31 13:26
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0032_auto_20220518_1534'),
    ]

    operations = [
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(blank=True, db_index=True, max_length=100, verbose_name='username')),
                ('operation', models.CharField(db_index=True, max_length=1, verbose_name='operation')),
                ('timestamp', models.DateTimeField(db_index=True, verbose_name='timestamp')),
                ('object', models.CharField(blank=True, max_length=4096, verbose_name='object')),
                ('object_id', models.PositiveIntegerField(db_index=True, verbose_name='object_id')),
                ('model_name', models.CharField(db_index=True, max_length=100, verbose_name='model')),
                ('app_name', models.CharField(db_index=True, max_length=100, verbose_name='app')),
            ],
            options={
                'verbose_name': 'AuditLog',
                'verbose_name_plural': 'AuditLogs',
                'ordering': ('-id',),
            },
        ),
    ]
