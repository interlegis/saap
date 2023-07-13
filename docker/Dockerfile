FROM python:3.9-slim-buster

# Define o mantenedor da imagem
LABEL maintainer="Interlegis"

# Setup env
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV DEBIAN_FRONTEND noninteractive
ENV SAAPDIR=/var/interlegis/saap

# Configura o sistema para usar UTF-8
#RUN apt-get update -y &&\
#    apt-get install -y locales &&\
#    rm -rf /var/lib/apt/lists/* &&\
#    localedef -i pt_BR -c -f UTF-8 -A /usr/share/locale/locale.alias pt_BR.UTF-8

# Pacotes usados na construcao da imagem
ENV BUILD_PACKAGES apt-utils apt-file build-essential dialog graphviz-dev \
                   libpq-dev libxml2-dev libjpeg-dev libssl-dev libcairo2-dev \
                   libffi-dev libxslt1-dev libmagic-dev libfreetype6-dev git sudo \ 
                   pkg-config python3-setuptools python3-pip python3-dev software-properties-common

# Pacotes usados na execucao da imagem
ENV RUN_PACKAGES bash curl vim \
                 fontconfig graphviz jq ttf-dejavu poppler-utils tzdata \
                 python python3-lxml python3-magic python3-psycopg2 python3-venv \
                 nginx postgresql-client

#RUN mkdir -p /var/interlegis/saap

# Instalacao dos pacotes
RUN apt-get update -y &&\
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends $BUILD_PACKAGES $RUN_PACKAGES && \
    fc-cache -fv

# Instalacao do Bower e Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_14.x | sudo -E bash - &&\
    sudo apt-get install -y nodejs &&\
    sudo npm install bower -g

# Clone do projeto do Github
RUN sudo git clone https://github.com/interlegis/saap $SAAPDIR && \
    pip install --ignore-installed --no-cache-dir -r /var/interlegis/saap/requirements/requirements.txt

# Instalacao do ambiente virtual
#RUN pip install virtualenvwrapper 

# Remocao dos pacotes usados na construcao da imagem
RUN SUDO_FORCE_REMOVE=yes apt-get purge -y --auto-remove $BUILD_PACKAGES &&\
    apt-get autoremove && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /var/interlegis/saap
ADD . /var/interlegis/saap

# Correcao da configuracao de alguns pacotes e requerimentos
CMD rm /usr/local/lib/python*/site-packages/rest_framework/* -R
RUN cp /var/interlegis/saap/config/django_db_models/base.py /usr/local/lib/python*/site-packages/django/db/models/
RUN cp /var/interlegis/saap/config/django_core_management/base.py /usr/local/lib/python*/site-packages/django/core/management/
RUN cp /var/interlegis/saap/config/rest_framework/* /usr/local/lib/python*/site-packages/rest_framework/ -R
RUN cp /var/interlegis/saap/config/smart-selects/* /usr/local/lib/python*/site-packages/smart_selects/static/smart-selects/admin/js/
RUN cp /var/interlegis/saap/config/reportlab/* /usr/local/lib/python*/site-packages/reportlab/platypus/
RUN cp /var/interlegis/saap/config/image_cropping/* /usr/local/lib/python*/site-packages/image_cropping

# Copia de arquivos usados na criacao da imagem
COPY start.sh $SAAPDIR
RUN chmod +x /var/interlegis/saap/start.sh 
COPY busy-wait.sh $SAAPDIR
COPY create_admin.py $SAAPDIR

# Copia do arquivo .env e dos arquivos do Nginx
COPY config/env_dockerfile $SAAPDIR/.env
COPY config/saap.conf /etc/nginx/conf.d
COPY config/nginx.conf /etc/nginx/nginx.conf

# Configuracao dos arquivos de log
RUN ln -sf /dev/stdout /var/log/nginx/access.log &&\
    ln -sf /dev/stderr /var/log/nginx/error.log &&\
    mkdir /var/log/saap/ && touch /var/interlegis/saap/saap.log &&\
    ln -s /var/interlegis/saap/saap.log /var/log/saap/saap.log

# Configuracao do bower e arquivos estaticos
RUN python3 manage.py bower install &&\
    python3 manage.py collectstatic --noinput --clear

ENV DEBIAN_FRONTEND teletype

EXPOSE 80 8000

VOLUME ["/var/interlegis/saap/data", "/var/interlegis/saap/media"]

# Execucao do script de inicializacao
CMD ["/var/interlegis/saap/start.sh"]
