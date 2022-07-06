#!/usr/bin/env bash

create_env() {
    echo "[CREATE_ENV] Creating .env file..."
    KEY=`python3 manage.py generate_secret_key`
    FILENAME="/var/interlegis/saap/.env"

    if [ -z "${DATABASE_URL:-}" ]; then
        DATABASE_URL="postgresql://saap:saap@saapdb:5432/saap"
    fi

    # ALWAYS replace the content of .env variable
    # If want to conditionally create only if absent then use IF below
    #    if [ ! -f $FILENAME ]; then

    touch $FILENAME

    # explicitly use '>' to erase any previous content
    echo "SECRET_KEY="$KEY > $FILENAME
    # now only appends
    echo "DATABASE_URL = "$DATABASE_URL >> $FILENAME

    echo "DEBUG = ""${DEBUG-False}" >> $FILENAME
    echo "DJANGO_TOOLBAR = ""${DJANGO_TOOLBAR-False}" >> $FILENAME

    echo "EMAIL_USE_TLS = ""${USE_TLS-True}" >> $FILENAME
    echo "EMAIL_PORT = ""${EMAIL_PORT-25}" >> $FILENAME
    echo "EMAIL_HOST = ""${EMAIL_HOST-''}" >> $FILENAME
    echo "EMAIL_HOST_USER = ""${EMAIL_HOST_USER-''}" >> $FILENAME
    echo "EMAIL_HOST_PASSWORD = ""${EMAIL_HOST_PASSWORD-''}" >> $FILENAME
    echo "EMAIL_SEND_USER = ""${EMAIL_HOST_USER-''}" >> $FILENAME

    echo "SITE_NAME = ""${SITE_NAME-''}" >> $FILENAME
    echo "SITE_DOMAIN = ""${SITE_DOMAIN-''}" >> $FILENAME

    echo "DADOS_NOME = ""${DADOS_NOME-''}" >> $FILENAME
    echo "DADOS_ENDERECO = ""${DADOS_ENDERECO-''}" >> $FILENAME
    echo "DADOS_MUNICIPIO = ""${DADOS_MUNICIPIO-''}" >> $FILENAME
    echo "DADOS_UF = ""${DADOS_UF-''}" >> $FILENAME
    echo "DADOS_CEP = ""${DADOS_CEP-''}" >> $FILENAME
    echo "DADOS_EMAIL = ""${DADOS_EMAIL-''}" >> $FILENAME
    echo "DADOS_TELEFONE = ""${DADOS_TELEFONE-''}" >> $FILENAME
    echo "DADOS_SITE = ""${DADOS_SITE-''}" >> $FILENAME
    echo "BRASAO_PROPRIO = ""${BRASAO_PROPRIO-False}" >> $FILENAME

    echo "[CREATE_ENV] Done!"
}

load_db() {

    /bin/bash busy-wait.sh $DATABASE_URL

    export PGPASSWORD="saap"

    echo "[LOAD_DB] Creating database structure..."
    yes yes | python3 manage.py migrate
    
    echo "[LOAD_DB] Done!"
}

create_superuser(){

    echo "[CREATE_SUPERUSER] Creating superuser..."

    user_created=$(python3 create_admin.py 2>&1)

    cmd=$(echo $user_created | grep 'ADMIN_USER_EXISTS')
    user_exists=$?

    cmd=$(echo $user_created | grep 'MISSING_ADMIN_PASSWORD')
    lack_pwd=$?

    if [ $user_exists -eq 0 ]; then
       echo "[CREATE_SUPERUSER] User admin already exists. Not creating"
    fi

    if [ $lack_pwd -eq 0 ]; then
       echo "[CREATE_SUPERUSER] Environment variable $ADMIN_PASSWORD for superuser admin was not set. Leaving container"
    fi

}

create_env

load_db

create_superuser

echo "-----------------------------------"
echo "| ███████╗ █████╗  █████╗ ██████╗ |"
echo "| ██╔════╝██╔══██╗██╔══██╗██╔══██╗|"
echo "| ███████╗███████║███████║██████╔╝|"
echo "| ╚════██║██╔══██║██╔══██║██╔═══╝ |"
echo "| ███████║██║  ██║██║  ██║██║     |"
echo "| ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     |"
echo "-----------------------------------"

gunicorn saap.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 960 &
/usr/sbin/nginx -g "daemon off;"
