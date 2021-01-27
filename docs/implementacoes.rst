***********************************************
Orientações gerais de implementação e testes
***********************************************   

Boas Práticas
--------------

* Utilize a língua portuguesa em todo o código, nas mensagens de commit e na documentação do projeto.

* Mensagens de commit seguem o padrão de 50/72 colunas. Comece toda mensagem de commit com o verbo no infinitivo. Para mais informações, clique nos links abaixo:

  - http://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html
  - http://stackoverflow.com/questions/2290016/git-commit-messages-50-72-formatting

* Mantenha todo o código de acordo com o padrão da PEP8 (sem exceções).

* Antes de todo ``git push``:

  - Execute ``git pull --rebase`` (quase sempre).
  - Em casos excepcionais, faça somente ``git pull`` para criar um merge.

* Antes de ``git commit``, sempre:

  - Execute ``./manage.py check``
  - Execute todos os testes com ``py.test`` na pasta raiz do projeto

* Lembre-se que o usuário do banco de dados ``saap`` deve ter a permissão ``create database`` no postgres para que os testes tenham sucesso

* Faça o fork deste repositório e envie pull requests. Todos são bem-vindos para contribuir. Por favor, faça uma pull request separada para cada correção ou criação de novas funcionalidades.

* Novas funcionalidades estão sujeitas a aprovação, uma vez que elas podem ter impacto em várias pessoas. Nós sugerimos que você abra uma nova issue para discutir novas funcionalidades. Elas podem ser escritas tanto em Português, quanto em Inglês.


Implementações do model ``User``
--------------

Em caso de Implementação de modelo que envolva a classe ``django.contrib.auth.models.User``, não a use diretamente, use para isso a função ``get_settings_auth_user_model()`` de ``saap.utils``. Exemplo:

  - no lugar de ``owner = models.ForeignKey(User, ... )``
  - use ``owner = models.ForeignKey(get_settings_auth_user_model(), ... )``

Não use em qualquer modelagem futura, ``ForeignKey`` com ``User`` ou mesmo ``settings.AUTH_USER_MODEL`` sem o import correto que não é o do projeto e sim o que está em ``saap.utils``, ou seja (``from django.conf import settings``)

    - em https://docs.djangoproject.com/en/1.9/topics/auth/customizing/#referencing-the-user-model é explicado por que ser dessa forma!

Já em qualquer uso em implementação de execução, ao fazer uma query, por exemplo:

    - não use ``django.contrib.auth.models.User`` para utilizar as caracteristicas do model, para isso, use esta função: django.contrib.auth.get_user_model()

Seguir esses passos simplificará qualquer customização futura que venha a ser feita na autenticação do usuários ao evitar correções de inúmeros import's e ainda, desta forma, torna a funcionalidade de autenticação reimplementável por qualquer outro projeto que venha usar partes ou o todo do SAAP.

Testes
------

* Escrever testes para todas as funcionalidades que você implementar.

* Manter a cobertura de testes próximo a 100%.

Configure a variável do ambiente, para que seja possível executar os testes

::

    export DJANGO_SETTINGS_MODULE=saap.settings

Para executar todos os testes você deve entrar em seu virtualenv e executar este comando **na raiz do seu projeto**

::

    py.test

Para executar os teste de cobertura use

::

    py.test --cov . --cov-report term --cov-report html && firefox htmlcov/index.html

Na primeira vez que for executar os testes após uma migração (``./manage.py migrate``) use a opção de recriação da base de testes.

::

    py.test --create-db

É necessário fazer usar esta opção apenas uma vez.
