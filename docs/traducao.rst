***********************************************
Instruções para Tradução
***********************************************   

O Interlegis utiliza o `Transifex <https://www.transifex.com>`_  para gerenciar as traduções do projeto.
Se você deseja contribuir, por favor crie uma conta no site e peça para se juntar a eles em `Transifex SAAP Page <https://www.transifex.com/projects/p/saap>`_.
Assim que for aceito, você já pode começar a traduzir.

Para integrar as últimas traduções ao projeto atual, siga estes passos:

* Siga as instruções em `Development Environment Installation`_.

* Instale `Transifex Client <http://docs.transifex.com/client/config/>`_.

Aviso:

   O Transifex Client armazena senhas em 'plain text' no arquivo ``~/.transifexrc``.

   Recomenda-se logar no site do Transifex por meio de redes sociais (GitHub, Google Plus, Linkedin) e modificar, frequentemente, a senha utilizada pelo cliente.

* Realize `pull translations <http://docs.transifex.com/client/pull/>`_  ou `push translations <http://docs.transifex.com/client/push/>`_  usando o client. Faça o Pull somente com o repositório vazio, isto é, faça o commit de suas mudanças antes de fazer o pull de novas traduções.

* Execute o programa com ``.manage.py runserver`` e cheque o sistema para ver se as traduções tiveram efeito.

Nota:

  O idioma do browser é utilizado para escolher as traduções que devem mostradas.
