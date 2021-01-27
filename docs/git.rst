De forma muito simples e em linhas gerais, o básico sobre Git e GitHub:

Glossário
---------

* Git - Sistema de controle de versão de aquivos
  
* GitHub - É um serviço web que oferece diversas funcionalidades extras aplicadas ao git

* Branch - Significa ramificar seu projeto, criar um snapshot.
  
* Merge - Significa incorporar seu branch no master


Comandos
-------------

Atualizar a base local:

::

    git pull --rebase git://github.com/ojonathacardoso/saap

Exibir informações:

::
  
    git status
 
 
Ver repositorio
  
::

    git remote -v


Para definir repositorio

::

    git remote set-url origin https://github.com/ojonathacardoso/saap.git


Para criar um branch
  
::

    git checkout -b nome_branch
    git add arquivos

Para remover um branch

::
  
    git branch -d nome-branch

Para comitar

::
  
    git commit -m "Comentário"

Para enviar o branch
  
::

    git push origin nome_branch


Na base local, para descartar alguma alteração feita nos arquivos:

::
  
    git checkout -- <arquivo>
  
Para, ao invés disso, remover todas as alterações e commits locais, recuperar o histórico mais recente do servidor e apontar para seu branch master local:
  

::
  
    git fetch origin
    git reset --hard origin/master

Para atualizar para alguma brach específica:

::

    git checkout branch

Para voltar para a branch master
  
::
  
    git checkout master

Para verificar 5 ultimos comits:

::

    git log --oneline -n 5

Referências
-------------
  
*`http://rogerdudler.github.io/git-guide/index.pt_BR.html`
*`http://tableless.com.br/tudo-que-voce-queria-saber-sobre-git-e-github-mas-tinha-vergonha-de-perguntar/`
