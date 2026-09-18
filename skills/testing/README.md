# Testing

## Objetivo

Definir a estratégia geral de testes do SaaS ERP Platform.

Os testes devem reduzir risco de regressões e validar os comportamentos importantes do sistema.

A estratégia deve considerar:

```text
Unit Tests
Integration Tests
API Tests
Frontend Tests
End-to-End Tests
Security Tests
Multi-tenant Tests
Contract Tests

Este documento complementa:

skills/00-project-overview.md
skills/01-project-structure.md
skills/02-architecture.md
skills/backend/testing.md
1. Princípios

Os testes devem ser:

confiáveis;
reproduzíveis;
independentes;
claros;
relevantes;
fáceis de manter.

O objetivo não é produzir a maior quantidade possível de testes.

O objetivo é proteger os comportamentos que possuem maior risco ou importância.

2. Pirâmide de Testes

A estratégia deve priorizar:

        E2E
       /   \
    API / Integration
      /       \
       Unit Tests

Preferir uma quantidade maior de testes rápidos e isolados.

Testes mais lentos ou dependentes de infraestrutura devem existir quando agregarem valor real.

3. Unit Tests

Testes unitários verificam comportamentos pequenos e isolados.

Podem ser utilizados para:

regras de negócio
validações
funções auxiliares
transformações
cálculos
estados

Devem ser rápidos e possuir poucas dependências externas.

4. Integration Tests

Testes de integração verificam a interação entre componentes.

Exemplos:

Service
+
Repository
+
PostgreSQL

ou:

Application
+
Redis

ou:

Worker
+
Queue

Esses testes são importantes quando mocks não conseguem representar adequadamente o comportamento real.

5. API Tests

Testes de API validam o contrato HTTP.

Devem verificar quando aplicável:

route
method
request
response
status code
authentication
authorization
validation
tenant isolation
6. Frontend Tests

O frontend deverá possuir testes próprios conforme a complexidade da aplicação.

Podem incluir:

component tests
hook tests
state tests
form tests
API interaction tests

O frontend não deve depender exclusivamente de testes E2E.

7. End-to-End Tests

E2E validam fluxos completos do sistema.

Exemplos:

Login
↓
Dashboard
↓
Criar cliente
↓
Criar produto
↓
Criar pedido
↓
Consultar pedido

Devem existir para fluxos críticos.

Evitar transformar toda a suíte em E2E, pois esses testes tendem a ser mais lentos e mais sensíveis à infraestrutura.

8. Security Tests

Testes de segurança devem proteger especialmente:

authentication
authorization
tenant isolation
privilege escalation
mass assignment
input validation

Esses testes não devem ser opcionais quando a funcionalidade afetar uma dessas áreas.

9. Multi-tenancy Tests

Toda funcionalidade que acessar dados de tenant deve considerar testes de isolamento.

Exemplo:

Tenant A
├── User A
└── Customer A

Tenant B
├── User B
└── Customer B

Validar:

User A → Customer A
✓

e:

User A → Customer B
✗
10. Security Boundary

Testes devem verificar não somente:

acesso autorizado

mas também:

acesso não autorizado

Exemplo:

permission correta
→ permitido
permission ausente
→ bloqueado
11. Authentication Tests

Devem cobrir quando aplicável:

login válido
senha inválida
usuário inexistente
usuário inativo
token inválido
token expirado
token ausente

Também verificar o vínculo correto entre:

User
+
Tenant
12. Authorization Tests

Testar:

permission presente
permission ausente
role correta
role incorreta
role removida
permission removida

Além de cenários de tentativa de elevação de privilégio.

13. Database Tests

Testes relacionados ao banco devem considerar:

constraints
foreign keys
unique
soft delete
transactions
indexes
relationships

Quando o comportamento depender especificamente do PostgreSQL, preferir PostgreSQL real em testes de integração.

14. Migration Tests

Migrations devem ser verificadas.

Quando relevante, validar:

upgrade
downgrade
schema result
constraints
indexes
data migration

Não assumir que uma migration gerada automaticamente está correta somente porque executou sem erro.

15. Test Database

Testes não devem utilizar:

produção
banco compartilhado de desenvolvimento

A infraestrutura de testes deve fornecer um banco isolado.

16. Test Data

Dados de teste devem ser:

determinísticos
pequenos
compreensíveis
reutilizáveis quando apropriado

Evitar dados aleatórios quando eles não agregarem valor.

17. Fixtures

Fixtures devem fornecer recursos comuns.

Exemplos:

database
tenant
user
authenticated client
test data

Evitar fixtures gigantes que escondam todo o estado criado pelo teste.

18. Test Isolation

Cada teste deve possuir estado independente.

Evitar depender da execução de outro teste.

Exemplo a evitar:

test_create
↓
test_update depende do create
↓
test_delete depende do update

Qualquer teste deve poder ser executado individualmente.

19. Determinism

Testes não devem depender desnecessariamente de:

hora atual
ordem de execução
rede externa
estado da máquina
aleatoriedade

Quando necessário, controlar essas variáveis.

20. External Services

Serviços externos devem normalmente ser simulados em testes automatizados.

Testar pelo menos:

success
timeout
429
500
authentication failure
invalid payload
unexpected response

Testes reais contra APIs externas devem ser separados e controlados.

21. Contract Tests

Quando uma integração for crítica, considerar testes de contrato.

O objetivo é garantir que:

request
+
response

continuem compatíveis com o contrato esperado.

Isso é particularmente importante para:

ERP API
Integration Hub
External APIs
22. API Contract

Alterações em:

request schema
response schema
status codes
error format
authentication

devem provocar revisão dos testes correspondentes.

Os testes devem proteger o contrato público da API.

23. Regression Tests

Quando um bug importante for corrigido, adicionar um teste que represente o comportamento problemático quando viável.

Fluxo:

Bug
↓
Teste reproduzindo problema
↓
Correção
↓
Teste passa
24. Critical Business Rules

As regras mais importantes do ERP devem possuir cobertura específica.

Exemplos:

estoque
pedidos
preços
totais
status
cancelamentos
permissões
multi-tenancy
25. Financial Tests

Operações financeiras devem testar precisão.

Utilizar:

Decimal

em vez de depender de float.

Testar valores como:

0.01
10.10
99.99
100.00

e operações que envolvam:

subtotal
desconto
total

quando fizerem parte do domínio.

26. Inventory Tests

Estoque deve possuir testes para:

entrada
saída
reserva
liberação
estoque insuficiente
quantidade inválida
produto inexistente
produto inativo

Quando houver concorrência, adicionar testes específicos.

27. Order Tests

Pedidos devem testar o ciclo de estados definido pelo domínio.

Exemplo:

draft
↓
confirmed
↓
completed

e cenários de:

cancelled

Também testar transições inválidas.

28. Soft Delete Tests

Entidades com deleted_at devem possuir comportamento consistente.

Testar:

registro ativo
→ aparece em consultas normais
soft delete
→ deixa de aparecer
restore
→ volta a aparecer

quando restore existir.

29. Pagination Tests

Listagens devem testar:

primeira página
página intermediária
última página
sem resultados
limite mínimo
limite máximo

Também validar ordenação estável.

30. Filter Tests

Testar:

sem filtros
um filtro
múltiplos filtros
valor inexistente
combinação de filtros
tenant + filtro

Os resultados devem respeitar todos os filtros aplicados.

31. Sorting Tests

Testar campos permitidos.

Exemplo:

name
created_at
updated_at

Também testar valores inválidos.

Não permitir entrada arbitrária para construir SQL.

32. Background Job Tests

Jobs devem possuir testes quando forem implementados.

Cobrir:

success
failure
retry
maximum attempts
idempotency
tenant context
reprocessing
33. Queue Tests

Quando uma fila for utilizada, testar:

job created
job consumed
job acknowledged
job failed
job retried

Também considerar:

duplicate delivery
worker interruption

quando o comportamento for relevante.

34. Idempotency Tests

Operações sujeitas a retry devem ser testadas através de repetição.

Exemplo:

operation
↓
execution 1
↓
execution 2

Validar que efeitos duplicados não ocorram quando o domínio exigir idempotência.

35. Concurrency Tests

Testes de concorrência devem existir quando uma funcionalidade puder apresentar condições de corrida.

Exemplos:

dois pedidos
→ mesmo estoque
duas sincronizações
→ mesmo registro

O resultado final deve permanecer consistente.

36. Frontend/API Integration Tests

Quando apropriado, testar a comunicação entre frontend e API.

Exemplos:

form
↓
API request
↓
validation error
↓
frontend displays error

ou:

login
↓
token
↓
authenticated request
37. E2E Critical Flows

Os fluxos E2E devem priorizar operações críticas.

Exemplos:

login
customer creation
product creation
order creation
inventory movement
permission management

Não testar cada pequena variação da interface em E2E.

38. Test Environment

O ambiente de testes deve possuir configurações próprias.

Não depender do:

.env

pessoal do desenvolvedor.

Consultar:

skills/infrastructure/environment.md

para regras de configuração.

39. CI

Os testes devem ser executáveis automaticamente no CI.

A pipeline deverá futuramente validar:

lint
unit tests
integration tests
coverage
build

conforme a evolução do projeto.

40. Local Execution

O desenvolvedor deve conseguir executar os testes localmente.

Para o backend:

cd backend
uv run pytest

Coverage:

uv run coverage run -m pytest
uv run coverage report

Formatação:

uv run ruff format --check .

Lint:

uv run ruff check .

Os comandos do frontend serão definidos na documentação específica do frontend.

41. Test Failures

Ao encontrar uma falha:

1. reproduzir
2. identificar causa
3. verificar comportamento esperado
4. corrigir implementação ou teste
5. executar novamente

Não alterar uma assertion somente para fazer o teste passar.

42. Warnings

Warnings relevantes devem ser investigados.

Evitar esconder warnings através de filtros globais sem compreender a causa.

Quando um warning for causado por uma dependência:

identificar
avaliar
documentar
corrigir quando apropriado
43. Coverage

Coverage deve ser um indicador.

Não utilizar:

100% coverage

como objetivo isolado.

Um projeto pode possuir alta cobertura e ainda não testar os comportamentos mais importantes.

Priorizar:

security
business rules
multi-tenancy
transactions
API contract
integrations
44. Branch Coverage

Quando existir lógica condicional relevante, testar os caminhos principais.

Exemplo:

if stock >= quantity:
    ...
else:
    ...

Ambas as situações devem ser testadas.

45. Negative Testing

Sempre que uma operação possuir regras de bloqueio, testar também o cenário inválido.

Exemplo:

usuário autorizado
→ permitido

e:

usuário não autorizado
→ bloqueado

Testes negativos são especialmente importantes para segurança.

46. Security Boundary Testing

Testar explicitamente fronteiras como:

unauthenticated
authenticated
authorized
unauthorized
same tenant
different tenant
owner
non-owner

Essas fronteiras devem ser preservadas durante refatorações.

47. Performance Tests

Testes de performance não devem fazer parte automaticamente da suíte funcional.

Utilizar quando existir:

requisito
problema identificado
consulta crítica
operação de alto volume

Medir antes e depois de alterações relevantes.

48. Load Tests

Load tests poderão ser adicionados futuramente para avaliar:

API throughput
database load
queue throughput
worker concurrency

Não executar cargas pesadas como parte do teste comum.

49. Testes de Segurança de Dados

Verificar que respostas não exponham:

password_hash
tokens
secrets
credentials
dados de outro tenant
campos internos

Esses testes são particularmente importantes para endpoints administrativos.

50. Testes de API Errors

Validar responses de erro relevantes:

400
401
403
404
409
422
500

somente quando aplicáveis.

Testar também a estrutura do erro.

51. Testes de Logging

Quando logging fizer parte do comportamento relevante, validar:

event
level
request_id
tenant_id
user_id
error_code

Não acoplar testes excessivamente ao texto das mensagens.

52. Audit Tests

Quando auditoria for implementada, testar:

actor
tenant
action
entity
entity_id
timestamp

Também verificar que dados sensíveis não sejam armazenados indevidamente.

53. Testes de Migrations

Quando uma migration for adicionada ou alterada:

migration applies
schema is correct
constraints are correct

quando aplicável.

Não editar uma migration já aplicada como forma de corrigir um problema.

Criar uma nova migration.

54. Testes e Refatoração

Refatorações internas devem preservar o comportamento esperado.

Se:

estrutura interna mudou

mas:

contrato externo permaneceu

os testes funcionais devem continuar passando.

Testes não devem depender excessivamente da implementação interna.

55. Testes e Arquitetura

A estrutura de testes deve refletir a arquitetura do projeto.

Exemplo:

unit
→ regras isoladas

integration
→ componentes reais

api
→ contrato HTTP

Evitar colocar todos os testes em um único diretório ou arquivo.

56. Testes e Documentação

Testes com nomes claros também funcionam como documentação executável.

Exemplo:

async def test_user_cannot_access_other_tenant_customer():
    ...

Esse nome comunica uma regra importante do sistema.

57. Testes de Integração com o ERP API

Como o Integration Hub consumirá a API real do ERP, os contratos importantes da API devem possuir testes que protejam:

authentication
authorization
tenant context
request schema
response schema
error responses
pagination

Isso reduz o risco de quebrar o consumidor futuro.

58. Testes do Integration Hub

Quando o Integration Hub for implementado, sua suíte deverá cobrir:

ERP API consumption
payload transformation
queue
worker
retry
idempotency
webhooks
failure handling

Os testes deverão validar tanto comportamento interno quanto integração com a API do ERP.

59. External API Isolation

Testes comuns não devem depender da disponibilidade de serviços externos reais.

O comportamento deve ser reproduzível mesmo quando:

internet
external API
provider

estiverem indisponíveis.

60. Test Naming

Nomes de testes devem comunicar:

contexto
ação
resultado esperado

Exemplo:

test_user_cannot_access_other_tenant_customer

Evitar:

test_case_01
test_case_02
61. Test Files

Organizar testes por domínio ou responsabilidade.

Exemplo:

tests/
├── unit/
│   ├── services/
│   └── schemas/
├── integration/
│   ├── repositories/
│   └── database/
└── api/
    ├── auth/
    ├── customers/
    └── orders/

A estrutura poderá evoluir conforme o volume crescer.

62. Test Helpers

Helpers de teste podem ser criados quando houver duplicação real.

Não criar um framework interno de testes antes de existir necessidade.

Preferir helpers simples e explícitos.

63. Factory de Dados

Factories podem ser utilizadas quando a criação manual de entidades estiver repetitiva.

Exemplo conceitual:

CustomerFactory
UserFactory
OrderFactory

Criar somente quando a repetição justificar.

64. Seed de Testes

Seeds ou fixtures permanentes podem ser utilizados para cenários comuns.

Não depender de dados criados manualmente no banco.

65. Test Cleanup

O mecanismo de limpeza deve ser previsível.

Possibilidades:

transaction rollback
truncate
isolated database
container

A estratégia deve ser centralizada.

66. Test Parallelism

Testes podem futuramente ser executados em paralelo.

Antes disso, garantir que:

dados
banco
arquivos
portas
recursos compartilhados

não criem dependências entre testes.

67. Temporary Files

Testes que criarem arquivos devem utilizar diretórios temporários.

Não gravar artefatos de teste aleatoriamente no repositório.

68. Environment Leakage

Testes não devem alterar permanentemente:

variáveis de ambiente
arquivos de configuração
banco local
estado global

Qualquer alteração temporária deve ser restaurada ao final.

69. Global State

Evitar depender de estado global mutável.

Quando isso for inevitável, os testes devem garantir isolamento e limpeza.

70. Async Tests

Operações assíncronas devem utilizar as ferramentas apropriadas.

O backend utiliza:

pytest-asyncio

conforme definido nas dependências do projeto.

71. Test Client

Para testes da API, utilizar a infraestrutura apropriada do FastAPI/HTTPX.

Exemplo atual do projeto:

from fastapi.testclient import TestClient

A estratégia poderá evoluir conforme a aplicação passar a utilizar infraestrutura assíncrona real.

72. Test Dependency Overrides

FastAPI permite substituir dependencies durante os testes.

Isso pode ser utilizado para:

test database
authenticated user
tenant
mock services

Os overrides devem permanecer restritos ao ambiente de testes.

73. Mocking

Mocks devem isolar:

external APIs
expensive infrastructure
unavailable services

quando apropriado.

Não mockar componentes internos simplesmente para evitar testes de integração.

74. Real Infrastructure

Utilizar infraestrutura real em testes quando ela fizer parte do comportamento que precisa ser validado.

Exemplos:

PostgreSQL
Redis
Queue

quando o comportamento depender especificamente deles.

75. Test Layers

Uma funcionalidade importante pode possuir:

Unit Test
+
Integration Test
+
API Test
+
E2E

Mas não é necessário reproduzir exatamente o mesmo cenário em todos os níveis.

Cada nível deve validar uma responsabilidade diferente.

76. Test Maintenance

Testes também precisam ser mantidos.

Ao alterar:

API
database
architecture
business rules
authentication
authorization

revisar os testes relacionados.

Não deixar testes obsoletos somente porque continuam passando.

77. Flaky Tests

Um teste que falha ocasionalmente deve ser tratado como problema.

Investigar causas como:

race condition
timing
external dependency
shared state
order dependence

Evitar simplesmente aumentar timeouts até esconder o problema.

78. Test Reliability

Antes de considerar uma suíte confiável, verificar:

repetibilidade
isolamento
determinismo
tempo de execução
dependências externas

Um teste que passa somente algumas vezes não deve ser considerado confiável.

79. Test Documentation

Quando a infraestrutura de testes possuir configuração não óbvia, documentar:

como executar
dependências
variáveis de ambiente
banco necessário
serviços necessários

O objetivo é permitir que outro desenvolvedor execute os mesmos testes.

80. Ordem de execução

A estratégia geral deve ser:

1. Unit tests
2. Integration tests
3. API tests
4. Security tests
5. E2E tests

A pipeline poderá combinar ou paralelizar etapas conforme a infraestrutura evoluir.

81. Pull Requests

Alterações significativas devem incluir testes apropriados.

Antes de considerar uma tarefa concluída:

implementação
↓
testes
↓
lint
↓
format
↓
review

quando aplicável.

82. Checklist

Antes de finalizar uma alteração:

 O comportamento principal possui teste;
 Casos de erro foram considerados;
 Segurança foi considerada;
 Multi-tenancy foi considerado;
 Testes de autenticação foram adicionados quando necessários;
 Testes de autorização foram adicionados quando necessários;
 Banco foi testado quando relevante;
 Transações foram testadas quando relevantes;
 Integrações foram testadas quando relevantes;
 Idempotência foi testada quando necessária;
 Concorrência foi considerada quando necessária;
 Testes são independentes;
 Testes são determinísticos;
 Não dependem de serviços externos reais sem necessidade;
 Warnings não foram simplesmente escondidos;
 Coverage foi usada como indicador;
 pytest passa;
 Lint passa;
 Formatação passa.
83. Regra principal

Testes devem proteger o comportamento importante do sistema.

A prioridade é:

Segurança
+
Regras de negócio
+
Multi-tenancy
+
Integridade
+
Contrato da API
+
Integrações

A cobertura numérica é apenas um indicador.

Um bom teste deve responder claramente:

Qual comportamento está sendo protegido?

e:

Qual regressão ele impediria?

A suíte deve evoluir junto com o sistema, mantendo equilíbrio entre confiança, velocidade e manutenção.