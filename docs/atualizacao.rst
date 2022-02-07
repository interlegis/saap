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

Em seguida, caso nenhum erro tenha sido apresentado, é necessário atualizar o banco de dados:

::

    ./manage.py migrate


3) Verificar alterações necessárias conforme release
----------------------------------------------------------------------------------------

Após a atualização, é importante verificar na release lançada se exise algum procedimento que deva ser realizado, como a atualização de arquivos ou instalação/atualização de programas.

4) Reiniciar sistema
----------------------------------------------------------------------------------------

Para concluir, basta reiniciar o Supervisor:

::

    sudo supervisorctl restart all

O SAAP deverá estar funcionando e atualizado.

Caso ocorreram modificações de layout, e a página ainda apareça com as configurações antigas, atualize a página usando Ctrl + Shift + R
