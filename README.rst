***********************************************
SAAP - Sistema de Apoio à Atividade Parlamentar
***********************************************


Instalação do Ambiente de Desenvolvimento
=========================================

* Procedimento testado nos seguintes SO's:

  * `Ubuntu 16.04 64bits <README.rst>`_;
  * `Debian Jessie 64bits <README.rst>`_;

        * edite e incremente outros, ou ainda, crie outros readme's dentro do projeto para outros SO's e adicione o link aqui.

Instalar as seguintes dependências do sistema::
----------------------------------------------------------------------------------------

* ::

    sudo apt-get install git python3-dev libpq-dev graphviz-dev graphviz \
    pkg-config software-properties-common build-essential libxml2-dev \
    libjpeg-dev libssl-dev libffi-dev libxslt1-dev python3-setuptools curl

    sudo easy_install3 pip lxml

    sudo -i
    curl -sL https://deb.nodesource.com/setup_6.x | bash -
    exit
    sudo apt-get install nodejs

    sudo npm install npm -g
    sudo npm install -g bower

Instalar o virtualenv usando python 3 para o projeto.
-----------------------------------------------------

* Para usar `virtualenvwrapper <https://virtualenvwrapper.readthedocs.org/en/latest/install.html#basic-installation>`_, instale com::

    sudo pip install virtualenvwrapper

    mkdir ~/Envs

* Edite o arquivo ``.bashrc`` e adicione ao seu final as configurações abaixo para o virtualenvwrapper::

    export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3
    export WORKON_HOME=$HOME/.virtualenvs
    export PROJECT_HOME=$HOME/Envs
    source /usr/local/bin/virtualenvwrapper.sh

* Saia do terminal e entre novamente para que as configurações do virtualenvwrapper sejam carregadas.

Clonar o projeto do github, ou fazer um fork e depois clonar
------------------------------------------------------------

* Para apenas clonar do repositório::

    cd ~/Envs
    git clone git://github.com/interlegis/saap

* Para fazer um fork e depois clonar, siga as instruções em https://help.github.com/articles/fork-a-repo que basicamente são:

  * Criar uma conta no github - é gratuíto.
  * Acessar https://github.com/interlegis/saap e clicar em **Fork**.

  Será criado um domínio pelo qual será possível **clonar, corrigir, customizar, melhorar, contribuir, etc**::

      cd ~/Envs
      git clone git://github.com/[SEU NOME]/saap

* As configurações e instruções de uso para o git estão espalhadas pela internet e possui muito coisa bacana. As tarefas básicas de git e suas interações com github são tranquilas de se aprender.


Criar o ambiente virtual de desenvolvimento para o SAAP
-------------------------------------------------------
* ::

    mkvirtualenv saap -a $HOME/Envs/saap -p /usr/bin/python3

Instalação e configuração das dependências do projeto
-----------------------------------------------------

* **Acesse o terminal e entre no virtualenv**::

    workon saap

* **Instalar dependências ``python``**::

    pip install -r requirements/dev-requirements.txt

* **Configurar arquivo ``.env``**:

    * Uma configuração mínima para funcional seria::

        SECRET_KEY=MUDE-PARA-RESULTADO-GENERATE-SECRET-KEY
        DEBUG=True

  * Criação da `SECRET_KEY <https://docs.djangoproject.com/es/1.9/ref/settings/#std:setting-SECRET_KEY>`_:

    Rodar o comando abaixo, um detalhe importante, esse comando só funciona com o django extensions, mas ele já está presente no arquivo requirements/requirements.txt desse projeto::

        python manage.py generate_secret_key

  * Copie a chave que aparecerá, edite o arquivo ``.env`` e altere o valor do parâmetro SECRET_KEY.

  * Um arquivo de configuração ``.env`` completo deve ter os seguintes parâmetros::

      DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/NAME
      SECRET_KEY=Gere alguma chave e coloque aqui
      DEBUG=[True/False]
      EMAIL_USE_TLS=[True/False]
      EMAIL_PORT=[Insira este parâmetro]
      EMAIL_HOST=[Insira este parâmetro]
      EMAIL_HOST_USER=[Insira este parâmetro]
      EMAIL_HOST_PASSWORD=[Insira este parâmetro]
      SOCIAL_AUTH_FACEBOOK_KEY=[Insira este parâmetro]
      SOCIAL_AUTH_FACEBOOK_SECRET=[Insira este parâmetro]
      SOCIAL_AUTH_GOOGLE_OAUTH2_KEY=[Insira este parâmetro]
      SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET=[Insira este parâmetro]
      SOCIAL_AUTH_TWITTER_KEY=[Insira este parâmetro]
      SOCIAL_AUTH_TWITTER_SECRET=[Insira este parâmetro]
      INITIAL_VALUE_FORMS_UF=[Insira este parâmetro]
      INITIAL_VALUE_FORMS_MUNICIPIO=[Insira este parâmetro]
      INITIAL_VALUE_FORMS_CEP=[Insira este parâmetro]

    * Um exemplo de configuração mínima para um ambiente de produção::

        DATABASE_URL=postgresql://saap:saap@localhost:5432/saap
        SECRET_KEY='Substitua esta linha pela copiada acima'
        DEBUG=True
        EMAIL_USE_TLS=True
        EMAIL_PORT=587
        EMAIL_HOST=
        EMAIL_HOST_USER=
        EMAIL_HOST_PASSWORD=
        SOCIAL_AUTH_FACEBOOK_KEY=
        SOCIAL_AUTH_FACEBOOK_SECRET=
        SOCIAL_AUTH_GOOGLE_OAUTH2_KEY=
        SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET=
        SOCIAL_AUTH_TWITTER_KEY=
        SOCIAL_AUTH_TWITTER_SECRET=
        INITIAL_VALUE_FORMS_UF='DF'
        INITIAL_VALUE_FORMS_MUNICIPIO='Brasília'
        INITIAL_VALUE_FORMS_CEP='71608-000'

* Instalar as dependências do ``bower``::

    ./manage.py bower install

* Atualizar e/ou criar a base de dados para refletir o modelo da versão clonada::

   ./manage.py migrate

* Atualizar arquivos estáticos::

   ./manage.py collectstatic --noinput

* Subir o servidor do django::

   ./manage.py runserver

* Acesse o SAAP em::

   http://localhost:8000/

Instruções para Tradução
========================

Nós utilizamos o `Transifex <https://www.transifex.com>`_  para gerenciar as traduções do projeto.
Se você deseja contribuir, por favor crie uma conta no site e peça para se juntar a nós em `Transifex SAAP Page <https://www.transifex.com/projects/p/saap>`_.
Assim que for aceito, você já pode começar a traduzir.

Para integrar as últimas traduções ao projeto atual, siga estes passos:

* Siga as instruções em `Development Environment Installation`_.

* Instale `Transifex Client <http://docs.transifex.com/client/config/>`_.

Aviso:

   O Transifex Client armazena senhas em 'plain text' no arquivo ``~/.transifexrc``.

   Nós preferimos logar no site do Transifex por meio de redes sociais (GitHub, Google Plus, Linkedin) e modificar, frequentemente, a senha utilizada pelo client.

* `Pull translations <http://docs.transifex.com/client/pull/>`_  ou `push translations <http://docs.transifex.com/client/push/>`_  usando o client. Faça o Pull somente com o repositório vazio, isto é, faça o commit de suas mudanças antes de fazer o Pull de novas traduções.

* Execute o programa com ``.manage.py runserver`` e cheque o sistema para ver se as traduções tiveram efeito.

Nota:

  O idioma do browser é utilizado para escolher as traduções que devem mostradas.



Orientações gerais de implementação
===================================

Boas Práticas
--------------

* Utilize a língua portuguesa em todo o código, nas mensagens de commit e na documentação do projeto.

* Mensagens de commit seguem o padrão de 50/72 colunas. Comece toda mensagem de commit com o verbo no infinitivo. Para mais informações, clique nos links abaixo:

  - Http://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html
  - Http://stackoverflow.com/questions/2290016/git-commit-messages-50-72-formatting

* Mantenha todo o código de acordo com o padrão da PEP8 (sem exceções).

* Antes de todo ``git push``:
  - Execute ``git pull --rebase`` (quase sempre).
  - Em casos excepcionais, faça somente ``git pull`` para criar um merge.

* Antes de ``git commit``, sempre:
  - Execute ``./manage.py check``
  - Execute todos os testes com ``py.test`` na pasta raiz do projeto

Atenção:

    O usuário do banco de dados ``saap`` deve ter a permissão ``create database`` no postgres para que os testes tenham sucesso

* Se você não faz parte da equipe principal, faça o fork deste repositório e envie pull requests.
  Todos são bem-vindos para contribuir. Por favor, faça uma pull request separada para cada correção ou criação de novas funcionalidades.

* Novas funcionalidades estão sujeitas a aprovação, uma vez que elas podem ter impacto em várias pessoas.
  Nós sugerimos que você abra uma nova issue para discutir novas funcionalidades. Elas podem ser escritas tanto em Português, quanto em Inglês.


Testes
------

* Escrever testes para todas as funcionalidades que você implementar.

* Manter a cobertura de testes próximo a 100%.

* Para executar todos os testes você deve entrar em seu virtualenv e executar este comando **na raiz do seu projeto**::

    py.test

* Para executar os teste de cobertura use::

    py.test --cov . --cov-report term --cov-report html && firefox htmlcov/index.html

* Na primeira vez que for executar os testes após uma migração (``./manage.py migrate``) use a opção de recriação da base de testes.
  É necessário fazer usar esta opção apenas uma vez::

    py.test --create-db

Issues
------

* Abra todas as questões sobre o desenvolvimento atual no `Github Issue Tracker <https://github.com/interlegis/saap/issues>`_.

* Você pode escrever suas ``issues`` em Português ou Inglês (ao menos por enquanto).


Referência
----------

* Este arquivo, bem como as configurações iniciais do ambiente foram copiados e extendidos a partir do  `Projeto CMJ da Câmara Municpal de Jataí <https://github.com/cmjatai/cmj>`_. Que por sua vez extendeu o `Projeto SAPL do Interlegis <https://github.com/interlegis/sapl>`_. Nesse repositório foram criadas modificações para tornar esse projeto independente do SAPL.

* O Sistema de autenticação foi copiado e extendido do `Projeto Wikilegis <https://github.com/labhackercd/wikilegis>`_.
