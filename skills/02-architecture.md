# Architecture

Este documento define os princípios e regras arquiteturais
do SaaS ERP Platform.

Toda nova funcionalidade deve respeitar a arquitetura existente
antes de introduzir novas camadas, padrões ou tecnologias.

---

# 1. Visão geral

O sistema é dividido em dois componentes principais:

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

O frontend e o backend são aplicações separadas.

O backend é responsável pela lógica da aplicação e pela
exposição da API.

O frontend é responsável pela interface e pelo consumo da API.

2. Arquitetura do backend

O backend utiliza separação por responsabilidades.

Fluxo principal:

HTTP Request
      |
      v
   Router
      |
      v
   Schema
      |
      v
   Service
      |
      v
 Repository
      |
      v
 SQLAlchemy
      |
      v
 PostgreSQL

Cada camada possui uma responsabilidade específica.

3. API / Router Layer

Localização:

backend/app/api/

Responsabilidade:

receber requisições HTTP;
definir endpoints;
receber parâmetros;
utilizar schemas;
autenticar e autorizar através das dependências apropriadas;
chamar services;
retornar respostas HTTP.

Exemplo:

POST /api/v1/customers
        |
        v
customers.py
        |
        v
CustomerService
Regras

Routers não devem:

executar SQL diretamente;
acessar o banco diretamente;
concentrar regras de negócio complexas;
implementar cálculos de negócio extensos;
duplicar lógica existente em services.

O router deve permanecer fino.

4. Schema Layer

Localização:

backend/app/schemas/

Responsabilidade:

validar dados de entrada;
definir contratos de entrada;
definir contratos de saída;
serializar dados;
desserializar dados.

Exemplo:

CustomerCreate
CustomerUpdate
CustomerResponse
Regras

Schemas não devem:

acessar banco de dados;
executar consultas;
controlar transações;
conter regras de negócio complexas.

A validação estrutural dos dados pertence aos schemas.

A regra de negócio pertence aos services.

5. Service Layer

Localização:

backend/app/services/

Responsável pelas regras de negócio.

Exemplo:

Create Order
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
Regras

Services podem:

aplicar regras de negócio;
validar condições;
coordenar operações;
utilizar repositories;
controlar fluxos de negócio;
iniciar operações transacionais quando necessário.

Services não devem:

depender diretamente da camada HTTP;
conhecer detalhes de apresentação do frontend;
retornar objetos específicos da interface HTTP quando não necessário.

A regra de negócio deve permanecer independente da interface HTTP.

6. Repository Layer

Localização:

backend/app/repositories/

Responsável pela persistência.

Exemplos:

CustomerRepository
ProductRepository
InventoryRepository
OrderRepository

Responsabilidades:

consultar dados;
inserir dados;
atualizar dados;
remover dados quando permitido;
executar operações de persistência;
encapsular detalhes de acesso ao banco.
Regra

Repository responde perguntas relacionadas à persistência.

Exemplo:

Repository:
"Buscar produto pelo ID"

Service:
"O produto pode ser vendido nesta situação?"

Repository não deve decidir regras de negócio complexas.

7. Model Layer

Localização:

backend/app/models/

Contém os modelos ORM do SQLAlchemy.

Exemplos:

Tenant
User
Role
Permission
Customer
Product
Category
Inventory
Order
OrderItem
AuditLog

Models representam entidades persistidas.

Regras

Models não devem concentrar:

lógica de API;
autenticação;
lógica de apresentação;
regras de negócio extensas.

Relacionamentos, tipos de coluna, constraints e características
de persistência devem ser definidos de acordo com as regras
da camada de banco.

8. Core Layer

Localização:

backend/app/core/

Contém componentes centrais e compartilhados.

Exemplos:

config.py
database.py
security.py
logging.py

Responsabilidades:

configuração da aplicação;
configuração de ambiente;
conexão com banco;
componentes de segurança;
configuração de logging;
componentes centrais compartilhados.

Evitar colocar lógica de negócio específica nessa camada.

9. Main

Arquivo:

backend/app/main.py

O main.py é o ponto de entrada da aplicação.

Responsabilidades:

criar a aplicação FastAPI;
configurar componentes globais;
registrar routers;
configurar eventos de inicialização;
configurar eventos de encerramento.

O main.py não deve conter regras de negócio.

10. Fluxo completo

Uma operação típica deve seguir:

Cliente
   |
   | HTTP
   v
Router
   |
   v
Schema
   |
   v
Service
   |
   v
Repository
   |
   v
SQLAlchemy
   |
   v
PostgreSQL

Resposta:

PostgreSQL
   |
   v
Repository
   |
   v
Service
   |
   v
Router
   |
   v
HTTP Response
11. Exemplo: criação de cliente

Fluxo esperado:

POST /api/v1/customers
          |
          v
     CustomerRouter
          |
          v
      CustomerCreate
          |
          v
     CustomerService
          |
          +---- validar regras
          |
          +---- verificar tenant
          |
          +---- verificar duplicidade
          |
          v
    CustomerRepository
          |
          v
       PostgreSQL

O router não deve implementar toda essa lógica.

11.1 Exemplo: criação de pedido

Fluxo esperado:

POST /api/v1/orders
          |
          v
     OrderRouter
          |  require_permissions("order.create")
          v
      OrderCreate
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
          +---- criar pedido (DRAFT)
          |
          +---- criar itens
          |
          +---- reservar estoque
          |
          v
    OrderRepository
          |
          v
       PostgreSQL

POST /api/v1/orders/{id}/confirm
          |
          v
     OrderService
          |
          +---- verificar status (DRAFT)
          |
          +---- confirmar pedido
          |
          +---- confirmar reservas
          |
          v
       PostgreSQL

POST /api/v1/orders/{id}/complete
          |
          v
     OrderService
          |
          +---- verificar status (CONFIRMED)
          |
          +---- completar pedido
          |
          +---- Baixar estoque
          |
          v
       PostgreSQL

12. Multi-tenancy

Multi-tenancy é um requisito estrutural do sistema.

Conceito:

Tenant
  |
  +---- Users
  +---- Customers
  +---- Products
  +---- Orders
  +---- Inventory

Entidades de negócio pertencentes a um tenant devem possuir
referência ao tenant correspondente quando aplicável.

Exemplo:

customers

id
tenant_id
name
email
created_at
updated_at
13. Isolamento entre tenants

O contexto do tenant deve ser obtido de uma fonte confiável
da autenticação da aplicação.

O sistema não deve confiar exclusivamente em um tenant_id
fornecido pelo cliente.

Exemplo:

Usuário autenticado
       |
       v
Tenant = 10
       |
       v
GET /api/v1/customers
       |
       v
Clientes do Tenant 10

Uma tentativa de acessar dados pertencentes a outro tenant
deve ser bloqueada.

14. Regra de acesso aos dados

Quando uma entidade pertence a um tenant, consultas e operações
sobre essa entidade devem considerar o contexto do tenant.

Conceitualmente:

Recurso
+
Tenant atual

em vez de somente:

Recurso

Exemplo conceitual:

query.where(
    Customer.id == customer_id,
    Customer.tenant_id == tenant_id,
)

A implementação concreta deve seguir as abstrações definidas
pelo projeto.

15. Authentication

A autenticação será baseada em JWT.

Fluxo:

Login
  |
  v
Validação de credenciais
  |
  v
Access Token
  |
  v
Request autenticada

Posteriormente:

Access Token
Refresh Token

Os tokens não devem ser enviados para logs.

16. Authorization

Autorização será baseada em RBAC.

Fluxo:

User
  |
  v
Role
  |
  v
Permission

Exemplo de roles:

ADMIN
MANAGER
SELLER
STOCK
VIEWER

Permissoes implementadas:

customer.read, customer.create, customer.update, customer.delete
category.read, category.create, category.update, category.delete
product.read, product.create, product.update, product.delete
inventory.read, inventory.update
order.read, order.create, order.update, order.cancel

Exemplo de uso:

```python
@router.get("/customers")
async def list_customers(
    current_user: CurrentUser = Depends(require_permissions("customer.read")),
):
    ...
```

A autenticação determina quem é o usuário.

A autorização determina o que o usuário pode fazer.

17. Transactions

Operações que alteram múltiplos dados relacionados devem
utilizar transações quando necessário para preservar
a consistência.

Exemplo:

Criar pedido
     |
     +---- criar Order
     |
     +---- criar OrderItems
     |
     +---- atualizar Inventory

Se uma operação crítica falhar, os dados dependentes
devem permanecer consistentes.

18. PostgreSQL

PostgreSQL é o banco principal da aplicação.

A aplicação utilizará:

SQLAlchemy
asyncpg

As alterações estruturais serão controladas pelo Alembic.

Fluxo:

Model
   |
   v
Alembic Migration
   |
   v
PostgreSQL

Alterações estruturais não devem depender de edições manuais
do banco como fluxo normal de desenvolvimento.

19. Redis

Redis será utilizado para recursos que não devem depender
diretamente do armazenamento transacional principal.

Usos planejados:

cache;
rate limiting;
dados temporários;
suporte a processamento assíncrono;
coordenação de tarefas.

Redis não substitui PostgreSQL como fonte principal dos dados
transacionais do ERP.

20. Workers

Workers serão utilizados para processos que podem ser
executados de forma assíncrona.

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

A implementação concreta do mecanismo de filas será
definida posteriormente.

21. Frontend

O frontend comunica-se com o backend somente através
da API.

Fluxo:

React
  |
  | HTTP / JSON
  v
FastAPI
  |
  v
Business Logic
  |
  v
Database

O frontend não deve:

acessar PostgreSQL;
acessar Redis diretamente;
implementar regras de negócio que pertencem ao backend;
depender diretamente da estrutura interna do banco.
22. API Versioning

As APIs devem utilizar versionamento.

Padrão:

/api/v1/

Exemplo:

/api/v1/customers
/api/v1/products
/api/v1/orders

Uma nova versão somente deve ser criada quando existir
necessidade real de manter contratos incompatíveis.

Não criar novas versões apenas para organização.

23. Error Handling

A API deve possuir respostas consistentes.

Exemplos de categorias:

400
Bad Request

401
Unauthorized

403
Forbidden

404
Not Found

409
Conflict

422
Validation Error

500
Internal Server Error

A aplicação não deve expor detalhes internos desnecessários
ao cliente.

Erros internos devem ser registrados nos logs apropriados.

24. Logging

Logs devem seguir um padrão estruturado.

Implementação atual:

- JSON ou texto configurável via LOG_JSON
- Timestamp com timezone (America/Sao_Paulo)
- request_id, tenant_id, user_id incluídos automaticamente
- Configuração via setup_logging() em core/logging.py

Exemplo JSON:

{
  "timestamp": "2026-09-19T10:30:00-03:00",
  "level": "INFO",
  "logger": "app.http",
  "message": "request_completed",
  "request_id": "...",
  "tenant_id": 10,
  "user_id": 32,
  "method": "GET",
  "path": "/api/v1/customers",
  "status_code": 200,
  "duration_ms": 45.2
}

Não registrar:

passwords;
JWT;
refresh tokens;
API keys;
secrets;
informações sensíveis desnecessárias.

As regras detalhadas de logging estão em:

skills/observability/

25. Request ID

Requisições possuem um identificador para rastreamento.

Implementação atual:

- X-Request-ID aceito no request ou gerado automaticamente (UUID)
- Máximo 128 caracteres
- Incluído em todos os logs da requisição
- Retornado no header X-Request-ID da resposta
- Gerenciado via ContextVar em core/request_context.py

26. Auditoria

Logs técnicos e auditoria de negócio são conceitos diferentes.

Log técnico:

database_connection_failed
request_timeout
internal_exception

Auditoria (implementada):

- Tabela `audit_logs` append-only
- Registro por tenant (tenant_id)
- Campos: action, entity_type, entity_id, user_id, tenant_id, details, ip_address, user_agent
- Consulta via GET /api/v1/audit-logs com filtros e paginação
- Service: services/audit_log.py
- Repository: repositories/audit_log.py
- Schema: schemas/audit_log.py

Eventos relevantes de negócio devem possuir registro
de auditoria apropriado.

27. Testabilidade

A arquitetura deve favorecer testes.

Exemplo:

Service
   |
   v
Repository

Regras de negócio devem poder ser testadas sem depender
necessariamente da camada HTTP.

Tipos de teste planejados:

Unit
API
Integration
Security
Multi-Tenant
28. Dependências entre camadas

Dependências esperadas:

Router
  ↓
Service
  ↓
Repository
  ↓
Database

Outros componentes devem respeitar essa organização.

Evitar:

Router
  ↓
PostgreSQL

Evitar:

Schema
  ↓
Database

Evitar:

Frontend
  ↓
PostgreSQL
29. Regra de responsabilidade única

Cada camada e cada componente deve possuir uma
responsabilidade clara.

Evitar componentes que misturem:

HTTP;
regras de negócio;
persistência;
configuração;
apresentação.

Quando uma funcionalidade crescer, ela deve ser organizada
de forma coerente com as responsabilidades já existentes.

30. Regra de simplicidade

Não criar novas camadas, abstrações ou componentes
sem necessidade técnica.

Antes de criar uma nova solução:

Existe um padrão existente?
       |
       +---- SIM
       |      |
       |      v
       |   reutilizar
       |
       +---- NÃO
              |
              v
        avaliar nova solução

A arquitetura deve evoluir conforme necessidades reais
do sistema.

31. Alterações arquiteturais

Alterações significativas na arquitetura devem ser
documentadas.

Exemplos:

criação de nova camada;
mudança no padrão de comunicação;
alteração do mecanismo de persistência;
mudança na estratégia de autenticação;
adoção de novo serviço;
alteração do modelo de multi-tenancy.

Documentação arquitetural deve ficar em:

docs/architecture/
32. Regra final

Toda nova funcionalidade deve responder claramente:

Onde fica?
Qual camada é responsável?
De quem depende?
Quem pode chamar?
Como será testada?

Antes de implementar uma alteração arquitetural,
consultar também as skills específicas da área envolvida.


### Onde fica

```text
saas-erp-platform/
└── skills/
    └── 02-architecture.md