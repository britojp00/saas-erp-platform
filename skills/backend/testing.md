# Backend Testing

## Objetivo

Definir os padrões para criação, organização, execução e manutenção dos testes do backend do SaaS ERP Platform.

Os testes devem proteger principalmente:

```text
Regras de negócio
API
Persistência
Autenticação
Autorização
Multi-tenancy
Integrações
Segurança

Este documento complementa:

skills/02-architecture.md
skills/backend/README.md
skills/backend/architecture.md
skills/backend/api.md
skills/backend/database.md
skills/backend/authentication.md
skills/backend/authorization.md
skills/backend/services.md
skills/backend/repositories.md
skills/backend/schemas.md
skills/backend/dependencies.md
skills/backend/exceptions.md
1. Princípios

Os testes devem ser:

confiáveis;
reproduzíveis;
rápidos quando possível;
independentes;
claros;
focados em comportamento.

Resultado atual: **269 passed**

Evitar testes criados somente para aumentar cobertura numérica.

O objetivo é detectar regressões reais.

2. Stack

O backend utiliza:

Pytest
pytest-asyncio
HTTPX
Coverage
FastAPI TestClient

Quando necessário, poderão ser utilizadas ferramentas adicionais já compatíveis com a arquitetura do projeto.

Novas dependências devem possuir justificativa.

3. Estrutura

Os testes ficam em:

backend/tests/

Estrutura:

tests/
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

A separação representa o nível de isolamento do teste.

4. Unit Tests

Testes unitários verificam uma unidade pequena do comportamento.

Exemplos:

Service
Validator
Helper
Domain logic

Normalmente não precisam de:

PostgreSQL real
Redis real
HTTP externo
5. Integration Tests

Testes de integração verificam a interação real entre componentes.

Exemplos:

Service
+
Repository
+
PostgreSQL

Também podem validar:

Transactions
Constraints
Indexes
Queries
Relationships

Quando o comportamento depender de PostgreSQL, testes reais de integração são preferíveis a mocks completos.

6. API Tests

Testes de API verificam:

HTTP Request
    ↓
FastAPI
    ↓
Dependencies
    ↓
Service
    ↓
Repository

Podem validar:

status code
response body
headers
validation
authentication
authorization
7. Quando utilizar cada tipo
Unit

Utilizar quando o objetivo for testar uma regra isoladamente.

Integration

Utilizar quando a interação entre componentes for importante.

API

Utilizar quando o contrato HTTP for parte do comportamento que precisa ser protegido.

Uma mesma funcionalidade pode possuir mais de um nível de teste.

8. Regra de comportamento

Testar comportamento, não detalhes internos.

Evitar testes excessivamente dependentes de:

nome de variável
implementação interna
quantidade exata de chamadas
estrutura privada

quando esses detalhes não fizerem parte do comportamento esperado.

9. Nomenclatura

Os nomes dos testes devem explicar o comportamento.

Preferir:

def test_create_customer_with_valid_data():
    ...
def test_create_customer_rejects_duplicate_email():
    ...
async def test_user_cannot_access_other_tenant_customer():
    ...

Evitar:

def test_customer_1():
    ...
10. Arrange / Act / Assert

Quando melhorar a clareza, estruturar os testes como:

Arrange
Act
Assert

Exemplo:

def test_example():
    # Arrange
    ...

    # Act
    result = ...

    # Assert
    assert result == ...

Não é obrigatório criar comentários quando o teste já for suficientemente claro.

11. Testes independentes

Cada teste deve poder executar independentemente.

Evitar:

teste A cria dado
↓
teste B depende desse dado
↓
teste C depende do teste B

A ordem dos testes não deve influenciar o resultado.

12. Dados de teste

Dados de teste devem ser:

previsíveis;
pequenos;
relevantes;
fáceis de compreender.

Evitar massas enormes de dados quando não forem necessárias.

13. Fixtures

Fixtures devem ser utilizadas para recursos realmente compartilhados.

Exemplos:

database session
test client
authenticated user
tenant

Evitar fixtures gigantes que criem todo o sistema para qualquer teste.

14. Fixtures simples

Uma fixture deve possuir responsabilidade clara.

Exemplo conceitual:

@pytest.fixture
async def db_session():
    ...

Outra:

@pytest.fixture
async def test_tenant():
    ...

Evitar uma única fixture que faça:

tenant
user
role
permissions
customers
products
orders

para todos os testes.

15. Test Database

Testes de persistência devem utilizar banco isolado.

Nunca executar testes destrutivos contra:

produção
banco de desenvolvimento compartilhado

A infraestrutura de testes deve garantir isolamento.

16. PostgreSQL Real

Quando uma funcionalidade depender de comportamento específico do PostgreSQL, utilizar PostgreSQL real em testes de integração.

Exemplos:

UUID
NUMERIC
JSONB
foreign keys
unique constraints
transactions
locking
indexes

Mocks não substituem completamente esses testes.

17. Testes de Repository

Repositories devem possuir testes para consultas importantes.

Exemplos:

get_by_id
get_by_email
list
create
update
soft_delete
restore

Quando aplicável, testar também:

pagination
sorting
filters
relationships
18. Tenant Isolation

Toda operação multi-tenant relevante deve possuir teste explícito de isolamento.

Exemplo:

Tenant A
└── Customer A

Tenant B
└── Customer B

Teste:

Tenant A → Customer A
✓

E:

Tenant A → Customer B
✗
19. Testes de GET

Para endpoints de leitura, testar:

recurso existente
recurso inexistente
tenant correto
tenant incorreto
registro excluído
filtros
paginação

quando aplicável.

20. Testes de CREATE

Para criação, testar:

dados válidos
dados inválidos
duplicidade
tenant correto
campos controlados pelo backend
constraints

quando aplicável.

21. Testes de UPDATE

Para atualização, testar:

recurso existente
recurso inexistente
tenant correto
tenant incorreto
campos permitidos
campos protegidos
validação
estado atual
22. Testes de DELETE

Para entidades com soft delete, testar:

registro ativo
↓
soft delete
↓
registro não aparece em consultas normais

Também testar:

outro tenant
→ operação bloqueada

quando aplicável.

23. Testes de Restore

Quando existir restore:

registro excluído
↓
restore
↓
registro volta a aparecer

Testar também:

registro ativo
→ restore

quando essa operação não fizer sentido.

24. Testes de Services

Services devem ser testados principalmente pelas regras de negócio.

Exemplos:

pedido pode ser cancelado
pedido não pode ser cancelado
estoque suficiente
estoque insuficiente
produto ativo
produto inativo
cliente duplicado

O teste deve comprovar o comportamento esperado.

25. Testes de Exceptions

Validar que a exception correta é gerada.

Exemplo:

with pytest.raises(InsufficientStockError):
    await service.create_order(...)

Isso protege a regra de domínio.

26. Testes de API + Exceptions

Além do service, validar a tradução para HTTP.

Exemplo:

InsufficientStockError
→ 409
CustomerNotFoundError
→ 404
PermissionDeniedError
→ 403
27. Testes de Authentication

Testar pelo menos:

login válido
senha incorreta
usuário inexistente
usuário inativo
usuário excluído
token válido
token inválido
token expirado
token ausente
28. Testes de Authorization

Testar:

usuário autenticado com permission
usuário autenticado sem permission

Exemplo:

customer.read
→ GET /customers
✓

Sem a permission:

customer.read
→ GET /customers
✗ 403
29. Testes de RBAC

Testar relações:

User
↓
Role
↓
Permission

Exemplos:

role possui permission
role não possui permission
usuário possui múltiplas roles
permission removida
role removida
30. Testes de Privilege Escalation

Testar tentativas de manipulação indevida.

Exemplo:

usuário comum
→ envia role Administrator

Resultado esperado:

acesso administrativo não concedido

Também testar tentativa de manipular:

tenant_id
user_id
permissions
roles

quando esses campos forem controlados pelo backend.

31. Testes Multi-tenant + Authorization

Testar as duas camadas juntas.

Exemplo:

Tenant A
User A
customer.read

deve permitir:

Customer A

mas não:

Customer B

mesmo com a permission correta.

32. Testes de Schemas

Testar validações estruturais.

Exemplos:

UUID inválido
email inválido
campo obrigatório
enum inválido
quantidade inválida
valor monetário
limites
33. Testes de Mass Assignment

Enviar campos que não deveriam ser controlados pelo cliente.

Exemplo:

{
  "name": "Cliente",
  "tenant_id": "other-tenant",
  "created_at": "2020-01-01T00:00:00Z"
}

O sistema não deve permitir que esses campos alterem o contexto ou os metadados controlados pelo backend.

34. Testes de Paginação

Testar:

primeira página
página intermediária
última página
página vazia
limite mínimo
limite máximo

Também testar ordenação estável.

35. Testes de Filtros

Quando um endpoint possuir filtros, testar:

sem filtro
um filtro
múltiplos filtros
valor inexistente
tenant + filtro

Os resultados devem respeitar todos os filtros simultaneamente.

36. Testes de Ordenação

Testar os campos permitidos.

Exemplo:

sort=name
sort=created_at

Também testar valores inválidos.

Não permitir que entrada arbitrária seja utilizada como coluna SQL.

37. Testes de Constraints

Quando a integridade depender do banco, validar:

UNIQUE
FOREIGN KEY
NOT NULL
CHECK

Exemplo:

SKU duplicado
→ operação rejeitada
38. Testes de Transactions

Operações multi-etapas devem testar rollback.

Exemplo:

Criar pedido
↓
Criar itens
↓
Atualizar estoque
↓
erro

Resultado esperado:

ROLLBACK

Nenhuma parte da operação deve permanecer persistida quando a unidade precisar ser atômica.

39. Testes de Concorrência

Funcionalidades sujeitas à concorrência devem possuir testes específicos quando necessário.

Exemplo:

Estoque = 1

Pedido A
+
Pedido B

O sistema não deve permitir:

estoque = -1

quando a regra do domínio proibir isso.

40. Testes de Idempotência

Operações idempotentes devem ser testadas através da repetição.

Exemplo:

mesma operação
↓
primeira execução
↓
segunda execução

O sistema deve produzir o comportamento definido pelo contrato sem duplicar efeitos indevidos.

41. Testes de Background Jobs

Workers devem ser testados para:

sucesso
falha
retry
limite de tentativas
idempotência
tenant context

quando essas funcionalidades forem implementadas.

42. Testes de Integrações

Integrações externas não devem depender necessariamente do serviço real em todos os testes.

Pode-se utilizar mocks ou servidores de teste para validar:

sucesso
timeout
HTTP 429
HTTP 500
payload inválido
resposta inesperada

Testes reais contra serviços externos devem ser separados e controlados.

43. Mocking

Mocks devem ser utilizados para isolar dependências externas quando necessário.

Não mockar tudo indiscriminadamente.

Exemplo:

Service
↓
Mock Repository

pode ser apropriado para unit test.

Enquanto:

Service
↓
Repository real
↓
PostgreSQL real

é apropriado para integração.

44. Mocking Excessivo

Evitar testes que simulam toda a implementação.

Exemplo problemático:

mock router
mock service
mock repository
mock database

e no final somente verificar que uma função chamou outra.

Esse tipo de teste pode passar mesmo quando a funcionalidade real está quebrada.

45. TestClient

O FastAPI TestClient pode ser utilizado para testes síncronos de API.

Exemplo:

from fastapi.testclient import TestClient

client = TestClient(app)

Testes assíncronos podem utilizar HTTPX conforme a necessidade.

46. Async Tests

Funções assíncronas devem utilizar a infraestrutura apropriada do pytest-asyncio.

Exemplo conceitual:

@pytest.mark.asyncio
async def test_example():
    ...

A configuração do projeto deve permanecer consistente.

47. Fixtures de API

Fixtures podem fornecer:

test client
async client
authenticated client
test user
test tenant

Evitar duplicar a criação desses objetos em dezenas de testes.

48. Authenticated Client

Pode ser útil possuir uma fixture que forneça um cliente autenticado.

Conceito:

authenticated_client

Essa fixture deve criar somente o contexto necessário.

Evitar esconder cenários importantes dentro de fixtures gigantes.

49. Database Cleanup

Os testes devem limpar ou isolar seus dados.

Estratégias possíveis:

transaction rollback
truncate
fresh database
containers

A estratégia final deve ser consistente com a infraestrutura de testes.

50. Test Order

Não depender da ordem de execução.

Evitar:

test_create
↓
test_update
↓
test_delete

onde cada teste depende do anterior.

Cada teste deve preparar seu próprio estado quando necessário.

51. Determinismo

Evitar testes dependentes de:

hora atual
UUID específico
ordem aleatória
rede externa
estado local do desenvolvedor

Quando necessário, controlar essas variáveis.

52. Time

Testes relacionados a tempo devem poder controlar o relógio quando o comportamento depender fortemente de:

expiração
TTL
created_at
updated_at
token expiration
retry schedule

Não depender exclusivamente do horário real da máquina.

53. Randomness

Quando utilizar dados aleatórios, garantir que o teste continue reproduzível.

Preferir dados fixos para cenários simples.

Não utilizar aleatoriedade onde ela não fornecer valor.

54. External Services

Testes que simulam APIs externas devem verificar:

request enviada corretamente
headers apropriados
payload correto
timeout
tratamento do status
retry

Não testar apenas o caso de sucesso.

55. Security Tests

Funcionalidades sensíveis devem possuir testes de segurança.

Exemplos:

cross-tenant access
privilege escalation
mass assignment
invalid JWT
missing authorization
resource ownership
56. Regression Tests

Quando um bug for corrigido, adicionar um teste que reproduza o comportamento problemático antes da correção, sempre que isso for viável.

Fluxo:

Bug
 ↓
Reprodução em teste
 ↓
Correção
 ↓
Teste passa

Isso reduz a chance de regressão.

57. Coverage

Coverage deve ser utilizada como indicador, não como objetivo isolado.

Uma cobertura de:

100%

não garante que o sistema esteja correto.

Priorizar testes de:

regras críticas
segurança
multi-tenancy
transações
operações financeiras
estoque
autenticação
58. Coverage de Branches

Quando uma regra possuir múltiplos caminhos, considerar cobertura de branches.

Exemplo:

if stock >= quantity:
    ...
else:
    ...

Testar ambos os caminhos.

59. Testes de Erros

Testar tanto:

sucesso

quanto:

falha esperada

e, quando relevante:

falha inesperada

Isso é especialmente importante para services e integrações.

60. Testes de Logs

Quando logging fizer parte do comportamento observável, testar campos importantes.

Exemplo:

event
request_id
tenant_id
user_id
error_code

Não criar acoplamento excessivo à mensagem textual.

61. Testes de Audit

Quando auditoria for implementada, testar:

ação registrada
actor correto
tenant correto
entidade correta
timestamp

Também verificar que informações sensíveis não sejam armazenadas indevidamente.

62. Testes de Exceptions HTTP

Verificar:

401
403
404
409
422
500

somente quando aplicáveis ao endpoint.

Não adicionar testes artificiais para status que a API não deveria produzir.

63. Testes de Health

O endpoint:

GET /health

deve possuir pelo menos um teste garantindo que a aplicação responde conforme o contrato estabelecido.

64. CI

Os testes devem poder executar no GitHub Actions.

O conjunto básico deverá incluir futuramente:

lint
tests
coverage
build

A execução deve ser reproduzível fora da máquina do desenvolvedor.

65. Comandos

A partir de:

backend/

executar:

uv run pytest

Coverage:

uv run coverage run -m pytest

Relatório:

uv run coverage report

HTML:

uv run coverage html

Lint:

uv run ruff check .

Formatação:

uv run ruff format --check .
66. Execução específica

Executar um arquivo:

uv run pytest tests/api/test_health.py

Executar um teste específico:

uv run pytest tests/api/test_health.py::test_health_check

Executar testes por palavra-chave:

uv run pytest -k customer
67. Warnings

Warnings relevantes não devem ser simplesmente ignorados.

Quando uma dependência ou framework gerar warning:

1. identificar causa
2. avaliar impacto
3. corrigir quando apropriado
4. evitar esconder com filtro indiscriminado

Não utilizar filterwarnings somente para deixar a saída visualmente limpa.

68. Test Failures

Ao corrigir um teste que falhou:

1. entender a causa
2. verificar se o comportamento esperado mudou
3. corrigir código ou teste
4. executar novamente

Não alterar assertions somente para fazer o teste passar sem verificar o comportamento.

69. Testes e Mudança de Contrato

Quando uma API mudar:

request schema
response schema
status code
error format

os testes correspondentes devem ser revisados.

Testes devem proteger o contrato real.

70. Testes e Banco

Quando uma migration alterar o schema, revisar os testes que dependem da estrutura.

Exemplos:

new column
constraint
index
foreign key
enum
71. Testes e Multi-tenancy

Qualquer nova entidade multi-tenant deve receber atenção específica para:

create
get
list
update
delete

Garantindo que o contexto do tenant seja mantido.

72. Testes e Soft Delete

Qualquer entidade com:

deleted_at

deve possuir comportamento consistente entre:

create
get
list
update
delete
restore

quando essas operações existirem.

73. Testes e Performance

Não criar testes extremamente lentos como padrão.

Quando uma operação possuir requisito de performance:

testar performance separadamente

Não misturar benchmarks pesados com a suíte funcional comum sem necessidade.

74. Benchmark

Benchmarks podem ser adicionados futuramente para consultas ou operações críticas.

Devem ser utilizados quando existir um problema ou requisito mensurável.

Não otimizar com base apenas em percepção subjetiva.

75. Testes de Segurança de Queries

Quando houver filtros ou ordenação dinâmicos, testar entradas inválidas ou malformadas para garantir que:

SQL injection

não seja possível através desses parâmetros.

A principal proteção deve permanecer no uso correto do SQLAlchemy.

76. Testes de Dados Monetários

Operações financeiras devem testar precisão.

Exemplo:

10.10
+
20.20
=
30.30

Não utilizar asserts baseados em comportamento impreciso de float para valores que utilizam Decimal.

77. Testes de Estoque

Operações de estoque devem testar:

quantidade suficiente
quantidade insuficiente
quantidade zero
quantidade inválida
produto inexistente
produto inativo
concorrência quando aplicável

Movimentações de estoque:

entrada (INCREASE)
saída (DECREASE)
quantidade inválida

Reservas de estoque:

criar reserva
confirmar reserva
liberar reserva
cancelar reserva
reserva com estoque insuficiente
reserva de produto inexistente
reserva de produto inativo

InventoryReservation:

order_item_id (nullable, FK para order_items)
reference (formato "order:{order_id}")
ondelete="SET NULL" para order_item_id
78. Testes de Pedidos

Pedidos devem testar estados importantes.

Exemplo:

DRAFT
↓
CONFIRMED
↓
COMPLETED

e:

CANCELLED

Transições válidas:

DRAFT → CONFIRMED
DRAFT → CANCELLED
CONFIRMED → COMPLETED
CONFIRMED → CANCELLED

Transições inválidas (devem falhar):

DRAFT → COMPLETED
CONFIRMED → DRAFT
COMPLETED → qualquer estado (terminal)
CANCELLED → qualquer estado (terminal)

Também testar:

order_number sequencial por tenant
itens do pedido
reserva de estoque
confirmação de reserva
cancelamento de reserva
notas do pedido

79. Testes de Integração Futura

O Integration Hub deverá possuir testes para:

API authentication
payload transformation
queue
worker
retry
idempotency
webhook
failure handling

Esses testes serão adicionados quando o projeto correspondente for implementado.

80. Testes e documentação

Quando um teste representar uma regra importante, o nome do teste pode servir como documentação executável.

Exemplo:

async def test_user_cannot_access_other_tenant_customer():
    ...

Isso facilita a compreensão do domínio.

81. O que não testar

Não é necessário criar testes para:

cada getter trivial
cada linha sem comportamento
implementação óbvia do framework
código externo já testado pela biblioteca

Priorizar comportamento relevante.

82. Refatoração

Refatorações devem manter os testes existentes passando.

Quando uma refatoração alterar somente estrutura interna:

comportamento externo
→ permanece igual

Os testes devem continuar validando o mesmo comportamento.

83. Testes antes da implementação

Quando apropriado, pode-se criar primeiro um teste que represente o comportamento esperado.

Fluxo:

requisito
↓
teste
↓
implementação
↓
teste passa

Não é obrigatório para toda tarefa, mas é útil para regras de negócio complexas.

84. Testes como contrato

Os testes devem funcionar como proteção contra mudanças acidentais.

Especialmente para:

API
Authentication
Authorization
Tenant Isolation
Business Rules
Database Integrity
85. Ordem de criação dos testes

Ao implementar uma nova funcionalidade, considerar:

1. Teste da regra de negócio
2. Teste de persistência
3. Teste da API
4. Teste de segurança
5. Teste de integração

Nem todos os níveis serão necessários para todas as funcionalidades.

86. Checklist

Antes de finalizar uma implementação:

 Existem testes para o comportamento principal;
 Casos de erro foram considerados;
 Authentication foi testada quando aplicável;
 Authorization foi testada quando aplicável;
 Tenant isolation foi testado;
 Soft delete foi testado quando aplicável;
 Constraints foram testadas quando relevantes;
 Transactions foram testadas quando relevantes;
 Concorrência foi considerada quando relevante;
 Idempotência foi testada quando relevante;
 Integrações externas possuem testes adequados;
 Testes não dependem da ordem;
 Testes são reproduzíveis;
 Warnings relevantes não foram simplesmente escondidos;
 Coverage foi utilizada como indicador;
 pytest passa;
 ruff check passa;
 ruff format --check passa.
87. Regra principal

Os testes devem proteger o comportamento que importa.

A prioridade é:

Segurança
+
Regras de negócio
+
Multi-tenancy
+
Integridade dos dados
+
Contrato da API
+
Integrações

Cobertura numérica é secundária.

Um teste deve existir porque protege um comportamento relevante, reduz risco de regressão ou documenta uma regra importante.