SaaS ERP Platform

Plataforma ERP SaaS multi-tenant desenvolvida para demonstrar práticas de desenvolvimento de software backend e frontend aplicadas a um sistema corporativo real.

O projeto será construído de forma incremental, com foco em arquitetura, regras de negócio, segurança, testes automatizados, observabilidade, integração entre sistemas e documentação técnica.

Objetivos

Construir um ERP SaaS com isolamento de dados entre empresas (multi-tenancy).

Disponibilizar uma API REST com FastAPI.

Criar uma interface web separada do backend.

Aplicar autenticação e controle de permissões.

Implementar regras de negócio reais de ERP.

Utilizar testes automatizados desde o desenvolvimento dos módulos.

Implementar logs técnicos e auditoria de operações.

Containerizar o ambiente com Docker.

Automatizar validações com GitHub Actions.

Preparar a API para ser consumida posteriormente pelo projeto integration-hub.

Arquitetura planejada

                         ┌──────────────────────┐
                         │       Frontend       │
                         │ React + TypeScript   │
                         └──────────┬───────────┘
                                    │ HTTP / JSON
                                    ▼
                         ┌──────────────────────┐
                         │       Backend        │
                         │   Python + FastAPI   │
                         └──────────┬───────────┘
                                    │
                  ┌─────────────────┼─────────────────┐
                  │                 │                 │
                  ▼                 ▼                 ▼
             PostgreSQL           Redis            Workers

Separação de responsabilidades

Frontend
  └── Interface, navegação e consumo da API

Backend
  ├── API
  ├── Autenticação
  ├── Regras de negócio
  ├── Multi-tenancy
  ├── Persistência
  ├── Logs
  └── Auditoria

PostgreSQL
  └── Dados persistentes

Redis
  └── Cache e recursos assíncronos

Workers
  └── Processamentos em segundo plano

Estrutura do repositório

saas-erp-platform/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── repositories/
│   │   ├── services/
│   │   └── main.py
│   │
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── api/
│   │
│   ├── migrations/
│   ├── pyproject.toml
│   ├── uv.lock
│   └── .python-version
│
├── frontend/
│
├── docs/
│   ├── architecture/
│   ├── api/
│   └── database/
│
├── .github/
│   └── workflows/
│
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md

Tecnologias

Backend

Python 3.13

FastAPI

SQLAlchemy

Alembic

Pydantic

PostgreSQL

asyncpg

PyJWT

pwdlib

Qualidade e testes

Pytest

pytest-asyncio

HTTPX

Coverage

Ruff

Ambiente e infraestrutura

Docker

Docker Compose

Redis

Git

GitHub

GitHub Actions

uv

Frontend

O frontend será desenvolvido separadamente do backend, utilizando React + TypeScript + Vite.

Funcionalidades planejadas

Fundação

Estrutura inicial do repositório

Ambiente Python com uv

FastAPI

Endpoint /health

Primeiro teste automatizado

Ruff

Repositório GitHub

Infraestrutura

Docker Compose

PostgreSQL

Redis

Variáveis de ambiente

Health checks dos serviços

Configuração de ambiente de desenvolvimento

Identidade e segurança

Tenant

Usuário

Autenticação JWT

Access token

Refresh token

Roles

Permissions

RBAC

Isolamento multi-tenant

ERP

Clientes

Produtos

Categorias

Estoque

Pedidos

Itens do pedido

Regras de estoque

Histórico de operações

Observabilidade

Logging estruturado

Request ID

Logs de erro

Auditoria de alterações

Registro de eventos de negócio

Testes

Testes unitários

Testes de API

Testes de integração

Testes de segurança

Testes de isolamento multi-tenant

Cobertura de código

Frontend

Estrutura React + TypeScript

Autenticação

Layout administrativo

Dashboard

Clientes

Produtos

Estoque

Pedidos

CI/CD

GitHub Actions

Ruff

Pytest

Coverage

Build Docker

Validação automática a cada Pull Request

Estratégia de testes

Os testes serão desenvolvidos junto com as funcionalidades.

Exemplos de regras que deverão ser cobertas:

Empresa A
   │
   ├── pode acessar seus clientes
   ├── pode acessar seus produtos
   └── NÃO pode acessar dados da Empresa B

Estoque = 10
Pedido   = 3

Resultado esperado:
Estoque = 7
Pedido criado

Estoque = 2
Pedido   = 5

Resultado esperado:
Pedido rejeitado
Estoque permanece = 2

Os testes também serão executados automaticamente pelo GitHub Actions.

Logging e auditoria

O projeto terá duas categorias principais de registros.

Logs técnicos

Exemplo:

{
  "level": "ERROR",
  "event": "order_creation_failed",
  "tenant_id": 10,
  "user_id": 32,
  "request_id": "..."
}

Auditoria

Exemplo:

Usuário: João
Ação: UPDATE_PRODUCT
Produto: 123

Antes:
Preço = 100.00

Depois:
Preço = 120.00

A auditoria ficará vinculada ao tenant, usuário, entidade e operação executada.

API

A API será versionada:

/api/v1/

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

A documentação será disponibilizada via OpenAPI/Swagger.

Roadmap

Fase 1 — Fundação

Estrutura, FastAPI, testes, lint e GitHub.

Fase 2 — Infraestrutura

Docker, PostgreSQL, Redis, configuração e migrations.

Fase 3 — Identidade

Tenant, usuários, autenticação e RBAC.

Fase 4 — Cadastro

Clientes, produtos e categorias.

Fase 5 — Operação

Estoque, pedidos e regras de negócio.

Fase 6 — Observabilidade

Logs estruturados, request ID e auditoria.

Fase 7 — Testes

Expansão da suíte unitária, API, integração e segurança.

Fase 8 — Frontend

Aplicação React consumindo a API real.

Fase 9 — CI/CD

GitHub Actions, validações e build.

Fase 10 — Integração

O projeto integration-hub será desenvolvido posteriormente para consumir a API deste ERP e demonstrar integração entre sistemas.

Status atual

Em desenvolvimento — Fase 1

O projeto já possui:

Python 3.13
FastAPI
Uvicorn
Pytest
Ruff
uv
Git
GitHub

Primeiro endpoint:

GET /health

Resposta:

{
  "status": "ok",
  "service": "saas-erp-platform"
}

Execução local

Backend

cd backend

uv sync

uv run uvicorn app.main:app --reload

API:

http://127.0.0.1:8000

Swagger:

http://127.0.0.1:8000/docs

Testes

cd backend

uv run pytest

Lint

uv run ruff check .

Formatação

uv run ruff format .

Projeto futuro

Este ERP será a base para o segundo projeto do portfólio:

Integration Hub

O Integration Hub consumirá a API REST deste sistema para demonstrar:

integração entre sistemas;

autenticação por API;

transformação de payloads;

filas;

workers;

retry;

idempotência;

webhooks;

rastreamento de integrações;

tratamento de falhas.

A comunicação será baseada na API real deste ERP, evitando integrações fictícias.

Licença

Projeto desenvolvido para fins de estudo, portfólio e demonstração técnica.