***********************************************
Instalação do Ambiente de Produção
***********************************************

Para efeitos deste documento, foram consideradas as tecnologias NGINX + Gunicorn + Supervisor para servir a aplicação Django SAAP.

O NGINX é o servidor WEB, o Gunicorn é o servidor da aplicação para o servidor Web, e o Supervisor é o serviço que ativa o Gunicorn automaticamente.

Daqui pra frente, os comandos devem ser executados dentro da pasta ``/var/interlegis/saap``.

1) Desativar modo debug
----------------------------------------------------------------------------------------

É altamente recomendável que, para produção, o SAAP não seja executado em modo debug. Para isso edite o arquivo ``.env`` criado anteriormente (``/var/interlegis/saap/.env``) e altere as opções:

::

    DEBUG = False
    DEBUG_TOOLBAR = False

2) Preparar arquivos estáticos
----------------------------------------------------------------------------------------

Com o ambiente em produção, os arquivos estáticos devem ser servidos pelo web service em ambiente de produção - em nosso caso, o NGINX. Para tanto, rode:

::

    sudo rm collected_static/styles/*
    ./manage.py collectstatic --no-input --clear

Com isto, ele coletará todos os arquivos estáticos do projeto e os guardará no diretório no qual o NGINX irá referenciar para a aplicação.


3) Instalar pacotes
----------------------------------------------------------------------------------------   

Instale o NGINX:

::

    sudo apt-get install nginx -y

Em seguida, instale o Gunicorn:

:: 

    sudo pip3 install gunicorn  

Por fim, instale o Supervisor:

::

    sudo apt-get install supervisor -y


3) Preparar o NGINX
----------------------------------------------------------------------------------------   

Crie o arquivo de configuração:

::

    sudo vim /etc/nginx/sites-available/saap.conf

Seu conteúdo deve ser o seguinte:

::

    server {
        listen 80;
        access_log /var/log/nginx-access.log;
        error_log /var/log/nginx-error.log;

        server_name [SERVERNAME];

        location / {
            proxy_pass http://127.0.0.1:8000;

            # As proximas linhas passam o IP real para o Gunicorn nao achar que são acessos locais
            proxy_pass_header Server;
            proxy_set_header X-Forwarded-Host $server_name;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header Host $http_host;
         }

         location /static {
             alias /var/interlegis/saap/collected_static;
         }

    }

Onde você deve preencher o nome do servidor no lugar de [SERVERNAME]

Lembre-se de criar a pasta onde ficarão os logs do SAAP e dar as permissões:

::

    sudo mkdir /var/log/saap
    sudo touch /var/log/saap/access.log
    sudo touch /var/log/saap/error.log
    sudo chown $USER:$USER /var/log/saap/*
    sudo chmod 755 /var/log/saap/*

Em seguida, é necessário criar o link simbólico para este arquivo que criamos. Antes, porém, é necessário excluir o arquivo ``default``, para que o SAAP seja o único site do NGINX. Salientando, novamente, que você pode configurar o NGINX da forma que preferir - este é apenas a forma básica pra termos nosso servidor pronto.

::

    sudo rm /etc/nginx/sites-enabled/default
   
    sudo ln -s /etc/nginx/sites-available/saap.conf /etc/nginx/sites-enabled/saap

4) Preparar o Gunicorn
----------------------------------------------------------------------------------------   
   
Nesse passo, você deve estar atento para duas variáveis, que podem ser manipuladas:

  * Workers: Cálculo que leva em base o número de processadores, sendo ``2 * CPU + 1``. Ou seja, para uma máquina de 1 CPU, seriam 3 workers. Faça o cálculo e substitua o [WORKERS] pelo valor desejado.
  * Timeout: Após diversos testes, verificou-se que determinados relatórios, devido à quantidade de registros e à montagem do conteúdo, passava do timeout padrão. Desta forma, definiu-se o valor de 960 para evitar problemas.

Dito isto, crie dentro de ``/var/interlegis/saap`` um arquivo chamado ``gunicorn_conf``, com o seguinte conteúdo:

::

    bind = "127.0.0.1:8000"
    logfile = "/var/log/gunicorn.log"
    workers = [WORKERS]
    limit_request_line = 0
    timeout = 960

Em seguida, edite o arquivo ``/var/interlegis/saap/gunicorn_start.sh`` e altere os parâmetros ``WORKERS`` E ``TIMEOUT`` conforme desejado:

::

    NUM_WORKERS=[WORKERS]
    TIMEOUT=960

4) Testar o servidor
---------------------------------------------------------------------------------------- 

Reinicie o servidor:

::
  
    sudo service nginx restart

Dentro da pasta ``/var/interlegis/saap``, execute o comando:

::

    ./gunicorn_start.sh

O SAAP deverá estar funcionando em ``http://[ENDERECO_SITE]`` ou em ``http://localhost``


5) Preparar o Supervisor
---------------------------------------------------------------------------------------- 

Como você deve ter percebido, o servidor só funciona enquanto o arquivo ``gunicorn_start.sh`` está em execução. Para não precisar disto, e pro NGINX + Gunicorn funcionar automaticamente ao ligar o servidor, usaremos o Gunicorn.

Crie o arquivo de configuração relacionado ao Gunicorn:

::

    sudo vim /etc/supervisor/conf.d/gunicorn.conf

Insira o seguinte conteúdo:

::

    [program:gunicorn]
    command=/var/interlegis/.virtualenvs/saap/bin/gunicorn saap.wsgi:application -c /var/interlegis/saap/gunicorn_conf
    directory=/var/interlegis/saap
    autostart=true
    autorestart=true
    redirect_stderr=true

Após isto, atualize o Supervisor para ler os arquivos inseridos:

::

    sudo supervisorctl reread
    sudo supervisorctl update

Por fim, reinicie o Supervisor, para iniciar o sistema

::

    sudo supervisorctl restart all

O SAAP deverá estar funcionando em ``http://[ENDERECO_SITE]`` ou em ``http://localhost``
