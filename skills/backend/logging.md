# Backend Logging

## Objetivo

Definir os padrões para geração, estruturação, segurança e utilização de logs no backend do SaaS ERP Platform.

Os logs devem permitir investigar:

```text
O que aconteceu?
Quando aconteceu?
Em qual requisição?
Em qual tenant?
Qual usuário estava envolvido?
Qual componente executou a operação?
Houve erro?

Este documento complementa:

skills/02-architecture.md
skills/backend/README.md
skills/backend/architecture.md
skills/backend/api.md
skills/backend/exceptions.md
skills/backend/dependencies.md
skills/observability/README.md
1. Princípios

Os logs devem ser:

úteis;
estruturados;
pesquisáveis;
consistentes;
seguros;
suficientemente detalhados para diagnóstico.

Evitar tanto:

logs insuficientes

quanto:

logs excessivos e inúteis
2. Objetivo dos Logs

Logs técnicos servem principalmente para:

diagnóstico
monitoramento
investigação de erros
rastreamento de requisições
análise operacional

Logs não devem ser utilizados como substituto de:

banco de dados
auditoria de negócio
métricas
tracing

Esses mecanismos possuem finalidades diferentes.

3. Logging Estruturado

Preferir logs estruturados.

Conceito:

{
  "timestamp": "2026-09-17T18:30:00Z",
  "level": "INFO",
  "event": "customer.created",
  "request_id": "uuid",
  "tenant_id": "uuid",
  "user_id": "uuid"
}

Os campos devem possuir nomes consistentes em toda a aplicação.

4. Campos Padrão

Quando disponíveis e relevantes, considerar:

timestamp
level
event
request_id
tenant_id
user_id
service
environment

Para erros:

error_type
error_code
message

Adicionar somente campos realmente úteis.

5. Timestamp

Todo log deve possuir timestamp.

Utilizar:

UTC
timezone-aware
ISO 8601

Exemplo:

2026-09-17T18:30:00Z

Não utilizar horários locais sem indicação de timezone.

6. Level

Os níveis devem possuir significado consistente.

Principais:

DEBUG
INFO
WARNING
ERROR
CRITICAL
DEBUG

Informações úteis principalmente durante desenvolvimento e investigação detalhada.

INFO

Eventos operacionais normais.

Exemplo:

application.started
customer.created
order.confirmed
WARNING

Situações anormais que não interromperam a operação.

Exemplo:

external_service.slow_response
retry.scheduled
ERROR

Falhas de uma operação ou componente.

Exemplo:

order.processing_failed
database.query_failed
CRITICAL

Falhas graves que exigem atenção imediata.

Utilizar somente para situações realmente críticas.

7. Event Name

Preferir nomes de eventos consistentes.

Exemplos:

application.started
application.shutdown
auth.login.success
auth.login.failed
customer.created
customer.updated
customer.deleted
order.created
order.cancelled
inventory.reserved
integration.failed

Preferir:

resource.action

quando essa estrutura fizer sentido.

8. Evitar Mensagens Genéricas

Evitar:

"deu erro"
"problema"
"falhou"
"erro no sistema"

Preferir um evento identificável:

order.creation_failed

com campos estruturados complementares.

9. Request ID

Cada requisição HTTP deve possuir um identificador de rastreamento.

Exemplo:

request_id = 4e1e...

Esse valor deve aparecer nos logs relevantes da requisição.

Fluxo:

HTTP Request
    ↓
request_id
    ↓
Router
    ↓
Service
    ↓
Repository
    ↓
External API

Isso permite correlacionar diferentes eventos.

10. Geração do Request ID

Quando não existir um identificador confiável, a aplicação deve gerar um novo.

A implementação pode utilizar middleware.

Conceito:

Request
   ↓
Generate request_id
   ↓
Attach to request context
   ↓
Process request

O mecanismo deve ser centralizado.

11. Request ID Recebido

Caso o sistema aceite um identificador vindo de um sistema upstream, ele deve ser validado conforme a estratégia de segurança adotada.

Não aceitar qualquer valor sem limites.

Evitar permitir valores gigantes ou formatos que possam poluir os logs.

12. Tenant ID

Em operações multi-tenant, incluir:

tenant_id

nos logs relevantes.

Exemplo:

{
  "event": "customer.created",
  "tenant_id": "uuid",
  "user_id": "uuid"
}

Isso facilita investigações específicas de um tenant.

13. User ID

Quando houver um usuário autenticado associado à operação, incluir:

user_id

Isso permite identificar o actor técnico associado à operação.

Não utilizar informações pessoais desnecessárias como identificador principal do log.

Preferir:

user_id

em vez de:

email

quando o ID for suficiente.

14. Actor

Quando necessário, pode existir um conceito de actor para diferenciar:

usuário humano
sistema
worker
integração

Exemplo:

actor_type=user
actor_id=uuid

ou:

actor_type=system

A implementação deve permanecer simples até existir necessidade real.

15. Service

Em arquiteturas com múltiplos componentes, pode ser útil registrar:

service

Exemplo:

service=backend

Isso facilita a centralização de logs quando futuramente houver:

backend
worker
integration-hub
frontend
16. Environment

Quando apropriado, incluir:

environment

Exemplos:

development
test
production

Isso ajuda a distinguir eventos de diferentes ambientes.

17. Nunca registrar Secrets

Nunca registrar:

password
password_hash
JWT secret
access token
refresh token
API key
database password
private key
credentials

Mesmo em:

DEBUG

Secrets nunca devem aparecer nos logs.

18. Tokens

Não registrar tokens completos.

Evitar:

Authorization: Bearer eyJ...

ou:

access_token=...

Se for necessário diagnosticar autenticação, utilizar somente informações não sensíveis, como:

token_present=true
authentication_result=failed
19. Senhas

Nunca registrar:

password
current_password
new_password
password_confirmation

nem mesmo parcialmente.

Não utilizar logs para depurar valores de senha.

20. Dados Pessoais

Não registrar dados pessoais sem necessidade.

Avaliar cuidadosamente:

email
phone
address
document numbers
financial information

Antes de incluir esse tipo de dado em logs.

Preferir IDs internos quando eles forem suficientes.

21. Payloads

Não registrar automaticamente request e response bodies completos.

Payloads podem conter:

passwords
tokens
personal data
financial data
large structures

Quando for necessário registrar parte de um payload, selecionar somente os campos seguros e relevantes.

22. Headers

Não registrar automaticamente todos os HTTP headers.

Especialmente não registrar:

Authorization
Cookie
Set-Cookie

ou outros headers que possam conter credenciais ou informações sensíveis.

23. Query Parameters

Query parameters podem conter informações sensíveis.

Evitar registrar a URL completa sem filtragem.

Exemplo de risco:

/auth/reset?token=secret

ou:

/users?email=user@example.com

Registrar somente parâmetros necessários e seguros.

24. Exception Logging

Quando ocorrer um erro inesperado, registrar contexto suficiente para investigação.

Exemplo conceitual:

{
  "level": "ERROR",
  "event": "order.creation_failed",
  "request_id": "uuid",
  "tenant_id": "uuid",
  "user_id": "uuid",
  "error_type": "DatabaseError"
}

Quando apropriado, o stack trace pode ser registrado no log interno.

Nunca retornar esse stack trace ao cliente.

25. Stack Trace

Stack traces são úteis para erros inesperados.

Devem ser utilizados principalmente em:

ERROR
CRITICAL

quando contribuírem para diagnóstico.

Não gerar stack trace para toda condição esperada de negócio.

Por exemplo:

CustomerNotFound

normalmente não precisa de um stack trace completo.

26. Business Errors

Erros esperados de negócio devem ser registrados com nível adequado.

Exemplo:

customer.not_found

não precisa necessariamente ser ERROR em toda situação.

Uma solicitação de recurso inexistente pode ser comportamento normal da API.

O nível deve refletir a gravidade operacional.

27. Authentication Logs

Eventos de autenticação relevantes podem gerar logs.

Exemplos:

auth.login.success
auth.login.failed
auth.token.invalid
auth.user.disabled

Registrar:

request_id
user_id quando disponível
tenant_id quando disponível
event
timestamp

Não registrar:

password
token
secret
28. Authorization Logs

Falhas de autorização importantes podem ser registradas.

Exemplo:

auth.authorization.denied

Campos possíveis:

request_id
user_id
tenant_id
permission
resource
action

Registrar somente o necessário.

29. Permission

É possível registrar a permission necessária em uma falha de autorização.

Exemplo:

required_permission=customer.delete

Não registrar listas desnecessariamente grandes de permissions se somente uma for relevante.

30. Tenant Isolation

Tentativas de acesso fora do tenant podem ser relevantes para investigação.

Exemplo:

tenant.access.denied

Entretanto, não transformar cada 404 ou acesso não encontrado em evento de segurança sem analisar o contexto.

Evitar gerar milhares de falsos positivos.

31. Database Logs

Erros relevantes de banco podem ser registrados.

Exemplos:

database.connection_failed
database.query_failed
database.transaction_failed

Não incluir automaticamente:

password
connection string
credentials
32. SQL Logging

SQL detalhado pode ser habilitado localmente para desenvolvimento.

Em produção, evitar logging indiscriminado de SQL.

Razões:

volume
performance
exposição de dados
dificuldade de leitura

Quando necessário, utilizar ferramentas específicas de diagnóstico.

33. External Services

Integrações externas devem registrar eventos importantes.

Exemplos:

external_request.started
external_request.completed
external_request.failed
external_request.timeout
external_request.retry

Campos possíveis:

request_id
tenant_id
integration
operation
status
duration_ms

Não registrar:

credentials
authorization headers
tokens
payloads sensíveis
34. Duration

Para operações relevantes, registrar duração pode ser útil.

Exemplo:

duration_ms=245

Isso ajuda a identificar:

queries lentas
APIs externas lentas
operações de negócio demoradas

Não medir absolutamente tudo sem necessidade.

35. Database Query Duration

Quando uma query for particularmente relevante ou lenta, o contexto pode incluir:

duration_ms
operation
repository

Não registrar automaticamente todos os parâmetros da query.

36. HTTP Request Logs

A aplicação pode registrar um evento para requisições HTTP.

Campos possíveis:

request_id
method
path
status_code
duration_ms
tenant_id
user_id

Exemplo:

{
  "event": "http.request",
  "method": "GET",
  "path": "/api/v1/customers",
  "status_code": 200,
  "duration_ms": 34
}
37. HTTP Response

Não registrar automaticamente o response body.

Normalmente são suficientes:

status_code
duration_ms
path
method

Isso reduz risco de exposição de dados.

38. Health Check

Health checks podem gerar muitos eventos.

Evitar registrar cada chamada de:

GET /health

em nível INFO quando isso gerar ruído.

Pode ser apropriado:

DEBUG

ou simplesmente utilizar métricas dedicadas.

39. Startup

A aplicação deve registrar eventos relevantes durante inicialização.

Exemplos:

application.starting
application.started

Podem incluir:

version
environment

Não incluir secrets.

40. Shutdown

Registrar encerramento quando isso ajudar no diagnóstico:

application.shutdown

Não é necessário registrar informações excessivas.

41. Worker Logs

Workers devem utilizar o mesmo padrão de logging.

Quando processando um job:

job.started
job.completed
job.failed
job.retry

Campos possíveis:

job_id
tenant_id
actor_user_id
request_id
operation
attempt
duration_ms
42. Job Correlation

Jobs originados por uma requisição HTTP podem preservar o contexto de correlação.

Exemplo:

HTTP Request
    ↓
request_id
    ↓
Create Job
    ↓
Worker
    ↓
same request_id

Quando isso for adequado, também registrar um identificador próprio do job.

43. Integration Hub

Quando o Integration Hub for implementado, os logs deverão permitir rastrear:

ERP API
    ↓
Integration Hub
    ↓
Queue
    ↓
Worker
    ↓
External API

Campos de correlação podem incluir:

request_id
job_id
integration_id
tenant_id

Isso será importante para diagnosticar retries e falhas de sincronização.

44. Log Correlation

Quando uma operação atravessar múltiplos componentes, utilizar identificadores de correlação.

Exemplo:

request_id
job_id
external_request_id

Não criar dezenas de IDs diferentes sem necessidade.

45. Audit Logs

Logs técnicos não substituem audit logs.

Exemplo:

Log técnico:
database.update.completed

Auditoria:

User 123 alterou preço do Product 456.

A auditoria deve possuir estrutura própria e seguir as regras de:

skills/observability/
46. Structured Fields

Preferir:

{
  "event": "order.created",
  "order_id": "uuid",
  "tenant_id": "uuid"
}

em vez de:

"Pedido 123 criado pelo tenant abc com usuário xyz"

Campos estruturados são mais fáceis de:

filtrar
pesquisar
agregar
monitorar
47. Dynamic Values

Não construir mensagens complexas concatenando grandes quantidades de dados.

Evitar:

logger.info(
    f"Pedido {order_id} criado pelo usuário {user_id} no tenant {tenant_id}"
)

Preferir logging estruturado quando a biblioteca utilizada permitir:

logger.info(
    "order.created",
    extra={
        "order_id": str(order_id),
        "user_id": str(user_id),
        "tenant_id": str(tenant_id),
    },
)

A implementação definitiva deve seguir a biblioteca de logging escolhida.

48. Consistência

Os mesmos conceitos devem utilizar os mesmos nomes.

Exemplo:

request_id
tenant_id
user_id
job_id
duration_ms
error_code

Não alternar entre:

requestId
request_identifier
req_id

sem uma decisão arquitetural.

49. Log Levels

Evitar utilizar:

ERROR

para todo problema.

Exemplo:

404 Not Found

não necessariamente é um erro de aplicação.

Da mesma forma:

database unavailable

provavelmente merece ERROR ou CRITICAL, dependendo do impacto.

50. Debug

Logs DEBUG podem ser mais detalhados durante desenvolvimento.

Mesmo assim:

password
token
secret
credentials

nunca devem ser registrados.

DEBUG não é exceção às regras de segurança.

51. Production

Em produção, priorizar:

INFO
WARNING
ERROR
CRITICAL

e utilizar DEBUG somente quando existir uma estratégia controlada.

Evitar alterar temporariamente o nível de log em produção sem avaliar volume e exposição.

52. Development

Durante desenvolvimento, logs podem possuir informações adicionais úteis para diagnóstico.

Mesmo assim, os princípios de segurança permanecem válidos.

Não usar ambiente de desenvolvimento como justificativa para registrar secrets.

53. Testes

Testes podem validar que eventos importantes foram registrados.

Quando relevante, testar:

event
level
request_id
tenant_id
error_code

Não testar conteúdo exato de mensagens quando isso criar acoplamento desnecessário.

Preferir validar campos estruturados.

54. Log Noise

Evitar logs repetitivos sem valor diagnóstico.

Exemplo:

function entered
function exited
variable value

em todas as funções.

Isso pode gerar enorme quantidade de logs sem ajudar a investigação.

55. Sensitive Data Filtering

Quando bibliotecas ou middlewares registrarem automaticamente requests, verificar se existe filtragem de:

Authorization
Cookie
password
token

Não presumir que o framework remove automaticamente todas as informações sensíveis.

56. Failure Safety

Se o sistema de logging falhar:

logging failure
≠
business operation failure

quando possível.

Logs não devem causar indisponibilidade da aplicação simplesmente porque o mecanismo de observabilidade encontrou um problema.

A estratégia depende da infraestrutura utilizada.

57. Performance

Logging possui custo.

Considerar:

I/O
serialização
volume
CPU
armazenamento

Evitar logging detalhado em loops grandes ou operações de alto volume sem necessidade.

58. Retenção

A retenção de logs deve ser definida pela infraestrutura.

O código da aplicação não deve presumir armazenamento ilimitado.

Logs devem possuir estratégia para:

rotação
retenção
arquivamento
remoção

conforme o ambiente.

59. Monitoramento

Logs podem futuramente alimentar ferramentas de observabilidade.

O formato estruturado facilita integração com:

log aggregation
alertas
dashboards
monitoramento

A aplicação não deve ficar acoplada a uma plataforma específica sem necessidade.

60. Alertas

Nem todo ERROR deve gerar alerta imediato.

Alertas devem considerar:

frequência
gravidade
impacto
repetição

Exemplo:

database.connection_failed

pode exigir alerta.

Já:

customer.not_found

normalmente não deve gerar alerta operacional imediato.

61. Error Rate

A observabilidade futura deve permitir identificar aumento de:

4xx
5xx
timeouts
retries
failed jobs

Logs podem contribuir para isso, mas métricas serão preferíveis para agregações e alertas.

62. Correlation com Métricas

Quando possível, eventos de log devem utilizar nomes compatíveis com métricas.

Exemplo:

order.processing_failed

pode coexistir com:

orders_processing_failures_total

A convenção final será definida na documentação de observabilidade.

63. Tracing

Quando tracing for adicionado futuramente, o logging deve ser preparado para receber identificadores de trace/span.

Exemplo conceitual:

trace_id
span_id

Não implementar tracing apenas para adicionar campos vazios.

64. Segurança

Logs devem ser tratados como dados potencialmente sensíveis.

Acesso aos logs deve ser controlado.

Mesmo quando um dado não for secreto, ele pode possuir informações internas relevantes para segurança.

65. Alterações no Logging

Ao adicionar um novo evento:

definir nome do evento;
definir nível;
definir campos;
verificar informações sensíveis;
adicionar correlação quando necessário;
verificar volume;
criar testes quando relevante.
66. Checklist

Antes de finalizar uma alteração de logging:

 Evento possui nome consistente;
 Level está adequado;
 request_id foi considerado;
 tenant_id foi considerado;
 user_id foi considerado;
 job_id foi considerado quando necessário;
 Dados sensíveis não são registrados;
 Tokens não são registrados;
 Senhas não são registradas;
 Payloads não são registrados indiscriminadamente;
 Stack trace somente quando necessário;
 Volume de logs foi considerado;
 Health checks não geram ruído excessivo;
 Audit log não foi confundido com log técnico;
 Testes foram considerados.
67. Regra principal

Os logs devem permitir reconstruir o caminho técnico de uma operação sem expor informações sensíveis.

A estrutura principal deve permanecer:

timestamp
    +
level
    +
event
    +
request_id
    +
tenant_id
    +
user_id
    +
contexto necessário

O objetivo não é registrar tudo.

O objetivo é registrar o que será necessário para entender o comportamento do sistema quando algo precisar ser investigado.