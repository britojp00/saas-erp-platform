# Backend Background Jobs

## Objetivo

Definir os padrões para criação, execução, retry, idempotência, rastreabilidade e tratamento de falhas em tarefas executadas fora do ciclo normal de uma requisição HTTP.

Background jobs serão utilizados quando uma operação:

- for demorada;
- não precisar bloquear a resposta HTTP;
- puder ser processada de forma assíncrona;
- precisar de retry;
- envolver processamento em massa;
- depender de integração externa;
- exigir execução posterior ou agendada.

Este documento complementa:

```text
skills/02-architecture.md
skills/backend/README.md
skills/backend/architecture.md
skills/backend/services.md
skills/backend/exceptions.md
skills/backend/dependencies.md
skills/backend/testing.md
skills/infrastructure/README.md
skills/infrastructure/docker-compose.md
1. Princípios

Jobs devem ser:

Confiáveis
Idempotentes quando necessário
Rastreáveis
Reprocessáveis
Isolados por tenant
Observáveis

Um job não deve depender de uma requisição HTTP permanecer aberta.

2. Quando utilizar

Background jobs são apropriados para:

processamento de integrações
sincronização de dados
envio de notificações
importações
exportações
processamentos em massa
rotinas demoradas
reprocessamento
tarefas agendadas

Não utilizar jobs para operações simples que possam ser concluídas rapidamente dentro da própria requisição.

3. Quando não utilizar

Evitar background jobs para operações que:

precisam retornar imediatamente o resultado
são extremamente simples
não possuem benefício assíncrono
exigem consistência imediata com a resposta

Adicionar uma fila somente quando ela resolver um problema real.

4. Arquitetura

O fluxo conceitual é:

HTTP Request
     ↓
Router
     ↓
Service
     ↓
Create Job
     ↓
Queue
     ↓
Worker
     ↓
Service
     ↓
Repository / External API

A regra de negócio deve permanecer no service.

O worker coordena a execução da tarefa.

5. Queue

A fila será utilizada para separar:

produção do job

de:

execução do job

Exemplo:

Backend
   ↓
Queue
   ↓
Worker

Redis poderá ser utilizado como parte da infraestrutura de filas conforme a solução escolhida.

A tecnologia definitiva da fila deve ser definida antes da implementação.

6. Worker

Worker é o processo responsável por consumir jobs.

Exemplo conceitual:

Queue
 ↓
Worker
 ↓
Job Handler
 ↓
Service

O worker deve possuir ciclo de execução independente da API HTTP.

7. Um processo por responsabilidade

O backend HTTP e os workers devem possuir responsabilidades separadas.

Conceito:

backend
→ API HTTP

worker
→ processamento assíncrono

Não transformar o processo da API em um worker genérico.

8. Container do Worker

Quando executado em Docker, o worker deverá possuir seu próprio processo/container quando isso for apropriado.

Exemplo conceitual:

docker-compose
├── postgres
├── redis
├── backend
└── worker

O worker não deve executar PostgreSQL ou Redis dentro do mesmo container.

9. Job Payload

Um job deve carregar somente as informações necessárias para sua execução.

Exemplo:

{
  "job_id": "uuid",
  "tenant_id": "uuid",
  "entity_id": "uuid",
  "operation": "sync_customer"
}

Evitar colocar no payload:

senhas
tokens
secrets
objetos enormes
dados redundantes
10. Job ID

Todo job deverá possuir um identificador próprio quando o mecanismo de fila não fornecer um identificador suficiente.

Exemplo:

job_id

Esse identificador deve ser utilizado para:

logs
rastreamento
retry
diagnóstico
auditoria quando necessário
11. Request ID

Quando um job for originado por uma requisição HTTP, preservar o contexto de correlação quando apropriado.

Exemplo:

HTTP Request
    ↓
request_id
    ↓
create job
    ↓
job
    ↓
worker

Isso facilita rastrear uma operação do início ao fim.

12. Tenant ID

Jobs que trabalham com dados de tenant devem carregar:

tenant_id

de forma explícita.

Exemplo:

{
  "job_id": "uuid",
  "tenant_id": "uuid",
  "entity_id": "uuid"
}

O worker deve utilizar esse contexto nas operações de persistência.

13. Tenant Isolation

Nunca assumir que:

tenant_id

presente no payload é suficiente para autorização.

O job deve ser criado por uma operação autorizada e seu contexto deve ser respeitado pelo worker.

Consultas e alterações continuam obrigadas a utilizar o escopo de tenant.

14. Actor User

Quando um usuário humano iniciar um job, pode ser útil carregar:

actor_user_id

Exemplo:

{
  "tenant_id": "uuid",
  "actor_user_id": "uuid",
  "entity_id": "uuid"
}

Isso permite rastrear quem originou a operação.

Não é obrigatório quando o job for puramente sistêmico.

15. System Jobs

Jobs automáticos podem não possuir usuário humano.

Nesse caso:

actor_type = system

ou equivalente.

A representação definitiva deve ser simples e consistente.

16. Job Status

Quando a aplicação precisar acompanhar o estado de jobs, considerar estados como:

queued
processing
completed
failed
retrying
cancelled

Não criar estados que não sejam utilizados pela aplicação.

17. Estado

A transição deve ser previsível:

queued
   ↓
processing
   ↓
completed

Em caso de falha transitória:

processing
   ↓
retrying
   ↓
processing

Após exceder o limite:

processing
   ↓
failed
18. Idempotência

Jobs devem ser idempotentes quando houver possibilidade de:

retry
timeout
duplicidade
reprocessamento
redelivery

Executar o mesmo job duas vezes não deve duplicar efeitos indevidos.

19. Estratégias de Idempotência

Dependendo do caso, utilizar:

idempotency_key
external_id
unique constraint
processed_at
status
deduplication key

A solução deve ser escolhida de acordo com o domínio.

Não utilizar uma estratégia genérica para todos os jobs.

20. Exemplo de problema

Considere:

Job
→ criar cliente externo

O worker envia a requisição e recebe timeout.

É possível que:

API externa
→ tenha criado o cliente

mas:

worker
→ não tenha recebido a resposta

Repetir a operação sem idempotência pode criar um duplicado.

A integração deve considerar esse cenário.

21. Retry

Retry deve ser utilizado somente para erros potencialmente transitórios.

Exemplos:

timeout
connection reset
HTTP 429
HTTP 502
HTTP 503

Não retryar automaticamente erros permanentes.

22. Não Retry

Evitar retry automático para:

payload inválido
permission denied
recurso inexistente
regra de negócio inválida
dados inconsistentes

Retry nesses casos normalmente não resolve a causa.

23. Número de Tentativas

Jobs devem possuir limite de tentativas.

Exemplo conceitual:

attempt = 1
attempt = 2
attempt = 3

Depois do limite:

failed

O limite definitivo deve ser definido conforme a operação.

Não utilizar tentativas infinitas.

24. Exponential Backoff

Retries devem considerar backoff quando apropriado.

Conceito:

1ª tentativa
↓
pequena espera

2ª tentativa
↓
espera maior

3ª tentativa
↓
espera ainda maior

Isso reduz pressão sobre serviços temporariamente indisponíveis.

25. Jitter

Quando muitos jobs puderem falhar simultaneamente, jitter pode evitar que todos sejam repetidos exatamente no mesmo instante.

Conceito:

backoff
+
jitter

Utilizar quando houver necessidade operacional real.

26. Rate Limiting

Jobs que consomem APIs externas devem respeitar limites externos.

Exemplo:

HTTP 429
↓
retry
+
backoff

Não aumentar a frequência de chamadas após um rate limit.

27. Timeout

Toda chamada externa realizada por um worker deve possuir timeout.

Nunca deixar:

worker
↓
external API
↓
aguardando indefinidamente

Timeout deve ser definido conforme a operação.

28. Falha de Worker

Caso o worker seja encerrado durante o processamento:

job
↓
processing
↓
worker stopped

a infraestrutura de fila deve permitir comportamento seguro conforme a tecnologia escolhida.

A estratégia definitiva deve considerar:

ack
visibility timeout
redelivery
retry
29. Acknowledgement

Jobs devem ser confirmados somente quando seu processamento tiver alcançado o estado esperado.

Evitar confirmar antes da conclusão quando isso puder fazer uma tarefa ser perdida.

A implementação depende da tecnologia de fila adotada.

30. Falhas após processamento

Existe um cenário importante:

processamento concluído
↓
worker falha antes do acknowledgement
↓
job pode ser entregue novamente

Por isso, idempotência continua sendo necessária mesmo quando o código aparenta possuir somente uma execução.

31. Transactions

Jobs que alteram o banco devem respeitar as mesmas regras transacionais do backend.

Exemplo:

Job
 ↓
criar pedido
 ↓
baixar estoque
 ↓
commit

Caso a operação precise ser atômica:

erro
↓
rollback
32. Job + External API

Quando um job envolve:

PostgreSQL
+
API externa

não manter uma transação PostgreSQL aberta enquanto aguarda uma chamada externa demorada sem necessidade.

Exemplo de risco:

BEGIN
 ↓
UPDATE database
 ↓
aguarda API externa
 ↓
COMMIT

Isso pode manter recursos do banco ocupados desnecessariamente.

O fluxo deve ser desenhado conforme a necessidade de consistência.

33. Distributed Consistency

Operações envolvendo sistemas externos não possuem necessariamente uma única transação.

Exemplo:

PostgreSQL
+
External API

Não assumir atomicidade entre os dois sistemas.

Considerar:

retry
idempotência
estado
compensação
reprocessamento

quando necessário.

34. Job Result

Quando o resultado precisar ser consultado posteriormente, persistir somente o necessário.

Exemplo:

job_id
status
result_reference
completed_at

Evitar armazenar respostas enormes ou dados sensíveis no registro do job.

35. Job Error

Quando um job falhar, registrar informações suficientes para diagnóstico.

Exemplo:

job_id
error_code
error_type
attempt
tenant_id
timestamp

Não armazenar secrets ou tokens.

36. Error Classification

Uma falha de job deve ser classificada como:

retryable
non_retryable

quando a infraestrutura precisar tomar essa decisão automaticamente.

Exemplo:

timeout
→ retryable
payload inválido
→ non_retryable
37. Dead Letter

Jobs que excederem o limite de tentativas podem ser encaminhados para uma estrutura de falhas.

Conceito:

Queue
 ↓
Retry
 ↓
Retry
 ↓
Retry
 ↓
Dead Letter

Isso permite:

investigação
reprocessamento
correção manual
monitoramento

A implementação poderá ser adicionada quando a infraestrutura de filas for definida.

38. Reprocessing

Jobs falhos podem futuramente ser reprocessados.

O reprocessamento deve considerar:

idempotência
estado atual
dados alterados
tenant
causa original da falha

Não simplesmente executar novamente um job antigo sem verificar o contexto atual.

39. Cancelamento

Jobs longos podem futuramente suportar cancelamento.

A implementação deve possuir uma forma clara de identificar:

cancel requested
cancelled

Não assumir que qualquer job pode ser interrompido imediatamente.

40. Scheduling

Tarefas agendadas podem futuramente executar:

sincronizações
relatórios
limpezas
rotinas administrativas

Exemplos:

a cada 5 minutos
diariamente
semanalmente

O mecanismo de scheduling deve ser escolhido conforme as necessidades reais.

41. Scheduled Jobs e Tenant

Jobs agendados que percorrem tenants devem sempre respeitar isolamento.

Fluxo:

Scheduler
 ↓
Tenant A
 ↓
Job A

Scheduler
 ↓
Tenant B
 ↓
Job B

Evitar consultas globais que misturem dados de diferentes tenants sem necessidade.

42. Batch Processing

Jobs de processamento em massa devem evitar carregar todos os registros na memória.

Preferir processamento em lotes:

100 registros
↓
processa
↓
próximos 100
↓
...

O tamanho do lote deve ser ajustado conforme a operação.

43. Large Jobs

Jobs longos devem considerar:

timeout
memory usage
progress
retry
checkpoint

Quando necessário, dividir uma operação grande em jobs menores.

44. Progress

Jobs que demorarem significativamente podem possuir progresso.

Exemplo:

processed = 250
total = 1000

Não implementar progresso detalhado para jobs pequenos.

45. Worker Concurrency

O número de workers/concor­rências deve considerar:

CPU
memória
PostgreSQL connections
Redis
rate limits externos
natureza do job

Não assumir que aumentar workers sempre melhora performance.

46. Database Connections

Cada worker pode utilizar conexões ao PostgreSQL.

A configuração do pool deve considerar a quantidade total de processos.

Exemplo:

backend workers
+
background workers
=
total possible connections

Evitar exceder a capacidade do banco.

47. Logging

Jobs devem utilizar os mesmos padrões de logging do backend.

Eventos possíveis:

job.created
job.started
job.completed
job.failed
job.retry
job.cancelled

Campos relevantes:

job_id
request_id
tenant_id
actor_user_id
attempt
duration_ms
48. Segurança nos Logs

Nunca registrar:

password
access_token
refresh_token
API key
secret
database password

Payloads externos também não devem ser registrados integralmente sem necessidade.

49. Audit

Quando um job representar uma ação de negócio iniciada por um usuário, a operação poderá precisar de auditoria.

Exemplo:

Usuário exportou dados
↓
Job
↓
arquivo gerado

A auditoria deve registrar a ação de negócio, não cada etapa técnica do worker.

50. Observabilidade

Jobs devem permitir identificar:

qual job
qual tenant
quem iniciou
quando começou
quando terminou
quantas tentativas
qual foi o resultado

Isso será especialmente importante no Integration Hub.

51. Integration Hub

A arquitetura futura do Integration Hub utilizará fortemente background jobs.

Exemplo:

ERP API
   ↓
Integration Hub
   ↓
Queue
   ↓
Worker
   ↓
External API

Jobs deverão lidar com:

retry
idempotência
rate limit
timeout
webhooks
falhas
logs
52. Worker e Services

Worker não deve duplicar regra de negócio que já existe no service.

Preferir:

Worker
 ↓
Service

em vez de:

Worker
 ↓
regra própria

Isso permite que a mesma regra seja utilizada por:

API
Worker
Integration Hub

quando necessário.

53. Worker e Dependencies

Workers não devem depender diretamente das FastAPI Dependencies HTTP.

Não utilizar:

Depends(...)

para construir o contexto do worker.

O worker deve montar explicitamente suas dependências.

54. Worker e HTTP

O worker não deve depender de:

Request
Response
HTTP headers
HTTP session

O processamento deve funcionar independentemente do ciclo HTTP.

55. Testes Unitários

Testar o comportamento do job handler isoladamente.

Exemplos:

payload válido
payload inválido
service executado
erro retryable
erro non-retryable
56. Testes de Retry

Testar:

falha 1
↓
retry
↓
sucesso

E:

falha
↓
retry
↓
retry
↓
limite
↓
failed
57. Testes de Idempotência

Executar o mesmo job duas vezes.

Resultado esperado:

efeitos duplicados
→ não

quando o caso de uso exigir idempotência.

58. Testes Multi-tenant

Validar:

Tenant A
↓
Job A
↓
dados A

E impedir:

Job A
↓
dados B
59. Testes de Falha

Testar cenários como:

PostgreSQL indisponível
Redis indisponível
API externa indisponível
timeout
rate limit
payload inválido

quando essas dependências existirem.

60. Testes de Concorrência

Quando necessário, testar múltiplos jobs processando o mesmo recurso.

Exemplo:

Job A
+
Job B
↓
mesmo estoque

ou:

Job A
+
Job B
↓
mesmo evento externo

Validar que o estado final permanece consistente.

61. Testes de integração

Testar:

Queue
+
Worker
+
PostgreSQL
+
Redis

quando o comportamento depender da infraestrutura real.

Mocks podem ser usados para APIs externas.

62. Testes de reprocessamento

Quando houver reprocessamento:

job failed
↓
corrigir causa
↓
reprocess
↓
completed

Validar que o segundo processamento não cria duplicidade.

63. Performance

Jobs devem possuir comportamento compatível com o volume esperado.

Para operações em massa, considerar:

batch size
database load
memory
queue throughput
external API limits

Não utilizar benchmarks pesados na suíte funcional padrão.

64. Falhas no Startup

O worker deve falhar de forma clara quando uma configuração obrigatória estiver ausente.

Exemplos:

QUEUE_URL
REDIS_URL
DATABASE_URL

quando forem requisitos do worker.

Não iniciar parcialmente com configuração inválida.

65. Graceful Shutdown

Workers devem tratar encerramento de forma adequada.

Quando possível:

receber sinal
↓
parar de receber novos jobs
↓
finalizar processamento atual
↓
encerrar

A estratégia depende da tecnologia de fila.

66. Job Timeout

Jobs com limite de execução devem possuir timeout apropriado.

Um job preso indefinidamente pode:

consumir worker
ocupar conexão
bloquear fila

Timeout deve resultar em tratamento conhecido e possível retry quando apropriado.

67. Jobs Exclusivos

Algumas tarefas podem exigir que apenas uma execução esteja ativa por tenant ou recurso.

Exemplo:

sync_products

pode não poder executar simultaneamente duas vezes para o mesmo tenant.

Quando necessário, utilizar mecanismos de:

distributed lock
unique job
deduplication

Somente quando houver requisito real.

68. Locks

Locks devem possuir:

escopo
timeout
liberação segura

Evitar locks permanentes.

Redis pode futuramente auxiliar nesse tipo de coordenação.

69. Jobs e Estado do Domínio

Um job deve verificar o estado atual antes de executar operações sensíveis.

Não assumir que o estado existente no momento da criação do job continua igual.

Exemplo:

job criado
↓
pedido = pending

Antes da execução:

pedido = cancelled

O service deve avaliar o estado atual.

70. Eventos atrasados

Jobs podem ser executados muito depois da criação.

Por isso, sempre que necessário:

revalidar recurso
revalidar tenant
revalidar estado
revalidar permissões relacionadas

Não confiar somente em informações antigas do payload.

71. Segurança

Um job nunca deve permitir que seu payload seja utilizado para elevar privilégios.

Evitar permitir que o payload determine arbitrariamente:

tenant_id
actor_user_id
permissions
roles

sem validação no momento da criação e execução.

72. Payload Versioning

Quando jobs puderem permanecer na fila por longos períodos, alterações de payload devem considerar compatibilidade.

Exemplo:

job_type
payload_version

Somente utilizar versionamento quando existir uma necessidade real.

73. Backward Compatibility

Deploys não devem quebrar silenciosamente jobs que já estejam aguardando processamento.

Antes de remover ou renomear campos utilizados por jobs:

verificar jobs pendentes

e considerar compatibilidade temporária.

74. Job Types

Os tipos de job devem possuir nomes claros.

Exemplos:

customer.sync
product.sync
order.export
inventory.recalculate
notification.send

Evitar nomes genéricos como:

process
task
background
job

quando não comunicarem a operação.

75. Job Handler

Cada tipo de job deve possuir um handler claramente identificado.

Conceito:

customer.sync
    ↓
CustomerSyncJob
    ↓
CustomerService

Isso mantém a organização previsível.

76. Job Registry

Não criar um registry complexo sem necessidade.

Uma estrutura simples de mapeamento pode ser suficiente:

job_type
    ↓
handler

A implementação deve acompanhar a tecnologia de filas escolhida.

77. Composição

A composição do worker deve seguir:

Queue
 ↓
Job Handler
 ↓
Service
 ↓
Repository

O worker não deve acessar tabelas diretamente quando existir regra de negócio envolvida.

78. Dependências externas

Quando um job utilizar:

PostgreSQL
Redis
External API

essas dependências devem ser injetadas ou construídas de forma previsível.

Isso facilita testes e substituições.

79. Configuração

Configurações do worker devem seguir:

skills/infrastructure/environment.md

Não armazenar secrets diretamente no código.

80. Deploy

A infraestrutura de produção deverá garantir:

API disponível
+
workers disponíveis
+
queue disponível

quando existirem jobs ativos.

Escalar API e worker de forma independente quando isso fizer sentido.

81. Escalabilidade

A arquitetura deve permitir aumentar:

API instances
worker instances

de maneira independente.

Não depender de estado local do processo para manter consistência de jobs.

82. Worker Stateless

Sempre que possível, workers devem ser stateless.

Estado importante deve permanecer em:

PostgreSQL
Redis
Queue

e não somente na memória do processo.

83. Checklist

Antes de finalizar um background job:

 O uso de job é realmente necessário;
 O tipo de job é claro;
 O payload possui somente dados necessários;
 job_id existe quando necessário;
 tenant_id foi considerado;
 actor_user_id foi considerado quando necessário;
 Idempotência foi avaliada;
 Retry foi avaliado;
 Backoff foi avaliado;
 Timeout foi definido quando necessário;
 Rate limit externo foi considerado;
 Estado atual é revalidado;
 Transação está correta;
 Falhas possuem classificação;
 Jobs não dependem de Depends;
 Regra de negócio permanece no service;
 Logs possuem correlação;
 Secrets não aparecem nos logs;
 Testes de sucesso e falha existem;
 Testes de tenant existem;
 Testes de idempotência existem quando necessários;
 Reprocessamento foi considerado;
 Não existe complexidade desnecessária.
84. Regra principal

Background jobs devem retirar trabalho do ciclo HTTP sem retirar as regras de segurança e consistência do sistema.

A estrutura principal deve permanecer:

API
 ↓
Service
 ↓
Queue
 ↓
Worker
 ↓
Service
 ↓
Repository

O worker executa o trabalho.

O service continua sendo responsável pela regra de negócio.

A fila fornece desacoplamento.

A idempotência, o retry e a observabilidade protegem o processamento contra falhas reais de sistemas distribuídos.