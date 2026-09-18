# Docker Compose

## Objetivo

Este documento define os padrões oficiais para utilização
do Docker Compose no SaaS ERP Platform.

O Docker Compose será utilizado para orquestrar os serviços
necessários para executar o sistema localmente e,
quando apropriado, em outros ambientes.

---

# 1. Arquivo principal

O arquivo principal será:

```text
docker-compose.yml

Localização:

saas-erp-platform/docker-compose.yml

O arquivo deve permanecer na raiz do projeto.

2. Serviços planejados

A infraestrutura será composta gradualmente pelos seguintes
serviços:

postgres
redis
backend
frontend
worker

Nem todos os serviços precisam existir desde a primeira versão.

Os serviços devem ser adicionados conforme forem
necessários para o sistema.

3. Responsabilidade de cada serviço
postgres

Responsável pela persistência principal do ERP.

postgres
    |
    v
PostgreSQL
redis

Responsável por recursos temporários e infraestrutura
auxiliar.

Usos planejados:

cache;
rate limiting;
dados temporários;
suporte a processamento assíncrono;
suporte aos workers.
backend

Responsável pela API e regras de negócio.

Tecnologias:

Python
FastAPI
frontend

Responsável pela interface web.

Tecnologias planejadas:

React
TypeScript
Vite
worker

Responsável por tarefas executadas em segundo plano.

Exemplo:

API
 |
 v
Queue
 |
 v
Worker
 |
 v
Processamento

O mecanismo específico de filas será definido
quando o processamento assíncrono for implementado.

4. Arquitetura dos serviços

Estrutura planejada:

                         ┌─────────────────┐
                         │    Frontend     │
                         └────────┬────────┘
                                  |
                                HTTP
                                  |
                                  v
                         ┌─────────────────┐
                         │     Backend     │
                         │     FastAPI     │
                         └────────┬────────┘
                                  |
                     ┌────────────┴────────────┐
                     |                         |
                     v                         v
              ┌─────────────┐          ┌─────────────┐
              │ PostgreSQL  │          │    Redis    │
              └─────────────┘          └──────┬──────┘
                                               |
                                               v
                                           Worker
5. Network

Os serviços do Compose devem compartilhar
uma rede interna quando precisarem se comunicar.

Exemplo conceitual:

erp-network

├── backend
├── postgres
├── redis
├── frontend
└── worker

Os serviços devem comunicar-se utilizando
o nome do serviço como hostname.

Exemplo:

postgres

e não um endereço IP fixo.

6. Não utilizar IP fixo

Não configurar comunicação interna utilizando
IPs fixos dos containers.

Evitar:

172.x.x.x

como endereço permanente de outro serviço.

Utilizar:

postgres
redis
backend

conforme o nome do serviço definido no Compose.

7. PostgreSQL

O PostgreSQL será um serviço do Compose.

Exemplo conceitual:

services:

  postgres:
    image: postgres:<versão-definida>

A versão deve ser explicitamente definida.

Não utilizar:

postgres:latest

como padrão do projeto.

8. Persistência do PostgreSQL

O PostgreSQL deve utilizar um volume nomeado.

Exemplo:

volumes:

  postgres_data:

e:

services:

  postgres:
    volumes:
      - postgres_data:/var/lib/postgresql/data

O objetivo é preservar os dados quando o container
for recriado.

9. Redis

Redis deverá utilizar uma imagem com versão explicitamente
definida.

Não utilizar:

redis:latest

como padrão.

Redis deve ser tratado como infraestrutura auxiliar.

10. Persistência do Redis

Redis não deve possuir persistência configurada
automaticamente apenas por copiar o padrão do PostgreSQL.

A necessidade de persistência deve depender
do uso específico.

Para cache puro:

Redis
→ dados descartáveis

pode não ser necessária persistência.

Quando Redis estiver armazenando dados que precisam
sobreviver à reinicialização, uma estratégia apropriada
deve ser definida.

11. Backend

O backend será adicionado ao Compose quando
o Dockerfile do backend estiver definido.

Conceito:

backend
    |
    +---- postgres
    |
    +---- redis

A aplicação deverá utilizar variáveis de ambiente
para descobrir esses serviços.

12. Frontend

O frontend será executado separadamente do backend.

Conceito:

frontend
    |
    | HTTP
    v
backend

O frontend não deve possuir acesso direto
ao PostgreSQL ou Redis.

13. Worker

Workers devem utilizar a mesma infraestrutura
necessária para seus processamentos.

Exemplo:

worker
   |
   +---- redis
   |
   +---- postgres

O acesso ao banco pelo worker deve seguir
as mesmas regras arquiteturais do backend.

14. Portas

Somente portas que precisarem ser acessadas
pelo host devem ser publicadas.

Exemplo:

Backend
8000

Frontend
porta definida pela aplicação

PostgreSQL
5432 somente quando acesso direto do host for necessário

Redis
6379 somente quando acesso direto do host for necessário

Não publicar uma porta apenas por conveniência.

15. Comunicação interna

Quando dois containers estiverem na mesma network,
eles devem comunicar-se através da porta interna
do serviço.

Exemplo:

backend
    |
    v
postgres:5432

e:

backend
    |
    v
redis:6379

A porta publicada para o host é independente
da comunicação interna entre containers.

16. Environment Variables

Valores dependentes do ambiente devem utilizar
variáveis de ambiente.

Exemplos:

DATABASE_URL
REDIS_URL
JWT_SECRET
APP_ENV
17. Arquivo .env

A configuração local será feita através de:

.env

O .env não deve ser versionado.

O arquivo:

.env.example

deve ser versionado.

18. .env.example

O .env.example deve conter apenas exemplos
e valores não sensíveis.

Exemplo:

APP_ENV=development

DATABASE_URL=postgresql+asyncpg://erp:erp@postgres:5432/erp

REDIS_URL=redis://redis:6379/0

JWT_SECRET=change-me

Os valores reais ficam no ambiente local.

19. Secrets

Nunca colocar secrets diretamente no:

docker-compose.yml
Dockerfile
código
README
logs

Exemplos:

database passwords
JWT secrets
API keys
tokens
20. Healthchecks

Serviços críticos devem possuir healthcheck
quando o estado de disponibilidade precisar
ser conhecido pelo Compose ou por outros serviços.

Exemplo conceitual:

healthcheck:
  test: [...]
  interval: 10s
  timeout: 5s
  retries: 5

O healthcheck deve representar uma verificação
real de disponibilidade do serviço.

21. PostgreSQL Healthcheck

O PostgreSQL deve utilizar uma verificação
que confirme que o servidor está aceitando conexões.

Conceito:

postgres
   |
   v
pg_isready
   |
   v
healthy

Não utilizar somente:

container running

como indicativo de banco pronto.

22. Redis Healthcheck

Quando necessário, o Redis deve possuir
um healthcheck que valide sua disponibilidade.

Conceito:

redis
   |
   v
PING
   |
   v
healthy
23. Backend Healthcheck

O backend possui:

GET /health

Esse endpoint poderá ser utilizado
como healthcheck do container quando o backend
estiver containerizado.

Exemplo:

backend
   |
   v
GET /health
   |
   v
200 OK
24. depends_on

depends_on pode ser utilizado para declarar
dependências de inicialização.

Porém:

container iniciado

não significa necessariamente:

serviço pronto

Quando apropriado, utilizar healthchecks
e condições de saúde para controlar dependências.

25. Backend e PostgreSQL

O backend depende do PostgreSQL.

Conceito:

backend
    |
    v
postgres

A inicialização do backend deve considerar
a disponibilidade real do banco quando necessário.

26. Backend e Redis

O backend também poderá depender do Redis
quando funcionalidades que utilizam Redis
estiverem habilitadas.

Conceito:

backend
    |
    v
redis

Não adicionar Redis como dependência obrigatória
em funcionalidades que não precisam dele.

27. Volumes

Volumes nomeados devem ser utilizados
quando dados precisarem sobreviver à recriação
dos containers.

Exemplo:

postgres_data

Evitar armazenar dados persistentes exclusivamente
na camada interna do container.

28. Bind Mounts

Durante desenvolvimento, bind mounts podem ser utilizados
para facilitar hot reload e edição do código.

Exemplo conceitual:

host/backend
      |
      v
container/backend

O uso de bind mounts deve ser avaliado de acordo
com o serviço e a estratégia de desenvolvimento.

29. Código fonte

O código fonte continua sendo mantido no repositório:

saas-erp-platform/

O container não é a fonte de verdade do código.

Alterações permanentes devem ser realizadas
nos arquivos versionados do projeto.

30. Docker Compose e desenvolvimento

O ambiente deve permitir posteriormente:

docker compose up -d

para iniciar os serviços necessários.

Para encerrar:

docker compose down

Quando existirem dados persistentes,
docker compose down não deve remover automaticamente
os volumes.

31. Remoção de volumes

A remoção de volumes é uma operação potencialmente destrutiva.

Exemplo:

docker compose down -v

pode remover volumes utilizados pelos serviços.

Não executar esse comando sem entender
que os dados persistidos podem ser apagados.

32. Logs

Os logs dos serviços devem estar disponíveis
através do Docker Compose.

Exemplo:

docker compose logs

Para um serviço:

docker compose logs backend

ou:

docker compose logs postgres
33. Logs da aplicação

Os logs internos da aplicação devem seguir
as regras definidas em:

skills/observability/

O Docker Compose não substitui o sistema
de logging da aplicação.

34. Restart Policy

Políticas de restart devem ser definidas
de acordo com o comportamento esperado de cada serviço.

Não adicionar:

restart: always

indiscriminadamente.

Em desenvolvimento, reinicialização automática
deve ser utilizada somente quando realmente ajudar
o fluxo de desenvolvimento.

35. Imagens

As imagens devem possuir versões explícitas.

Evitar:

latest

como referência padrão.

Exemplo:

postgres:VERSAO
redis:VERSAO

As versões utilizadas devem ser atualizadas
de forma consciente.

36. Builds

Quando um serviço for construído a partir do código
do projeto, o Compose deve utilizar build.

Exemplo conceitual:

backend:
  build:
    context: ./backend

A estrutura final do Dockerfile deve seguir
as skills de Docker.

37. Contexto de build

O contexto de build deve ser o menor possível
para o serviço.

Evitar enviar desnecessariamente todo o repositório
para o contexto de uma imagem específica.

Utilizar .dockerignore quando apropriado.

38. Dockerfile

O docker-compose.yml não deve concentrar
instruções de construção complexas.

A construção da imagem deve permanecer no:

Dockerfile

O Compose deve principalmente orquestrar:

serviços
redes
volumes
variáveis
dependências
39. Banco e migrations

O banco será inicializado através do serviço PostgreSQL.

As alterações estruturais serão aplicadas pelo Alembic.

Fluxo:

PostgreSQL
    |
    v
Alembic
    |
    v
Database Schema

O Compose não deve esconder a execução
das migrations.

O processo deve ser reproduzível e documentado.

40. Migrations e inicialização

A execução das migrations pode posteriormente
ser realizada por:

comando manual

ou:

serviço/job específico

A estratégia definitiva será definida
quando a infraestrutura do backend estiver pronta.

Não executar migrations automaticamente
em todo início do backend sem avaliar
os riscos dessa abordagem.

41. Desenvolvimento incremental

Os serviços devem ser adicionados gradualmente.

Ordem planejada:

PostgreSQL
    |
    v
Redis
    |
    v
Backend
    |
    v
Frontend
    |
    v
Worker

A ordem pode mudar conforme as necessidades
reais do projeto.

42. Escopo inicial

A primeira versão do Docker Compose deverá
concentrar-se nos serviços necessários para
a Fase 2.

Inicialmente:

postgres
redis

Depois:

backend
frontend
worker

Não adicionar serviços futuros
antes de existir necessidade.

43. Multi-tenancy

O Docker Compose não é responsável
pelo isolamento entre tenants.

O Compose fornece a infraestrutura.

O isolamento de dados é responsabilidade
da aplicação e do banco conforme definido em:

skills/database/multi-tenancy.md
44. Segurança

Não assumir que um serviço está seguro
apenas por estar em uma network interna.

Avaliar:

portas expostas
credenciais
permissions
secrets
comunicação
45. Ambientes

A configuração de desenvolvimento não deve
ser confundida automaticamente com produção.

Quando existirem múltiplos ambientes,
suas diferenças deverão ser documentadas.

46. Alterações no Compose

Antes de alterar docker-compose.yml:

verificar serviços existentes;
verificar dependências;
verificar volumes;
verificar networks;
verificar portas;
verificar environment;
verificar healthchecks;
verificar impacto na aplicação;
consultar a skill de infraestrutura correspondente.
47. Novos serviços

Antes de adicionar um novo serviço:

Qual problema resolve?

É realmente necessário?

Existe serviço existente que já resolve?

Precisa de persistência?

Precisa de uma porta pública?

Precisa de healthcheck?

Possui dependências?

Qual o impacto no ambiente?

Não adicionar serviços apenas para aumentar
a quantidade de tecnologias utilizadas.

48. Comandos principais

Iniciar:

docker compose up -d

Iniciar reconstruindo imagens:

docker compose up -d --build

Ver status:

docker compose ps

Ver logs:

docker compose logs

Ver logs de um serviço:

docker compose logs backend

Parar serviços:

docker compose down

Parar e remover volumes:

docker compose down -v

O último comando é destrutivo para os dados
armazenados nos volumes removidos.

49. Validação

Depois de alterar o Compose, verificar:

O YAML é válido?

Os serviços iniciam?

Os containers ficam saudáveis?

O backend consegue acessar PostgreSQL?

O backend consegue acessar Redis?

As portas necessárias estão disponíveis?

Os volumes persistem corretamente?

Os logs estão disponíveis?
50. Regra final

O docker-compose.yml deve permanecer:

simples
+
explícito
+
versionado
+
reproduzível
+
seguro

Cada serviço deve possuir uma responsabilidade clara.

Não adicionar infraestrutura sem necessidade técnica.

O Docker Compose deve facilitar o desenvolvimento
do sistema, não esconder sua arquitetura.


### Local exato

```text
C:\Users\joao\Projetos\saas-erp-platform\skills\infrastructure\docker-compose.md