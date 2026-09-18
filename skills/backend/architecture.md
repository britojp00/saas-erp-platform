# Backend Architecture

## Objetivo

Definir as decisões arquiteturais e os padrões de implementação utilizados no backend do SaaS ERP Platform.

Este documento complementa:

```text
skills/02-architecture.md
skills/backend/README.md

As regras aqui são específicas para a implementação do backend.

1. Fluxo principal

O fluxo padrão de uma operação HTTP deve seguir:

HTTP Request
     ↓
Router
     ↓
Dependencies
     ↓
Schema
     ↓
Service
     ↓
Repository
     ↓
SQLAlchemy
     ↓
PostgreSQL
     ↓
Repository
     ↓
Service
     ↓
Schema
     ↓
HTTP Response

Nem toda operação precisará obrigatoriamente utilizar todas as camadas, mas a responsabilidade de cada camada deve permanecer clara.

2. Router

Os routers ficam em:

backend/app/api/v1/

O router deve ser responsável principalmente por:

definição dos endpoints;
métodos HTTP;
parâmetros;
dependencies;
schemas de entrada;
schemas de saída;
status codes;
chamada dos services.

Exemplo conceitual:

@router.post(
    "/customers",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_customer(
    data: CustomerCreate,
    service: CustomerService = Depends(get_customer_service),
):
    return await service.create(data)

Evitar colocar regras extensas dentro do endpoint.

Evitar consultas SQL diretamente no router.

Evitar manipulação manual de entidades do banco dentro do router quando isso puder ser responsabilidade de outra camada.

3. Dependencies

Dependencies do FastAPI devem ser utilizadas para responsabilidades transversais e obtenção de contexto.

Exemplos:

Database Session
Authenticated User
Current Tenant
Authorization
Request Context

Uma dependency deve resolver uma responsabilidade clara.

Evitar utilizar dependencies como local genérico para regras de negócio.

4. Schemas

Os schemas devem representar os contratos da API.

Estrutura conceitual:

schemas/
├── customer.py
├── product.py
├── order.py
└── ...

Separar quando necessário:

Create
Update
Response
List
Filter

Exemplo:

class CustomerCreate(BaseModel):
    name: str
    email: str | None = None


class CustomerResponse(BaseModel):
    id: UUID
    name: str
    email: str | None = None

O schema não deve conhecer detalhes de infraestrutura.

Evitar:

class CustomerCreate(BaseModel):
    async def save_to_database(self):
        ...

Validação relacionada exclusivamente ao formato dos dados deve ficar nos schemas.

Validações de regra de negócio devem ficar nos services.

5. Services

Services representam os casos de uso da aplicação.

Estrutura conceitual:

services/
├── customer.py
├── product.py
├── inventory.py
├── order.py
└── ...

Um service pode:

validar regras de negócio;
consultar repositories;
coordenar múltiplas operações;
controlar transações;
chamar serviços externos;
publicar eventos;
coordenar processamento assíncrono.

Exemplo conceitual:

class OrderService:

    async def create_order(...):
        ...

O service não deve depender diretamente da camada HTTP.

Evitar importar Request, Response ou detalhes específicos do FastAPI dentro da regra central de negócio quando não forem necessários.

6. Repositories

Repositories isolam o acesso aos dados.

Estrutura conceitual:

repositories/
├── customer.py
├── product.py
├── inventory.py
└── order.py

Um repository pode realizar:

SELECT
INSERT
UPDATE
DELETE
JOIN
FILTER
PAGINATION

Mas não deve decidir regras de negócio que pertencem ao service.

Exemplo:

customer = await repository.get_by_id(customer_id)

O repository pode determinar como buscar o registro.

O service determina o que fazer com o resultado.

7. Dependência entre camadas

A direção das dependências deve ser previsível:

Router
  ↓
Service
  ↓
Repository
  ↓
Database

Evitar dependências no sentido contrário.

Por exemplo, um repository não deve depender de um router.

Um model não deve importar um service.

Um schema não deve importar um router.

Quanto menor o acoplamento entre as camadas, mais simples será testar e evoluir o backend.

8. Models

Os models ficam em:

backend/app/models/

Eles representam entidades persistidas.

Os models não devem conter:

regras HTTP;
responses da API;
autenticação;
lógica de apresentação;
código específico do frontend.

Regras relacionadas ao banco devem permanecer próximas ao model quando apropriado, como:

foreign keys;
constraints;
índices;
relacionamentos;
tipos das colunas.
9. Banco de dados e Session

A sessão do banco deve ser gerenciada de forma centralizada.

A implementação deve permitir:

abertura da sessão;
uso durante a requisição;
commit;
rollback;
fechamento.

O ciclo conceitual é:

Request
   ↓
Session
   ↓
Service
   ↓
Repository
   ↓
Commit / Rollback
   ↓
Close

Não criar conexões manualmente em cada endpoint.

10. Transações

A fronteira da transação deve acompanhar a operação de negócio.

Exemplo:

Criar Pedido
├── validar cliente
├── criar pedido
├── criar itens
├── atualizar estoque
└── registrar operação

Quando essas operações fizerem parte de uma única unidade de negócio, devem permanecer consistentes.

Em caso de falha:

ROLLBACK

O sistema não deve deixar registros parcialmente persistidos.

11. Multi-tenancy

Toda operação que manipula dados pertencentes a um tenant deve utilizar o contexto do tenant autenticado.

Fluxo conceitual:

JWT
 ↓
Authenticated User
 ↓
Tenant Context
 ↓
Service
 ↓
Repository
 ↓
tenant_id filter

Nunca confiar diretamente em:

tenant_id enviado pelo frontend

como fonte de autorização.

Exemplo conceitual:

await repository.get_by_id(
    entity_id=customer_id,
    tenant_id=current_tenant.id,
)

A filtragem pelo tenant deve fazer parte do padrão das operações multi-tenant.

12. Isolamento entre tenants

Uma consulta como:

SELECT *
FROM customers
WHERE id = :customer_id;

pode ser insuficiente em um sistema multi-tenant.

Quando a entidade pertence a um tenant, a consulta deve considerar o contexto:

SELECT *
FROM customers
WHERE id = :customer_id
  AND tenant_id = :tenant_id;

O mesmo princípio vale para:

UPDATE;
DELETE;
listagens;
relacionamentos;
buscas;
cache;
jobs;
integrações.
13. Soft Delete

Entidades de negócio utilizarão:

deleted_at

Regra:

deleted_at IS NULL
    → registro ativo

deleted_at IS NOT NULL
    → registro logicamente excluído

Consultas normais devem ignorar registros excluídos logicamente.

Operações administrativas ou de manutenção podem utilizar consultas específicas quando necessário.

O comportamento deve ser consistente em todos os repositories.

14. Autenticação

A autenticação deve seguir:

Credentials
     ↓
Validate Identity
     ↓
Generate JWT
     ↓
Authenticated Request

O JWT representa a identidade autenticada.

O token não deve ser considerado substituto de autorização.

Depois de identificar o usuário, o backend ainda deve verificar:

User
 ↓
Tenant
 ↓
Role
 ↓
Permission
 ↓
Action
15. Autorização

Autorização deve ser baseada nas permissões da aplicação.

Fluxo:

Request
 ↓
Authenticated User
 ↓
Permission Check
 ↓
Business Operation

Exemplo conceitual:

customer.read
customer.create
customer.update
customer.delete

A regra deve ser centralizada o máximo possível para evitar verificações inconsistentes.

16. Contexto autenticado

Durante uma requisição autenticada, o backend poderá possuir um contexto semelhante a:

request_id
user_id
tenant_id
roles
permissions

Esse contexto pode ser utilizado por:

autorização;
logs;
auditoria;
queries;
serviços;
processamento assíncrono.

O contexto não deve depender de informações manipuláveis pelo cliente.

17. Status HTTP

Os endpoints devem utilizar status HTTP adequados.

Exemplos:

200 OK
201 Created
204 No Content
400 Bad Request
401 Unauthorized
403 Forbidden
404 Not Found
409 Conflict
422 Unprocessable Entity
500 Internal Server Error

A escolha deve refletir o significado real da operação.

Não utilizar 200 OK indiscriminadamente para erros de negócio.

18. Erros de domínio

Regras de negócio que falham devem possuir representação consistente.

Exemplos:

CustomerNotFound
ProductNotFound
InsufficientStock
DuplicateCustomer
OrderAlreadyProcessed
PermissionDenied

Esses erros podem ser convertidos em respostas HTTP por uma camada apropriada.

Evitar espalhar strings arbitrárias de erro por todo o sistema.

19. Erros internos

Erros inesperados devem:

gerar rollback quando necessário;
ser registrados nos logs;
não expor detalhes internos ao cliente;
possuir resposta HTTP consistente.

Não retornar:

stack trace
SQL query interna
senha
token
secret
credencial

na resposta da API.

20. Paginação

Listagens potencialmente grandes devem possuir paginação.

Evitar endpoints que retornem quantidade ilimitada de registros.

Estratégias aceitas podem incluir:

offset / limit
cursor pagination

A estratégia escolhida deve considerar:

volume de dados;
performance;
ordenação;
estabilidade dos resultados;
necessidade da API.
21. Filtros

Filtros devem ser explícitos e validados.

Exemplo conceitual:

GET /customers?search=joao&status=active

Evitar montar SQL diretamente utilizando strings fornecidas pelo cliente.

As consultas devem utilizar os mecanismos de parametrização do SQLAlchemy.

22. Ordenação

A ordenação recebida pela API deve ser validada contra campos permitidos.

Não permitir que o cliente injete nomes arbitrários de colunas diretamente em SQL.

Exemplo conceitual:

sort=name
sort=created_at

O backend deve mapear esses valores para colunas conhecidas.

23. Cache

Quando Redis for utilizado para cache, a chave deve considerar o contexto necessário.

Em dados multi-tenant, evitar:

customer:123

quando 123 puder existir em diferentes contextos.

Preferir uma estrutura que isole o tenant, por exemplo:

tenant:{tenant_id}:customer:{customer_id}

A estratégia final deve considerar a natureza do dado.

24. Background Jobs

Jobs devem carregar o contexto mínimo necessário para executar corretamente.

Quando uma tarefa depender de tenant:

job
 ├── tenant_id
 ├── entity_id
 └── operation

O worker deve validar novamente esse contexto.

Não assumir que dados presentes em uma mensagem ou fila são automaticamente confiáveis.

Operações críticas devem ser idempotentes sempre que possível.

25. Idempotência

Operações que podem ser repetidas devido a:

retry;
timeout;
reprocessamento;
duplicidade de mensagens;
falhas de rede;

devem considerar idempotência.

Exemplo:

external_id
idempotency_key
unique constraint
processed_at

A estratégia depende do caso de uso.

Não criar mecanismos de idempotência genéricos sem uma necessidade concreta.

26. Integrações externas

Chamadas externas devem possuir:

timeout
tratamento de erro
logs
retry quando apropriado

Não permitir que uma API externa fique bloqueando indefinidamente uma requisição do backend.

Quando uma operação puder ser processada de maneira assíncrona, considerar background jobs ou workers.

27. Request ID

Cada requisição deve possuir um identificador de rastreamento.

Conceito:

HTTP Request
    ↓
request_id
    ↓
logs
    ↓
service
    ↓
external integration

O request_id facilita investigação de erros e correlação de eventos.

Quando possível, preservar um identificador recebido por sistemas confiáveis ou gerar um novo.

28. Auditoria

Auditoria de negócio não deve depender somente dos logs técnicos.

Exemplos de ações que podem exigir auditoria:

Login
Alteração de permissões
Exclusão de cliente
Alteração de preço
Movimentação de estoque
Cancelamento de pedido

O registro de auditoria deve considerar pelo menos:

tenant_id
user_id
action
entity
entity_id
timestamp

Informações adicionais podem ser adicionadas quando forem necessárias.

29. Observabilidade

O backend deve permitir identificar:

quem
fez o quê
quando
em qual tenant
em qual requisição

Quando aplicável, correlacionar:

request_id
tenant_id
user_id
event

Logs técnicos, métricas e auditoria devem possuir responsabilidades distintas.

30. Testabilidade

A arquitetura deve permitir testar cada camada isoladamente quando fizer sentido.

Exemplo:

Service
  ↓
Mock Repository

Isso permite testar regras de negócio sem depender sempre do banco real.

Para comportamentos de integração:

API
  ↓
Service
  ↓
Repository
  ↓
Test Database

Os testes devem escolher o nível adequado ao comportamento que está sendo validado.

31. Evitar overengineering

Não introduzir automaticamente:

Factory
Abstract Factory
Generic Repository
Event Bus
CQRS
Dependency Injection Framework
Microservices

sem necessidade concreta.

O projeto deve utilizar a menor complexidade capaz de atender corretamente aos requisitos.

Arquitetura evolui conforme o sistema evolui.

32. Reutilização

Código compartilhado deve ser criado quando existir reutilização real.

Evitar criar funções genéricas apenas porque duas operações parecem semelhantes.

Primeiro priorizar:

clareza
correção
consistência

Depois abstrair quando houver repetição comprovada.

33. Segurança por padrão

Novas funcionalidades devem partir do princípio:

não autenticado
    → sem acesso

tenant diferente
    → sem acesso

sem permissão
    → sem acesso

O acesso deve ser concedido explicitamente conforme as regras da aplicação.

34. Ordem de implementação

Ao desenvolver uma nova funcionalidade de backend:

1. Regra de negócio
2. Model
3. Migration
4. Schema
5. Repository
6. Service
7. Router
8. Authorization
9. Tests
10. Documentation

Nem toda funcionalidade exigirá alterações em todas essas etapas.

A ordem serve como referência para evitar começar pelo endpoint antes de compreender a regra de negócio e a persistência.

35. Checklist arquitetural

Antes de finalizar uma implementação:

 A responsabilidade está na camada correta;
 Router não possui regra de negócio excessiva;
 Schema representa corretamente o contrato;
 Service concentra a regra de negócio;
 Repository concentra acesso ao banco;
 Multi-tenancy foi considerado;
 Autorização foi considerada;
 Transações estão corretas;
 Soft delete foi considerado quando aplicável;
 Erros possuem comportamento consistente;
 Logs não expõem secrets;
 Testes cobrem o comportamento;
 Não foi adicionada complexidade desnecessária.
36. Regra principal

A arquitetura do backend deve permanecer:

Clara
Modular
Testável
Segura
Multi-tenant
Observável
Evolutiva

A separação de responsabilidades deve existir para tornar o sistema mais previsível e sustentável, e não para criar camadas desnecessárias.