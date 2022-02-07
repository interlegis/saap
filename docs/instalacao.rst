***********************************************
Instalação do Ambiente de Desenvolvimento
***********************************************

Procedimento testado no ``Debian 10 Buster x64`` e ``Ubuntu 20.04 Focal Fossa x64``.

Você pode escolher qualquer usuário de sistema para esse processo - todas as referências para ``$USER`` devem ser substituídas por esse usuário. O mesmo deve ter as devidas permissões para instalação e configuração. 

1) Instalar dependências do sistema
----------------------------------------------------------------------------------------

Atualize o sistema:

:: 

    sudo apt-get update && sudo apt-get upgrade -y

Instale os pacotes:

::

    sudo apt-get install -y git python3-dev libpq-dev graphviz-dev graphviz \
    pkg-config postgresql postgresql-contrib pgadmin3 python3-psycopg2 \
    software-properties-common build-essential libxml2-dev libjpeg-dev \
    libssl-dev libffi-dev libxslt1-dev python3-setuptools \
    python3-pip poppler-utils antiword default-jre python3-venv \
    curl vim openssh-client

Instale o Node.js e o Bower

::

    curl -fsSL https://deb.nodesource.com/setup_12.x | sudo -E bash -
    sudo apt-get install -y nodejs

::

    curl -L https://npmjs.org/install.sh | sudo sh

::

    sudo npm install npm -g
    sudo npm install bower -g

2) Instalar o virtualenv usando Python 3 para o projeto
-----------------------------------------------------

Instale o `virtualenvwrapper <https://virtualenvwrapper.readthedocs.org/en/latest/install.html#basic-installation>`_:

::

    sudo pip3 install virtualenvwrapper

::

    sudo mkdir -p /var/interlegis/.virtualenvs

Ajuste as permissões:

::

    sudo chown -R $USER:$USER /var/interlegis/
    sudo chown -R $USER:$USER /home/$USER/
    

Edite o arquivo ``.bashrc``:

::

    vim /home/$USER/.bashrc

Adicione ao seu final as configurações abaixo para o ``virtualenvwrapper``:

::

    export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3
    export WORKON_HOME=/var/interlegis/.virtualenvs
    export PROJECT_HOME=/var/interlegis
    source /usr/local/bin/virtualenvwrapper.sh

Carregue as configurações do virtualenvwrapper:

::

    source /home/$USER/.bashrc

3) Clonar o projeto do GitHub, ou fazer um fork e depois clonar
------------------------------------------------------------

::

    cd /var/interlegis

::

    git clone git://github.com/interlegis/saap
    

Para fazer um fork e depois clonar, clique `aqui <https://help.github.com/articles/fork-a-repo>`_ e siga as instruções, que basicamente são:

    * Criar uma conta no GitHub - é gratuíto.
    * Acessar https://github.com/interlegis/saap e clicar em Fork.
    * Copiar o domínio que será criado um domínio, pelo qual será possível clonar, corrigir, customizar, melhorar, contribuir, entre outros.

::

    git clone git://github.com/[SEU NOME]/saap

As configurações e instruções de uso para o Git estão espalhadas pela Internet. As tarefas básicas de git e suas interações com GitHub são tranquilas de se aprender.

4) Criar o ambiente virtual de desenvolvimento para o SAAP
-------------------------------------------------------

::

    mkvirtualenv -a /var/interlegis/saap -p python3 -r requirements/requirements.txt saap

5) Configurar o banco de dados PostgreSQL
-----------------------------------------------------

Crie o usuário ``saap`` que será usado no banco. Caso você queira alterar a senha, fique a vontade - só lembre de informá-la no arquivo ``.env``:

::

    sudo -u postgres psql -c "CREATE ROLE saap LOGIN ENCRYPTED PASSWORD 'saap' SUPERUSER INHERIT CREATEDB NOCREATEROLE NOREPLICATION;"

    sudo -u postgres psql -c "ALTER ROLE saap VALID UNTIL 'infinity';"

    sudo -u postgres psql -c "CREATE DATABASE saap WITH OWNER = saap ENCODING = 'UTF8' TABLESPACE = pg_default LC_COLLATE = 'pt_BR.UTF-8' LC_CTYPE = 'pt_BR.UTF-8' CONNECTION LIMIT = -1 TEMPLATE template0;"

Altere também a senha do usuário ``postgres``:

::

    sudo -u postgres psql -c "ALTER ROLE postgres WITH ENCRYPTED PASSWORD 'postgres';"


Em seguida, é necessário editar o arquivo ``/etc/postgresql/[VERSÃO]/main/pg_hba.conf`` e alterar nas linhas finais a opção ``peer`` para ``md5``. 

::

    sudo vim /etc/postgresql/[VERSÃO]/main/pg_hba.conf


Então, reinicie o servidor:

::

    sudo /etc/init.d/postgresql restart

Para concluir, crie a função ``unaccent``, que será usada em diversas consultas dentro do SAAP:

::

    psql -U saap
    
    CREATE EXTENSION unaccent;

    exit;

No ambiente de desenvolvimento, a role deve ter permissão para criar outro banco. Isso é usado pelos testes automatizados.

Caso você já possua uma instalação do PostgreSQL anterior ao processo de instalação do ambiente de desenvolvimento do SAAP em sua máquina ou em outro servidor, e saiba como fazer, esteja livre para proceder como desejar. Porém, ao configurar o arquivo ``.env`` a seguir, as mesmas definições deverão ser usadas

6) Configurar permissões e arquivo de configuração
-----------------------------------------------------

Ajuste as permissões, onde $USER deve ser trocado pelo usuário:

::

    eval $(echo "sudo chown -R $USER:$USER /var/interlegis/")

Crie um arquivo ``.env`` dentro da pasta ``/var/interlegis/saap/``. 

::

    vim /var/interlegis/saap/.env

O mesmo terá o seguinte conteúdo:

::

    DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/NAME
    SECRET_KEY=[Insira este parâmetro]
    DEBUG=[True/False]
    DJANGO_TOOLBAR=[True/False]
    SITE_NAME='Sistema de Apoio à Atividade Parlamentar'
    SITE_DOMAIN=[Insira este parâmetro]
    EMAIL_USE_TLS=[Insira este parâmetro]
    EMAIL_PORT=[Insira este parâmetro]
    EMAIL_HOST=[Insira este parâmetro]
    EMAIL_SEND_USER=[Insira este parâmetro]
    EMAIL_HOST_USER=[Insira este parâmetro]
    EMAIL_HOST_PASSWORD=[Insira este parâmetro]
    DADOS_NOME=[Insira este parâmetro]
    DADOS_ENDERECO=[Insira este parâmetro]
    DADOS_MUNICIPIO=[Insira este parâmetro]
    DADOS_UF=[Insira este parâmetro]
    DADOS_CEP=[Insira este parâmetro]
    DADOS_EMAIL=[Insira este parâmetro]
    DADOS_TELEFONE=[Insira este parâmetro]
    DADOS_SITE=[Insira este parâmetro]
    BRASAO_PROPRIO=[True/False]

Onde:

    * Você deve preencher os dados do banco de dados
    * Para desenvolvimento, deixe as opções ``DEBUG`` e ``DJANGO_TOOLBAR`` em True
    * Informe os dados do servidor de e-mail
    * Preencha os dados da Câmara. Os mesmos serão utilizados no cabeçalho e rodapé da página. Além disto, informe corretamente o seu município e a UF, de forma ao sistema carregar corretamente os campos que dependem dessas informações
    * Caso você queria usar um brasão próprio na barra superior, coloque-o na pasta ``/var/interlegis/saap/saap/static/img``, com o nome de ``brasao-camara.png`` e ative com True. Deixando como False, o brasão exibido será o da República.

Como exemplo de arquivo ``.env``, veja:

::

    DATABASE_URL=postgresql://saap:saap@localhost:5432/saap
    SECRET_KEY='MUDE-PARA-RESULTADO-GENERATE-SECRET-KEY'
    DEBUG=True
    DJANGO_TOOLBAR=True
    SITE_NAME='Sistema de Apoio à Atividade Parlamentar'
    SITE_DOMAIN='saap.camaranh.rs.gov.br'
    EMAIL_USE_TLS=True
    EMAIL_PORT=
    EMAIL_HOST=
    EMAIL_SEND_USER=
    EMAIL_HOST_USER=
    EMAIL_HOST_PASSWORD=
    DADOS_NOME='Câmara Municipal de Novo Hamburgo'
    DADOS_ENDERECO='Rua Almirante Barroso, 261'
    DADOS_MUNICIPIO='Novo Hamburgo'
    DADOS_UF='RS'
    DADOS_CEP='93510-290'
    DADOS_EMAIL='camaranh@camaranh.rs.gov.br'
    DADOS_TELEFONE='(51) 3594-0500'
    DADOS_SITE='portal.camaranh.rs.gov.br'
    BRASAO_PROPRIO=True

7) Corrigir problemas de configuração em alguns pacotes
-----------------------------------------------------

Após a instalação, foram detectados alguns problemas em pacotes como o Django, Rest Framework, Bootstrap, entre outros. Obviamente esses problemas exigem uma análise mais aprofundada e uma solução mais precisa. Porém, para que o sistema possa funcionar corretamente, os arquivos com as devidas correções estão dentro da pasta ``config``, e devem ser copiados com os seguintes comandos:

Lembrando, antes, que [PYTHON] deve ser trocada pela pasta com a versão do Python que foi instalada - por exemplo, o Python 3.7.

* Django Models

::

    cp /var/interlegis/saap/config/django_db_models/base.py /var/interlegis/.virtualenvs/saap/lib/[PYTHON]/site-packages/django/db/models/


* Django Core Management

::

    cp /var/interlegis/saap/config/django_core_management/base.py /var/interlegis/.virtualenvs/saap/lib/[PYTHON]/site-packages/django/core/management/


* Rest Framework

::

    rm /var/interlegis/.virtualenvs/saap/lib/[PYTHON]/site-packages/rest_framework/* -R

    cp /var/interlegis/saap/config/rest_framework/* /var/interlegis/.virtualenvs/saap/lib/[PYTHON]/site-packages/rest_framework/ -R 

* Bootstrap 

::

    cp /var/interlegis/saap/config/bootstrap_admin/filter.html /var/interlegis/.virtualenvs/saap/lib/[PYTHON]/site-packages/bootstrap_admin/templates/admin/ 

* Smart Selects (usado para carregar os campos de Estado, Município, Bairro...)

::

    cp /var/interlegis/saap/config/smart-selects/* /var/interlegis/.virtualenvs/saap/lib/[PYTHON]/site-packages/smart_selects/static/smart-selects/admin/js/

* ReportLab (usado na geração de relatórios PDF)

::

    cp /var/interlegis/saap/config/reportlab/* /var/interlegis/.virtualenvs/saap/lib/[PYTHON]/site-packages/reportlab/platypus/
    
* Image Cropping

::

    cp /var/interlegis/saap/config/image_cropping/* /var/interlegis/.virtualenvs/saap/lib/[PYTHON]/site-packages/image_cropping/

8) Gerar a chave secreta
-----------------------------------------------------

Daqui pra frente, os comandos devem ser executados dentro da pasta ``/var/interlegis/saap``.

Para gerar a `SECRET_KEY <https://docs.djangoproject.com/es/1.9/ref/settings/#std:setting-SECRET_KEY>`_, rode o comando:

::

    ./manage.py generate_secret_key

Copie a chave para o arquivo ``.env``, na linha correspondente. O conteúdo deve estar entre aspas simples:

::

    SECRET_KEY='MUDE-PARA-RESULTADO-GENERATE-SECRET-KEY'

9) Carregar o banco de dados
-----------------------------------------------------

Inicialmente, atualize a base de dados, para refletir o modelo da versão clonada:

::

    ./manage.py migrate

Após isto, é necessário fazer a carga de dados básicos. Para isto, rode os comandos, na sequência:

::

    sudo -u postgres psql saap < config/initial_data/django_content_type.sql

::
   
    ./manage.py loaddata config/initial_data/*.json

Para concluir, é necessário criar o super-usuário, que terá permissão de admin. Ele solicitará e-mail e senha.

::

    ./manage.py createsuperuser

10) Configurar bower e arquivos estáticos
-----------------------------------------------------

Instale as dependências do ``bower``

::

    ./manage.py bower install

Por fim, atualize os arquivos estáticos. Lembre-se de colocar na pasta ``/var/interlegis/saap/saap/static/img`` o brasão do seu município, caso não queira usar o brasão da república. Para maiores dúvidas, leia o final da explicação sobre o arquivo ``.env``:

::

    ./manage.py collectstatic --noinput

Subir o servidor
-----------------------------------------------------

::
  
    ./manage.py runserver nome-do-servidor:8000

Fique à vontade para informar o nome do host/endereço IP, ou a porta que deseja. 

Para acessar o SAAP:

::

    http://nome-do-servidor:8000/

O painel de administração está disponível ao adicionar ``/admin`` no final do endereço:

::

    http://nome-do-servidor:8000/admin
