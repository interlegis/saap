#!/bin/bash

PythonDir=$(ls /var/interlegis/.virtualenvs/saap/lib/)

echo "Corrigindo problemas de configuração em alguns pacotes.."

echo "* Arquivos do Django Models..."
cp /var/interlegis/saap/config/django_db_models/base.py /var/interlegis/.virtualenvs/saap/lib/$PythonDir/site-packages/django/db/models/

echo "* Arquivos do Django Core Management..."
cp /var/interlegis/saap/config/django_core_management/base.py /var/interlegis/.virtualenvs/saap/lib/$PythonDir/site-packages/django/core/management/

echo "* Arquivos do Rest Framework"
rm /var/interlegis/.virtualenvs/saap/lib/$PythonDir/site-packages/rest_framework/* -R
cp /var/interlegis/saap/config/rest_framework/* /var/interlegis/.virtualenvs/saap/lib/$PythonDir/site-packages/rest_framework/ -R

echo "* Arquivos do Smart Selects (usado para carregar os campos de Estado, Município, Bairro...)..."
cp /var/interlegis/saap/config/smart-selects/* /var/interlegis/.virtualenvs/saap/lib/$PythonDir/site-packages/smart_selects/static/smart-selects/admin/js/

echo "* Arquivos do ReportLab (usado na geração de relatórios PDF)..."
cp /var/interlegis/saap/config/reportlab/* /var/interlegis/.virtualenvs/saap/lib/$PythonDir/site-packages/reportlab/platypus/

echo "* Arquivos do Image Cropping..."
cp /var/interlegis/saap/config/image_cropping/* /var/interlegis/.virtualenvs/saap/lib/$PythonDir/site-packages/image_cropping/

echo "Arquivos corrigidos!"
