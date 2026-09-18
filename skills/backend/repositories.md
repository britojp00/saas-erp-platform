# Backend Repositories

## Objetivo

Definir os padrões para criação, organização e utilização dos repositories responsáveis pelo acesso aos dados no SaaS ERP Platform.

O repository encapsula as operações de persistência e consulta ao banco, mantendo detalhes do PostgreSQL e SQLAlchemy separados das regras de negócio.

Este documento complementa:

```text
skills/02-architecture.md
skills/backend/README.md
skills/backend/architecture.md
skills/backend/database.md
skills/backend/services.md
skills/database/README.md
skills/database/modeling.md
skills/database/multi-tenancy.md
skills/database/postgresql.md
1. Responsabilidade

O repository responde principalmente:

Como acessar os dados?
Como consultar?
Como inserir?
Como atualizar?
Como excluir?

A regra de negócio continua pertencendo ao service.

Fluxo esperado:

Router
   ↓
Service
   ↓
Repository
   ↓
SQLAlchemy
   ↓
PostgreSQL
2. Localização

Os repositories ficam em:

backend/app/repositories/

Exemplo:

repositories/
├── customer.py
├── product.py
├── category.py
├── inventory.py
├── order.py
└── user.py

A organização deve acompanhar os principais domínios persistidos.

3. Responsabilidades do Repository

Um repository pode:

buscar registros;
listar registros;
inserir entidades;
atualizar entidades;
realizar soft delete;
aplicar filtros;
realizar paginação;
carregar relacionamentos;
executar consultas específicas de persistência;
preservar o escopo do tenant.
4. O que não pertence ao Repository

Evitar colocar no repository:

regras de negócio
autenticação
autorização
lógica HTTP
respostas HTTP
HTML
lógica do frontend

Exemplo a evitar:

if order.status == "completed":
    raise OrderCannotBeCancelledError()

A decisão de negócio pertence ao service.

O repository deve fornecer os dados necessários para essa decisão.

5. Service x Repository

A separação deve ser:

Service
→ O pedido pode ser cancelado?

Repository
→ Como buscar o pedido?

Outro exemplo:

Service
→ O produto possui estoque suficiente?

Repository
→ Como consultar e atualizar o estoque?
6. Session

O repository deve utilizar a session fornecida pela infraestrutura.

Não criar uma nova engine ou session independente para cada operação.

Conceito:

class CustomerRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

A implementação definitiva deve seguir o padrão central de banco adotado pelo projeto.

7. Async

Como o backend utiliza SQLAlchemy assíncrono, repositories que realizam operações de banco devem respeitar o modelo async.

Exemplo:

async def get_by_id(...):
    result = await self.session.execute(...)

Não utilizar operações bloqueantes sem uma justificativa técnica.

8. Queries

Queries devem ser construídas através do SQLAlchemy.

Evitar montar SQL por concatenação de strings utilizando valores fornecidos pelo cliente.

Evitar:

query = f"SELECT * FROM customers WHERE name = '{name}'"

Preferir os mecanismos parametrizados do SQLAlchemy.

9. Tenant Context

Repositories de entidades multi-tenant devem considerar explicitamente o tenant_id.

Exemplo:

stmt = select(Customer).where(
    Customer.id == customer_id,
    Customer.tenant_id == tenant_id,
)

O repository não deve permitir consultas fora do escopo definido.

10. Tenant como requisito

Para entidades multi-tenant, operações como:

get
list
update
delete

devem considerar o tenant quando o domínio exigir.

Evitar métodos que permitam consultar uma entidade multi-tenant sem qualquer possibilidade de restrição de contexto.

11. Buscar por ID

Evitar:

async def get_by_id(self, customer_id):
    ...

para entidades cujo acesso obrigatoriamente dependa de tenant, se isso permitir esquecer o isolamento.

Preferir um contrato que torne o contexto explícito:

async def get_by_id(
    self,
    customer_id,
    tenant_id,
):
    ...
12. Not Found

O repository pode retornar:

None

quando um registro não existir.

Exemplo:

customer = await repository.get_by_id(
    customer_id,
    tenant_id,
)

if customer is None:
    raise CustomerNotFoundError()

A decisão sobre o significado de "não encontrado" pertence ao service ou à camada apropriada.

O repository não deve automaticamente transformar toda ausência em HTTPException.

13. Listagem

Repositories podem fornecer operações de listagem específicas.

Exemplo:

async def list(
    self,
    tenant_id,
    *,
    offset: int,
    limit: int,
):
    ...

A consulta deve realizar a paginação no banco.

Não buscar todos os registros para depois paginar em Python.

14. Filtros

Filtros devem ser aplicados no banco.

Exemplo conceitual:

stmt = select(Customer).where(
    Customer.tenant_id == tenant_id,
    Customer.deleted_at.is_(None),
)

if search:
    stmt = stmt.where(
        Customer.name.ilike(f"%{search}%")
    )

A construção definitiva deve seguir as regras de consulta do projeto.

15. Ordenação

Ordenação deve utilizar somente campos conhecidos.

Evitar:

stmt = stmt.order_by(text(sort))

quando sort vier diretamente do cliente.

Preferir um mapa controlado:

SORT_FIELDS = {
    "name": Customer.name,
    "created_at": Customer.created_at,
}

O valor recebido pela API deve ser validado antes de chegar à query.

16. Paginação

O repository deve realizar paginação no banco.

Exemplo conceitual:

stmt = (
    select(Customer)
    .where(...)
    .order_by(Customer.created_at.desc())
    .offset(offset)
    .limit(limit)
)

Os limites devem ser validados pela camada apropriada.

17. Ordenação estável

Paginação deve possuir ordenação estável.

Quando necessário:

created_at DESC
id DESC

Exemplo:

stmt = stmt.order_by(
    Customer.created_at.desc(),
    Customer.id.desc(),
)

Isso reduz resultados instáveis entre páginas.

18. Soft Delete

Repositories devem respeitar:

deleted_at IS NULL

nas consultas normais de entidades de negócio.

Exemplo:

stmt = select(Customer).where(
    Customer.tenant_id == tenant_id,
    Customer.deleted_at.is_(None),
)

Consultas que precisam acessar registros excluídos devem ser explicitamente identificadas.

19. Soft Delete Operation

Para uma exclusão lógica:

entity.deleted_at = datetime.now(timezone.utc)

Depois, o fluxo transacional deve seguir o padrão do projeto.

Não remover fisicamente o registro sem que essa seja uma decisão explícita do domínio.

20. Create

O repository pode encapsular a persistência inicial da entidade.

Exemplo:

async def create(self, customer: Customer) -> Customer:
    self.session.add(customer)
    await self.session.flush()
    return customer

O commit não deve ser automaticamente realizado pelo repository quando fizer parte de uma transação maior.

21. Commit

Repositories não devem executar commit() indiscriminadamente.

Evitar:

async def create(...):
    ...
    await self.session.commit()

quando o service precisar executar outras operações na mesma transação.

Preferir que a fronteira transacional seja controlada de forma centralizada.

22. Flush

flush() pode ser utilizado quando a aplicação precisar que o banco processe a operação antes do commit.

Exemplo:

self.session.add(order)
await self.session.flush()

Isso pode ser útil para:

obter ID
validar constraints
utilizar a entidade em operações seguintes

Não chamar flush() sem necessidade.

23. Update

Atualizações devem respeitar:

tenant_id
deleted_at
identificador

quando aplicáveis.

Evitar uma operação de update somente pelo ID em entidades multi-tenant.

Exemplo:

stmt = (
    update(Customer)
    .where(
        Customer.id == customer_id,
        Customer.tenant_id == tenant_id,
        Customer.deleted_at.is_(None),
    )
    .values(...)
)
24. Delete

Para entidades de negócio, utilizar soft delete quando esse for o padrão.

O repository deve possuir uma operação explicitamente nomeada:

soft_delete

quando isso melhorar a clareza.

Evitar um método genérico delete() cuja semântica possa gerar dúvida sobre exclusão física ou lógica.

25. Restore

Caso o domínio permita restaurar registros excluídos logicamente, criar uma operação específica:

restore

Exemplo:

entity.deleted_at = None

A operação deve possuir autorização e regras de negócio adequadas.

26. Relationships

Repositories podem carregar relacionamentos quando isso for necessário para a operação.

Exemplos:

selectinload
joinedload

A escolha deve considerar:

cardinalidade
volume
performance
necessidade da resposta

Não carregar relacionamentos automaticamente em todas as consultas.

27. N+1

Repositories devem evitar o padrão:

1 query
+
N queries adicionais

quando uma estratégia de carregamento adequada puder resolver o problema.

Exemplo:

stmt = select(Order).options(
    selectinload(Order.items)
)

A solução deve ser baseada no uso real.

28. Projeções

Repositories podem retornar somente os campos necessários quando isso reduzir custo de uma consulta.

Exemplo:

select(
    Customer.id,
    Customer.name,
)

Isso pode ser apropriado para:

autocomplete
selects
dashboards
listagens específicas

Não criar projeções excessivamente complexas sem necessidade.

29. Exists

Quando somente a existência de um registro for necessária, considerar uma consulta apropriada para existência em vez de carregar uma entidade completa.

Exemplos:

verificar SKU
verificar email
verificar relacionamento

A estratégia deve ser escolhida conforme a consulta e os índices existentes.

30. Count

Quando a API exigir total, o repository pode realizar uma consulta de contagem separada ou outra estratégia apropriada.

A contagem deve utilizar os mesmos filtros da listagem.

Exemplo conceitual:

list(...)
+
count(...)

Ambas devem respeitar:

tenant_id
deleted_at
filtros
31. Bulk Operations

Operações em massa podem ser necessárias para:

importações
sincronizações
ajustes
processamentos administrativos

Antes de utilizar bulk operations, avaliar:

triggers
events
relationships
updated_at
auditoria
regras de negócio

Não substituir automaticamente operações individuais por bulk update.

32. Concorrência

Repositories responsáveis por dados sujeitos a concorrência devem suportar a estratégia de proteção definida pelo service e pelo banco.

Possibilidades:

atomic update
SELECT FOR UPDATE
constraints
transaction isolation

Exemplo conceitual:

select(Product).where(
    Product.id == product_id,
    Product.tenant_id == tenant_id,
).with_for_update()

Utilizar locking somente quando necessário.

33. Estoque

Operações de estoque são particularmente sensíveis à concorrência.

Uma implementação que:

SELECT stock
↓
verifica
↓
UPDATE stock

sem proteção pode apresentar condição de corrida.

Quando necessário, utilizar uma estratégia atômica ou locking apropriado.

34. Constraints

Repositories não devem tentar substituir constraints do banco.

Exemplo:

UNIQUE
FOREIGN KEY
NOT NULL
CHECK

A aplicação pode fornecer validações amigáveis, mas o banco continua responsável por garantir integridade estrutural.

35. IntegrityError

Erros de integridade devem ser tratados de forma apropriada.

Exemplo:

unique violation
foreign key violation
check violation

O service ou uma camada de persistência adequada pode transformar o erro em uma exceção de domínio.

Não expor a mensagem bruta do PostgreSQL ao cliente.

36. Query Performance

Não otimizar queries sem evidência.

Quando uma consulta apresentar problema:

1. reproduzir
2. identificar query
3. avaliar índices
4. analisar plano quando necessário
5. alterar
6. medir novamente

Evitar criar índices indiscriminadamente.

37. Índices e Repository

A necessidade de índices deve surgir dos padrões reais de consulta.

Exemplos:

tenant_id + created_at
tenant_id + sku
tenant_id + status
tenant_id + external_id

A decisão deve ser tomada em conjunto com a modelagem e as migrations.

Consultar:

skills/database/postgresql.md
38. External IDs

Repositories que trabalham com integrações externas podem possuir métodos específicos:

get_by_external_id
find_by_source_and_external_id

Exemplo:

await repository.get_by_external_id(
    tenant_id=tenant_id,
    source_system="integration_x",
    external_id=external_id,
)

A consulta deve respeitar o escopo definido pelo domínio.

39. Idempotência

Repositories podem colaborar com mecanismos de idempotência através de:

unique constraints
idempotency keys
external IDs
processed markers

A decisão principal deve permanecer no service ou na operação de negócio.

40. Repository e cache

O repository não deve automaticamente implementar cache para toda consulta.

Preferir colocar decisões de cache em uma camada apropriada, normalmente acima do acesso puro ao banco.

Exemplo conceitual:

Service
   ↓
Cache
   ↓
Repository

O objetivo é evitar misturar persistência e estratégia de cache sem necessidade.

41. Repository e Redis

Redis não deve ser tratado como banco principal dentro do repository PostgreSQL.

Se uma operação depender de:

Redis
+
PostgreSQL

essa coordenação deve possuir uma responsabilidade arquitetural clara.

Não esconder uma operação complexa de múltiplas infraestruturas em um método aparentemente simples.

42. Transactions

Repositories devem participar de transações iniciadas conforme o padrão da aplicação.

Um repository não deve assumir que é responsável pela transação inteira quando a operação de negócio envolver múltiplos repositories.

Exemplo:

OrderService
   ↓
OrderRepository
   ↓
InventoryRepository
   ↓
commit
43. Rollback

O tratamento de rollback deve permanecer consistente com a infraestrutura de session.

Repositories não devem executar rollback silenciosamente e esconder uma falha importante da camada superior.

Exceções devem ser propagadas ou transformadas de forma explícita.

44. Exceptions

Repositories podem traduzir erros técnicos em exceções de persistência quando isso melhorar o isolamento da infraestrutura.

Exemplo:

DatabaseIntegrityError
DatabaseConnectionError

A camada superior decide como isso se relaciona com o domínio.

Não retornar HTTPException diretamente do repository.

45. Testes unitários

Repositories podem possuir testes específicos para:

filtros
tenant isolation
soft delete
paginação
ordenação
relationships
queries específicas

O foco é validar o comportamento da persistência.

46. Testes de integração

Quando a query depender fortemente de PostgreSQL, preferir testes de integração contra um banco real de teste.

Isso é especialmente importante para:

constraints
indexes
transactions
JSONB
PostgreSQL-specific behavior
locking

Mocks não substituem completamente esses testes.

47. Testes Multi-tenant

Toda entidade multi-tenant relevante deve testar:

Tenant A → registros A
Tenant B → registros B

E verificar:

Tenant A → registros B
✗

Esse teste deve existir também para:

get
list
update
soft_delete

quando aplicável.

48. Testes de Soft Delete

Validar:

registro ativo
→ aparece na listagem
registro excluído
→ não aparece na listagem normal
registro excluído
→ pode ser recuperado somente através de consulta explícita

quando essa funcionalidade existir.

49. Testes de Paginação

Testar:

limit
offset
ordenação
página vazia
última página

Também verificar que:

page N

não contém registros pertencentes a outro contexto de tenant.

50. Testes de Constraints

Quando uma regra depende do banco:

UNIQUE
FK
CHECK
NOT NULL

criar testes que confirmem o comportamento.

Isso protege a integridade mesmo quando a aplicação for modificada.

51. Nomenclatura dos métodos

Os métodos devem ser claros.

Exemplos:

get_by_id
get_by_email
get_by_external_id
list
create
update
soft_delete
restore
exists
count

Evitar nomes genéricos:

process
handle
run
execute

quando não comunicarem o objetivo.

52. Métodos genéricos

Evitar criar um repository universal com métodos excessivamente genéricos.

Exemplo:

BaseRepository

pode ser útil para comportamentos realmente comuns, mas não deve esconder particularidades importantes.

Não criar uma abstração genérica somente para reduzir algumas linhas de código.

53. Repository Base

Um BaseRepository poderá existir futuramente para comportamentos repetitivos, como:

session
get
add

Mas repositories específicos devem continuar livres para implementar consultas próprias.

Não forçar todos os repositories a possuir uma abstração genérica quando os domínios forem diferentes.

54. Clareza

Um método como:

get_active_customer_by_id()

pode ser mais claro que:

find()

quando a semântica da consulta for importante.

A prioridade é comunicar o comportamento da operação.

55. Segurança

Repositories devem assumir que os argumentos podem estar incorretos.

Não confiar em:

tenant_id
user_id
entity_id

somente por terem vindo de uma camada superior.

O isolamento deve ser reforçado na própria consulta quando apropriado.

56. Dados retornados

Repositories não devem retornar mais dados do que o necessário quando isso puder aumentar:

custo
acoplamento
exposição

Especialmente em listagens e consultas administrativas.

57. Repository e API Response

Não formatar diretamente responses HTTP no repository.

Evitar:

return {
    "status": 200,
    "data": customer,
}

A resposta HTTP pertence à camada da API.

O repository retorna dados de persistência.

58. Repository e Logs

Repositories não devem registrar cada query automaticamente em logs de aplicação.

Logs de SQL para desenvolvimento podem existir como configuração temporária.

Em produção, logging excessivo de queries pode:

aumentar volume
expor dados
reduzir performance

Logs de aplicação devem se concentrar em eventos relevantes.

59. Repository e auditoria

Repositories não devem ser automaticamente responsáveis por auditoria de negócio.

Exemplo:

UPDATE customers

não necessariamente significa:

customer.price_changed

A primeira é uma operação de persistência.

A segunda é um evento de negócio.

Essa distinção deve ser mantida.

60. Ordem de implementação

Ao criar um novo repository:

1. Identificar entidade
2. Identificar consultas necessárias
3. Definir escopo de tenant
4. Definir comportamento de soft delete
5. Definir filtros
6. Definir ordenação
7. Definir paginação
8. Implementar query
9. Avaliar índices
10. Criar testes
11. Integrar ao service

Não criar métodos genéricos antes de conhecer os casos reais de uso.

61. Checklist

Antes de finalizar um repository:

 Responsabilidade está limitada à persistência;
 Não contém regras de negócio;
 Não contém lógica HTTP;
 Utiliza a session centralizada;
 Operações são assíncronas quando apropriado;
 Queries utilizam SQLAlchemy;
 Tenant isolation foi aplicado;
 Soft delete foi considerado;
 Paginação ocorre no banco;
 Ordenação é controlada;
 Não existe SQL inseguro;
 N+1 foi considerado;
 Relationships são carregados somente quando necessários;
 Transactions são respeitadas;
 Commit não ocorre arbitrariamente;
 Constraints do banco são respeitadas;
 Testes existem;
 Não foi criada abstração desnecessária.
62. Regra principal

O repository deve responder somente à pergunta:

Como o sistema acessa e persiste os dados?

A separação deve permanecer:

Router
→ HTTP

Schema
→ contrato e validação

Service
→ regra de negócio

Repository
→ persistência

PostgreSQL
→ integridade e armazenamento

Um repository bem definido mantém a infraestrutura de dados isolada sem esconder a lógica de negócio dentro de consultas genéricas.