# Docker

## Objetivo

Este documento define os padrões para criação e manutenção
de Dockerfiles e imagens Docker utilizados no SaaS ERP Platform.

Estas regras complementam:

```text
skills/infrastructure/README.md
skills/infrastructure/docker-compose.md
skills/database/
skills/01-project-structure.md
skills/02-architecture.md
1. Objetivo do Docker

Docker será utilizado para:

padronizar ambientes;
facilitar a execução local;
tornar serviços reproduzíveis;
isolar dependências;
simplificar a configuração do projeto;
preparar o sistema para diferentes ambientes.

Docker não substitui o código fonte versionado.

2. Dockerfile

Cada serviço que precisar de uma imagem própria
deve possuir seu Dockerfile.

Exemplos futuros:

backend/Dockerfile
frontend/Dockerfile
worker/Dockerfile

A localização deve seguir a estrutura oficial do projeto.

3. Responsabilidade do Dockerfile

O Dockerfile deve definir principalmente:

imagem base;
diretório de trabalho;
dependências;
arquivos necessários;
usuário;
comando de inicialização;
configuração mínima necessária para execução.

A orquestração dos serviços deve permanecer no:

docker-compose.yml
4. Imagem base

A imagem base deve ser escolhida de acordo
com o serviço.

Para o backend Python, utilizar uma imagem oficial
e compatível com a versão de Python definida pelo projeto.

Exemplo conceitual:

FROM python:<versão>

A versão deve ser explicitamente definida.

Não utilizar latest como padrão.

5. Versão do Python

O backend utiliza:

Python 3.13

O Dockerfile do backend deve utilizar uma versão compatível
com o ambiente Python definido em:

backend/.python-version
backend/pyproject.toml

O ambiente local e o ambiente do container não devem
utilizar versões incompatíveis sem uma decisão documentada.

6. uv

O backend utiliza uv para gerenciamento do ambiente
e das dependências Python.

A estratégia oficial de instalação e utilização do uv
dentro da imagem deve permanecer consistente com:

backend/pyproject.toml
backend/uv.lock

Quando possível, a instalação das dependências deve
utilizar o lockfile para garantir reprodutibilidade.

Não instalar dependências manualmente com uma sequência
de pip install que ignore o gerenciamento oficial
do projeto.

7. Lockfile

O arquivo:

backend/uv.lock

faz parte do código versionado e deve ser utilizado
para reproduzir as dependências do backend.

Quando as dependências forem alteradas:

pyproject.toml

e:

uv.lock

devem permanecer consistentes.

8. Diretório de trabalho

O Dockerfile deve definir um diretório de trabalho
claro para o serviço.

Exemplo conceitual:

WORKDIR /app

A estrutura interna do container deve ser simples
e previsível.

9. Cópia de arquivos

Copiar somente os arquivos necessários para
construir e executar o serviço.

Evitar copiar arquivos desnecessários para a imagem.

Exemplos que normalmente não devem ser enviados
para a imagem:

.git/
.venv/
.pytest_cache/
.ruff_cache/
__pycache__/
.env

O .dockerignore deve ser utilizado para impedir
o envio desses arquivos para o contexto de build.

10. .dockerignore

O backend deve possuir um:

.dockerignore

quando utilizar Dockerfile próprio.

Exemplo:

.venv/
__pycache__/
.pytest_cache/
.ruff_cache/
.coverage
htmlcov/
.git/
.gitignore
.env
*.pyc

O conteúdo deve ser ajustado conforme
os arquivos reais do serviço.

11. Secrets

Secrets nunca devem ser copiados para a imagem.

Nunca incluir:

.env
API keys
JWT secrets
database passwords
tokens
credentials

no processo normal de build.

Secrets devem ser fornecidos pelo ambiente
de execução.

12. Variáveis de ambiente

Configurações devem ser fornecidas através
de variáveis de ambiente.

Exemplos:

APP_ENV
DATABASE_URL
REDIS_URL
JWT_SECRET

O Dockerfile não deve possuir valores secretos
fixos para essas configurações.

13. Usuário do container

Sempre que possível, a aplicação deve executar
com um usuário não privilegiado.

Evitar executar a aplicação como root
quando isso não for necessário.

Exemplo conceitual:

RUN useradd ...
USER app

A implementação deve ser compatível com
as permissões necessárias pelo serviço.

14. Permissões

Os arquivos copiados para a imagem devem possuir
permissões adequadas ao usuário que executará
a aplicação.

Evitar:

chmod 777

ou permissões excessivamente amplas.

15. Dependências do sistema

Instalar somente dependências de sistema
necessárias para o serviço.

Evitar instalar ferramentas que não sejam
utilizadas durante build ou execução.

Exemplos que não devem ser adicionados
automaticamente:

editors
debuggers
compilers
shell utilities

quando não forem necessários.

16. Build reprodutível

O build da imagem deve ser reproduzível.

Utilizar:

versões explícitas;
lockfile;
imagens base controladas;
dependências declaradas;
configuração versionada.

Evitar depender de estado externo não documentado.

17. Camadas

Organizar o Dockerfile de maneira que etapas
que mudam com menor frequência possam ser
aproveitadas pelo cache do Docker.

Exemplo conceitual:

Imagem base
    ↓
Dependências
    ↓
Código da aplicação
    ↓
Comando

Evitar invalidar desnecessariamente o cache
a cada alteração no código.

18. Dependências antes do código

Quando apropriado, copiar primeiro:

pyproject.toml
uv.lock

e instalar as dependências antes de copiar
todo o código da aplicação.

Depois:

código

Isso permite melhor aproveitamento do cache.

19. Execução da aplicação

O Dockerfile deve definir um comando
de execução claro para o serviço.

Para o backend, o processo deverá executar
a aplicação FastAPI através do Uvicorn.

Exemplo conceitual:

uvicorn app.main:app

A configuração de host e porta deve ser compatível
com o ambiente Docker.

20. Host do backend

Quando o backend estiver em container e precisar
aceitar conexões de outros containers ou do host,
deve escutar na interface adequada.

Exemplo comum:

0.0.0.0

O uso de 127.0.0.1 dentro do container pode impedir
que outros containers consigam acessar o serviço.

21. Porta

A porta interna do serviço deve ser definida
de acordo com a aplicação.

O Dockerfile pode declarar a porta esperada
através de:

EXPOSE <porta>

A publicação da porta para o host permanece
responsabilidade do Docker Compose.

EXPOSE não substitui o mapeamento de portas
do Compose.

22. Healthcheck

Quando o serviço possuir uma forma apropriada
de verificar seu funcionamento, avaliar um
healthcheck.

No backend:

GET /health

pode ser utilizado como verificação da aplicação.

A configuração do healthcheck no ambiente de
orquestração deve permanecer consistente com
as regras de:

skills/infrastructure/docker-compose.md
23. Containers devem ser descartáveis

A aplicação não deve depender de modificações
manuais realizadas dentro do container.

Alterações permanentes devem existir no:

Dockerfile
docker-compose.yml
código
configuração versionada

Não considerar um container modificado manualmente
como fonte oficial da configuração.

24. Dados persistentes

O container da aplicação não deve ser utilizado
como armazenamento principal de dados persistentes.

Dados persistentes devem ficar em serviços apropriados,
como:

PostgreSQL

com volumes definidos pelo Compose.

25. PostgreSQL e Redis

PostgreSQL e Redis possuem seus próprios containers
de infraestrutura.

O Dockerfile do backend não deve instalar:

PostgreSQL
Redis

dentro da imagem do backend.

Arquitetura:

Backend
   |
   +---- PostgreSQL
   |
   +---- Redis

e não:

Backend
   |
   +---- PostgreSQL dentro da mesma imagem
   |
   +---- Redis dentro da mesma imagem
26. Um processo principal

Cada container deve possuir uma responsabilidade
principal clara.

Evitar utilizar um único container para executar:

FastAPI
PostgreSQL
Redis
Worker

simultaneamente.

Serviços independentes devem possuir containers
independentes quando isso fizer sentido.

27. Backend e Worker

Quando o worker for implementado, ele poderá utilizar
uma imagem compatível com o backend.

Dependendo da necessidade, poderá existir:

backend/Dockerfile

e uma configuração de Compose que execute
um processo diferente para o worker.

Não duplicar Dockerfiles sem necessidade.

28. Frontend

O frontend possuirá sua própria estratégia de imagem.

Não misturar:

React
Python
FastAPI

na mesma imagem.

O frontend deve possuir um processo e uma imagem
adequados à sua arquitetura.

29. Multi-stage builds

Quando fizer sentido, utilizar builds em múltiplos estágios.

Exemplo conceitual:

Build Stage
    |
    v
Runtime Stage

Objetivos:

reduzir tamanho da imagem final;
remover ferramentas de build desnecessárias;
reduzir superfície de ataque;
separar compilação de execução.

Não utilizar multi-stage apenas por complexidade;
utilizar quando houver benefício real.

30. Runtime

A imagem final deve conter somente o necessário
para executar o serviço.

Não incluir ferramentas utilizadas apenas
durante desenvolvimento quando não forem necessárias
em runtime.

31. Ambiente de desenvolvimento

O ambiente de desenvolvimento pode possuir
necessidades diferentes do ambiente de execução.

Exemplos:

hot reload
debug
ferramentas de desenvolvimento

Essas diferenças devem ser controladas de forma explícita.

Não copiar automaticamente toda a configuração
de desenvolvimento para uma imagem de produção.

32. Hot Reload

Quando o backend for executado com hot reload
durante o desenvolvimento, o código pode ser
montado como volume.

Exemplo conceitual:

Host
  |
  v
Container

Isso é uma preocupação do Compose,
não do Dockerfile.

33. Produção

O modo de produção não deve utilizar
automaticamente:

--reload

Hot reload é uma funcionalidade de desenvolvimento.

34. Logs

A aplicação deve escrever logs de forma compatível
com o ambiente de containers.

Preferir logs enviados para:

stdout
stderr

em vez de depender exclusivamente
de arquivos internos do container.

O padrão detalhado está em:

skills/observability/
35. Arquivos de log

Evitar armazenar logs importantes
somente em arquivos dentro do container.

Containers podem ser recriados.

Logs devem utilizar o mecanismo de observabilidade
definido pelo projeto.

36. Segurança

Antes de finalizar um Dockerfile, verificar:

Imagem base
Versão
Usuário
Permissões
Secrets
Dependências
Portas
Arquivos copiados

Não copiar arquivos sensíveis
para a imagem.

37. Tamanho da imagem

Evitar adicionar arquivos ou dependências
desnecessárias.

Avaliar:

imagem base
dependências
arquivos copiados
cache
ferramentas

Uma imagem menor normalmente reduz superfície
e tempo de transferência, mas tamanho não deve
ser otimizado sacrificando clareza ou segurança.

38. Atualização da imagem base

A imagem base deve possuir uma versão explícita.

Antes de atualizar:

Python
Node
PostgreSQL
Redis

verificar compatibilidade com o projeto.

Não utilizar atualização automática sem controle
da versão.

39. Build

Quando o Dockerfile for alterado, validar:

docker build .

ou, quando integrado ao Compose:

docker compose build

A estratégia de build deve seguir
a configuração do serviço.

40. Execução

Após o build, validar:

container inicia
serviço responde
healthcheck funciona
logs aparecem
conexões funcionam

Quando o backend depender de PostgreSQL ou Redis,
validar a comunicação através da configuração
do Docker Compose.

41. Alterações no Dockerfile

Antes de alterar um Dockerfile:

verificar o Dockerfile atual;
verificar o .dockerignore;
verificar o docker-compose.yml;
verificar variáveis de ambiente;
verificar dependências;
verificar impacto no runtime;
consultar esta skill;
validar o build.
42. Não esconder problemas

Não utilizar Docker para esconder problemas
da aplicação.

Exemplos:

instalar dependência aleatória
ignorar erro de import
executar como root sem necessidade
copiar toda a máquina para a imagem

O container deve executar uma aplicação
que esteja corretamente configurada.

43. Regra para Python

O backend utiliza:

Python 3.13
uv
FastAPI

A imagem deve manter consistência com
o ambiente local.

Referências:

backend/pyproject.toml
backend/uv.lock
backend/.python-version
44. Regra para novos Dockerfiles

Antes de criar um Dockerfile:

Qual serviço será executado?

Qual é a imagem base?

Quais dependências são necessárias?

Quais arquivos precisam entrar na imagem?

Qual usuário executará o processo?

Qual comando iniciará o serviço?

Qual porta será utilizada?

Existe healthcheck?

Existem secrets?

Existe necessidade de multi-stage?
45. Princípio final

Um Dockerfile deve ser:

simples
+
reproduzível
+
seguro
+
pequeno quando possível
+
explícito
+
versionado

O objetivo não é criar uma imagem sofisticada.

O objetivo é criar uma imagem previsível,
segura e adequada à responsabilidade do serviço.


### Local exato

```text
C:\Users\joao\Projetos\saas-erp-platform\skills\infrastructure\docker.md