# Backend Dependencies

## Objetivo

Definir os padrões para utilização das Dependencies do FastAPI no backend do SaaS ERP Platform.

Dependencies são utilizadas para resolver responsabilidades transversais da aplicação, como:

```text
Database Session
Authenticated User
Tenant Context
Authorization
Request Context

Este documento complementa:

skills/02-architecture.md
skills/backend/README.md
skills/backend/architecture.md
skills/backend/api.md
skills/backend/authentication.md
skills/backend/authorization.md
skills/backend/database.md
skills/backend/services.md
skills/backend/exceptions.md
1. Princípios

Dependencies devem:

possuir responsabilidade clara;
ser reutilizáveis;
evitar duplicação;
centralizar preocupações transversais;
facilitar testes;
respeitar a arquitetura do backend.

Não utilizar Dependencies como local genérico para colocar qualquer lógica da aplicação.

2. Localização

As dependencies podem ser organizadas dentro de:

backend/app/core/

ou em um módulo específico de dependencies, conforme a estrutura adotada pelo projeto.

Exemplo possível:

app/
└── core/
    ├── config.py
    ├── database.py
    ├── security.py
    └── dependencies.py

Caso a quantidade de dependencies cresça significativamente, elas poderão ser separadas por responsabilidade.

3. Database Session

A session do banco deve ser fornecida através de uma dependency.

Conceito:

async def get_db():
    async with session_factory() as session:
        yield session

O endpoint consome a session através do mecanismo de dependency injection do FastAPI.

Exemplo:

async def list_customers(
    db: AsyncSession = Depends(get_db),
):
    ...
4. Session Lifecycle

A dependency deve garantir:

Request
   ↓
Create Session
   ↓
Use Session
   ↓
Close Session

A session não deve permanecer aberta desnecessariamente.

O gerenciamento de:

commit
rollback
close

deve seguir o padrão definido pela infraestrutura do banco.

5. Uma Session por Request

Como regra geral, uma requisição HTTP deve utilizar a session correspondente ao seu contexto de execução.

Evitar criar várias sessions independentes para operações que deveriam fazer parte da mesma transação.

Exemplo a evitar:

Endpoint
 ├── Session A
 ├── Session B
 └── Session C

quando todas as operações fazem parte de uma única unidade de negócio.

6. Current User

Uma dependency deve resolver o usuário autenticado.

Conceito:

async def get_current_user(
    token: str = Depends(oauth2_scheme),
):
    ...

Fluxo:

Authorization Header
       ↓
JWT
       ↓
Validate Token
       ↓
User ID
       ↓
Load User
       ↓
Current User
7. Usuário ativo

A dependency de usuário autenticado deve verificar se a conta ainda está ativa quando essa verificação fizer parte do contrato de autenticação.

Exemplo:

User
 ↓
active?
 ↓
yes → continue
no  → 401

Não assumir que um token válido significa que a conta continua habilitada.

8. Usuário excluído

Quando o modelo utilizar deleted_at, a dependency deve considerar o status da conta.

Conceito:

deleted_at IS NULL
    ↓
usuário ativo para autenticação

deleted_at IS NOT NULL
    ↓
usuário não deve autenticar

A implementação exata deve seguir o comportamento definido em authentication.md.

9. Tenant Context

Uma dependency deve ser capaz de resolver o contexto do tenant do usuário autenticado.

Fluxo:

JWT
 ↓
Current User
 ↓
Tenant
 ↓
Current Tenant

Exemplo conceitual:

async def get_current_tenant(
    current_user: User = Depends(get_current_user),
):
    ...
10. Tenant Context não vem do frontend

Não utilizar um valor arbitrário recebido pelo cliente como fonte principal do tenant.

Evitar:

X-Tenant-ID
tenant_id no body
tenant_id na query

como mecanismo automático de autorização.

O tenant deve ser derivado de uma relação confiável.

11. Current Tenant

Uma dependency pode retornar uma estrutura de contexto.

Exemplo conceitual:

@dataclass
class TenantContext:
    tenant_id: UUID
    user_id: UUID

Isso pode ser útil quando a operação precisar de:

tenant_id
user_id

simultaneamente.

Não criar um objeto de contexto complexo sem necessidade.

12. Authorization Dependency

Dependencies também podem realizar verificações de autorização.

Conceito:

require_permission("customer.read")

Fluxo:

Request
 ↓
Current User
 ↓
Current Tenant
 ↓
Permission Check
 ↓
Endpoint
13. Factory de Permission

Uma função pode gerar uma dependency específica.

Exemplo conceitual:

def require_permission(permission: str):
    async def dependency(
        current_user: User = Depends(get_current_user),
    ):
        ...
    
    return dependency

Isso permite:

Depends(require_permission("customer.read"))

A implementação final deve manter essa lógica simples e testável.

14. Permission Check

A dependency deve verificar se o usuário possui a permission necessária.

Exemplo:

customer.read

Caso não possua:

403 Forbidden

A dependency não deve alterar a regra de negócio do recurso.

15. Authorization ≠ Business Rule

Dependency de autorização responde:

O usuário possui permissão?

Service responde:

A operação pode acontecer considerando o estado do domínio?

Exemplo:

customer.delete
+
permission válida

não significa que:

cliente pode ser excluído

O service continua responsável pelas regras do domínio.

16. Dependency Order

Quando uma rota precisar de múltiplas dependencies, manter uma ordem lógica.

Conceito:

Request
 ↓
Database
 ↓
Current User
 ↓
Current Tenant
 ↓
Permission
 ↓
Service

Nem toda rota precisará utilizar todas essas etapas.

17. Reutilização

Uma dependency deve ser criada quando houver responsabilidade recorrente.

Exemplos apropriados:

get_db
get_current_user
get_current_tenant
require_permission
get_request_context

Evitar criar uma dependency exclusiva para uma única linha de código sem necessidade.

18. Não colocar regra de negócio em Dependency

Evitar:

async def get_current_customer(...):
    if customer.status == "...":
        ...

quando essa decisão fizer parte da regra do domínio.

A dependency deve resolver contexto ou infraestrutura.

O service decide o comportamento do negócio.

19. Database Dependency

A dependency do banco não deve:

consultar clientes
criar pedidos
validar estoque

Sua responsabilidade é fornecer a infraestrutura necessária para acessar o banco.

20. Current User Dependency

A dependency de usuário pode:

validar token
extrair identidade
buscar usuário
verificar status

Não deve executar operações de negócio.

21. Current Tenant Dependency

A dependency de tenant pode:

obter tenant_id
validar associação do usuário
carregar tenant
verificar status do tenant

quando essas verificações fizerem parte do contrato de identidade e contexto.

Não deve implementar regras específicas de customers, products ou orders.

22. Permission Dependency

A dependency de permission deve:

identificar permission necessária
obter contexto autorizado
verificar permission

Não deve implementar:

cancelamento de pedido
cálculo de estoque
cálculo financeiro

Essas regras pertencem ao service.

23. Request Context

O backend poderá utilizar uma dependency para obter informações da requisição.

Exemplos:

request_id
client information
correlation context

Esse contexto pode ser utilizado para:

logs
auditoria
rastreamento

Não incluir informações desnecessárias.

24. Request ID

Uma dependency ou middleware pode garantir que exista um request_id.

Fluxo:

HTTP Request
 ↓
request_id
 ↓
Dependencies
 ↓
Service
 ↓
Logs

O mecanismo definitivo pode ser implementado através de middleware quando isso for mais apropriado que uma dependency.

A escolha deve evitar duplicação.

25. Header Values

Headers recebidos do cliente não devem ser tratados automaticamente como informações confiáveis.

Exemplo:

X-User-ID
X-Tenant-ID
X-Role
X-Permission

não devem conceder privilégios simplesmente por estarem presentes.

26. Optional Authentication

Algumas rotas podem permitir acesso autenticado e não autenticado.

Nesse caso, criar uma dependency explicitamente opcional.

Conceito:

get_optional_current_user

Essa dependency deve ser utilizada somente quando o endpoint realmente possuir comportamento público e autenticado diferente.

Não transformar endpoints protegidos em opcionais por conveniência.

27. Public Endpoints

Endpoints públicos devem ser explicitamente definidos.

Exemplo:

GET /health
POST /auth/login

Uma rota sem dependency de autenticação não deve ser considerada pública por acidente.

28. Dependencies em Routers

Dependencies podem ser aplicadas:

endpoint
router
application

Exemplo:

router = APIRouter(
    prefix="/customers",
    dependencies=[Depends(get_current_user)],
)

Isso pode ser apropriado para um conjunto inteiro de endpoints protegidos.

29. Authorization por Router

Quando todos os endpoints de um router exigirem uma permission comum, pode ser possível definir a proteção em nível de router.

Entretanto, quando cada operação possuir permission diferente:

GET → customer.read
POST → customer.create
PATCH → customer.update
DELETE → customer.delete

o check deve ser definido de forma específica.

30. Evitar duplicação

Não fazer simultaneamente:

Router
 ├── autentica usuário
 └── endpoint autentica usuário novamente

quando a mesma dependency já está sendo herdada.

Centralizar a responsabilidade.

31. Dependency Injection

Utilizar o mecanismo nativo do FastAPI.

Evitar adicionar um framework externo de dependency injection sem necessidade.

O sistema já possui:

Depends
Annotated

e mecanismos suficientes para a arquitetura inicial.

32. Annotated

Quando melhorar a legibilidade, considerar o uso de Annotated.

Exemplo conceitual:

CurrentUser = Annotated[
    User,
    Depends(get_current_user),
]

Isso pode reduzir repetição em endpoints.

A adoção deve permanecer consistente.

33. Type Safety

Dependencies devem possuir tipos claros.

Exemplo:

async def get_current_user(...) -> User:
    ...

Evitar:

async def dependency(...) -> Any:
    ...

quando existir um tipo conhecido.

34. Testes

Cada dependency importante deve possuir testes.

Cobrir:

get_db
get_current_user
get_current_tenant
require_permission

quando forem implementadas.

35. Testes de Authentication

Testar:

token válido
token inválido
token expirado
token ausente
usuário inexistente
usuário inativo
36. Testes de Tenant

Testar:

User A → Tenant A

permitido.

E:

User A → Tenant B

bloqueado.

37. Testes de Authorization

Testar:

permission presente
→ permitido
permission ausente
→ 403

E:

usuário não autenticado
→ 401
38. Overrides de Dependency

FastAPI permite substituir dependencies durante testes.

Isso pode ser útil para:

mock user
mock tenant
test database

Exemplo conceitual:

app.dependency_overrides[get_current_user] = override_current_user

Os overrides devem permanecer limitados ao ambiente de teste.

39. Test Database Dependency

A dependency do banco pode ser substituída por uma session de teste.

Isso permite testar endpoints sem utilizar o banco de desenvolvimento.

A configuração deve garantir isolamento entre testes.

40. Transaction Scope

A dependency do banco e o padrão transacional do projeto devem trabalhar juntos.

Evitar definir um commit automático genérico se determinadas operações precisarem controlar a transação de maneira mais ampla.

A estratégia deve ser definida centralmente.

41. Exceptions

Dependencies devem produzir exceptions compatíveis com a camada responsável pelo erro.

Exemplos:

token inválido
→ AuthenticationError / 401

sem permission
→ AuthorizationError / 403

Não retornar respostas HTTP inconsistentes diretamente de diferentes dependencies.

42. Logging

Dependencies não devem gerar logs excessivos.

Registrar eventos relevantes, como:

authentication failure
authorization failure
context resolution failure

Não registrar:

password
JWT completo
secret
access token
refresh token
43. Performance

Dependencies executadas em todas as requisições devem ser eficientes.

Exemplos:

get_current_user
get_current_tenant

podem ser chamadas frequentemente.

Quando necessário, avaliar:

query optimization
caching
relationship loading

Sem comprometer segurança.

44. Cache

Cache de identidade ou autorização deve considerar:

user_id
tenant_id

e possuir invalidação adequada.

Não utilizar cache global que possa misturar contextos de diferentes tenants.

45. Background Jobs

Workers não devem depender automaticamente de FastAPI Depends.

Um worker não possui o mesmo ciclo de vida de uma requisição HTTP.

Em background jobs:

job
 ↓
context
 ↓
service

As dependências necessárias devem ser construídas de acordo com o ambiente do worker.

Não transportar mecanicamente dependencies HTTP para workers.

46. Services

Services não devem depender diretamente de Depends.

Exemplo a evitar:

class OrderService:

    def __init__(
        self,
        user=Depends(get_current_user),
    ):
        ...

Dependencies pertencem à composição da aplicação.

O service recebe suas dependências explicitamente.

47. Repositories

Repositories também não devem utilizar Depends.

Evitar:

class CustomerRepository:

    def __init__(
        self,
        db=Depends(get_db),
    ):
        ...

Preferir:

CustomerRepository(session)

A composição ocorre na camada da aplicação.

48. Dependency Composition

A composição pode seguir:

FastAPI Dependency
        ↓
Service
        ↓
Repository
        ↓
Database Session

Exemplo conceitual:

get_db
   ↓
get_customer_service
   ↓
CustomerService
   ↓
CustomerRepository

Isso mantém a arquitetura explícita.

49. Service Factory

Quando necessário, uma dependency pode construir um service.

Exemplo conceitual:

async def get_customer_service(
    db: AsyncSession = Depends(get_db),
) -> CustomerService:
    repository = CustomerRepository(db)
    return CustomerService(repository)

Isso é útil para centralizar a composição.

Não criar factories para todos os objetos automaticamente.

50. Circular Dependencies

Evitar:

get_user
 ↓
get_permission
 ↓
get_user

ou dependências que formem ciclos.

Quando isso acontecer, revisar a responsabilidade de cada componente.

51. Granularidade

Dependencies devem possuir tamanho e responsabilidade adequados.

Evitar uma dependency única que faça:

authentication
authorization
customer lookup
inventory validation
audit

Tudo ao mesmo tempo.

Separar responsabilidades.

52. Segurança por padrão

As dependencies de autenticação e autorização devem seguir:

não autenticado
→ negar

tenant inválido
→ negar

permission ausente
→ negar

Não utilizar comportamento permissivo como fallback.

53. Ordem de implementação

Ao implementar dependencies:

1. Database session
2. Authentication
3. Current user
4. Tenant context
5. Authorization
6. Request context
7. Service factories quando necessárias
8. Test overrides
9. Tests

A ordem pode ser ajustada conforme as dependências reais da aplicação.

54. Checklist

Antes de finalizar uma dependency:

 Possui responsabilidade clara;
 Não contém regra de negócio desnecessária;
 Não acessa diretamente o frontend;
 Não confia em headers arbitrários;
 Authentication está separada de Authorization;
 Tenant context é confiável;
 Session possui lifecycle correto;
 Services não dependem diretamente de Depends;
 Repositories não dependem diretamente de Depends;
 Exceptions são consistentes;
 Não existem dependências circulares;
 Testes existem;
 Dependency overrides são utilizados somente nos testes;
 Logs não expõem secrets;
 Performance foi considerada;
 Não foi criada complexidade desnecessária.
55. Regra principal

FastAPI Dependencies devem cuidar de contexto e infraestrutura.

A separação deve permanecer:

Dependency
→ resolve contexto

Router
→ recebe request

Schema
→ valida contrato

Service
→ executa regra de negócio

Repository
→ acessa dados

Dependencies existem para conectar essas partes de forma organizada, e não para substituir qualquer uma delas.