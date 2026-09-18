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
├── .env.example
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
│   │   └── v1/
│   ├── core/
│   ├── models/
│   ├── schemas/
│   ├── repositories/
│   ├── services/
│   └── main.py
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── api/
│
├── migrations/
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

Exemplos futuros:

auth.py
customers.py
products.py
orders.py
inventory.py

A camada de API não deve concentrar regras de negócio
complexas.

5. Core

Localização:

backend/app/core/

Contém componentes centrais e configurações compartilhadas.

Exemplos futuros:

config.py
database.py
security.py
logging.py

Pode conter:

configuração da aplicação;
configuração de ambiente;
conexão com banco;
segurança;
configuração de logs;
componentes compartilhados.
6. Models

Localização:

backend/app/models/

Contém os modelos ORM utilizados pelo SQLAlchemy.

Exemplos futuros:

tenant.py
user.py
role.py
permission.py
customer.py
product.py
category.py
inventory.py
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

CustomerCreate
CustomerUpdate
CustomerResponse

ProductCreate
ProductUpdate
ProductResponse

OrderCreate
OrderResponse

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

tenant_repository.py
customer_repository.py
product_repository.py
inventory_repository.py
order_repository.py

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

customer_service.py
product_service.py
inventory_service.py
order_service.py

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
├── integration/
└── api/
11.1 Unit

Localização:

backend/tests/unit/

Utilizado para testar componentes e regras de forma isolada.

Exemplos:

test_order_service.py
test_inventory_service.py
test_auth.py
11.2 Integration

Localização:

backend/tests/integration/

Utilizado para testes que envolvem múltiplos componentes
ou infraestrutura de teste.

Exemplos:

test_customer_repository.py
test_order_repository.py
test_database.py
11.3 API

Localização:

backend/tests/api/

Utilizado para testar endpoints HTTP.

Exemplos:

test_health.py
test_auth.py
test_customers.py
test_products.py
test_orders.py
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
├── api/
└── database/
architecture/

Documentação de arquitetura e decisões arquiteturais.

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

Exemplos futuros:

ci.yml
tests.yml

Esses arquivos serão responsáveis por automações como:

testes;
lint;
validações;
build;
outras etapas de CI/CD.
17. Docker

Arquivos relacionados à execução do ambiente em containers
serão mantidos de acordo com as definições das skills de
infraestrutura.

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