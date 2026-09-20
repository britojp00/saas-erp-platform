# Infrastructure Skills

## Objetivo

Esta pasta contém os padrões, regras e procedimentos
relacionados à infraestrutura do SaaS ERP Platform.

As definições desta área devem ser utilizadas sempre que
uma tarefa envolver:

- Docker;
- Docker Compose;
- containers;
- PostgreSQL;
- Redis;
- volumes;
- redes;
- portas;
- healthchecks;
- variáveis de ambiente;
- configuração de serviços;
- ambiente de desenvolvimento;
- execução local da aplicação.

---

# 1. Infraestrutura principal

O ambiente do projeto será baseado em containers.

Componentes principais planejados:

```text
Frontend
Backend
PostgreSQL
Redis
Workers

Arquitetura conceitual:

                Docker Compose
                     |
      ┌──────────────┼──────────────┐
      |              |              |
      v              v              v
  Frontend        Backend       PostgreSQL
                     |
                     v
                   Redis
                     |
                     v
                  Workers

Os serviços serão adicionados conforme a evolução
do projeto.

2. Docker

Docker será utilizado para tornar o ambiente reproduzível
entre diferentes máquinas e ambientes.

O projeto não deve depender de instalações manuais
específicas na máquina do desenvolvedor quando o serviço
puder ser executado através de container.

Exemplos de serviços que serão executados através
do Docker:

PostgreSQL
Redis
Backend
Frontend
Workers
3. Docker Compose

O arquivo principal de orquestração será:

docker-compose.yml

Localização:

saas-erp-platform/docker-compose.yml

O Docker Compose será responsável por definir:

serviços;
imagens;
builds;
portas;
volumes;
redes;
variáveis de ambiente;
dependências entre serviços;
healthchecks.
4. Serviços

Cada serviço deve possuir uma responsabilidade clara.

Exemplo:

postgres
→ banco de dados

redis
→ cache e recursos temporários

backend
→ API

frontend
→ interface

worker
→ processamento assíncrono

Não criar containers separados apenas por organização
quando não houver uma necessidade real.

5. PostgreSQL

O PostgreSQL será executado através de container.

Responsabilidade:

persistência principal dos dados do ERP

O banco não deve depender de uma instalação manual
do PostgreSQL no Windows para o ambiente padrão do projeto.

6. Redis

Redis será executado através de container.

Responsabilidades planejadas:

cache;
dados temporários;
rate limiting;
suporte a processamento assíncrono;
suporte a workers.

Redis não substitui PostgreSQL como banco principal.

7. Volumes

Dados persistentes devem utilizar volumes apropriados.

Exemplo conceitual:

PostgreSQL
    |
    v
Docker Volume
    |
    v
dados persistentes

Não armazenar dados persistentes exclusivamente
na camada efêmera do container.

Ao remover e recriar um container, os dados persistentes
não devem ser perdidos quando o serviço possuir persistência.

8. Código da aplicação

O código fonte do projeto deve permanecer fora
do container como fonte primária durante o desenvolvimento.

O container deve receber ou montar o código
conforme a estratégia definida para cada serviço.

Não utilizar containers como única localização
do código fonte.

9. Redes

Os serviços do Docker Compose devem conseguir se comunicar
através da rede interna do Compose quando necessário.

Exemplo:

backend
   |
   +---- postgres
   |
   +---- redis

O backend deve utilizar os nomes dos serviços para comunicação
interna quando essa estratégia estiver definida.

Não depender de endereços IP internos fixos dos containers.

10. Portas

Portas expostas ao host devem ser definidas
somente quando forem necessárias.

Exemplo:

Backend
8000

Frontend
porta definida pelo frontend

PostgreSQL
5432 quando acesso direto do host for necessário

Redis
6379 quando acesso direto do host for necessário

Serviços que somente precisam ser acessados
internamente devem preferencialmente permanecer
na rede interna.

11. Variáveis de ambiente

Configurações dependentes do ambiente devem utilizar
variáveis de ambiente.

Exemplos:

DATABASE_URL
REDIS_URL
JWT_SECRET
APP_ENV

Credenciais não devem ser armazenadas diretamente
em arquivos versionados.

12. .env

O arquivo:

.env

é destinado à configuração local.

Ele não deve ser versionado.

O arquivo:

.env.example

deve apresentar as variáveis necessárias
sem expor valores secretos reais.

13. Secrets

Nunca colocar em:

Dockerfile
docker-compose.yml
código Python
código TypeScript
README
logs

valores secretos reais.

Exemplos:

passwords
JWT secrets
API keys
database credentials
tokens
14. .env.example

O .env.example deve:

listar as variáveis necessárias;
utilizar valores de exemplo;
documentar configurações importantes;
não conter credenciais reais.

Exemplo:

DATABASE_URL=postgresql+asyncpg://erp:erp@postgres:5432/erp
REDIS_URL=redis://redis:6379/0
JWT_SECRET=change-me
APP_ENV=development

Os valores reais devem permanecer no ambiente local.

15. Healthchecks

Serviços críticos devem possuir healthchecks quando
isso for necessário para determinar se estão realmente
disponíveis.

Exemplo conceitual:

PostgreSQL
    |
    v
healthcheck
    |
    v
healthy

O estado do container estar running não deve ser
considerado automaticamente equivalente a serviço saudável.

16. Dependências entre serviços

Quando um serviço depender de outro, essa dependência
deve ser configurada de forma explícita quando necessário.

Exemplo:

Backend
   |
   +---- PostgreSQL
   |
   +---- Redis

A inicialização deve considerar não apenas a ordem
de criação dos containers, mas a disponibilidade
real do serviço quando isso for necessário.

17. Backend e PostgreSQL

Durante o desenvolvimento:

Backend
   |
   | DATABASE_URL
   v
PostgreSQL

A aplicação deve utilizar variáveis de ambiente
para descobrir o endereço do banco.

Não fixar credenciais ou hosts específicos
diretamente no código.

18. Backend e Redis

Durante o desenvolvimento:

Backend
   |
   | REDIS_URL
   v
Redis

A conexão deve ser configurável através
do ambiente.

19. Ambiente de desenvolvimento

O ambiente local deve ser reproduzível.

Um novo desenvolvedor deve conseguir, com a documentação
do projeto:

1. obter o código;
2. configurar variáveis;
3. iniciar os serviços;
4. executar migrations;
5. executar o backend;
6. executar testes.

Evitar depender de configurações manuais que não estejam
documentadas.

20. Execução local

A infraestrutura deverá permitir posteriormente
um fluxo semelhante a:

docker compose up -d
        |
        +---- PostgreSQL
        +---- Redis
        +---- Backend
        +---- Frontend

O fluxo final será definido conforme cada serviço
for incorporado ao projeto.

21. Desenvolvimento do backend

Durante o desenvolvimento, o backend pode continuar
sendo executado diretamente pelo ambiente Python:

uv
+
Python
+
FastAPI

enquanto os serviços de infraestrutura,
como PostgreSQL e Redis, permanecem em containers.

Exemplo:

Windows
   |
   +---- uv / Python
   |       |
   |       +---- FastAPI
   |
   +---- Docker
           |
           +---- PostgreSQL
           +---- Redis

A estratégia de execução totalmente containerizada
será definida posteriormente.

22. Dockerfile

Quando um serviço possuir Dockerfile,
ele deve ser específico para a responsabilidade daquele serviço.

Não utilizar um único Dockerfile genérico para todos
os componentes sem necessidade.

Exemplo futuro:

backend/Dockerfile
frontend/Dockerfile

A localização final deverá seguir a organização
definida na skill de estrutura do projeto.

23. Imagens

As imagens utilizadas devem ser:

oficiais quando apropriado;
conhecidas;
versionadas;
compatíveis com o projeto.

Evitar utilizar:

latest

como estratégia padrão para dependências de infraestrutura
quando isso puder causar builds imprevisíveis.

Preferir versões explicitamente definidas.

24. Atualização de versões

Atualizações de imagens e serviços devem ser realizadas
de forma consciente.

Antes de atualizar:

PostgreSQL
Redis
Python
Node

verificar compatibilidade com o projeto.

Não atualizar múltiplos componentes de infraestrutura
simultaneamente sem necessidade.

25. Persistência

Serviços que armazenam dados persistentes devem possuir
estratégia explícita de persistência.

Exemplo:

PostgreSQL
   |
   v
Named Volume

O projeto não deve depender do armazenamento interno
efêmero de containers para dados que precisam sobreviver
à recriação do serviço.

26. Backup

O ambiente de desenvolvimento não deve ser considerado
um mecanismo de backup.

Volumes Docker não substituem uma estratégia de backup
quando os dados forem importantes.

Procedimentos de backup para outros ambientes
serão documentados separadamente caso sejam necessários.

27. Logs de containers

Logs dos serviços devem permanecer disponíveis
para investigação.

Exemplo:

docker compose logs backend
docker compose logs postgres
docker compose logs redis

Os logs de aplicação devem seguir as regras
definidas em:

skills/observability/
28. Segurança de containers

Evitar:

executar processos como root quando não for necessário;
expor portas sem necessidade;
armazenar secrets na imagem;
copiar arquivos sensíveis para a imagem;
utilizar credenciais fixas;
adicionar ferramentas desnecessárias à imagem.
29. Desenvolvimento com Docker

Não modificar containers manualmente esperando
que a alteração seja permanente.

Quando uma configuração precisar ser reproduzida,
ela deve ser expressa em:

Dockerfile
docker-compose.yml
variáveis de ambiente
configuração versionada

A configuração manual dentro de um container não
deve ser considerada parte do estado oficial do projeto.

30. Rebuild

Quando arquivos que fazem parte da imagem forem alterados,
o serviço deve ser reconstruído conforme necessário.

Exemplo:

Dockerfile alterado
    |
    v
docker compose build

Não assumir que um container antigo contém
automaticamente as alterações da imagem.

31. Desenvolvimento e produção

As configurações de desenvolvimento e produção
não devem ser misturadas indiscriminadamente.

Diferenças relevantes devem ser documentadas
quando existirem.

O ambiente local deve priorizar:

facilidade
+
reprodutibilidade
+
segurança
32. Testes da infraestrutura

Quando alterações de infraestrutura afetarem
o comportamento da aplicação, considerar testes
e validações apropriadas.

Exemplos:

PostgreSQL disponível
Redis disponível
Backend consegue conectar
Migrations executam
Healthchecks funcionam
33. Alterações no Docker Compose

Antes de modificar docker-compose.yml:

verificar serviços existentes;
verificar dependências;
verificar volumes;
verificar redes;
verificar portas;
verificar variáveis;
verificar healthchecks;
verificar impacto no ambiente;
consultar skills específicas de infraestrutura.
34. Novos serviços

Antes de adicionar um novo container:

Qual problema ele resolve?
É realmente necessário?
Existe serviço existente que já resolve?
Qual o impacto no ambiente?
Possui persistência?
Possui healthcheck?
Precisa ficar exposto ao host?

Não adicionar infraestrutura somente para aumentar
a complexidade ou quantidade de tecnologias do projeto.

35. Ordem de evolução

A infraestrutura será adicionada gradualmente.

Ordem planejada:

1. PostgreSQL
2. Redis
3. Backend containerizado
4. Frontend containerizado
5. Workers
6. Outros serviços necessários

A ordem pode ser alterada caso exista uma necessidade
técnica justificada.

36. Documentação específica

As regras detalhadas podem ser divididas em:

skills/infrastructure/
├── README.md
├── docker.md
├── docker-compose.md
└── environment.md
docker.md

Padrões específicos para Dockerfiles e imagens.

docker-compose.md

Padrões específicos para serviços, redes, volumes,
healthchecks e comunicação entre containers.

environment.md

Padrões para variáveis, ambientes e configuração.

37. Regra para infraestrutura

Antes de adicionar ou alterar infraestrutura:

Identificar necessidade
        |
        v
Verificar infraestrutura existente
        |
        v
Consultar skill específica
        |
        v
Implementar
        |
        v
Validar
        |
        v
Documentar quando necessário
38. CI/CD (GitHub Actions)

O projeto utiliza GitHub Actions para integração contínua.

Workflow principal:

.github/workflows/ci.yml

39. Triggers

O CI é executado em:

push para master
pull request para master

40. Jobs

O workflow possui um único job ci que executa:

1. Checkout do código
2. Configuração do Python 3.13
3. Instalação do uv
4. Instalação de dependências (uv sync --frozen)
5. Ruff check
6. Ruff format check
7. Alembic check
8. Alembic upgrade head
9. pytest
10. Docker build

41. PostgreSQL no CI

O CI utiliza GitHub Actions services para PostgreSQL 17.

Configuração:

image: postgres:17-alpine
POSTGRES_DB: saas_erp_ci
POSTGRES_USER: postgres
POSTGRES_PASSWORD: postgres

O banco de teste é criado automaticamente pelo conftest.py.

42. Variáveis de ambiente do CI

Definidas no workflow:

APP_ENV=test
APP_TIMEZONE=America/Sao_Paulo
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/saas_erp_ci
REDIS_URL=redis://localhost:6379/0
JWT_SECRET_KEY=ci-test-secret-key-do-not-use-in-production

Nenhum secret real é utilizado.

43. Redis no CI

Redis NÃO é necessário para a suíte atual.

A variável REDIS_URL é fornecida apenas para satisfazer
a configuração obrigatória do pydantic-settings.

44. Dockerfile

O backend possui Dockerfile propio:

backend/Dockerfile

O CI executa docker build para validar que a aplicação
é empacotável. A imagem não é enviada para registry.

45. Cache

O CI utiliza cache do uv via astral-sh/setup-uv.

46. CD

O deploy automático ainda não foi implementado.

O proximo estara podera incluir:

GitHub -> CI -> Docker image -> Registry -> Deploy -> Health check

47. Princípio final

A infraestrutura deve ser:

reproduzível
+
segura
+
simples
+
versionada
+
observável
+
manutenível

Não adicionar complexidade sem uma necessidade técnica clara.


### Local exato

```text
C:\Users\joao\Projetos\saas-erp-platform\skills\infrastructure\README.md