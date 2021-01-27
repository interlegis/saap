***********************************************
Atualização da versão do SAAP
***********************************************

Para atualizar o SAAP para a última versão disponível, são feitos os seguintes passos - lembrando que, daqui pra frente, os comandos devem ser executados dentro da pasta ``/var/interlegis/saap``:

1) Verificar atualizações locais
----------------------------------------------------------------------------------------

Acesse a pasta do SAAP e verificar se houve alguma alteração.

::

    workon saap
    git status


O Git retornará todos os arquivos que sofreram alteração. É importante analisar as alterações feitas e verificar se, ao buscar a atualização do repositório, não haverá nenhum conflito de arquivos/versões.

2) Executar atualização
----------------------------------------------------------------------------------------

Primeiro, vamos buscar os arquivos do repositório. Para isto, você deve entrar, antes, no ambiente virtual, rodando os comandos citados no passo 1.

::

    git pull


Após a atualização, caso nenhum erro tenha sido apresentado, é necessário atualizar o banco de dados:

::

    ./manage.py migrate

Para concluir, basta reiniciar o Supervisor:

::

    sudo supervisorctl restart all

O SAAP deverá estar funcionando e atualizado.
