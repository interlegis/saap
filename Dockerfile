FROM debian

RUN apt-get update && apt-get upgrade

RUN apt-get update && apt-get install -y --no-install-recommends apt-utils

# Evitar erros de dialog frontend
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get install -y git python3-dev libpq-dev graphviz-dev graphviz \
pkg-config software-properties-common build-essential libxml2-dev \
libjpeg-dev libssl-dev libffi-dev libxslt1-dev python3-setuptools curl \
vim openssh-client

RUN easy_install3 setuptools
RUN easy_install3 pip lxml

RUN curl -sL https://deb.nodesource.com/setup_6.x | bash -

RUN apt-get install -y nodejs

RUN curl -o- https://raw.githubusercontent.com/creationix/nvm/v0.33.11/install.sh | bash

RUN npm install npm strip-ansi -g
RUN npm install -g bower

RUN pip install virtualenvwrapper

#ENV VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3
#ENV WORKON_HOME=/var/.virtualenvs
#ENV PROJECT_HOME=/var/interlegis/saap
#RUN /bin/bash -c "source /usr/local/bin/virtualenvwrapper.sh"

RUN echo "export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3 \
export WORKON_HOME=/var/interlegis/.virtualenvs \
export PROJECT_HOME=/var/interlegis \
source '/usr/local/bin/virtualenvwrapper.sh'" >> /root/.bashrc

RUN /bin/bash -c "source /root/.bashrc"

RUN mkdir -p /var/interlegis/.virtualenvs

WORKDIR /var/interlegis/saap/

ADD . /var/interlegis/saap/

ENV mkvirtualenv saap -a /var/interlegis/saap -p /usr/bin/python3

RUN pip install -r requirements/dev-requirements.txt

#FROM alpine:3.7

#ENV BUILD_PACKAGES postgresql-dev graphviz-dev graphviz build-base git pkgconfig \
#python3-dev libxml2-dev jpeg-dev libressl-dev libffi-dev libxslt-dev nodejs py3-lxml \
#py3-magic postgresql-client poppler-utils antiword vim openssh-client

#RUN apk update --update-cache && apk upgrade

#RUN apk --update add fontconfig ttf-dejavu && fc-cache -fv

#RUN apk add --no-cache python3 nginx tzdata && \
#    python3 -m ensurepip && \
#    rm -r /usr/lib/python*/ensurepip && \
#    pip3 install --upgrade pip setuptools && \
#    rm -r /root/.cache && \
#    rm -f /etc/nginx/conf.d/*

#RUN mkdir -p /var/interlegis/saap && \
#    apk add --update --no-cache $BUILD_PACKAGES

#RUN npm install -g bower && \
#    npm cache clean --force

#WORKDIR /var/interlegis/saap/

#ADD . /var/interlegis/saap/

#COPY start.sh /var/interlegis/saap/
#COPY config/nginx/saap.conf /etc/nginx/conf.d
#COPY config/nginx/nginx.conf /etc/nginx/nginx.conf

#RUN pip install -r /var/interlegis/saap/requirements/dev-requirements.txt --upgrade setuptools && \
#    rm -r /root/.cache

#COPY config/env_dockerfile /var/interlegis/saap/saap/.env

#COPY config/rest_framework/compat.py /usr/lib/python3.6/site-packages/rest_framework/
#COPY config/rest_framework/relations.py /usr/lib/python3.6/site-packages/rest_framework/
#COPY config/rest_framework/reverse.py /usr/lib/python3.6/site-packages/rest_framework/
#COPY config/rest_framework/routers.py /usr/lib/python3.6/site-packages/rest_framework/
#COPY config/rest_framework/rest_framework.py /usr/lib/python3.6/site-packages/rest_framework/templatetags/
#COPY config/rest_framework/breadcrumbs.py /usr/lib/python3.6/site-packages/rest_framework/utils/

#RUN python3 manage.py bower_install -- --allow-root --no-input && \
#    python3 manage.py compilescss

#RUN python3 manage.py collectstatic --noinput --clear

# Remove .env(fake) e saap.db da imagem
#RUN rm -rf /var/interlegis/saap/saap/.env && \
#    rm -rf /var/interlegis/saap/saap.db

#RUN chmod +x /var/interlegis/saap/start.sh && \
#    ln -sf /dev/stdout /var/log/nginx/access.log && \
#    ln -sf /dev/stderr /var/log/nginx/error.log && \
#    mkdir /var/log/saap/

#VOLUME ["/var/interlegis/saap/data", "/var/interlegis/saap/media"]

#CMD ["/var/interlegis/saap/start.sh"]
