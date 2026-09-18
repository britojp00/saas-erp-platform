# Backend Integrations

## Objetivo

Definir os padrões para integração do SaaS ERP Platform com APIs, serviços e sistemas externos.

As integrações devem ser tratadas como componentes externos ao domínio principal e possuir limites claros entre:

```text
ERP
 ↓
Integration Client
 ↓
External System

Este documento complementa:

skills/02-architecture.md
skills/backend/README.md
skills/backend/architecture.md
skills/backend/services.md
skills/backend/repositories.md
skills/backend/exceptions.md
skills/backend/logging.md
skills/backend/background-jobs.md
skills/infrastructure/environment.md
1. Princípios

Integrações devem ser:

isoladas;
testáveis;
observáveis;
resilientes;
seguras;
idempotentes quando necessário;
independentes dos detalhes internos do ERP.

Uma falha externa não deve contaminar desnecessariamente toda a arquitetura interna.

2. Arquitetura

O fluxo esperado é:

Router
   ↓
Service
   ↓
Integration Client
   ↓
External API

Quando a operação for assíncrona:

Router
   ↓
Service
   ↓
Queue
   ↓
Worker
   ↓
Integration Client
   ↓
External API
3. Integration Client

O client encapsula a comunicação com o sistema externo.

Responsabilidades:

HTTP
Headers
Authentication
Timeout
Payload
Response
External errors

Exemplo conceitual:

CustomerSyncService
       ↓
ExternalCustomerClient
       ↓
External API

O service não deve precisar conhecer detalhes de URL, headers ou bibliotecas HTTP específicas.

4. Service x Integration Client

O service decide:

O que precisa ser sincronizado?
Quando deve ser enviado?
Quais regras devem ser aplicadas?

O client decide:

Como chamar a API externa?
Qual endpoint?
Quais headers?
Qual payload HTTP?
Como interpretar a resposta?
5. Localização

Clients de integração podem ser organizados em:

backend/app/integrations/

Exemplo:

integrations/
├── erp/
├── payments/
├── notifications/
└── external_system/

A estrutura definitiva deve acompanhar a quantidade e o tipo de integrações existentes.

6. Um client por sistema

Quando uma integração possuir comportamento relevante, preferir um client próprio.

Exemplo:

ExternalSystemClient

em vez de espalhar chamadas HTTP por vários services.

Isso centraliza:

authentication
base URL
headers
timeouts
serialization
error handling
7. HTTP Client

A biblioteca HTTP utilizada deve ser definida centralmente.

Evitar criar clients diferentes sem necessidade.

A escolha deve considerar:

async support
timeouts
connection pooling
testability
observability

O código de negócio não deve depender diretamente dos detalhes da biblioteca.

8. Base URL

URLs externas devem vir de configuração.

Exemplo:

EXTERNAL_API_URL=https://api.example.com

Nunca colocar a URL diretamente em regras de negócio.

9. Credentials

Credenciais devem vir de variáveis de ambiente ou mecanismo seguro equivalente.

Exemplo:

EXTERNAL_API_TOKEN=change-me

Nunca armazenar no código:

API_TOKEN = "real-token"
10. Environment Configuration

Uma integração pode possuir configurações como:

EXTERNAL_API_URL
EXTERNAL_API_TOKEN
EXTERNAL_API_TIMEOUT
EXTERNAL_API_ENABLED

Essas configurações devem ser centralizadas.

Consultar:

skills/infrastructure/environment.md
11. Secrets

Nunca registrar em logs:

API key
Bearer token
password
secret
private key
credentials

Não incluir secrets em:

exceptions
responses
audit logs
job payloads
12. Authentication

Cada integração deve possuir uma estratégia explícita de autenticação.

Possibilidades:

Bearer Token
API Key
Basic Authentication
OAuth 2.0

A implementação deve seguir o contrato do sistema externo.

Não criar uma camada de autenticação genérica antes de existirem integrações que justifiquem essa abstração.

13. Headers

Headers comuns podem ser definidos pelo client.

Exemplo conceitual:

Authorization
Content-Type
Accept
Idempotency-Key
X-Correlation-ID

Headers devem ser construídos no client.

Não espalhar essa lógica pelos services.

14. Timeout

Toda chamada externa deve possuir timeout.

Exemplo conceitual:

timeout = 10.0

O valor definitivo deve ser configurável quando necessário.

Nunca permitir espera indefinida.

15. Timeout por operação

Operações diferentes podem exigir timeouts diferentes.

Exemplo:

GET simples
→ timeout menor

exportação
→ timeout maior

Não criar valores diferentes arbitrariamente.

A diferenciação deve possuir justificativa.

16. Connection Pooling

Quando a biblioteca utilizada suportar pooling, considerar reutilização de conexões.

Isso pode reduzir:

latência
overhead
quantidade de conexões

A configuração deve considerar o número de workers.

17. External Response

O client deve validar respostas recebidas.

Considerar:

status code
headers
content type
payload structure
required fields

Não assumir que uma resposta HTTP 200 sempre possui payload válido.

18. Payload Validation

Quando necessário, respostas externas devem ser validadas com schemas específicos.

Exemplo conceitual:

ExternalCustomerResponse
ExternalOrderResponse

Não confiar cegamente em dict arbitrários.

19. External Request Models

Quando um sistema externo possuir contrato específico, considerar schemas ou DTOs próprios para o payload externo.

Exemplo:

Internal Customer
      ↓
Transformation
      ↓
ExternalCustomerPayload

Não obrigar o model interno a possuir exatamente o mesmo formato da API externa.

20. Payload Transformation

Integrações frequentemente possuem modelos diferentes.

Exemplo:

ERP:
first_name
last_name

External:
name

A transformação deve ocorrer na camada de integração.

Não alterar o domínio interno somente para acomodar o formato externo.

21. Internal Model ≠ External Model

Nunca assumir que:

ERP Customer
=
External Customer

Mesmo quando os campos pareçam semelhantes.

Uma API externa pode:

renomear campos
usar tipos diferentes
possuir campos obrigatórios adicionais
usar códigos próprios

A transformação deve ser explícita.

22. External IDs

Dados sincronizados devem possuir identificadores externos quando necessário.

Exemplo:

external_id
source_system

Possível estrutura:

tenant_id
source_system
external_id

Essa combinação pode possuir constraint de unicidade conforme a regra do domínio.

23. Idempotência

Operações externas sujeitas a repetição devem considerar idempotência.

Exemplo:

POST /customers

pode ser repetido após:

timeout
network failure
worker restart

Se o sistema externo suportar:

Idempotency-Key

considerar sua utilização.

24. Internal Idempotency

Quando o sistema externo não fornecer idempotência, o ERP poderá utilizar mecanismos próprios.

Exemplos:

external_id
idempotency_key
sync_status
processed_at
unique constraint

A estratégia depende da operação.

25. Retry

Retry somente deve ocorrer para falhas potencialmente transitórias.

Exemplos:

timeout
connection reset
HTTP 429
HTTP 502
HTTP 503

Não retryar automaticamente qualquer erro.

26. Non-retryable Errors

Normalmente não retryar:

HTTP 400
HTTP 401
HTTP 403
HTTP 404
payload inválido
regra de negócio inválida

A classificação final depende do contrato da API externa.

27. Retry Policy

Quando retry existir, definir:

maximum attempts
backoff
jitter quando necessário
retryable errors

Exemplo conceitual:

Attempt 1
   ↓
falha
   ↓
backoff
   ↓
Attempt 2
   ↓
falha
   ↓
backoff
   ↓
Attempt 3

Evitar retries infinitos.

28. Rate Limits

APIs externas podem possuir limites de requisição.

Exemplo:

HTTP 429

O sistema deve respeitar:

Retry-After
backoff
provider limits

quando essas informações estiverem disponíveis.

Não aumentar agressivamente o volume de requisições depois de receber rate limit.

29. Circuit Breaker

Circuit breakers podem ser considerados quando uma integração crítica apresentar indisponibilidade recorrente.

Conceito:

External API failing
      ↓
Circuit Open
      ↓
stop unnecessary requests
      ↓
recovery check
      ↓
Circuit Closed

Não implementar circuit breaker genericamente antes de existir uma necessidade operacional clara.

30. Fallback

Algumas integrações podem possuir fallback.

Exemplo:

Primary Service
      ↓
failure
      ↓
Secondary Service

Fallback somente deve existir quando houver uma estratégia real e claramente definida.

Não esconder falhas utilizando fallback arbitrário.

31. External Errors

Erros externos devem ser encapsulados em exceptions apropriadas.

Exemplos:

ExternalServiceTimeoutError
ExternalServiceUnavailableError
ExternalServiceRateLimitError
ExternalServiceResponseError

Criar somente exceptions necessárias.

32. Erro externo ≠ erro de domínio

Exemplo:

External API → timeout

não significa automaticamente:

Pedido inválido

São categorias diferentes:

Infrastructure / External failure
vs
Business rule failure

Essa distinção deve ser preservada.

33. HTTP Status Mapping

Um status externo não deve ser repassado automaticamente ao cliente.

Exemplo:

External API
→ 503

não significa necessariamente que:

ERP API
→ 503

A camada de service deve determinar o comportamento apropriado do domínio e da API.

34. External 429

Quando um sistema externo responder:

429 Too Many Requests

considerar:

retry
backoff
job retry
rate limit local

conforme o caso.

35. External Authentication Failure

Exemplo:

External API
→ 401

Esse erro pode representar:

credencial inválida
token expirado
configuração incorreta

Não retornar a credencial ou token ao cliente.

Registrar somente informações seguras para diagnóstico.

36. External 404

Um 404 externo pode possuir significados diferentes.

Exemplo:

cliente não existe no sistema externo

Isso pode ser:

not found esperado
ou
estado inconsistente

A interpretação deve permanecer no service.

37. Webhooks

Integrações poderão receber webhooks.

Fluxo:

External System
      ↓
Webhook Endpoint
      ↓
Validate Request
      ↓
Persist Event / Queue
      ↓
Worker
      ↓
Service

Webhook não deve executar processamento pesado diretamente quando isso puder causar timeout ou duplicidade.

38. Webhook Authentication

Webhooks devem possuir mecanismo de autenticação ou assinatura quando fornecido pelo sistema externo.

Possibilidades:

HMAC signature
Bearer token
API key
mTLS

A implementação deve seguir o contrato do provedor.

39. Webhook Validation

Antes de processar:

signature
timestamp quando aplicável
event type
payload

devem ser validados.

Não confiar no payload simplesmente porque chegou ao endpoint.

40. Webhook Idempotency

Webhooks podem ser entregues mais de uma vez.

Exemplo:

Event 123
↓
delivery 1

Event 123
↓
delivery 2

O sistema deve evitar processamento duplicado quando o provedor utilizar identificadores únicos.

Possíveis mecanismos:

event_id
external_id
unique constraint
processed_at
41. Webhook Response

Webhooks devem responder rapidamente quando o contrato do provedor exigir acknowledgement rápido.

Preferir:

Webhook
 ↓
validate
 ↓
persist/enqueue
 ↓
HTTP 2xx
 ↓
process asynchronously

quando apropriado.

42. Webhook Failures

Quando o processamento interno falhar depois do acknowledgement:

webhook received
↓
job created
↓
HTTP 2xx
↓
worker fails

o sistema deve possuir mecanismos internos de:

retry
dead letter
reprocessamento
observabilidade

conforme necessário.

43. Polling

Quando o sistema externo não possuir webhooks, polling poderá ser utilizado.

Exemplo:

Scheduler
↓
External API
↓
buscar alterações
↓
Queue
↓
Worker

Polling deve considerar:

interval
pagination
rate limits
last synchronization
idempotency
44. Incremental Sync

Sincronizações devem, quando possível, buscar somente alterações desde a última execução.

Exemplo:

updated_since
last_cursor
last_sync_at

Isso reduz:

carga
tempo
volume de dados
45. Full Sync

Full sync pode ser necessário para:

primeira sincronização
reconstrução
recuperação
reconciliação

Mas não deve ser executado indiscriminadamente em grandes volumes.

46. Pagination Externa

Ao consumir APIs paginadas, processar página por página.

Exemplo:

Page 1
↓
process

Page 2
↓
process

Page 3
↓
process

Evitar carregar toda a integração em memória.

47. Cursor

Quando a API externa utilizar cursor:

next_cursor

o client deve preservá-lo conforme o contrato.

Não converter automaticamente para offset sem necessidade.

48. External Data Mapping

Ao receber dados externos:

External
↓
Validation
↓
Transformation
↓
Domain

Não persistir diretamente o payload externo em uma entidade de negócio sem validação.

49. Raw Payload

Guardar o payload bruto pode ser útil em integrações específicas.

Quando necessário, utilizar estrutura apropriada, possivelmente:

JSONB

ou armazenamento específico.

Não guardar payloads enormes indiscriminadamente.

50. Sensitive External Data

Payloads externos podem possuir:

credentials
personal data
financial data
tokens

Esses dados devem receber tratamento adequado.

Não colocar payload completo em logs apenas para facilitar debugging.

51. Integration Logs

Registrar eventos relevantes:

integration.request.started
integration.request.completed
integration.request.failed
integration.retry
integration.rate_limited
integration.webhook.received

Campos possíveis:

request_id
tenant_id
integration
operation
status
duration_ms

Nunca registrar secrets.

52. Correlation

Quando possível, correlacionar:

ERP request_id
+
job_id
+
external request id

Exemplo:

HTTP Request
   ↓
request_id = A
   ↓
job_id = B
   ↓
External Request ID = C

Isso facilita investigação ponta a ponta.

53. External Request ID

Quando o provedor retornar um identificador da requisição, preservar esse valor para diagnóstico.

Exemplo conceitual:

external_request_id

Não confundir com:

request_id

do ERP.

54. Observability

Integrações devem permitir identificar:

qual sistema
qual operação
qual tenant
qual request
qual job
qual tentativa
qual resultado

Esses dados devem ser suficientes para diagnosticar falhas sem armazenar payloads sensíveis.

55. Transactions

Evitar manter uma transação PostgreSQL aberta durante uma chamada externa lenta.

Problema:

BEGIN
 ↓
UPDATE database
 ↓
aguarda API externa
 ↓
COMMIT

Isso pode ocupar conexões e locks desnecessariamente.

Separar etapas quando a consistência permitir.

56. Distributed Consistency

Não assumir uma transação única entre:

PostgreSQL
+
External API

Cada sistema possui seu próprio estado.

Quando necessário, utilizar:

state machine
retry
idempotency
compensation
reconciliation
57. Reconciliation

Integrações críticas podem precisar de processos de reconciliação.

Exemplo:

ERP
vs
External System

A reconciliação pode detectar:

registros ausentes
duplicidades
status divergentes
valores divergentes

Não implementar reconciliação genérica antes de existir uma integração que exija isso.

58. Integration State

Quando necessário, persistir o estado da sincronização.

Exemplo:

pending
processing
synced
failed
retrying

Também pode ser útil armazenar:

last_sync_at
last_error
attempt_count
external_id

A estrutura deve seguir o caso de uso.

59. Per Tenant Configuration

Quando cada tenant possuir configurações próprias de integração:

Tenant
 ↓
Integration Configuration
 ↓
External System

Credenciais devem permanecer protegidas.

Exemplos:

external_account_id
external_api_key
external_settings

A modelagem deve evitar exposição dessas credenciais na API.

60. Multi-tenancy

Toda integração que trabalha com dados de tenant deve considerar:

tenant_id
external_id
source_system

Uma operação de Tenant A nunca deve processar automaticamente dados de Tenant B.

61. Background Jobs

Integrações demoradas devem preferir:

Service
 ↓
Queue
 ↓
Worker
 ↓
Integration Client

quando a operação não precisar de resposta imediata.

Consultar:

skills/backend/background-jobs.md
62. Integration Hub

O futuro Integration Hub será o principal consumidor de muitos desses padrões.

Arquitetura planejada:

SaaS ERP Platform
        ↓
      REST API
        ↓
Integration Hub
        ↓
      Queue
        ↓
      Worker
        ↓
External Systems

O Integration Hub poderá realizar:

authentication
payload transformation
queueing
retry
idempotency
webhooks
logging
failure handling
63. ERP API como upstream

O ERP possuirá uma API real que poderá ser consumida pelo Integration Hub.

Isso significa que:

ERP
→ sistema upstream

Integration Hub
→ consumidor da API

A API do ERP deve permanecer suficientemente estável e documentada para permitir esse consumo.

64. Não acoplar ao Integration Hub

A implementação inicial do ERP não deve depender do futuro Integration Hub.

O ERP deve continuar funcionando independentemente.

O Integration Hub será um consumidor externo da API.

65. API Contract

Integrações devem consumir contratos documentados.

Não depender de:

tabelas internas
queries
estrutura do banco
objetos SQLAlchemy

O contrato público é:

HTTP
+
JSON
+
Authentication
66. Backward Compatibility

Alterações na API do ERP devem considerar o impacto sobre integrações.

Especialmente:

renomear campos
remover campos
alterar tipos
alterar significado
remover endpoints

Quando necessário, utilizar:

API versioning
compatibility period
migration strategy
67. Testes

Cada integração deve possuir testes apropriados.

Cobrir:

sucesso
timeout
429
500
payload inválido
autenticação inválida
resposta inesperada
68. Mock External API

Testes de integração externa podem utilizar mock server ou mecanismo equivalente.

O objetivo é validar:

request
headers
payload
response parsing
error handling
retry

Sem depender do serviço externo real em toda execução.

69. Contract Tests

Quando uma integração for crítica, considerar contract tests.

Esses testes podem verificar que:

request
+
response

continuam compatíveis com o contrato esperado do sistema externo.

70. Idempotency Tests

Testar repetição da mesma operação.

Exemplo:

sync_customer
↓
execução 1
↓
execução 2

Resultado esperado:

sem duplicidade

quando o caso de uso exigir.

71. Webhook Tests

Testar:

assinatura válida
assinatura inválida
event_id duplicado
payload inválido
evento desconhecido
processamento assíncrono
72. Retry Tests

Testar:

falha transitória
↓
retry
↓
sucesso

e:

falha permanente
↓
sem retry
73. Rate Limit Tests

Simular:

HTTP 429

e verificar:

backoff
retry
limite de tentativas

quando essas funcionalidades forem implementadas.

74. Timeout Tests

Simular timeout e verificar que:

exception correta
job retryável quando apropriado
logs produzidos
nenhum estado inconsistente
75. Integration Security Tests

Testar que:

credenciais não aparecem em responses
credenciais não aparecem nos logs
tenant A não acessa configuração de tenant B

quando aplicável.

76. Testes Multi-tenant

Para integrações configuradas por tenant:

Tenant A
→ External Account A

e:

Tenant B
→ External Account B

O sistema não deve misturar os contextos.

77. Testes de Reprocessamento

Quando uma sincronização falhar:

failed
↓
reprocess
↓
success

verificar que o resultado permanece consistente e que operações não são duplicadas.

78. Performance

Integrações devem considerar:

latência externa
throughput
rate limits
conexões
memória
queue depth

Não executar testes pesados na suíte comum sem necessidade.

79. Segurança

Nunca confiar em sistemas externos automaticamente.

Toda entrada externa deve ser tratada como não confiável.

Validar:

payload
types
required fields
authentication
signature
status

quando aplicável.

80. Disponibilidade

O ERP não deve necessariamente ficar indisponível porque um sistema externo está indisponível.

Quando possível, isolar a dependência através de:

queue
retry
timeout
circuit breaker
async processing

conforme a criticidade da operação.

81. Falha parcial

Uma operação que envolve múltiplos sistemas pode ter sucesso parcial.

Exemplo:

ERP
→ sucesso

External System
→ falha

O estado deve representar essa realidade.

Evitar marcar tudo como "sucesso" simplesmente porque uma etapa foi concluída.

82. Estados de sincronização

Quando necessário, utilizar estados explícitos:

pending
syncing
synced
failed
retrying

Esses estados devem possuir transições claras.

83. Reconciliation Job

Para integrações críticas, um job de reconciliação pode comparar periodicamente:

ERP state
vs
External state

Isso ajuda a detectar inconsistências que não foram capturadas por eventos ou webhooks.

84. Documentation

Cada integração relevante deve documentar:

sistema externo
autenticação
endpoints
timeout
retry
idempotência
webhooks
limitações
mapping

A documentação deve ficar próxima da integração ou em:

docs/

conforme a organização do projeto.

85. Configuration Documentation

Toda nova variável de ambiente de integração deve ser adicionada ao:

.env.example

e documentada quando necessário.

Nunca depender somente do .env pessoal de um desenvolvedor.

86. Dependency Management

Uma integração não deve adicionar uma biblioteca HTTP diferente para cada provedor sem necessidade.

Preferir reutilizar a infraestrutura existente.

Antes de adicionar uma dependência:

verificar stack atual
avaliar manutenção
avaliar compatibilidade
avaliar testabilidade
87. Não criar Generic Integration Framework prematuramente

Evitar criar:

GenericIntegrationManager
GenericProviderFactory
UniversalConnector
GenericSyncEngine

antes de existirem integrações reais suficientes para justificar essas abstrações.

Primeiro implementar integrações concretas.

Depois identificar padrões realmente repetidos.

88. Abstração baseada em evidência

Depois de múltiplas integrações reais, padrões como:

authentication
retry
pagination
idempotency
mapping
webhooks

poderão ser abstraídos.

A abstração deve surgir de necessidades comprovadas.

89. Checklist

Antes de finalizar uma integração:

 Existe um Integration Client claro;
 Service e client possuem responsabilidades separadas;
 URL vem de configuração;
 Credentials estão fora do código;
 Timeout está definido;
 Response é validada;
 Payload externo não é tratado como model interno;
 Transformation está explícita;
 External IDs foram considerados;
 Idempotência foi avaliada;
 Retry foi avaliado;
 Rate limit foi considerado;
 Webhook foi considerado quando aplicável;
 Multi-tenancy foi considerado;
 Logs possuem correlação;
 Secrets não aparecem nos logs;
 Testes de sucesso e falha existem;
 Testes de idempotência existem quando necessários;
 Reprocessamento foi considerado;
 Não existe acoplamento desnecessário ao sistema externo;
 Não existe abstração genérica prematura.
90. Regra principal

Integrações devem possuir uma fronteira clara:

ERP Domain
     ↓
Service
     ↓
Integration Client
     ↓
External System

Quando o processamento for assíncrono:

ERP
 ↓
Service
 ↓
Queue
 ↓
Worker
 ↓
Integration Client
 ↓
External System

O sistema externo nunca deve ditar a arquitetura interna do ERP.

O domínio interno deve permanecer independente, enquanto a camada de integração adapta o contrato externo ao modelo da aplicação.