***********************************************
Orientações gerais de implementação e testes
***********************************************   

Aviso
-------------
Tais orientações são replicações das mesmas orientadas no SAPL. Entretanto, as mesmas ainda não estão totalmente ativas - principalmente o teste.


Boas Práticas
--------------

* Utilize a língua portuguesa em todo o código, nas mensagens de commit e na documentação do projeto.

* Mensagens de commit seguem o padrão de 50/72 colunas. Comece toda mensagem de commit com o verbo no infinitivo. Para mais informações, clique nos links abaixo:

  - http://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html
  - http://stackoverflow.com/questions/2290016/git-commit-messages-50-72-formatting

* Mantenha todo o código de acordo com o padrão da PEP8 (sem exceções).

* Faça o fork deste repositório e envie pull requests. Todos são bem-vindos para contribuir. Por favor, faça uma pull request separada para cada correção ou criação de novas funcionalidades.

* Novas funcionalidades estão sujeitas a aprovação, uma vez que elas podem ter impacto em várias pessoas. Nós sugerimos que você abra uma nova issue para discutir novas funcionalidades. Elas devem ser escritas preferencialmente em Português.

* Em caso de Implementação de modelo que envolva a classe ``django.contrib.auth.models.User``:
  - Não a use diretamente, use para isso a função ``get_settings_auth_user_model()`` de ``saap.utils``. Por exemplo, no lugar de ``owner = models.ForeignKey(User, ... )``, use ``owner = models.ForeignKey(get_settings_auth_user_model(), ... )``.
  - Não use em qualquer modelagem futura, ``ForeignKey`` com ``User`` ou mesmo ``settings.AUTH_USER_MODEL`` sem o import correto que não é o do projeto e sim o que está em ``saap.utils``, ou seja (``from django.conf import settings``). Em https://docs.djangoproject.com/en/1.9/topics/auth/customizing/#referencing-the-user-model é explicado por que ser dessa forma!
  - Em qualquer uso em implementação de execução, ao fazer uma query, por exemplo, não use ``django.contrib.auth.models.User`` para utilizar as caracteristicas do model, para isso, use esta função: django.contrib.auth.get_user_model()
  - Seguir esses passos simplificará qualquer customização futura que venha a ser feita na autenticação do usuários ao evitar correções de inúmeros import's e ainda, desta forma, torna a funcionalidade de autenticação reimplementável por qualquer outro projeto que venha usar partes ou o todo do SAAP.

Sincronização do ambiente de desenvolvimento
______________

* Antes de começar a atualizar, execute o arquivo ``sync.sh`` na raiz do projeto, para buscar eventuais atualizações.
 
* Antes de enviar atualizações, sempre execute ``./manage.py check`` para verificar algum problema.

* Para enviar as atualizações, execute o arquivo ``release.sh``, que além de atualizar em seu repositório fork, também atualiza o número da versão do sistema.

Testes após desenvolvimento
------

Ainda é necessário implementar e testar corretamente a rotina de testes de funcionalidades no SAAP. Para isto, usar como base as orientações do `SAPL <https://github.com/interlegis/sapl/blob/3.1.x/docs/implementacoes.rst#testes>`_.
