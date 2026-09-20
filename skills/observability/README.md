# Observability

## Objetivo

Definir os padrões gerais de observabilidade do SaaS ERP Platform.

Observabilidade deve permitir compreender o comportamento do sistema através de:

```text
Logs
Metrics
Tracing
Audit Logs
Health Checks
Monitoring
Alerts

O objetivo é permitir responder:

O sistema está funcionando?
O que está acontecendo?
Onde ocorreu a falha?
Qual tenant foi afetado?
Qual usuário iniciou a operação?
Qual componente apresentou problema?
Qual foi o impacto?

Este documento complementa:

skills/02-architecture.md
skills/backend/logging.md
skills/backend/exceptions.md
skills/backend/background-jobs.md
skills/backend/integrations.md
skills/security/README.md
1. Princípios

A observabilidade deve ser:

útil;
estruturada;
segura;
correlacionável;
mensurável;
independente de uma ferramenta específica quando possível.

Não adicionar observabilidade apenas por adicionar tecnologia.

Cada mecanismo deve possuir uma finalidade clara.

2. Os quatro pilares

O projeto utilizará principalmente:

Logs
Metrics
Traces
Audit Logs

Cada mecanismo responde perguntas diferentes.

Logs

O que aconteceu?

Metrics

Com que frequência e em qual escala aconteceu?

Traces

Por onde uma operação passou?

Audit Logs

Quem executou qual ação de negócio?

3. Logs

Logs técnicos devem registrar eventos relevantes da aplicação.

Exemplos:

application.started
http.request
database.query_failed
job.failed
integration.request.failed

As regras detalhadas ficam em:

skills/backend/logging.md
4. Structured Logging

Preferir logs estruturados.

Exemplo:

{
  "timestamp": "2026-09-17T18:30:00Z",
  "level": "INFO",
  "event": "order.created",
  "request_id": "uuid",
  "tenant_id": "uuid",
  "user_id": "uuid"
}

Evitar depender somente de mensagens textuais.

5. Metrics

Métricas representam valores agregáveis ao longo do tempo.

Exemplos:

HTTP request count
HTTP error count
HTTP request duration
Database connection count
Database query duration
Queue depth
Job failures
Job retries
External API latency

Métricas são preferíveis a logs para:

contagens
taxas
percentuais
latências
tendências
6. Metric Naming

Métricas devem possuir nomes consistentes.

Exemplo conceitual:

http_requests_total
http_request_duration_seconds
jobs_processed_total
jobs_failed_total
external_requests_total

A convenção definitiva deverá ser mantida consistente em todo o projeto.

7. Counters

Counters representam valores que normalmente crescem ao longo do tempo.

Exemplos:

requests_total
errors_total
jobs_completed_total
jobs_failed_total
retries_total

Não utilizar counter para valores que podem aumentar e diminuir.

8. Gauges

Gauges representam valores que podem aumentar ou diminuir.

Exemplos:

queue_depth
active_connections
active_workers

Utilizar gauge quando o valor representa um estado atual.

9. Histograms

Histograms podem representar distribuições.

Exemplos:

request duration
database query duration
external API duration
job duration

São úteis para observar latência sem depender somente da média.

10. HTTP Metrics

A API deve futuramente permitir observar:

requests
errors
latency
status codes

Exemplo conceitual:

GET /api/v1/customers
→ 200
→ 35 ms

Também identificar:

4xx rate
5xx rate
11. Métricas por Endpoint

Quando apropriado, métricas podem possuir dimensões como:

method
route
status_code

Evitar utilizar valores de alta cardinalidade indiscriminadamente.

Não utilizar:

user_id
request_id
UUID arbitrário

como labels de métricas em grande escala.

12. Cardinalidade

Métricas devem evitar dimensões com cardinalidade excessiva.

Exemplo problemático:

http_requests_total{
    request_id="..."
}

Como cada requisição possui um valor diferente, isso pode produzir quantidade enorme de séries.

Preferir dimensões estáveis, como:

route
method
status_code
13. Tenant Metrics

Métricas agregadas por tenant devem ser avaliadas com cuidado.

Não adicionar:

tenant_id

como label de toda métrica indiscriminadamente.

Isso pode gerar cardinalidade excessiva em ambientes com muitos tenants.

Quando uma análise por tenant for necessária, considerar:

logs
audit
analytics
queries específicas

em vez de transformar todo tenant em label de métricas.

14. Database Metrics

Monitorar quando aplicável:

connection pool
active connections
query latency
transaction failures
database errors

Essas métricas ajudam a identificar gargalos no PostgreSQL.

15. Redis Metrics

Quando Redis for utilizado, observar:

connections
memory
latency
commands
errors
queue usage

conforme a infraestrutura escolhida.

16. Queue Metrics

Filas devem permitir observar:

queue depth
jobs processed
jobs failed
jobs retried
processing duration
oldest pending job

Essas métricas serão importantes para o futuro Integration Hub.

17. Worker Metrics

Workers podem possuir métricas como:

jobs_started_total
jobs_completed_total
jobs_failed_total
jobs_retried_total
job_duration_seconds
active_jobs

Isso permite identificar problemas de capacidade ou falhas recorrentes.

18. Integration Metrics

Integrações externas devem permitir observar:

requests
successes
failures
timeouts
rate limits
latency
retries

Exemplo conceitual:

external_requests_total
external_request_failures_total
external_request_duration_seconds
19. Business Metrics

Algumas métricas de negócio podem ser úteis.

Exemplos:

orders_created
orders_cancelled
products_created
inventory_adjustments

Essas métricas devem ser escolhidas conforme os requisitos do sistema.

Não transformar toda ação de negócio em uma métrica automaticamente.

20. Technical Metrics x Business Metrics

Diferenciar:

Technical
→ API latency

Business
→ orders created

Métricas técnicas ajudam a monitorar o sistema.

Métricas de negócio ajudam a observar o comportamento da aplicação.

21. Distributed Tracing

Tracing poderá ser adicionado conforme o sistema ganhar múltiplos componentes.

Exemplo:

HTTP Request
   ↓
Backend
   ↓
Database
   ↓
Queue
   ↓
Worker
   ↓
External API

Um trace permite observar esse fluxo como uma única operação distribuída.

22. Trace ID

Quando tracing existir, operações relacionadas poderão compartilhar:

trace_id

Esse identificador permite correlacionar:

logs
metrics where appropriate
spans
external calls

Não confundir:

trace_id
request_id
job_id

Cada um possui finalidade própria.

23. Span

Cada etapa relevante de uma operação pode possuir um span.

Exemplo:

Trace
├── HTTP request
├── database query
├── service operation
├── queue publish
└── external API request

Não criar spans para cada função trivial.

24. Tracing e Performance

Tracing pode ajudar a identificar:

database bottleneck
external API latency
slow service
queue delay

Especialmente em operações distribuídas.

25. External Trace Context

Quando sistemas externos suportarem propagação de contexto, considerar enviar identificadores de correlação.

Exemplo:

ERP
↓
Integration Hub
↓
External API

A estratégia deve respeitar o padrão suportado pela integração.

Não expor informações internas desnecessárias para provedores externos.

26. Request ID x Trace ID

Utilizar conceitos diferentes:

request_id
→ identifica uma requisição da aplicação

trace_id
→ identifica um fluxo distribuído

job_id
→ identifica um processamento assíncrono

Quando uma operação utilizar os três:

request_id
+
trace_id
+
job_id

a correlação deve permanecer clara.

27. Correlation

Uma operação pode atravessar:

HTTP
↓
Service
↓
Queue
↓
Worker
↓
External API

Correlacionar os componentes através de:

request_id
trace_id
job_id
external_request_id

somente quando esses identificadores existirem.

28. Audit Logs

Audit logs registram ações relevantes de negócio.

Exemplo:

Usuário alterou preço do produto.

Um audit log pode possuir:

tenant_id
user_id
action
entity
entity_id
timestamp
29. Technical Log x Audit

Não confundir:

Technical Log
→ como o sistema funcionou

Audit Log
→ qual ação de negócio ocorreu

Exemplo:

database.query.completed

é técnico.

Enquanto:

product.price_changed

pode ser auditável.

30. Audit Actor

Auditoria deve identificar o actor quando possível.

Exemplos:

user
system
worker
integration
ai

Quando aplicável:

actor_type
actor_id

A estrutura final deve permanecer simples.

31. Audit Tenant

Toda ação de negócio multi-tenant deve possuir:

tenant_id

quando aplicável.

Isso permite investigar as ações de cada organização sem misturar os contextos.

32. Audit Security

Audit logs não devem armazenar:

password
password_hash
JWT
access_token
refresh_token
API keys
secrets
private keys
33. Audit Immutability

Audit logs devem ser tratados como registros históricos.

Evitar permitir alterações arbitrárias no histórico.

Operações administrativas sobre audit logs devem ser altamente controladas.

34. Audit Retention

A retenção de audit logs deve seguir os requisitos do sistema.

Considerar:

volume
necessidade operacional
requisitos legais
segurança
custo

Não definir retenção definitiva somente no código.

35. Health Checks

O sistema deve possuir health checks para identificar disponibilidade.

O endpoint atual é:

GET /health

A implementação atual verifica somente que a aplicação está respondendo.

Checks mais profundos poderão ser adicionados posteriormente.

36. Liveness

Liveness responde:

A aplicação está viva?

Exemplo conceitual:

GET /health/live

Não precisa depender de todos os serviços externos.

Um banco temporariamente indisponível não necessariamente significa que o processo HTTP deixou de estar vivo.

37. Readiness

Readiness responde:

A aplicação está pronta para receber tráfego?

Pode considerar:

database
redis
required infrastructure

Exemplo conceitual:

GET /health/ready

A implementação poderá ser adicionada quando a aplicação possuir dependências reais.

38. Health Checks e Dependências

Diferenciar:

application alive

de:

application ready

Evitar um health check único que sempre execute consultas pesadas ao banco.

39. Startup Checks

Durante startup, validar configurações obrigatórias.

Exemplos:

DATABASE_URL
JWT_SECRET_KEY
REDIS_URL

quando forem necessárias.

Falhas de configuração devem ser identificadas cedo.

40. Dependency Health

Serviços críticos podem possuir indicadores de saúde.

Exemplos:

PostgreSQL
Redis
Queue
External API

Não considerar um serviço externo "healthy" somente porque a configuração existe.

41. External APIs

Não fazer chamadas externas desnecessárias a cada health check.

Isso pode:

consumir rate limit
aumentar latência
gerar custos

Health checks externos devem ser usados com cuidado.

42. Alerting

Alertas devem ser baseados em sinais relevantes.

Exemplos:

5xx rate elevada
database indisponível
queue crescendo continuamente
workers falhando
integration failure rate elevado
43. Alert Fatigue

Evitar alertas para todo erro.

Um alerta deve representar uma condição que realmente exige ação.

Exemplo:

404
→ geralmente não precisa de alerta

PostgreSQL indisponível
→ pode exigir alerta
44. Alert Thresholds

Thresholds devem ser baseados no comportamento esperado.

Exemplo conceitual:

5xx > limite
durante determinado período
→ alerta

Os valores reais devem ser definidos depois que houver métricas reais do sistema.

Não inventar thresholds arbitrários.

45. SLO / SLA

Conforme o projeto crescer, poderão ser definidos:

SLO
SLA
SLI

Exemplos:

availability
latency
error rate
job processing time

Não definir metas de disponibilidade sem requisitos reais do produto.

46. Error Budget

Caso o projeto adote SLOs, poderá utilizar error budgets para equilibrar:

reliability
+
feature development

Essa prática será introduzida somente quando houver necessidade operacional.

47. Monitoring

Monitoramento deve observar pelo menos:

Application
Database
Redis
Workers
Queues
External Integrations
Infrastructure

A cobertura deve aumentar conforme novos componentes forem adicionados.

48. Application Monitoring

Monitorar:

request rate
error rate
latency
active requests

quando a infraestrutura fornecer esses indicadores.

49. Database Monitoring

Monitorar:

connections
CPU
memory
storage
query latency
locks
errors

A coleta pode ser realizada pela infraestrutura de observabilidade.

50. Redis Monitoring

Monitorar conforme o uso:

memory
connections
latency
evictions
queue usage
51. Worker Monitoring

Monitorar:

active workers
jobs processing
jobs failed
jobs retrying
queue delay
job duration
52. Queue Monitoring

Uma fila saudável deve permitir observar:

volume
processing rate
failure rate
backlog
age of oldest job

Backlog crescente pode indicar:

worker capacity issue
external dependency issue
database bottleneck
53. Integration Monitoring

Para APIs externas:

success rate
error rate
latency
timeouts
429
retries

Isso ajuda a diferenciar problemas internos de problemas externos.

54. Logs + Metrics

Logs podem explicar um evento específico.

Métricas mostram se esse evento está se tornando um padrão.

Exemplo:

Metric:
external_requests_failures_total ↑

Depois:

Log:
external_request.failed
provider=...
status=503

Utilizar ambos de maneira complementar.

55. Logs + Traces

Logs podem incluir:

trace_id
span_id

quando tracing existir.

Isso permite navegar:

metric
↓
trace
↓
log

em plataformas compatíveis.

56. Audit + Logs

Uma ação pode produzir:

Audit
+
Technical Log

Exemplo:

Audit:
order.cancelled

Technical Log:
database.transaction.completed

Os dois registros possuem objetivos diferentes.

57. Sensitive Information

Nenhum mecanismo de observabilidade deve expor:

password
password_hash
JWT
access_token
refresh_token
API key
secret
private key
database credentials

Essa regra vale para:

logs
metrics
traces
audit
errors
58. High Cardinality Data

Evitar colocar dados únicos em labels/tags de métricas.

Exemplos perigosos:

request_id
user_id
tenant_id
entity_id
external_id

Esses valores podem ser adequados para logs e traces, mas não necessariamente para métricas.

59. Privacy

Observabilidade também pode conter dados pessoais.

Antes de registrar:

email
phone
address
documents
financial data

verificar se o dado realmente é necessário.

Preferir identificadores internos.

60. Observability Costs

Observabilidade possui custo de:

storage
CPU
network
indexing
query

Evitar coletar tudo sem necessidade.

61. Sampling

Tracing poderá utilizar sampling quando o volume crescer.

Exemplo:

100% em desenvolvimento
↓
sampling controlado em produção

A estratégia final deve considerar:

volume
criticidade
custo
diagnóstico

Não descartar indiscriminadamente traces de operações importantes.

62. Error Sampling

Erros podem merecer maior retenção ou sampling diferenciado.

Exemplo:

successful requests
→ sampling

failed requests
→ maior retenção

A configuração depende da ferramenta adotada.

63. Local Development

Durante desenvolvimento, observabilidade pode ser mais simples.

Exemplo:

console logs
local metrics
local traces

Não exigir infraestrutura complexa para executar o projeto localmente.

64. Production

Produção deve possuir mecanismos apropriados para:

aggregation
retention
monitoring
alerting
access control

Os componentes específicos poderão ser escolhidos conforme a infraestrutura do projeto.

65. Tool Agnostic

As skills não devem obrigar uma plataforma específica sem necessidade.

Possíveis tecnologias futuras incluem:

OpenTelemetry
Prometheus
Grafana
Loki
Jaeger
Tempo

A escolha deverá ser feita conforme:

necessidade
custo
complexidade
compatibilidade

Não adicionar todas essas ferramentas automaticamente.

66. OpenTelemetry

OpenTelemetry poderá ser utilizado futuramente como camada de instrumentação.

Possíveis sinais:

traces
metrics
logs

A adoção deve acontecer quando o projeto possuir necessidade real de observabilidade distribuída.

67. Development Observability

Durante desenvolvimento, o foco inicial deve ser:

logs úteis
errors claros
request_id
health checks

Depois evoluir para:

metrics
tracing
dashboards
alerts
68. Incident Investigation

Ao investigar um problema, seguir uma sequência aproximada:

1. Identificar sintoma
2. Verificar métricas
3. Localizar período
4. Localizar request/trace/job
5. Consultar logs
6. Verificar banco/fila/integração
7. Identificar causa
8. Corrigir
9. Criar teste/regressão quando necessário

Não começar alterando código sem identificar o problema.

69. Request Investigation

Para investigar uma requisição:

request_id
   ↓
logs
   ↓
trace_id
   ↓
database / queue / external call

quando os mecanismos estiverem implementados.

70. Job Investigation

Para investigar um job:

job_id
   ↓
job logs
   ↓
attempt
   ↓
service
   ↓
database / external API
71. Integration Investigation

Para uma integração:

request_id
+
job_id
+
external_request_id

podem permitir rastrear:

ERP
↓
Queue
↓
Worker
↓
External API
72. Observability Testing

A observabilidade também deve ser testada quando fizer parte do comportamento esperado.

Exemplos:

request_id criado
event correto
error code correto
audit registrado
job correlation preservada
73. Observability During Failures

Falhas não devem destruir os próprios mecanismos necessários para investigá-las.

Mesmo quando:

database
external API
queue

falharem, logs e sinais básicos de erro devem permanecer disponíveis quando tecnicamente possível.

74. Health Endpoint Security

Health endpoints não devem revelar detalhes desnecessários.

Evitar respostas públicas contendo:

database credentials
connection strings
internal IPs
secrets
stack traces
75. Readiness Detail

Um readiness check pode informar internamente qual dependência está falhando.

Mas a resposta pública deve possuir somente o nível de detalhe necessário.

76. Observability Access

Acesso a logs, métricas, traces e auditoria deve ser controlado.

Nem todo usuário do ERP precisa acessar:

technical logs
infrastructure metrics
traces
audit administration
77. Tenant Visibility

Quando a aplicação oferecer observabilidade específica para tenants, garantir:

Tenant A
→ somente dados autorizados de Tenant A

Nunca expor informações operacionais de outro tenant.

78. Administrative Observability

Ferramentas administrativas podem possuir visão global do sistema.

Essa capacidade deve ser explicitamente autorizada.

Não usar o simples fato de possuir acesso técnico como justificativa para permitir qualquer visualização no produto.

79. Retention

Definir retenção de acordo com cada tipo de sinal:

Logs
Metrics
Traces
Audit

Eles podem possuir necessidades diferentes.

Não aplicar automaticamente o mesmo período a todos.

80. Data Deletion

Quando existir requisito de remoção de dados, avaliar também:

logs
audit
traces
backups
metrics

Observabilidade pode possuir dados históricos que precisam ser tratados conforme a política aplicável.

81. Backup e Observability

Dados críticos de auditoria podem exigir estratégia própria de backup.

A infraestrutura deverá definir:

backup
retention
restore
security
82. Documentation

Novos mecanismos de observabilidade devem ser documentados.

Exemplos:

metric
event
trace
health check
alert

A documentação deve permanecer próxima da implementação ou em:

docs/

quando apropriado.

83. Checklist

Antes de finalizar uma alteração relacionada à observabilidade:

 O evento é realmente útil;
 Log possui estrutura adequada;
 request_id foi considerado;
 tenant_id foi considerado quando apropriado;
 user_id foi considerado quando apropriado;
 Metrics foram consideradas;
 Cardinalidade foi avaliada;
 Tracing foi considerado quando necessário;
 Audit foi separado de log técnico;
 Health check foi considerado quando aplicável;
 Alertas não geram ruído desnecessário;
 Secrets não são expostos;
 Dados pessoais não são registrados sem necessidade;
 Custo de armazenamento foi considerado;
 Testes foram atualizados quando necessário;
 A solução não adicionou infraestrutura desnecessária.
84. Regra principal

Observabilidade deve permitir investigar o sistema sem modificar o sistema durante a investigação.

A visão ideal é:

                ┌──────────────┐
                │   Metrics    │
                └──────┬───────┘
                       ↓
                identificar padrão
                       ↓
                ┌──────────────┐
                │    Trace     │
                └──────┬───────┘
                       ↓
                localizar fluxo
                       ↓
                ┌──────────────┐
                │     Logs     │
                └──────┬───────┘
                       ↓
                identificar evento
                       ↓
                ┌──────────────┐
                │ Audit / Data │
                └──────────────┘

O sistema deve fornecer contexto suficiente para diagnosticar problemas técnicos e acompanhar ações de negócio, mantendo segurança, privacidade e isolamento entre tenants.

## Implementação Atual

### Componentes

```text
app/core/logging.py         — Formatters JSON/Text + setup_logging()
app/core/request_context.py — Contextvars (request_id, user_id, tenant_id)
app/api/middleware.py        — HTTPLoggingMiddleware
app/core/exceptions.py      — Exception handlers com logging
app/main.py                 — Integração (startup/shutdown)
tests/api/test_observability.py — 21 testes
```

### Configuração

```env
LOG_LEVEL=INFO    # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_JSON=true     # true=JSON, false=Text
```

### Eventos Implementados

| Evento | Level | Origem |
|---|---|---|
| application_started | INFO | main.py startup |
| application_shutdown | INFO | main.py shutdown |
| request_completed | INFO/WARNING/ERROR | middleware |
| request_failed | ERROR | middleware (exception) |
| customer.not_found | WARNING | exceptions.py |
| product.not_found | WARNING | exceptions.py |
| inventory.not_found | WARNING | exceptions.py |
| order.not_found | WARNING | exceptions.py |
| order.invalid_state | WARNING | exceptions.py |
| category.not_found | WARNING | exceptions.py |
| validation_error | WARNING | exceptions.py |
| internal_error | ERROR | exceptions.py |
| login.success | INFO | auth.py |
| login.failure | WARNING | auth.py |

### Request ID

- Gerado automaticamente (UUID v4) quando ausente ou inválido
- Preservado do header X-Request-ID quando válido (max 128 chars)
- Retornado no header X-Request-ID da resposta
- Incluído em todos os logs da request via contextvars

### Segurança

- Senhas nunca aparecem nos logs
- JWT tokens nunca são logados
- Authorization headers nunca são logados
- Request/response bodies não são logados automaticamente
- Secrets da aplicação não são expostos

### Docker/Dozzle

Logs escritos em stdout (JSON format) são automaticamente capturados por:
- Docker logs
- Dozzle (visualização web)
- Qualquer coletor de logs baseado em stdout

### Testes

21 testes em tests/api/test_observability.py cobrindo:
- Request ID (geração, preservação, oversized, independência)
- HTTP logging (method, path, status_code, duration_ms, request_id)
- Error handling (404 com request_id, sem traceback)
- Security (password, JWT, Authorization header, secrets, request body)
- Context (user_id autenticado, tenant_id autenticado, isolamento)