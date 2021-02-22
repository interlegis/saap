#!/usr/bin/env bash

##
## Versioning info: [major].[minor].[patch], example: 3.0.112, 3.1.23
##

VERSION_PATTERN='([0-9]+)\.([0-9]+)\.([0-9]+)?'

LATEST_VERSION=$(git tag --sort=committerdate | egrep $VERSION_PATTERN | tail -1)

LAST_DIGIT=`echo $LATEST_VERSION | cut -f 3 -d '.'`
MAIN_REV=`echo $LATEST_VERSION | cut -f 1,2 -d '.'`
NEXT_NUMBER=$(($LAST_DIGIT + 1))
NEXT_VERSION=$MAIN_REV'.'$NEXT_NUMBER

FINAL_VERSION=

function change_files {

    echo "Atualizando de "$LATEST_VERSION" para "$NEXT_VERSION"..."

    sed -E -i "s|$LATEST_VERSION|$NEXT_VERSION|g" saap/templates/base.html

    sed -E -i "s|$LATEST_VERSION|$NEXT_VERSION|g" saap/settings.py
}

function commit_and_push {
   echo "Criando o commit..."

   git add .
   git commit -m "Release: $NEXT_VERSION"
   git tag $NEXT_VERSION

   echo "Versão criada e gerada localmente."

   echo "Enviando para o GitHub a versão $NEXT_VERSION..."

   git push origin master

   echo "Concluído"
}

git fetch
echo "Release atual: "$LATEST_VERSION
change_files
commit_and_push
