# Project Overview

## Nome do projeto

SaaS ERP Platform

## Descrição

O SaaS ERP Platform é uma plataforma ERP web desenvolvida
com arquitetura SaaS e suporte a múltiplos tenants.

O projeto tem como objetivo demonstrar o desenvolvimento de
um sistema corporativo moderno, com separação entre frontend
e backend, API REST, banco de dados relacional, autenticação,
autorização, regras de negócio, testes automatizados,
observabilidade e integração entre sistemas.

O projeto será utilizado para estudo, desenvolvimento
prático e portfólio profissional.

---

## Objetivo principal

Construir uma plataforma ERP funcional e escalável,
capaz de atender diferentes empresas utilizando a mesma
aplicação, mantendo os dados de cada empresa isolados.

O projeto também deverá servir posteriormente como base
para um segundo projeto chamado `integration-hub`.

---

## Principais objetivos técnicos

O projeto deve demonstrar conhecimentos em:

- desenvolvimento backend;
- desenvolvimento frontend;
- APIs REST;
- banco de dados relacionais;
- arquitetura de software;
- multi-tenancy;
- autenticação;
- autorização;
- controle de permissões;
- regras de negócio;
- testes automatizados;
- logging;
- auditoria;
- processamento assíncrono;
- containerização;
- CI/CD;
- integração entre sistemas.

---

## Stack tecnológica

### Backend

- Python 3.13
- FastAPI
- SQLAlchemy
- Alembic
- Pydantic
- PostgreSQL
- asyncpg
- Redis
- PyJWT
- pwdlib

### Frontend

- React
- TypeScript
- Vite

### Testes

- Pytest
- pytest-asyncio
- HTTPX
- Coverage

### Qualidade de código

- Ruff

### Infraestrutura

- Docker
- Docker Compose

### Controle de versão

- Git
- GitHub
- GitHub Actions

### Gerenciamento Python

- uv

---

## Estrutura conceitual do sistema

O sistema será dividido principalmente em frontend e backend.

```text
Frontend
    |
    | HTTP / JSON
    v
Backend API
    |
    +---- PostgreSQL
    |
    +---- Redis
    |
    +---- Workers
Frontend

O frontend será responsável pela interface da aplicação,
navegação, formulários, apresentação das informações e
consumo da API.

Backend

O backend será responsável pela API, autenticação,
autorização, regras de negócio, persistência, segurança,
logs, auditoria e processamento.

Banco de dados

O PostgreSQL será o banco de dados principal da aplicação.

Redis

O Redis será utilizado para recursos como cache,
dados temporários, controle de requisições e suporte
a processos assíncronos.

Workers

Workers serão utilizados posteriormente para tarefas
que não precisam ser executadas diretamente durante
uma requisição HTTP.

Conceito de multi-tenancy

A aplicação será utilizada por diferentes empresas.

Cada empresa representa um tenant.

Exemplo:

Tenant 1
Empresa A

Tenant 2
Empresa B

Tenant 3
Empresa C

Cada tenant possui seus próprios usuários e dados de negócio.

Os dados de um tenant não podem ser acessados por outro tenant.

Módulos planejados

O ERP deverá possuir inicialmente módulos relacionados a:

Tenant
Users
Roles
Permissions
Customers
Products
Categories
Inventory
Orders
Order Items
Audit Logs

Os módulos podem ser expandidos conforme a evolução do projeto.

Segurança

A aplicação deverá possuir:

autenticação;
autorização;
JWT;
refresh token;
RBAC;
controle de permissões;
isolamento entre tenants;
proteção de credenciais.

Informações sensíveis não devem ser armazenadas diretamente
no código da aplicação.

Testes

Os testes automatizados fazem parte do desenvolvimento
das funcionalidades.

O projeto deverá possuir:

Unit Tests
API Tests
Integration Tests
Security Tests
Multi-Tenant Tests

As regras críticas do sistema deverão possuir testes
específicos.

Observabilidade

O sistema deverá possuir recursos para facilitar a
identificação e investigação de problemas.

Estão planejados:

logs estruturados;
request ID;
logs de erros;
logs de eventos;
auditoria de operações relevantes.

Informações sensíveis não devem ser registradas nos logs.

API

A API utilizará versionamento.

Padrão:

/api/v1/

Endpoints serão adicionados conforme os módulos forem
implementados.

Exemplos planejados:

GET    /health

POST   /api/v1/auth/login

GET    /api/v1/customers
POST   /api/v1/customers
GET    /api/v1/customers/{id}

GET    /api/v1/products
POST   /api/v1/products

GET    /api/v1/inventory

POST   /api/v1/orders
GET    /api/v1/orders/{id}
Integração futura

Depois da conclusão do ERP será desenvolvido o projeto:

integration-hub

O Integration Hub deverá consumir a API REST do
SaaS ERP Platform.

O objetivo será demonstrar:

integração entre sistemas;
consumo de APIs;
autenticação por API;
transformação de dados;
filas;
workers;
retry;
idempotência;
webhooks;
tratamento de falhas;
rastreamento de integrações.

A API do ERP será uma das APIs reais utilizadas
pelo projeto de integração.

Estado atual do projeto

O projeto está em fase inicial de desenvolvimento.

Atualmente possui:

Python 3.13;
uv;
FastAPI;
Uvicorn;
endpoint /health;
Pytest;
Ruff;
Git;
GitHub.

Próximas etapas:

Docker;
PostgreSQL;
Redis;
SQLAlchemy;
Alembic;
autenticação;
multi-tenancy;
RBAC;
módulos ERP;
logging;
auditoria;
frontend;
CI/CD;
Integration Hub.
Princípios gerais

O projeto deve priorizar:

simplicidade;
consistência;
segurança;
testabilidade;
manutenção;
separação de responsabilidades;
documentação;
reutilização de padrões existentes.

A arquitetura deve evoluir conforme as necessidades reais
do sistema, evitando complexidade desnecessária.


### Onde exatamente fica

```text
saas-erp-platform/
└── skills/
    └── 00-project-overview.md