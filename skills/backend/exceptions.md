# Backend Exceptions

## Objetivo

Definir os padrões para criação, organização, propagação e tratamento de exceções no backend do SaaS ERP Platform.

As exceções devem permitir separar claramente:

```text
Erro de entrada
Erro de autenticação
Erro de autorização
Erro de negócio
Erro de persistência
Erro externo
Erro inesperado

Este documento complementa:

skills/02-architecture.md
skills/backend/README.md
skills/backend/architecture.md
skills/backend/api.md
skills/backend/authentication.md
skills/backend/authorization.md
skills/backend/services.md
skills/backend/repositories.md
skills/backend/schemas.md
1. Princípios

Erros devem ser:

previsíveis;
explícitos;
consistentes;
rastreáveis;
seguros;
fáceis de testar.

O sistema deve evitar transformar qualquer falha em:

500 Internal Server Error

quando a aplicação consegue identificar corretamente o tipo de erro.

2. Tipos de erro

O backend deve distinguir pelo menos:

Validation Error
Authentication Error
Authorization Error
Domain Error
Persistence Error
External Service Error
Internal Error

Cada categoria possui tratamento diferente.

3. Validation Error

Representa uma entrada que não atende ao contrato da API.

Exemplos:

campo obrigatório ausente
tipo incorreto
UUID inválido
data inválida
valor fora do limite
enum inválido

Esses erros normalmente são tratados pelo FastAPI/Pydantic.

Resposta esperada:

422 Unprocessable Entity

quando aplicável ao contrato da API.

4. Authentication Error

Representa falha na identificação do usuário.

Exemplos:

token ausente
token expirado
token inválido
credenciais inválidas

Resposta:

401 Unauthorized

Não utilizar 403 para uma identidade que não foi autenticada.

5. Authorization Error

Representa um usuário autenticado que não possui autorização suficiente.

Exemplo:

usuário autenticado
+
sem customer.delete

Resposta:

403 Forbidden
6. Domain Error

Representa uma regra de negócio que impede a operação.

Exemplos:

CustomerNotFoundError
DuplicateCustomerError
ProductInactiveError
InsufficientStockError
OrderNotCancelableError
OrderAlreadyCancelledError

Esses erros normalmente são produzidos pelos services.

7. Domain Exceptions

Exceções de negócio devem possuir nomes claros.

Preferir:

class InsufficientStockError(Exception):
    ...

em vez de:

class BusinessException(Exception):
    ...

quando o comportamento puder ser identificado de forma específica.

8. Base Domain Exception

Pode existir uma exceção base para erros de domínio.

Exemplo conceitual:

class DomainError(Exception):
    """Base exception for business rule violations."""

Depois:

class InsufficientStockError(DomainError):
    ...

Isso permite tratamento agrupado sem perder a especificidade do erro.

9. Código do erro

Erros expostos pela API devem possuir códigos estáveis quando necessário.

Exemplo:

INSUFFICIENT_STOCK
CUSTOMER_NOT_FOUND
DUPLICATE_CUSTOMER
ORDER_NOT_CANCELABLE

O código deve ser independente do texto exibido ao usuário.

10. Message

A mensagem deve ser clara e segura.

Exemplo:

Estoque insuficiente para o produto informado.

Evitar mensagens contendo:

SQL
stack trace
caminho interno
credenciais
tokens
secrets
11. Error Response

O formato da resposta de erro deve permanecer consistente.

Exemplo conceitual:

{
  "detail": {
    "code": "INSUFFICIENT_STOCK",
    "message": "Estoque insuficiente para o produto informado."
  }
}

O formato definitivo deve ser centralizado antes da expansão da API.

12. Domain Error → HTTP

O domínio não deve depender diretamente do HTTP.

Evitar:

from fastapi import HTTPException

raise HTTPException(
    status_code=409,
    detail="..."
)

dentro do service somente para representar uma regra de negócio.

Preferir:

raise DuplicateCustomerError()

e realizar a tradução em uma camada apropriada.

13. HTTP Exception

HTTPException pode ser utilizada quando o erro realmente pertence à camada HTTP.

Exemplos:

autenticação
headers
HTTP-specific behavior

Entretanto, erros de domínio devem continuar independentes do FastAPI quando possível.

14. Exception Handler

Erros conhecidos podem ser convertidos para responses através de exception handlers.

Conceito:

DomainError
    ↓
Exception Handler
    ↓
HTTP Response

Isso evita repetir a mesma conversão em todos os endpoints.

15. Handler de DomainError

Um handler pode mapear tipos conhecidos:

InsufficientStockError
    ↓
409 Conflict
CustomerNotFoundError
    ↓
404 Not Found
DuplicateCustomerError
    ↓
409 Conflict

A tabela definitiva de mapeamento deve ser mantida consistente no projeto.

16. Not Found

Quando o recurso não existir:

404 Not Found

Exemplos:

CustomerNotFoundError
ProductNotFoundError
OrderNotFoundError

Em recursos multi-tenant, não revelar dados que permitam descobrir a existência de recursos de outro tenant.

17. Conflict

Quando a operação conflitar com o estado atual:

409 Conflict

Exemplos:

DuplicateCustomerError
SkuAlreadyExistsError
OrderAlreadyCancelledError
OrderNotCancelableError

O código deve representar a condição real do domínio.

18. Bad Request

400 Bad Request pode representar solicitações inválidas que não se encaixem melhor em validação automática ou outro status específico.

Não utilizar 400 para absolutamente todo erro.

Preferir status mais específicos quando apropriado.

19. Unauthorized

Utilizar:

401 Unauthorized

somente para falhas de autenticação.

Exemplos:

token ausente
token inválido
token expirado
credenciais inválidas
20. Forbidden

Utilizar:

403 Forbidden

quando:

usuário autenticado
+
sem autorização

Exemplo:

PermissionDeniedError
21. Unprocessable Entity

Utilizar:

422 Unprocessable Entity

quando aplicável às validações de entrada da API.

Pydantic/FastAPI já fornece mecanismos para grande parte dessas validações.

Não criar exceptions manuais para substituir validações que o schema já consegue realizar.

22. Persistence Error

Erros originados no banco ou camada de persistência devem ser separados das regras de negócio.

Exemplos:

DatabaseConnectionError
DatabaseIntegrityError
DatabaseTimeoutError

A nomenclatura definitiva deve refletir o tipo de falha.

23. Integrity Errors

Exemplo:

UNIQUE violation
FOREIGN KEY violation
CHECK violation

A camada de persistência pode identificar a falha e transformá-la em uma exceção apropriada.

Quando a causa tiver um significado de negócio conhecido, ela pode ser traduzida para um erro de domínio.

24. Não expor erros do PostgreSQL

Evitar retornar diretamente:

psycopg / asyncpg error

para o cliente.

Não expor:

nome de tabela
nome de constraint
SQL
host
database
stack trace

em responses de produção.

25. External Service Error

Integrações externas podem falhar por motivos como:

timeout
connection error
HTTP 500
HTTP 429
payload inválido
serviço indisponível

Esses erros devem ser diferenciados de erros internos do ERP.

Exemplos:

ExternalServiceTimeoutError
ExternalServiceUnavailableError
ExternalServiceRateLimitError
ExternalServiceResponseError

somente quando houver necessidade real.

26. Retryable Errors

Alguns erros externos ou de infraestrutura podem ser temporários.

Exemplo:

timeout
connection reset
HTTP 503
HTTP 429

A aplicação pode identificar esses casos como candidatos a retry.

Não realizar retry automaticamente em qualquer exception.

27. Idempotência e Exceptions

Operações com retry devem considerar o impacto da repetição.

Exemplo:

create_order()

Se houver timeout depois que o banco confirmou a operação, repetir indiscriminadamente pode criar duplicidade.

O tratamento deve considerar:

idempotency key
external_id
unique constraint
processed state

quando aplicável.

28. Internal Error

Erros inesperados devem ser tratados como erro interno.

Exemplo:

bug
estado impossível
erro não previsto
falha de configuração

Resposta:

500 Internal Server Error

A resposta pública deve ser genérica.

O detalhe técnico deve permanecer nos logs.

29. Segurança

Nunca retornar diretamente:

str(exception)

para o cliente quando a exception puder conter informações internas.

Evitar:

return {"error": str(exc)}

como mecanismo genérico.

30. Logging de Exceptions

Exceptions relevantes devem ser registradas com contexto suficiente para investigação.

Quando disponível:

request_id
tenant_id
user_id
error_code
event
timestamp

Não registrar:

password
token
JWT
secret
API key
credentials
31. Stack Trace

Stack traces são úteis para diagnóstico interno.

Entretanto:

production response
≠
internal log

O stack trace pode ser registrado internamente em erros inesperados, mas não deve ser enviado ao cliente em produção.

32. Exception Context

Quando for útil, uma exception de domínio pode carregar dados estruturados.

Exemplo conceitual:

class InsufficientStockError(DomainError):
    def __init__(self, product_id, available, requested):
        ...

Esses dados podem ser usados para:

logs
auditoria
mensagem
monitoramento

Somente expor ao cliente o que fizer parte do contrato público.

33. Exceptions e Tenant

Erros relacionados a recursos multi-tenant não devem revelar informações sobre outro tenant.

Exemplo:

Tenant A solicita Customer B

Não retornar:

"Customer B existe, mas pertence ao Tenant B"

quando essa informação não deveria ser revelada.

O comportamento deve ser compatível com o modelo de segurança adotado.

34. Exceptions e autorização

Quando a operação não for autorizada:

403 Forbidden

Não substituir uma falha de autorização por uma exceção genérica de negócio.

Isso facilita:

API contract
logs
monitoramento
testes
35. Exceptions em Services

Services devem lançar exceções específicas para condições esperadas.

Exemplo:

if product.deleted_at is not None:
    raise ProductInactiveError()

Evitar:

raise Exception("Produto inválido")
36. Exceptions em Repositories

Repositories podem lançar ou traduzir erros técnicos de persistência.

Exemplo:

DatabaseIntegrityError
DatabaseUnavailableError

Não retornar HTTPException.

Não esconder erros silenciosamente.

37. Propagação

A propagação deve ser previsível:

Repository
    ↓
Persistence Error
    ↓
Service
    ↓
Domain Error / propagate
    ↓
Exception Handler
    ↓
HTTP Response

Não capturar exceptions sem necessidade somente para evitar que subam na stack.

38. Catch específico

Preferir:

try:
    ...
except IntegrityError:
    ...

em vez de:

try:
    ...
except Exception:
    ...

quando o objetivo for tratar uma condição específica.

Catches genéricos devem ser utilizados somente quando houver uma razão clara.

39. Não engolir erros

Evitar:

try:
    ...
except Exception:
    pass

Isso pode ocultar falhas importantes e deixar o sistema em estado inconsistente.

Quando um erro não puder ser resolvido, propagá-lo ou tratá-lo explicitamente.

40. Retry

Retry deve ocorrer somente quando:

erro é potencialmente transitório
+
operação pode ser repetida com segurança

Não realizar retry automático para:

regra de negócio
payload inválido
permission denied
not found
unique violation
41. Transactions e Exceptions

Quando uma exception ocorrer dentro de uma operação transacional:

erro
    ↓
rollback
    ↓
propagação

A session não deve continuar em estado inválido.

42. Background Jobs

Workers também devem distinguir:

retryable
non-retryable

Exemplo:

HTTP 503
→ retry

payload inválido
→ não retry

permission inválida
→ não retry

O job deve possuir política explícita de retry e limite de tentativas.

43. Dead Letter

Quando jobs falharem repetidamente, uma estratégia futura poderá encaminhá-los para uma estrutura de falhas, como:

Dead Letter Queue

Isso permite:

investigação
reprocessamento
monitoramento

Não implementar uma infraestrutura complexa até existir necessidade real.

44. Exception e Auditoria

Nem toda exception precisa gerar audit log.

Diferenciar:

erro técnico

de:

evento de negócio relevante

Exemplo:

DatabaseTimeout
→ log técnico
Usuário cancelou pedido
→ auditoria de negócio

quando a operação for auditável.

45. Testes

Exceptions devem possuir testes específicos.

Testar:

tipo correto
status HTTP correto
error code correto
message apropriada
não exposição de detalhes internos
46. Testes de domínio

Exemplo:

estoque insuficiente
→ InsufficientStockError
pedido cancelável
→ cancelamento executado
pedido não cancelável
→ OrderNotCancelableError

Os testes devem validar o comportamento do service.

47. Testes de API

Validar a tradução:

DomainError
    ↓
HTTP response

Exemplo:

CustomerNotFoundError
→ 404
DuplicateCustomerError
→ 409
PermissionDenied
→ 403
AuthenticationError
→ 401
48. Testes de segurança

Verificar que erros não revelam:

dados de outro tenant
estrutura do banco
credentials
tokens
secrets
stack traces

Esses testes são especialmente importantes em endpoints públicos ou multi-tenant.

49. Organização

As exceptions podem ser organizadas em:

backend/app/
└── core/
    └── exceptions.py

ou em uma estrutura equivalente caso o projeto evolua.

A localização definitiva deve ser única e consistente.

50. Hierarquia conceitual

Uma possível hierarquia:

AppError
├── DomainError
│   ├── CustomerNotFoundError
│   ├── ProductNotFoundError
│   ├── DuplicateCustomerError
│   ├── InsufficientStockError
│   └── OrderNotCancelableError
│
├── AuthenticationError
│
├── AuthorizationError
│
├── PersistenceError
│   ├── DatabaseIntegrityError
│   └── DatabaseUnavailableError
│
└── ExternalServiceError

A hierarquia final deve ser mantida simples.

Não criar dezenas de abstrações somente para organizar classes.

51. Error Codes

Os códigos devem possuir convenção consistente.

Exemplo:

CUSTOMER_NOT_FOUND
DUPLICATE_CUSTOMER
INSUFFICIENT_STOCK
ORDER_NOT_CANCELABLE
UNAUTHORIZED
FORBIDDEN
DATABASE_ERROR
EXTERNAL_SERVICE_ERROR

Evitar codes baseados em mensagens longas.

52. Mensagens

Mensagens podem ser:

"Cliente não encontrado."
"Estoque insuficiente."
"Pedido não pode ser cancelado neste estado."

O código deve permanecer estável mesmo que a mensagem seja alterada.

Isso permite que consumidores programem comportamentos com base no código e não no texto.

53. Internacionalização

A aplicação poderá futuramente suportar múltiplos idiomas.

Por isso, evitar utilizar mensagens como identificadores de lógica.

Preferir:

code

como identificador estável.

A implementação de internacionalização não deve ser criada antes de existir requisito real.

54. Documentação

Erros relevantes da API devem ser documentados no OpenAPI quando isso melhorar o contrato.

Exemplo:

POST /orders

pode documentar:

201
400
401
403
409
422

conforme os comportamentos reais do endpoint.

Não documentar status que a implementação não produz.

55. Checklist

Antes de finalizar uma alteração relacionada a exceptions:

 O erro possui categoria clara;
 Erros de domínio possuem exception específica;
 Authentication e Authorization estão separadas;
 HTTP status está correto;
 Error code é estável;
 Message não expõe informação interna;
 PostgreSQL errors não são retornados diretamente;
 Stack traces não são expostos em produção;
 Tenant isolation foi considerado;
 Retry foi avaliado quando aplicável;
 Transação realiza rollback quando necessário;
 Exceptions não são engolidas;
 Logs possuem contexto apropriado;
 Secrets não aparecem nos logs;
 Testes cobrem a exception;
 API documenta os erros relevantes.
56. Regra principal

A aplicação deve tratar erros como parte do contrato e da arquitetura.

A separação deve permanecer:

Schema
→ valida entrada

Authentication
→ identifica usuário

Authorization
→ controla acesso

Service
→ identifica regras de negócio inválidas

Repository
→ identifica falhas de persistência

Exception Handler
→ converte falhas conhecidas em respostas HTTP

Logs
→ preservam detalhes técnicos para diagnóstico

Erros devem ser tratados de maneira explícita, segura e previsível, sem esconder problemas nem expor detalhes internos para os consumidores da API.