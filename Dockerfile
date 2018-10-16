FROM alpine:3.5

ENV BUILD_PACKAGES postgresql-dev graphviz-dev graphviz build-base git pkgconfig \
python3-dev libxml2-dev jpeg-dev libressl-dev libffi-dev libxslt-dev nodejs py3-lxml \
py3-magic postgresql-client vim

RUN apk add --no-cache python3 nginx && \
    python3 -m ensurepip && \
    rm -r /usr/lib/python*/ensurepip && \
    pip3 install --upgrade pip setuptools && \
    rm -r /root/.cache && \
    rm -f /etc/nginx/conf.d/*

RUN mkdir -p /var/interlegis/saap && \
    apk add --update --no-cache $BUILD_PACKAGES && \
    npm install -g bower && \
    npm cache clean

WORKDIR /var/interlegis/saap/

ADD . /var/interlegis/saap/

COPY start.sh /var/interlegis/saap/
COPY config/nginx/saap.conf /etc/nginx/conf.d
COPY config/nginx/nginx.conf /etc/nginx/nginx.conf

RUN pip install -r /var/interlegis/saap/requirements/dev-requirements.txt --upgrade setuptools && \
    rm -r /root/.cache && \
    rm -r /tmp/*

COPY config/env_dockerfile /var/interlegis/saap/saap/.env

# manage.py bower install bug: https://github.com/nvbn/django-bower/issues/51

RUN python3 manage.py bower_install -- --allow-root --no-input 
#    python3 manage.py compilescss

RUN python3 manage.py collectstatic --noinput --clear
 
# Remove .env(fake) e saap.db da imagem
RUN rm -rf /var/interlegis/saap/saap/.env && \
    rm -rf /var/interlegis/saap/saap.db

RUN chmod +x /var/interlegis/saap/start.sh && \
    ln -sf /dev/stdout /var/log/nginx/access.log && \
    ln -sf /dev/stderr /var/log/nginx/error.log

VOLUME ["/var/interlegis/saap/data", "/var/interlegis/saap/media"]

CMD ["/var/interlegis/saap/start.sh"]

#FROM debian
#FROM alpine:3.7

#MAINTAINER Jonatha Cardoso

#ENV BUILD_PACKAGES git python3-dev libpq-dev graphviz-dev graphviz \
#pkgconfig software-properties-common build-essential libxml2-dev \
#libjpeg-dev libssl-dev libffi-dev libxslt1-dev python3-setuptools curl \
#postgresql-dev build-base jpeg-dev libressl-dev nodejs py3-lxml \
#postgresql-client poppler-utils antiword vim openssh-client py3-magic

#RUN apk update --update-cache && apk upgrade
#RUN apk --update add fontconfig ttf-dejavu && fc-cache -fv

#RUN apk add --no-cache python3 nginx tzdata && \
#    python3 -m ensurepip && \
#    rm -r /usr/lib/python*/ensurepip && \
#    pip3 install --upgrade pip setuptools && \
#    rm -r /root/.cache && \
#    rm -f /etc/nginx/conf.d/*
    
#RUN mkdir -p /var/interlegis/saap

#RUN apk add --update --no-cache $BUILD_PACKAGES
#    apk add --update --no-cache $BUILD_PACKAGES && \
##    easy_install3 pip lxml && \
##    npm install -g npm && \
#    npm install -g bower && \
#    npm cache verify
    
#    apk add --update --no-cache $BUILD_PACKAGES && \
#    npm install -g bower && \
#    npm cache verify
    
#RUN curl -sL https://deb.nodesource.com/setup_6.x | bash -
#RUN exit

#RUN pip install virtualenvwrapper django-image-cropping django-extensions social-auth-app-django 

#RUN mkdir ~/Envs

#RUN echo "export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3 \
#export WORKON_HOME=$HOME/.virtualenvs \
#export PROJECT_HOME=$HOME/Envs \
#source /usr/local/bin/virtualenvwrapper.sh" >> .bashrc

#RUN cd ~/Envs
#RUN git clone git://ojonathacardoso@github.com/ojonathacardoso/saap

#RUN mkvirtualenv saap -a $HOME/Envs/saap -p /usr/bin/python3

#RUN workon saap

#RUN pip install -r requirements/dev-requirements.txt
