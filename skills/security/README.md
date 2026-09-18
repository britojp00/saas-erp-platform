# Security

## Objetivo

Definir os princípios e padrões gerais de segurança do SaaS ERP Platform.

Segurança deve ser considerada em todas as camadas:

```text
Frontend
Backend
Database
Infrastructure
Authentication
Authorization
Integrations
Logs
CI/CD
AI-assisted Development

Este documento complementa:

skills/02-architecture.md
skills/backend/authentication.md
skills/backend/authorization.md
skills/backend/dependencies.md
skills/backend/exceptions.md
skills/backend/logging.md
skills/database/multi-tenancy.md
skills/infrastructure/environment.md
skills/infrastructure/docker.md
skills/testing/README.md
1. Princípios

O projeto deve seguir principalmente:

Least Privilege
Secure by Default
Defense in Depth
Fail Secure
Explicit Authorization
Tenant Isolation
Secret Management
Input Validation

Nenhuma camada deve assumir que outra camada sozinha garante toda a segurança.

2. Security by Default

Novas funcionalidades devem partir de um estado protegido.

Conceito:

não autenticado
    ↓
negado

autenticado
+
sem permission
    ↓
negado

tenant incorreto
    ↓
negado

O acesso deve ser concedido explicitamente.

3. Least Privilege

Usuários, serviços, workers e integrações devem possuir somente as permissões necessárias.

Evitar:

usuário comum
→ acesso administrativo

worker
→ credenciais desnecessárias

serviço
→ acesso irrestrito ao banco

Cada componente deve receber somente o acesso necessário.

4. Authentication

Recursos protegidos devem exigir autenticação válida.

A autenticação deve verificar:

token
assinatura
algoritmo
expiração
identidade
status da conta

Consultar:

skills/backend/authentication.md

para os detalhes da implementação.

5. Authorization

Autenticação não significa autorização.

A aplicação deve verificar:

User
↓
Tenant
↓
Role
↓
Permission
↓
Resource
↓
Business Rule

A autorização deve permanecer no backend.

6. Tenant Isolation

O isolamento entre tenants é um requisito crítico.

Uma requisição de:

Tenant A

não pode acessar dados de:

Tenant B

somente porque possui um ID válido.

Todas as operações multi-tenant devem considerar o contexto autorizado.

7. Tenant ID

Não confiar em:

tenant_id enviado pelo frontend

como mecanismo de autorização.

O tenant deve ser derivado de um contexto confiável.

Exemplo conceitual:

JWT
↓
User
↓
Tenant
↓
Database Query
8. Cross-tenant Access

Tentativas de acesso cross-tenant devem ser bloqueadas.

Exemplo:

User A
Tenant A
    ↓
Customer B
Tenant B

Resultado:

acesso negado

Esse comportamento deve ser protegido por testes.

9. Resource Ownership

Alguns recursos podem exigir:

Permission
+
Tenant
+
Owner

Não assumir que possuir uma permission global dentro do tenant concede acesso irrestrito a todos os recursos quando o domínio possuir regras de propriedade.

10. Input Validation

Toda entrada externa deve ser considerada não confiável.

Fontes incluem:

HTTP body
query parameters
path parameters
headers
cookies
webhooks
external APIs
queue messages
uploaded files

Validar formato, tipo e limites.

11. Pydantic

O backend deve utilizar Pydantic para validação estrutural dos dados da API.

Validar quando aplicável:

UUID
email
datetime
Enum
Decimal
strings
quantidades
limites

Regras que dependem do estado do sistema continuam sendo responsabilidade do service.

12. SQL Injection

Nunca concatenar entrada do usuário diretamente em SQL.

Evitar:

query = f"SELECT * FROM customers WHERE name = '{name}'"

Preferir:

SQLAlchemy
+
queries parametrizadas

Filtros e ordenações dinâmicas também devem ser controlados.

13. Dynamic Sorting

Nunca utilizar diretamente um valor recebido do cliente como nome de coluna SQL.

Evitar:

text(sort)

sem validação.

Preferir um conjunto explícito de campos permitidos.

14. Mass Assignment

Não permitir que o cliente atualize campos arbitrários da entidade.

Campos controlados pelo backend incluem, conforme o domínio:

tenant_id
user_id
created_at
updated_at
deleted_at
roles
permissions

Utilizar schemas explícitos de criação e atualização.

15. Authentication Secrets

Nunca colocar secrets no código.

Exemplos:

JWT_SECRET_KEY
API_TOKEN
DATABASE_PASSWORD
PRIVATE_KEY

Devem ser fornecidos por mecanismos apropriados de configuração.

Consultar:

skills/infrastructure/environment.md
16. .env

O arquivo:

.env

não deve ser versionado.

O projeto deve fornecer:

.env.example

sem credenciais reais.

17. Git Secrets

Antes de realizar um commit, verificar se não foram adicionados:

passwords
tokens
API keys
private keys
.env
credentials

O Git não deve ser utilizado como armazenamento de secrets.

18. Secret Exposure

Secrets não devem aparecer em:

source code
logs
exceptions
API responses
audit logs
job payloads
screenshots
documentation
tests

quando não forem estritamente necessários.

19. Passwords

Senhas devem ser armazenadas somente como hashes.

Nunca armazenar:

plain password

Utilizar o mecanismo de hashing definido pelo projeto.

Atualmente:

pwdlib
20. Password Hash

O hash da senha é informação sensível.

Não retornar:

{
  "password_hash": "..."
}

através da API.

Também não registrar esse valor em logs.

21. JWT

JWT deve:

possuir assinatura
possuir expiração
utilizar algoritmo conhecido
utilizar secret protegido

Não utilizar tokens sem expiração.

22. JWT Payload

Colocar no token somente informações necessárias.

Evitar incluir:

password
password_hash
secret
tokens externos
dados pessoais desnecessários
payloads grandes
23. JWT Algorithm

O backend deve definir explicitamente o algoritmo esperado.

Não aceitar qualquer algoritmo indicado pelo cliente.

24. Token Exposure

Nunca registrar:

Authorization: Bearer ...

completo.

Também não retornar tokens em mensagens de erro ou logs.

25. Cookies e Headers

Quando cookies forem utilizados, avaliar:

Secure
HttpOnly
SameSite

conforme a estratégia de autenticação.

Headers de autenticação também devem ser tratados como informações sensíveis.

26. CORS

CORS deve ser configurado explicitamente.

Evitar permitir indiscriminadamente:

*

em ambientes que utilizem autenticação ou dados privados.

As origens permitidas devem vir de configuração apropriada.

27. CSRF

Quando a autenticação utilizar cookies, avaliar proteção contra CSRF.

A estratégia dependerá da forma final de autenticação do frontend.

Não assumir que JWT elimina automaticamente todos os riscos relacionados a CSRF.

28. XSS

O frontend deve tratar dados provenientes de:

usuário
API
external APIs
webhooks

como conteúdo potencialmente não confiável.

Não renderizar HTML arbitrário sem sanitização adequada.

29. Frontend Security

O frontend nunca deve ser considerado uma barreira de segurança.

Esconder:

botão
menu
rota visual

não impede chamadas diretas à API.

Toda autorização deve existir no backend.

30. Sensitive Data

Evitar exposição desnecessária de:

documentos
informações financeiras
dados pessoais
credenciais
dados internos

Retornar somente os campos necessários ao consumidor.

31. Error Messages

Erros públicos não devem revelar:

SQL
stack trace
filesystem path
database host
credentials
internal implementation

O cliente deve receber mensagens seguras.

Detalhes técnicos permanecem nos logs internos.

32. Exception Handling

Exceções devem ser tratadas de forma consistente.

Não retornar diretamente:

str(exception)

quando isso puder expor detalhes internos.

Consultar:

skills/backend/exceptions.md
33. Logging Security

Logs devem ser tratados como informações potencialmente sensíveis.

Nunca registrar:

password
password_hash
access_token
refresh_token
JWT
API key
secret
private key

Consultar:

skills/backend/logging.md
34. Request Logging

Não registrar automaticamente:

Authorization
Cookie
Set-Cookie

nem payloads completos que possam conter informações sensíveis.

35. Audit Security

Audit logs devem registrar ações relevantes sem armazenar secrets.

Exemplo:

user_id
tenant_id
action
entity
entity_id
timestamp

Evitar registrar credenciais ou dados sensíveis desnecessários.

36. Database Security

O banco deve utilizar credenciais específicas do ambiente.

Não utilizar credenciais administrativas para todos os componentes se níveis menores forem suficientes.

37. Database Permissions

Aplicações devem possuir somente os privilégios necessários no banco.

Quando apropriado, separar:

application user
migration user
administrative user

Essa separação pode ser adicionada conforme a infraestrutura de produção evoluir.

38. Database Exposure

PostgreSQL não deve ser exposto publicamente sem necessidade.

Em ambientes containerizados:

backend
↓
private network
↓
postgres

deve ser preferível a exposição pública.

39. Redis Security

Redis não deve ser exposto publicamente sem necessidade.

Deve ser acessível apenas pelos componentes que precisam utilizá-lo.

40. Docker Security

Containers devem:

usar imagens versionadas
evitar secrets embutidos
utilizar usuário não-root quando apropriado
possuir somente dependências necessárias

Consultar:

skills/infrastructure/docker.md
41. Docker Images

Evitar utilizar:

latest

como referência única de produção.

Preferir versões explícitas e reprodutíveis.

42. Container Secrets

Nunca colocar secrets dentro da imagem através de:

Dockerfile
COPY .env
ARG SECRET
ENV SECRET=...

durante o build.

Secrets devem ser fornecidos no runtime através de mecanismos apropriados.

43. Container Network

Não utilizar IPs fixos como estratégia padrão de comunicação interna.

Preferir nomes de serviço do Docker Compose.

Exemplo:

postgres
redis
backend
worker
44. Dependency Security

Antes de adicionar dependências:

compatibilidade
manutenção
necessidade
risco

devem ser avaliados.

Evitar bibliotecas desnecessárias.

45. Dependency Updates

Dependências devem ser mantidas atualizadas de forma controlada.

Atualizações devem ser testadas.

Não atualizar dezenas de dependências automaticamente sem verificar possíveis impactos.

46. Lock Files

Arquivos de lock devem ser versionados.

Backend:

uv.lock

Isso ajuda a manter builds reproduzíveis.

47. Supply Chain

Dependências externas devem ser tratadas como parte da superfície de ataque.

Considerar:

origem
reputação
manutenção
versão
vulnerabilidades

antes de adicionar novos pacotes.

48. File Uploads

Quando o sistema futuramente permitir upload de arquivos, validar:

tipo
extensão
tamanho
nome
conteúdo
local de armazenamento

Não confiar somente na extensão do arquivo.

49. Path Traversal

Nunca permitir que valores fornecidos pelo cliente controlem diretamente caminhos do filesystem.

Evitar:

open(user_input)

sem validação e normalização apropriadas.

50. SSRF

Integrações que permitirem URLs configuráveis devem considerar riscos de SSRF.

Não permitir que usuários forneçam arbitrariamente:

URL
host
IP
porta

para o backend acessar sem validação.

51. Webhooks

Webhooks devem ser tratados como entrada externa não confiável.

Validar quando disponível:

signature
timestamp
event type
event id
payload
52. Webhook Replay

Quando o provedor fornecer identificador ou timestamp de evento, considerar proteção contra replay.

Mecanismos possíveis:

event_id
timestamp
unique constraint
processed_at
53. External APIs

Toda resposta externa deve ser considerada não confiável.

Validar:

status
content type
payload
required fields
types
54. Rate Limiting

Endpoints sensíveis podem utilizar rate limiting.

Especialmente:

login
password recovery
webhooks
expensive operations
external integrations

Redis poderá ser utilizado quando necessário.

55. Brute Force

Tentativas repetidas de autenticação devem possuir proteção apropriada.

Possibilidades:

rate limiting
temporary lock
attempt tracking

A estratégia deve evitar tanto ataques de força bruta quanto bloqueios abusivos.

56. Account Enumeration

Mensagens de autenticação não devem revelar desnecessariamente se uma conta existe.

Exemplo:

credenciais inválidas

pode ser preferível a respostas distintas que permitam enumerar usuários.

57. Authorization Failures

Falhas de autorização relevantes podem ser registradas para investigação.

Não expor ao cliente informações adicionais sobre:

roles
permissions internas
estrutura administrativa
outros tenants

sem necessidade.

58. Multi-tenant Cache

Caches devem possuir escopo correto.

Evitar:

customer:123

quando IDs puderem existir em diferentes tenants.

Preferir chaves que incluam o contexto necessário:

tenant:{tenant_id}:customer:{customer_id}
59. Multi-tenant Jobs

Jobs devem respeitar:

tenant_id

e não permitir processamento cruzado.

O worker deve utilizar queries tenant-aware.

60. Multi-tenant Integrations

Configurações de integração devem permanecer vinculadas ao tenant correto.

Exemplo:

Tenant A
→ External Account A

Tenant B
→ External Account B

Nunca misturar credenciais ou dados de tenants diferentes.

61. Background Jobs Security

Jobs devem ser tratados como mensagens potencialmente manipuláveis.

Validar:

job type
payload
tenant
entity
state

antes de executar operações críticas.

62. Idempotency Security

Idempotência ajuda também na proteção contra:

duplicação
replay
redelivery
retries

quando utilizada corretamente.

63. Concurrency Security

Concorrência pode produzir condições que resultem em:

saldo incorreto
estoque negativo
duplicidade
estado inconsistente

Utilizar mecanismos de banco apropriados quando necessário.

64. Database Constraints

Regras importantes devem ser reforçadas pelo banco quando apropriado.

Exemplos:

UNIQUE
FOREIGN KEY
NOT NULL
CHECK

Isso cria uma segunda camada de proteção.

65. Security Through Multiple Layers

Para uma operação crítica:

API Validation
    ↓
Authentication
    ↓
Authorization
    ↓
Tenant Isolation
    ↓
Business Rules
    ↓
Database Constraints

Não depender de uma única camada.

66. Secrets in Tests

Testes não devem utilizar secrets reais.

Utilizar:

dummy values
test credentials
isolated environments

quando necessário.

67. CI/CD Security

CI/CD não deve expor secrets nos logs.

Evitar imprimir:

env
tokens
credentials

durante workflows.

Secrets devem ser fornecidos através do mecanismo apropriado da plataforma.

68. GitHub Actions

Workflows devem possuir permissões mínimas quando possível.

Evitar conceder acesso administrativo ao workflow sem necessidade.

69. Pull Requests

Alterações de segurança devem ser revisadas cuidadosamente.

Considerar:

authentication
authorization
tenant isolation
secrets
database
dependencies
external integrations
70. Security Tests

Testar explicitamente:

cross-tenant access
privilege escalation
invalid token
expired token
missing permission
mass assignment
SQL injection attempts
webhook validation

quando aplicável.

71. Regression Security Tests

Quando uma vulnerabilidade ou falha de segurança for corrigida:

falha encontrada
↓
teste reproduzindo falha
↓
correção
↓
teste passa

O teste deve permanecer na suíte.

72. Security and AI-assisted Development

IA utilizada no desenvolvimento deve seguir todas as regras de segurança do projeto.

A IA não deve:

inventar credentials
expor secrets
desabilitar autenticação
remover tenant filters
ignorar authorization

somente para fazer uma implementação funcionar.

73. AI-generated Code

Código gerado por IA deve ser revisado.

Verificar especialmente:

authentication
authorization
tenant isolation
SQL queries
input validation
secrets
logging
external integrations

Não considerar código gerado automaticamente como confiável por padrão.

74. AI Context

Ao fornecer contexto para ferramentas de IA, evitar incluir:

passwords
API keys
JWT secrets
private keys
production credentials

Utilizar placeholders quando esses dados não forem necessários para a análise.

75. Prompt Injection

Conteúdo externo consumido pela aplicação, como:

webhooks
emails
documentos
integrações
dados de usuários

não deve ser tratado como instrução confiável para agentes de IA.

Quando o projeto futuramente utilizar IA em fluxos automáticos, separar:

System Instructions
+
Application Context
+
Untrusted User / External Data
76. AI Actions

Quando agentes de IA puderem executar ações no sistema, suas permissões devem ser explicitamente limitadas.

Evitar conceder automaticamente:

admin
database access
all API permissions

a agentes de IA.

77. AI Auditability

Ações importantes executadas por agentes de IA devem possuir rastreabilidade adequada.

Quando aplicável:

actor_type = ai
actor_id
tenant_id
action
entity
timestamp

Isso será definido quando funcionalidades de IA executarem ações reais.

78. Production Security

Produção deve possuir configurações diferentes do ambiente de desenvolvimento.

Principalmente:

debug
credentials
CORS
database
logging
external integrations

Não promover configurações de desenvolvimento para produção sem revisão.

79. Debug

Não habilitar debug em produção sem uma necessidade operacional controlada.

Debug pode revelar:

stack traces
configuration
internal state
80. Environment Isolation

Ambientes devem permanecer separados:

development
test
production

Credenciais e bancos de dados não devem ser compartilhados sem necessidade.

81. Backups

Dados importantes devem possuir estratégia de backup no ambiente de produção.

A infraestrutura de backup deve considerar:

frequency
retention
restoration
security

Não armazenar backups em locais públicos.

82. Disaster Recovery

Sistemas críticos devem considerar recuperação após:

database failure
infrastructure failure
data corruption
credential compromise

A estratégia será definida conforme a infraestrutura de produção evoluir.

83. Security Monitoring

A observabilidade deverá permitir identificar eventos como:

login failures
authorization denials
unusual error rates
external integration failures
worker failures

Alertas devem ser definidos conforme o risco real.

84. Incident Response

Quando houver um incidente de segurança:

detectar
↓
conter
↓
investigar
↓
corrigir
↓
validar
↓
documentar

O processo operacional será detalhado conforme a necessidade do projeto.

85. Security Documentation

Decisões de segurança importantes devem ser documentadas.

Exemplos:

authentication strategy
tenant model
token strategy
secret management
external integration authentication

Evitar depender somente de conhecimento implícito no código.

86. Security Review

Antes de concluir uma funcionalidade sensível, verificar:

Quem pode acessar?
Qual tenant?
Qual recurso?
Qual permission?
Quais dados são expostos?
O que acontece se houver falha?
O que acontece se o cliente manipular a requisição?
87. Security Checklist

Antes de finalizar uma funcionalidade:

 Entrada externa foi validada;
 Authentication foi considerada;
 Authorization foi considerada;
 Tenant isolation foi considerada;
 Resource ownership foi considerado quando necessário;
 Secrets não estão no código;
 Secrets não aparecem nos logs;
 Erros não expõem detalhes internos;
 Queries são parametrizadas;
 Dynamic filters/sorting são controlados;
 Mass assignment foi evitado;
 Dados sensíveis não são expostos;
 Cache respeita tenant;
 Jobs respeitam tenant;
 Integrações validam entrada externa;
 Webhooks possuem validação quando aplicável;
 Rate limiting foi considerado;
 Idempotência foi considerada;
 Concorrência foi considerada;
 Testes de segurança existem;
 Código gerado por IA foi revisado;
 Nenhuma credencial real foi adicionada.
88. Regra principal

Segurança deve existir em camadas.

O fluxo esperado é:

Input Validation
      ↓
Authentication
      ↓
Authorization
      ↓
Tenant Isolation
      ↓
Business Rules
      ↓
Database Integrity
      ↓
Logging / Audit
      ↓
Monitoring

Nenhuma funcionalidade deve depender de uma única barreira de segurança.

O sistema deve assumir que:

clientes podem enviar dados inválidos
usuários podem tentar acessar recursos indevidos
integrações podem falhar
workers podem repetir jobs
redes podem falhar
dependências podem possuir vulnerabilidades
código gerado por IA pode conter erros

A arquitetura deve permanecer segura mesmo diante desses cenários.