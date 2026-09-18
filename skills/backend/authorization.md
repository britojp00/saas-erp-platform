# Backend Authorization

## Objetivo

Definir como o SaaS ERP Platform controla o acesso às funcionalidades e aos dados depois que o usuário já foi autenticado.

Este documento complementa:

```text
skills/02-architecture.md
skills/backend/README.md
skills/backend/architecture.md
skills/backend/api.md
skills/backend/authentication.md
skills/database/multi-tenancy.md

O sistema deve separar claramente:

Authentication
    ↓
Quem é o usuário?

Authorization
    ↓
O que esse usuário pode fazer?

Tenant Isolation
    ↓
Quais dados esse usuário pode acessar?
1. Princípios

A autorização deve seguir o princípio de menor privilégio.

Um usuário deve possuir somente as permissões necessárias para suas atividades.

O acesso deve ser:

Explícito
Verificável
Consistente
Multi-tenant
Testável

Nunca considerar que um usuário autenticado possui acesso automático a todos os recursos.

2. Authentication x Authorization

Autenticação:

JWT válido
    ↓
usuário identificado

Autorização:

usuário identificado
    ↓
role / permission
    ↓
operação permitida?

Exemplo:

JWT válido
+
customer.read
→ acesso permitido

Mas:

JWT válido
+
sem customer.delete
→ 403 Forbidden
3. Modelo RBAC

O sistema utilizará RBAC:

User
  ↓
Role
  ↓
Permission

Conceito:

Usuário
   ↓
uma ou mais Roles
   ↓
uma ou mais Permissions

Isso permite separar a identidade do usuário das regras de acesso.

4. User

O usuário representa a identidade autenticada.

Exemplo conceitual:

User
├── id
├── tenant_id
├── name
├── email
├── password_hash
└── active

O usuário não deve possuir necessariamente uma lista de permissões armazenada diretamente em uma coluna.

O acesso deve ser modelado através das relações apropriadas.

5. Role

Uma Role representa um conjunto de permissões.

Exemplos:

Administrator
Manager
Seller
StockOperator
Viewer

Uma role não deve representar somente uma tela do frontend.

Ela representa um conjunto coerente de capacidades do sistema.

6. Permission

Uma Permission representa uma ação específica.

Formato recomendado:

resource.action

Exemplos:

customer.read
customer.create
customer.update
customer.delete

Produtos:

product.read
product.create
product.update
product.delete

Pedidos:

order.read
order.create
order.update
order.cancel
7. Nomenclatura

As permissões devem possuir nomes:

consistentes;
previsíveis;
curtos;
relacionados ao domínio.

Preferir:

customer.read

em vez de:

can_manage_customer_screen

Evitar nomes vinculados exclusivamente à interface gráfica.

8. Relações

O modelo conceitual poderá ser:

users
  ↓
user_roles
  ↓
roles
  ↓
role_permissions
  ↓
permissions

Exemplo:

User João
    ↓
Role Seller
    ↓
customer.read
customer.create
order.read
order.create

O usuário recebe as permissões através das roles.

9. Many-to-many

Relacionamentos entre:

User ↔ Role
Role ↔ Permission

devem utilizar tabelas de associação.

Exemplo:

user_roles
role_permissions

Não armazenar IDs de roles ou permissions dentro de uma string ou JSON quando a relação for estruturalmente relacional.

10. Escopo do Tenant

Roles e permissions devem respeitar a estratégia multi-tenant do sistema.

Na primeira versão, os usuários pertencem a um tenant.

Conceito:

Tenant A
├── User A
├── Role A
└── Permission set A

Tenant B
├── User B
├── Role B
└── Permission set B

Um usuário do Tenant A não deve receber autorização baseada em estruturas pertencentes ao Tenant B.

11. Tenant Isolation

Autorização não substitui isolamento de dados.

Mesmo que um usuário possua:

customer.read

isso significa:

pode ler customers autorizados

e não:

pode ler qualquer customer do banco

O acesso deve respeitar:

Permission
+
Tenant Context
+
Resource Ownership

quando aplicável.

12. Authorization Context

Durante uma requisição autenticada, o backend poderá possuir um contexto semelhante a:

user_id
tenant_id
roles
permissions

Esse contexto pode ser utilizado para decisões de autorização.

O contexto deve ser derivado de fontes confiáveis.

Não confiar em:

user_id
tenant_id
role
permission

recebidos diretamente pelo frontend.

13. Permission Check

A aplicação deve possuir uma forma consistente de verificar permissões.

Conceito:

require_permission("customer.read")

ou através de uma dependency equivalente do FastAPI.

A implementação definitiva deve seguir o padrão adotado no projeto.

Evitar repetir manualmente a mesma lógica em dezenas de endpoints.

14. Dependency de autorização

FastAPI dependencies podem ser utilizadas para proteger endpoints.

Conceito:

@router.get(
    "/customers",
    dependencies=[Depends(require_permission("customer.read"))],
)
async def list_customers():
    ...

A implementação real deve respeitar a estrutura e o padrão de dependencies do projeto.

15. Router e autorização

O router pode declarar qual permissão o endpoint exige.

Exemplo conceitual:

GET /customers
→ customer.read

POST /customers
→ customer.create

PATCH /customers/{id}
→ customer.update

DELETE /customers/{id}
→ customer.delete

O router não deve implementar manualmente toda a lógica de RBAC.

16. Service e autorização

O service continua responsável pelas regras de negócio.

Uma permissão não substitui uma regra de negócio.

Exemplo:

order.cancel

permite que o usuário tente cancelar um pedido.

Mas o service ainda deve verificar se o pedido pode ser cancelado naquele estado.

Portanto:

Permission
+
Business Rule
=
Operation allowed
17. Exemplo de diferença

Usuário possui:

order.cancel

Isso não significa automaticamente:

qualquer pedido pode ser cancelado

O service pode verificar:

pedido existe?
pedido pertence ao tenant?
pedido está em estado cancelável?

Somente depois realizar a operação.

18. HTTP 403

Quando:

usuário autenticado
+
sem permissão necessária

retornar:

403 Forbidden

Não utilizar 401 Unauthorized nesse caso.

401 representa falha de autenticação.

403 representa ausência de autorização suficiente.

19. HTTP 401

Utilizar:

401 Unauthorized

quando não houver autenticação válida.

Exemplos:

token ausente
token expirado
token inválido
assinatura inválida
20. Default Deny

O sistema deve adotar uma abordagem de negação por padrão.

Conceito:

sem autenticação
→ negar

autenticado
+
sem permission
→ negar

autenticado
+
permission correta
→ avaliar regra de negócio

Não criar endpoints protegidos com acesso aberto por acidente.

21. Public Endpoints

Endpoints públicos devem ser explicitamente definidos.

Exemplos possíveis:

GET /health
POST /auth/login

Apenas endpoints realmente públicos devem permanecer sem autenticação.

A ausência de um check não deve ser interpretada automaticamente como decisão de negócio.

22. Hierarquia de decisão

Para uma operação protegida, considerar:

1. Request válida?
        ↓
2. Usuário autenticado?
        ↓
3. Usuário ativo?
        ↓
4. Tenant válido?
        ↓
5. Possui permission?
        ↓
6. Recurso pertence ao tenant?
        ↓
7. Regra de negócio permite?
        ↓
8. Executar operação

Nem toda operação utilizará todas as etapas, mas a ordem conceitual deve permanecer clara.

23. Roles administrativas

Uma role administrativa poderá possuir várias permissões.

Exemplo:

Administrator
├── customer.read
├── customer.create
├── customer.update
├── customer.delete
├── product.read
├── product.create
├── product.update
├── product.delete
└── order.*

Mesmo uma role administrativa deve continuar respeitando o tenant.

Administrador do Tenant A não deve administrar dados do Tenant B.

24. Superadmin

Um eventual usuário global do sistema pode possuir responsabilidades fora do tenant.

Entretanto, isso deve ser explicitamente modelado.

Não criar um "superadmin" simplesmente como uma role com todas as permissões de tenant.

Caso exista necessidade de operações globais:

Global Administration

deve ser distinguida de:

Tenant Administration
25. Permission Granularity

As permissions devem possuir granularidade suficiente para controlar as ações importantes.

Evitar uma única permissão:

customer.manage

quando o sistema precisar diferenciar:

customer.read
customer.create
customer.update
customer.delete

Por outro lado, não criar permissões excessivamente específicas sem uma necessidade real.

26. Frontend

O frontend poderá utilizar permissões para:

mostrar / esconder ações
desabilitar funcionalidades
organizar menus

Mas isso não representa segurança.

Exemplo:

Botão "Excluir"
→ escondido no frontend

não impede:

DELETE /customers/{id}

O backend sempre deve validar a autorização.

27. Segurança da API

O backend não deve aceitar:

{
  "role": "Administrator"
}

como forma de conceder acesso.

Também não confiar em:

{
  "permissions": [
    "customer.delete"
  ]
}

enviado pelo frontend.

Essas informações devem ser determinadas pelo backend.

28. Alterações de Roles

Alterações em roles e permissions podem possuir alto impacto.

Operações como:

criar role
alterar role
adicionar permission
remover permission

devem possuir autorização adequada.

Essas ações também podem exigir auditoria.

29. Alterações de Permissions

Permissões devem ser modificadas através de operações controladas.

Não alterar diretamente estruturas internas do banco como fluxo normal da aplicação.

Quando a aplicação possuir uma interface administrativa, ela deverá utilizar endpoints protegidos.

30. Auditoria

Alterações relacionadas a autorização devem ser auditáveis quando relevantes.

Exemplos:

role.created
role.updated
permission.added
permission.removed
user.role_changed

Registrar informações como:

tenant_id
user_id
action
target
timestamp

Nunca registrar secrets ou credenciais.

31. Cache

Quando permissões forem armazenadas em cache:

tenant_id
+
user_id

devem fazer parte do escopo quando necessário.

Não utilizar uma chave genérica como:

user_permissions:{user_id}

se o mesmo usuário puder posteriormente existir em múltiplos contextos.

Além disso, alterações de roles devem invalidar o cache correspondente.

32. JWT e Permissions

Não considerar obrigatório armazenar todas as permissions dentro do JWT.

Quando permissions estiverem no token:

role/permission alterada
    ↓
token antigo ainda pode conter dados antigos

Por isso, a estratégia deve considerar:

expiração do token
revogação
validação server-side

quando alterações imediatas forem necessárias.

A decisão final deve ser definida junto da implementação de autenticação.

33. Resource Ownership

Alguns recursos podem exigir mais do que permission.

Exemplo:

document.read

pode permitir leitura geral dentro do tenant.

Enquanto outro recurso pode exigir:

document.read
+
document.user_id == current_user.id

quando houver uma regra de propriedade.

A autorização pode combinar:

Permission
+
Tenant
+
Ownership
34. Dados sensíveis

Alguns recursos podem exigir permissions específicas mesmo dentro do mesmo tenant.

Exemplos:

financial.read
financial.update
audit.read
user.manage
permission.manage

Não assumir que uma permission genérica concede acesso a informações sensíveis.

35. Authorization no Service

Quando a regra de acesso depender do estado ou conteúdo do recurso, a decisão deve ocorrer em conjunto com a regra de negócio.

Exemplo:

customer.update
+
cliente pertence ao tenant
+
cliente está ativo
→ operação permitida

O service deve impedir situações que uma simples permission não consegue representar.

36. Background Jobs

Workers também precisam respeitar autorização e contexto de tenant.

Entretanto, o worker não possui um usuário HTTP tradicional.

A tarefa deve carregar somente o contexto necessário para executar a operação.

Exemplo:

job
├── tenant_id
├── actor_user_id
├── entity_id
└── operation

Quando uma operação exigir rastreabilidade, registrar o usuário que originou o job.

37. Integrações externas

Integrações devem utilizar credenciais próprias e não reutilizar permissões de usuários finais sem necessidade.

Uma chamada automática do Integration Hub pode representar:

system integration

e não necessariamente:

human user session

As responsabilidades devem ser mantidas separadas.

38. Falha segura

Em caso de erro ao determinar autorização:

não permitir acesso

É preferível falhar fechando o acesso do que executar uma operação sem confirmação de autorização.

39. Testes de RBAC

Testar pelo menos:

usuário sem autenticação
usuário autenticado sem permission
usuário com permission
usuário com múltiplas roles
usuário com role removida
40. Testes por recurso

Exemplo:

customer.read
→ GET /customers
customer.create
→ POST /customers
customer.update
→ PATCH /customers/{id}
customer.delete
→ DELETE /customers/{id}

Verificar que permissions diferentes realmente produzem comportamentos diferentes.

41. Testes Multi-tenant + RBAC

O cenário deve ser testado em conjunto.

Exemplo:

Tenant A
User A
customer.read

User A deve conseguir:

ler Customer A

mas não:

ler Customer B

Mesmo possuindo:

customer.read

A permission não pode ultrapassar o isolamento do tenant.

42. Testes de privilege escalation

Testar cenários como:

usuário comum
→ tenta adicionar Administrator a si mesmo

ou:

usuário comum
→ tenta enviar role de admin no payload

ou:

usuário de Tenant A
→ tenta atribuir role de Tenant B

Essas operações devem ser bloqueadas.

43. Testes de acesso direto

Nunca assumir que esconder uma ação no frontend seja suficiente.

Testar diretamente a API:

GET
POST
PATCH
DELETE

sem a permission necessária.

O backend deve bloquear a operação.

44. Testes de regressão

Toda alteração importante em RBAC deve manter testes para cenários anteriores.

Alterar uma permission não deve acidentalmente liberar outro recurso.

Testes devem proteger as fronteiras de autorização.

45. Performance

A verificação de autorização deve ser eficiente, mas sem sacrificar segurança.

Quando necessário, utilizar:

cache
eager loading
queries otimizadas

Somente depois de identificar uma necessidade real.

Não duplicar permissions no JWT, banco e Redis sem um motivo claro.

46. Complexidade

A implementação inicial deve permanecer simples.

Começar com:

User
↓
Role
↓
Permission

Adicionar mecanismos mais avançados somente quando o domínio exigir:

ABAC
policy engine
hierarquias complexas
resource-level policies

Não implementar essas abstrações prematuramente.

47. Ordem de implementação

Ao implementar autorização:

1. Permission model
2. Role model
3. User ↔ Role
4. Role ↔ Permission
5. Seed inicial de permissions
6. Authorization dependency
7. Permission checks
8. Tenant isolation
9. Resource ownership quando necessário
10. Audit
11. Tests
12. Documentation

A ordem pode ser ajustada conforme as dependências reais.

48. Checklist

Antes de finalizar uma alteração relacionada à autorização:

 Authentication está separada de Authorization;
 Permission possui nome consistente;
 Roles agrupam permissions;
 Relações many-to-many utilizam tabelas próprias;
 Tenant isolation foi considerado;
 O frontend não é tratado como mecanismo de segurança;
 401 e 403 estão diferenciados;
 Default deny foi respeitado;
 Regras de negócio continuam no service;
 Ownership foi considerado quando necessário;
 Alterações críticas podem ser auditadas;
 Cache respeita tenant e usuário;
 Background jobs preservam contexto quando necessário;
 Testes de RBAC existem;
 Testes cross-tenant existem;
 Testes de privilege escalation existem.
49. Regra principal

Autorização deve responder:

Quem é o usuário?
        ↓
Qual é o tenant?
        ↓
Qual permission ele possui?
        ↓
Qual recurso está sendo acessado?
        ↓
A regra de negócio permite?

Somente depois dessas verificações a operação deve ser executada.

A segurança do sistema deve permanecer no backend, independentemente do comportamento da interface do frontend.