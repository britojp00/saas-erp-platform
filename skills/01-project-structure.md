# Project Structure

Este documento define a estrutura oficial de diretórios
do projeto SaaS ERP Platform.

Antes de criar novos arquivos ou diretórios, verificar
esta estrutura e utilizar o local correspondente à
responsabilidade do código.

---

# 1. Estrutura geral

```text
saas-erp-platform/
│
├── AGENTS.md
│
├── backend/
│
├── frontend/
│
├── docs/
│
├── skills/
│
├── .github/
│
├── docker-compose.yml
├── docker-compose.prod.yml
├── .env.example
├── .env.prod.example
├── .gitignore
└── README.md
2. Backend

O backend está localizado em:

backend/

Sua responsabilidade é fornecer a API, regras de negócio,
autenticação, autorização, persistência, segurança,
logs e demais funcionalidades do servidor.

Estrutura principal:

backend/
│
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── auth.py
│   │   │   ├── customers.py
│   │   │   ├── categories.py
│   │   │   ├── products.py
│   │   │   ├── inventory.py
│   │   │   ├── orders.py
│   │   │   └── audit_logs.py
│   │   ├── middleware.py
│   │   └── dependencies.py
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── security.py
│   │   ├── exceptions.py
│   │   ├── logging.py
│   │   └── request_context.py
│   ├── db/
│   │   ├── models/
│   │   ├── base.py
│   │   ├── database.py
│   │   └── mixins.py
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── customer.py
│   │   ├── category.py
│   │   ├── product.py
│   │   ├── inventory.py
│   │   ├── order.py
│   │   └── audit_log.py
│   ├── repositories/
│   │   ├── user.py
│   │   ├── tenant.py
│   │   ├── customer.py
│   │   ├── category.py
│   │   ├── product.py
│   │   ├── inventory.py
│   │   ├── inventory_movement.py
│   │   ├── inventory_reservation.py
│   │   ├── order.py
│   │   ├── order_item.py
│   │   ├── role.py
│   │   ├── permission.py
│   │   └── audit_log.py
│   ├── services/
│   │   ├── auth.py
│   │   ├── authorization.py
│   │   ├── customer.py
│   │   ├── category.py
│   │   ├── product.py
│   │   ├── inventory.py
│   │   ├── order.py
│   │   └── audit_log.py
│   └── main.py
│
├── tests/
│   ├── api/
│   │   ├── test_auth.py
│   │   ├── test_health.py
│   │   ├── test_timezone.py
│   │   ├── test_rbac.py
│   │   ├── test_customers.py
│   │   ├── test_categories.py
│   │   ├── test_products.py
│   │   ├── test_inventory.py
│   │   ├── test_orders.py
│   │   ├── test_audit_logs.py
│   │   └── test_observability.py
│   ├── unit/
│   │   └── test_security.py
│   └── conftest.py
│
├── migrations/
├── scripts/
│   └── seed_dev.py
├── Dockerfile
├── .dockerignore
├── .python-version
├── pyproject.toml
└── uv.lock
3. Backend / app

A pasta:

backend/app/

contém o código principal da aplicação.

Suas principais áreas são:

api/
core/
models/
schemas/
repositories/
services/
main.py

Cada área possui uma responsabilidade específica.

4. API

Localização:

backend/app/api/

As rotas da API devem ser organizadas em:

backend/app/api/v1/

Responsabilidades:

definir endpoints;
receber requisições HTTP;
receber parâmetros;
utilizar schemas;
chamar services;
retornar respostas HTTP.

Exemplos:

auth.py
customers.py
categories.py
products.py
inventory.py
orders.py
audit_logs.py

A camada de API não deve concentrar regras de negócio
complexas.

5. Core

Localização:

backend/app/core/

Contém componentes centrais e configurações compartilhadas.

Arquivos:

config.py
security.py
exceptions.py
logging.py
request_context.py

Pode conter:

configuração da aplicação;
configuração de ambiente;
conexão com banco;
segurança;
configuração de logs;
componentes compartilhados.
6. Models

Localização:

backend/app/db/models/

Contém os modelos ORM utilizados pelo SQLAlchemy.

Arquivos:

tenant.py
user.py
user_role.py
role.py
role_permission.py
permission.py
customer.py
category.py
product.py
inventory.py
inventory_movement.py
inventory_reservation.py
order.py
order_item.py
audit_log.py

Models representam entidades persistidas no banco de dados.

Regras de negócio complexas não devem ser concentradas
nos models.

7. Schemas

Localização:

backend/app/schemas/

Contém os schemas Pydantic utilizados pelos contratos da API.

Exemplos:

auth.py
customer.py
category.py
product.py
inventory.py
order.py
audit_log.py

Responsabilidades:

validação de entrada;
validação de saída;
definição dos contratos;
serialização;
desserialização.

Schemas não devem acessar diretamente o banco de dados.

Schemas não devem conter regras de negócio complexas.

8. Repositories

Localização:

backend/app/repositories/

Contém a camada responsável pela persistência.

Exemplos:

user.py
tenant.py
customer.py
category.py
product.py
inventory.py
inventory_movement.py
inventory_reservation.py
order.py
order_item.py
role.py
permission.py
audit_log.py

Responsabilidades:

consultar dados;
criar registros;
atualizar registros;
remover registros quando permitido;
executar operações de persistência.

Repositories não devem concentrar regras de negócio complexas.

9. Services

Localização:

backend/app/services/

Contém a lógica de negócio da aplicação.

Exemplos:

auth.py
authorization.py
customer.py
category.py
product.py
inventory.py
order.py
audit_log.py

Responsabilidades:

aplicar regras de negócio;
validar condições de negócio;
coordenar operações;
utilizar repositories;
controlar fluxos de negócio.

Exemplo:

Criar pedido
    |
    v
OrderService
    |
    +---- validar cliente
    |
    +---- verificar estoque
    |
    +---- calcular valores
    |
    +---- criar pedido
    |
    +---- atualizar estoque
10. Main

Arquivo:

backend/app/main.py

É o ponto de entrada da aplicação FastAPI.

Responsabilidades principais:

criação da instância FastAPI;
configuração inicial da aplicação;
registro dos routers;
configuração de eventos de inicialização e encerramento;
configuração de componentes globais.

A lógica específica de negócio não deve ficar em main.py.

11. Testes

Localização:

backend/tests/

Estrutura:

backend/tests/
├── unit/
│   └── test_security.py
├── api/
│   ├── test_auth.py
│   ├── test_health.py
│   ├── test_timezone.py
│   ├── test_rbac.py
│   ├── test_customers.py
│   ├── test_categories.py
│   ├── test_products.py
│   ├── test_inventory.py
│   ├── test_orders.py
│   ├── test_audit_logs.py
│   └── test_observability.py
└── conftest.py

11.1 Unit

Localização:

backend/tests/unit/

Utilizado para testar componentes e regras de forma isolada.

Exemplos:

test_security.py

11.2 API

Localização:

backend/tests/api/

Utilizado para testar endpoints HTTP.

Exemplos:

test_auth.py
test_health.py
test_timezone.py
test_rbac.py
test_customers.py
test_categories.py
test_products.py
test_inventory.py
test_orders.py
test_audit_logs.py
test_observability.py
12. Migrations

Localização:

backend/migrations/

Contém as migrations do banco utilizando Alembic.

As alterações estruturais do banco devem ser controladas
através de migrations.

Exemplos futuros:

versions/

Não criar alterações estruturais diretamente no banco como
substituição do fluxo de migrations.

13. Frontend

O frontend está localizado em:

frontend/

O frontend será uma aplicação separada do backend.

Estrutura planejada:

frontend/
│
├── src/
│   ├── components/
│   ├── pages/
│   ├── layouts/
│   ├── services/
│   ├── hooks/
│   ├── utils/
│   └── ...
│
├── public/
├── package.json
└── ...

Responsabilidades:

interface;
navegação;
formulários;
apresentação;
estado da interface;
consumo da API.

O frontend não deve acessar diretamente:

PostgreSQL
Redis

A comunicação deve ocorrer através da API do backend.

14. Documentation

Documentação específica deve ficar em:

docs/

Estrutura:

docs/
├── architecture/
│   └── ci-cd.md
├── api/
└── database/
architecture/

Documentação de arquitetura e decisões arquiteturais.

ci-cd.md

Documentação de CI/CD, GitHub Actions e Coolify.

api/

Documentação específica sobre APIs e contratos.

database/

Documentação relacionada ao banco de dados.

15. Skills

As regras e padrões do projeto ficam em:

skills/

Estrutura:

skills/
├── 00-project-overview.md
├── 01-project-structure.md
├── 02-architecture.md
│
├── backend/
├── frontend/
├── database/
├── infrastructure/
├── testing/
├── observability/
├── security/
├── development/
└── tasks/

As skills devem ser consultadas antes de realizar
alterações relevantes.

Exemplos:

Criar endpoint
→ skills/backend/
→ skills/testing/

Alterar banco
→ skills/database/

Alterar Docker
→ skills/infrastructure/

Alterar autenticação
→ skills/security/
16. GitHub Actions

Os workflows de CI/CD ficam em:

.github/workflows/

Arquivo atual:

ci.yml

Executa em push e pull request para master:

Ruff check;
Ruff format;
Alembic check;
Migrations;
Testes;
Docker build.

Em push para master, após CI passar:

Deploy via Coolify Deploy Webhook (job separado).
17. Docker

Arquivos relacionados à execução do ambiente em containers:

backend/Dockerfile
backend/.dockerignore
docker-compose.yml
docker-compose.prod.yml

O Dockerfile do backend utiliza python:3.13-slim com uv
para gerenciamento de dependências.

docker-compose.yml é o arquivo de desenvolvimento local.

docker-compose.prod.yml é o arquivo de produção
(backend + postgres + redis).

O arquivo principal previsto na raiz é:

docker-compose.yml

As regras detalhadas de Docker serão definidas em:

skills/infrastructure/
18. Environment

Configurações sensíveis devem utilizar variáveis de ambiente.

Arquivo de referência:

.env.example

Arquivo local:

.env

O .env não deve ser versionado.

19. Regra para criação de novos arquivos

Antes de criar um arquivo:

identificar sua responsabilidade;
verificar a estrutura existente;
verificar se já existe um arquivo responsável pela mesma função;
consultar a skill correspondente;
criar o arquivo na camada apropriada.
20. Regra para criação de novos diretórios

Novos diretórios somente devem ser criados quando houver
uma necessidade estrutural real.

Não criar novas camadas ou diretórios apenas por organização
visual.

Quando uma nova camada for necessária, a decisão deve ser
avaliada junto à arquitetura existente.

21. Regra de responsabilidade

Cada arquivo deve possuir uma responsabilidade clara.

Evitar arquivos que concentrem:

API;
regras de negócio;
persistência;
configuração;
múltiplas responsabilidades diferentes.

A organização deve favorecer:

cohesão
+
separação de responsabilidades
+
testabilidade
+
manutenção

### Onde fica

```text
saas-erp-platform/
└── skills/
    └── 01-project-structure.md