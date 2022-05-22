#!/usr/bin/env bash

function update_repo {

   echo "Sincronizando e atualizando repositório local..."

   git fetch upstream
   git checkout master
   git merge upstream/master

   echo "Repositório sincronizado"
}

update_repo
