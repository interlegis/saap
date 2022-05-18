**********************************************
Implantação do SAAP com container Docker
**********************************************

Para implantar o SAAP utilizando o container docker, é necessário realizar os passos demonstrados nesse tutorial.

1) Instalar pacotes
----------------------------------------------------------------------------------------

Atualize o sistema:

:: 

    sudo apt-get update && sudo apt-get upgrade -y

Instale os pacotes:

::

    sudo apt-get install docker docker-compose -y


2) Preparar docker-compose
----------------------------------------------------------------------------------------

Após a instalação do docker, é necessário preparar o arquivo de configuração que fará o procedimento de instalação e configuração, tanto do SAAP quanto do banco de dados. 

Para isto, use o arquivo `docker-compose.yml <https://github.com/interlegis/saap/blob/master/docker/docker-compose.yml>`_ disponível aqui. O mesmo pode estar em qualquer localização que for desejada - nossa sugestão é mantê-lo em uma pasta /var/interlegis/docker

É importante verificar os seguintes itens:

- Se os mapeamentos de volume estão corretos
- Se a versão do SAAP referenciada no arquivo é a desejada - na dúvida, mantenha a expressão ``latest``
- Se os dados da seção environment condizem com a Casa Legislativa.
	
	- O campo ``SITE_DOMAIN`` deve conter o endereço que será usado para acessar o SAAP
	- Os campos ``EMAIL_*`` devem conter os dados corretos do servidor de e-mail, incluindo usuário/senha para envio de mensagens
	- Os campos ``DADOS_*`` são usados no rodapé do site
	- O campo ``BRASAO_PROPRIO`` exibe ou não um brasão personalizado. Caso ``False``, será usado o Brasão de Armas do Brasil. Caso ``True``, deverá ser feita a cópia do arquivo do brasão, conforme mostra a seção correspondente logo abaixo.
	- Os campos ``ADMIN_*`` devem conter os dados do primeiro usuário que será criado, com permissão de administração. Posteriormente é possível alterar o e-mail e/ou senha do mesmo.


3) Instalar imagens
----------------------------------------------------------------------------------------

Com o docker-compose preparado, é necessário rodar o seguinte comando, dentro da pasta onde está localizado o arquivo.

:: 

    sudo docker-compose up


O docker iniciará o download, instalação e configuração das imagens. Após alguns minutos, ao aparecer a palavra ``SAAP``, o Ngnix e o Gunicorn iniciarão o serviço. Então, basta testar se o sistema está funcionando.

Para rodar as imagens em background, deve-se primeiramente abortar a execução das imagens, apertando ``Ctrl + C``.

Então, basta rodar o ``docker-compose`` com a opção ``-d``:

::

    sudo docker-compose up -d


4) Atualizar o brasão
----------------------------------------------------------------------------------------

Se a opção ``BRASAO_PROPRIO`` está com ``True``, é necessário atualizar a imagem do brasão. Para isto, basta colocar a imagem desejada, em formado PNG, com o nome de ``brasao-camara.png``, e rodar o comando:

::

    docker cp brasao-camara.png saap:/var/interlegis/saap/saap/static/img/brasao-camara.png


Parar imagens
----------------------------------------------------------------------------------------


Para interromper a execução das imagens rodando em background, basta rodar:

::

    sudo docker-compose stop


Backup e restauração do banco
----------------------------------------------------------------------------------------

Para realizar o backup do banco do SAAP, basta rodar o seguinte comando:

::

    docker exec postgres pg_dump -U saap -v -Fc saap > ~/saap.dump

O destino e o nome do arquivo gerado são personalizáveis.

Para realizar a restauraçao do banco, é necessário previamente excluir o banco atual, para, então, fazer o processo:

::

    docker exec postgres psql -U postgres -c 'DROP DATABASE saap'
    docker exec postgres psql -U postgres -c "CREATE DATABASE saap ENCODING 'UTF8' template template0"

::

    docker cp saap.dump postgres:/tmp/
    docker exec postgres pg_restore -v -U saap -d saap /tmp/saap.dump

Atualizar imagem
----------------------------------------------------------------------------------------

Para atualizar a imagem, é necessário, primeiramente, fazer o backup do banco, conforme explicado acima. Então, basta rodar o comando abaixo:

::

    docker-compose up --force-recreate --build -d

Por fim, restaurar o brasão, conforme passo 4, e restaurar o banco, conforme explicado acima.
