# Backend Services

## Objetivo

Definir os padrões para criação, organização e evolução dos services do SaaS ERP Platform.

Os services representam os casos de uso e as regras de negócio da aplicação.

Este documento complementa:

```text
skills/02-architecture.md
skills/backend/README.md
skills/backend/architecture.md
skills/backend/api.md
skills/backend/database.md
skills/backend/authentication.md
skills/backend/authorization.md
1. Responsabilidade

O service é responsável por transformar uma solicitação da aplicação em uma operação de negócio.

Exemplo:

HTTP Request
    ↓
Router
    ↓
Service
    ↓
Regra de negócio
    ↓
Repository
    ↓
Banco

O service deve responder:

O que precisa acontecer?
Em quais condições?
Em qual ordem?
O que deve acontecer quando algo falhar?
2. Service não é CRUD automático

Nem todo service deve simplesmente reproduzir:

create
get
list
update
delete

O service deve representar comportamentos reais do domínio.

Exemplo:

OrderService.create_order()
OrderService.cancel_order()
OrderService.confirm_order()
InventoryService.reserve_stock()
InventoryService.release_stock()

Os métodos devem representar casos de uso.

3. Estrutura

Os services ficam em:

backend/app/services/

Exemplo:

services/
├── auth.py
├── customer.py
├── product.py
├── category.py
├── inventory.py
├── order.py
└── ...

A organização deve acompanhar os domínios da aplicação.

4. Responsabilidades do Service

Um service pode:

validar regras de negócio;
coordenar repositories;
coordenar múltiplas entidades;
iniciar ou participar de transações;
verificar estado do recurso;
coordenar integrações;
disparar eventos ou jobs;
aplicar regras de autorização relacionadas ao domínio;
transformar resultados para o contrato esperado.
5. O que não deve ficar no Service

Evitar colocar no service:

HTML
CSS
lógica de interface
código React
detalhes de apresentação

Também evitar dependência desnecessária de:

Request
Response
Headers
Cookies

quando a lógica não precisar desses conceitos.

O service deve permanecer independente da camada HTTP sempre que possível.

6. Service e Router

Preferir:

Router
   ↓
Service

Em vez de:

Router
   ├── valida regra A
   ├── consulta banco
   ├── valida regra B
   ├── atualiza banco
   └── retorna

O router deve permanecer fino.

Exemplo:

@router.post("/customers")
async def create_customer(
    data: CustomerCreate,
    service: CustomerService = Depends(get_customer_service),
):
    return await service.create(data)
7. Service e Repository

Preferir:

Service
   ↓
Repository

O service determina o que fazer.

O repository determina como acessar os dados.

Exemplo:

CustomerService
    ↓
CustomerRepository.get_by_email()

Evitar que o service monte diretamente todas as queries SQL.

8. Regra de negócio

Regras de negócio pertencem ao service quando dependem do comportamento do domínio.

Exemplos:

cliente não pode possuir determinado estado
pedido não pode ser cancelado após faturamento
estoque não pode ficar negativo
produto inativo não pode ser vendido

Exemplo conceitual:

if product.deleted_at is not None:
    raise ProductInactiveError()

Essas regras não devem ficar escondidas no router.

9. Validação de entrada x Regra de negócio

Diferenciar:

Schema
→ formato dos dados

Service
→ significado e regra do negócio

Exemplo:

email precisa ter formato válido
→ Schema
cliente não pode possuir dois cadastros ativos com o mesmo identificador
→ Service + banco

O schema não deve assumir responsabilidades que dependem do estado do sistema.

10. Orquestração

Um dos principais papéis do service é coordenar diferentes componentes.

Exemplo de criação de pedido:

OrderService
   ↓
validar cliente
   ↓
buscar produtos
   ↓
validar estoque
   ↓
criar pedido
   ↓
criar itens
   ↓
baixar estoque
   ↓
finalizar operação

O service deve controlar essa sequência.

11. Services pequenos

Um service não deve se tornar um arquivo gigante.

Evitar um único arquivo contendo:

Customer
Product
Inventory
Order
Authentication
Reports
Integrations

Preferir separar por domínio.

12. Métodos

Métodos devem possuir responsabilidade clara.

Evitar:

async def process_everything(...):
    ...

Preferir:

async def create_order(...):
    ...

async def cancel_order(...):
    ...

async def confirm_order(...):
    ...

Cada método deve possuir um objetivo compreensível.

13. Nomes

Os nomes devem representar ações reais do domínio.

Preferir:

create_customer
update_customer
cancel_order
confirm_order
reserve_stock
release_stock

Evitar nomes genéricos como:

process
handle
execute
do_operation
manage

quando eles não comunicarem claramente a intenção.

14. Retorno

O service deve retornar dados necessários para a camada superior.

Pode retornar:

Entity
DTO
Schema-compatible object
Result object

conforme o padrão definido no projeto.

Não retornar objetos específicos da infraestrutura quando eles não forem apropriados para a camada superior.

15. Service não deve depender do frontend

Nunca assumir que uma regra pode ser protegida apenas pela interface.

O service deve funcionar corretamente mesmo que a chamada venha diretamente da API:

Frontend
API Client
Postman
Integration Hub
Outro consumidor

A regra de negócio pertence ao backend.

16. Tenant Context

Services que trabalham com entidades multi-tenant devem receber ou resolver o contexto do tenant de forma confiável.

Conceito:

Authenticated User
       ↓
Tenant Context
       ↓
Service
       ↓
Repository

Não utilizar um tenant_id arbitrário enviado pelo cliente como fonte de autorização.

17. Tenant Isolation

Antes de manipular um recurso:

recurso existe?
recurso pertence ao tenant?
recurso está disponível?

Exemplo conceitual:

customer = await repository.get_by_id(
    customer_id,
    tenant_id=current_tenant.id,
)

O service não deve ignorar o escopo do tenant.

18. Authorization

Uma permission pode permitir uma operação, mas não substitui as regras do domínio.

Exemplo:

Permission:
order.cancel

não significa:

qualquer pedido pode ser cancelado

O service ainda pode verificar:

pedido existe
pedido pertence ao tenant
pedido está em estado cancelável
19. Transactions

Quando uma operação envolver múltiplas alterações relacionadas, o service deve respeitar a fronteira transacional definida pela aplicação.

Exemplo:

create_order()
    ↓
create order
    ↓
create items
    ↓
update inventory
    ↓
commit

Se uma etapa falhar:

rollback

A operação não deve deixar o sistema em estado parcialmente atualizado.

20. Commit

Evitar commits arbitrários dentro de cada método individual.

Problema:

await repository.create(...)
await session.commit()

await repository.create_item(...)
await session.commit()

Se a segunda operação falhar, o sistema poderá ficar parcialmente persistido.

Preferir uma unidade transacional única quando o domínio exigir atomicidade.

21. Falhas

Falhas esperadas do domínio devem ser representadas de forma explícita.

Exemplos:

CustomerNotFound
ProductNotFound
InsufficientStock
ProductInactive
OrderNotFound
OrderAlreadyCancelled
OrderNotCancelable
DuplicateCustomer

Os nomes devem refletir comportamentos reais.

22. Exceptions

Não utilizar Exception genérica para representar toda regra de negócio.

Evitar:

raise Exception("erro")

Preferir uma exceção específica:

raise InsufficientStockError()

A camada HTTP poderá transformar essa exceção em um status adequado.

23. Service e HTTP Status

O service não deve precisar conhecer o status HTTP para executar sua regra.

Evitar:

raise HTTPException(
    status_code=409,
    detail="..."
)

diretamente na regra de negócio, quando isso puder ser separado.

Preferir:

raise DuplicateCustomerError()

e deixar a camada apropriada transformar o erro em:

409 Conflict
24. Service e FastAPI

Services não devem ficar fortemente acoplados ao FastAPI.

Evitar importar:

from fastapi import HTTPException

em toda regra de negócio.

Isso facilita:

unit tests
background jobs
CLI tools
workers
integrações internas
25. Service e schemas

Schemas são contratos da API.

O service pode receber dados representados por schemas ou por objetos equivalentes, mas não deve depender da camada HTTP para funcionar.

Quando necessário, considerar modelos internos ou estruturas específicas do domínio.

Evitar criar conversões excessivamente complexas sem necessidade.

26. Services compostos

Um service pode utilizar outro service quando isso representar uma dependência real de negócio.

Exemplo:

OrderService
    ↓
InventoryService

Mas evitar dependências circulares:

OrderService
    ↓
InventoryService
    ↓
OrderService

Se isso acontecer, revisar a separação das responsabilidades.

27. Dependency Injection

Dependências dos services devem ser fornecidas de forma previsível.

Exemplo conceitual:

class CustomerService:

    def __init__(
        self,
        repository: CustomerRepository,
    ):
        self.repository = repository

Isso facilita testes e reduz acoplamento.

Não criar containers ou frameworks de dependency injection adicionais sem necessidade.

28. Testabilidade

Um service deve poder ser testado sem depender obrigatoriamente de:

HTTP
Frontend
Internet
Serviços externos reais

Exemplo:

CustomerService
    ↓
Fake / Mock Repository

Isso permite testar as regras de negócio isoladamente.

29. Unit Tests

Testes unitários devem validar o comportamento do service.

Exemplo:

create_order()
    ↓
estoque suficiente
→ pedido criado
create_order()
    ↓
estoque insuficiente
→ InsufficientStockError

O foco deve estar na regra de negócio.

30. Integration Tests

Testes de integração devem validar a interação real entre:

Service
+
Repository
+
Database

Exemplo:

OrderService
    ↓
OrderRepository
    ↓
PostgreSQL

Esses testes são importantes para validar queries, constraints e transações.

31. Concorrência

Services que operam recursos compartilhados devem considerar concorrência.

Exemplo:

Usuário A
    ↓
compra último produto

Usuário B
    ↓
compra último produto

Uma simples verificação:

if stock > 0:

pode não ser suficiente em cenários concorrentes.

A solução deve utilizar mecanismos adequados de banco e transação.

32. Estoque

Operações de estoque devem preservar as regras do domínio.

Exemplo:

reserve_stock()
release_stock()
adjust_stock()

Quando aplicável, validar:

produto existe
produto está ativo
quantidade válida
estoque disponível
tenant correto

A proteção contra condições de corrida deve ocorrer na camada apropriada.

33. Idempotência

Services responsáveis por operações sujeitas a retry devem considerar idempotência.

Exemplo:

process_payment()
process_webhook()
sync_customer()

Uma repetição da mesma operação não deve produzir efeitos duplicados quando o caso de uso exigir idempotência.

34. Background Jobs

Um service deve poder ser utilizado por workers quando fizer sentido.

Exemplo:

HTTP Request
    ↓
Service

Worker
    ↓
Service

A regra de negócio não deve depender exclusivamente de um request HTTP.

Isso será importante para:

Integration Hub
sincronizações
processamentos em massa
tarefas assíncronas
35. Integrações externas

Não misturar detalhes de HTTP externo diretamente com toda a regra de negócio.

Preferir:

Service
   ↓
Integration Client
   ↓
External API

O service coordena a operação.

O client encapsula detalhes como:

URL
headers
authentication
timeout
payload
response
36. Retry

Retry não deve ser implementado indiscriminadamente.

Antes de repetir uma operação, avaliar:

erro transitório?
operação idempotente?
timeout?
rate limit?
erro permanente?

Retries inadequados podem duplicar efeitos.

37. Logs

Services podem registrar eventos relevantes, mas não devem gerar logs indiscriminadamente.

Registrar informações úteis para diagnóstico.

Exemplo:

order.created
order.cancelled
inventory.reserved
customer.created

Quando apropriado:

request_id
tenant_id
user_id
entity_id

Nunca registrar:

password
token
secret
credentials
38. Auditoria

Quando uma operação possuir relevância de negócio, o service pode disparar ou registrar a necessidade de auditoria.

Exemplo:

alteração de preço
cancelamento de pedido
mudança de permissão
movimentação de estoque

A implementação definitiva deve seguir as regras de observabilidade e auditoria do projeto.

39. Cache

Services podem utilizar cache quando apropriado.

Exemplo:

Service
   ↓
Cache
   ↓
Repository

Mas o cache não deve alterar incorretamente a regra de negócio.

Considerar:

tenant_id
invalidação
TTL
consistência
40. Performance

Não transformar services em uma sequência de consultas desnecessárias.

Evitar:

buscar cliente
buscar cliente novamente
buscar tenant
buscar tenant novamente
buscar produto individualmente várias vezes

quando os dados puderem ser obtidos de forma adequada.

Antes de otimizar, identificar o problema real.

41. Métodos longos

Métodos excessivamente longos devem ser avaliados.

Exemplo problemático:

async def create_order(...):
    # 300 linhas
    ...

Quando existir lógica independente e reutilizável, considerar extrair uma operação específica.

Mas não fragmentar artificialmente um método simples em dezenas de helpers.

42. Helpers privados

Métodos privados podem ser utilizados quando melhorarem a clareza.

Exemplo:

def _validate_order_state(...):
    ...

def _calculate_total(...):
    ...

Criar helpers somente quando existir responsabilidade claramente separável.

43. Cálculos de negócio

Cálculos importantes devem ser executados no backend.

Exemplos:

subtotal
desconto
impostos
total
saldo
quantidade disponível

Não confiar exclusivamente em valores calculados pelo frontend.

Quando o frontend enviar valores calculados, o backend deve validar ou recalcular conforme a regra do domínio.

44. Dados derivados

Quando um valor puder ser derivado de informações persistidas, definir claramente se ele deve ser:

calculado em tempo de consulta
armazenado
atualizado automaticamente

Evitar duplicação de estado sem necessidade.

45. Estados

Entidades com fluxo de estados devem ter transições controladas.

Exemplo:

Order
↓
draft
↓
confirmed
↓
completed

Não permitir transições arbitrárias.

Exemplo:

completed
→ draft

somente se existir regra explícita permitindo essa transição.

46. State Transition

Quando uma operação alterar o estado de um recurso, o service deve validar:

estado atual
+
operação solicitada
=
novo estado válido

Exemplo:

draft
→ confirm
→ confirmed

mas:

cancelled
→ confirm
→ inválido
47. Consistência

O service deve evitar deixar o domínio em estados impossíveis.

Exemplos:

pedido sem tenant
item sem pedido
estoque negativo
pedido cancelado ainda processando como ativo

A proteção pode envolver:

Service
+
Database Constraints
+
Transaction
48. Segurança

Services nunca devem assumir que dados vindos do router já estão autorizados.

Devem existir verificações apropriadas para:

tenant
ownership
estado
permissão

quando o caso de uso exigir.

49. Ordem de implementação

Ao criar um novo caso de uso:

1. Definir regra de negócio
2. Identificar entidades envolvidas
3. Identificar repositories necessários
4. Definir transação
5. Definir erros
6. Implementar service
7. Implementar router
8. Implementar autorização
9. Criar testes
10. Validar integração

Não começar pela rota sem compreender o comportamento do domínio.

50. Checklist

Antes de finalizar um service:

 Representa um caso de uso ou domínio claro;
 Regra de negócio está no local apropriado;
 Router permanece simples;
 Acesso ao banco está no repository;
 Tenant isolation foi considerado;
 Autorização foi considerada;
 Transações estão corretas;
 Erros de domínio são específicos;
 Não depende desnecessariamente do FastAPI;
 Pode ser testado isoladamente;
 Concorrência foi considerada quando necessária;
 Idempotência foi considerada quando necessária;
 Logs não expõem informações sensíveis;
 Não existe complexidade desnecessária.
51. Regra principal

O service deve ser o centro da regra de negócio.

A separação principal é:

Router
→ Como a requisição chega?

Schema
→ Qual formato os dados possuem?

Service
→ O que o sistema deve fazer?

Repository
→ Como os dados são persistidos?

Database
→ Como a integridade é garantida?

O objetivo é manter a regra de negócio independente da interface HTTP e suficientemente isolada para ser testada, reutilizada e evoluída.