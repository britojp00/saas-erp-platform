# Backend Authentication

## Objetivo

Definir os padrões de autenticação, identidade, senhas, JWT e sessão lógica do usuário no backend do SaaS ERP Platform.

Este documento complementa:

```text
skills/02-architecture.md
skills/backend/README.md
skills/backend/architecture.md
skills/backend/api.md
skills/security/README.md

A autenticação deve garantir que o backend consiga responder de forma confiável:

Quem é o usuário?
Qual identidade está autenticada?
A qual tenant essa identidade pertence?
O token ainda é válido?

Autenticação não substitui autorização.

1. Conceitos

O sistema deve separar claramente:

Authentication
    ↓
Identity
    ↓
Tenant Context
    ↓
Authorization
Authentication

Verifica a identidade apresentada pelo usuário.

Identity

Representa o usuário autenticado no sistema.

Tenant Context

Determina o contexto multi-tenant em que a operação será executada.

Authorization

Determina se o usuário possui permissão para realizar uma determinada operação.

2. Usuário

O usuário do sistema será representado pela entidade:

User

O usuário poderá possuir informações como:

id
tenant_id
name
email
password_hash
active
created_at
updated_at
deleted_at

A estrutura definitiva deve seguir as regras de modelagem do projeto.

3. Senhas

Senhas nunca devem ser armazenadas em texto puro.

Nunca armazenar:

password
senha
plain_password

como valor persistente do usuário.

O banco deve armazenar somente o hash da senha.

Exemplo conceitual:

password
    ↓
password hashing
    ↓
password_hash
    ↓
database
4. Password Hashing

O projeto utiliza pwdlib para gerenciamento de senhas.

O algoritmo utilizado deve seguir o padrão recomendado pela biblioteca e pela configuração adotada pelo projeto.

A implementação deve encapsular o processo de:

hash
verify

Evitar implementar manualmente algoritmos criptográficos.

5. Verificação de senha

Durante o login:

Email
+
Password
    ↓
Buscar usuário
    ↓
Verificar password_hash
    ↓
Identidade válida

Não comparar senha em texto puro.

Exemplo conceitual:

password_hasher.verify(password, user.password_hash)
6. Usuário inexistente

Quando o usuário informado não existir, o comportamento externo deve ser consistente com uma tentativa de autenticação inválida.

Evitar respostas que revelem excessivamente:

"esse e-mail existe"
"esse usuário não existe"

quando isso permitir enumeração de contas.

7. Usuário inativo

Usuários desativados não devem conseguir autenticar.

Exemplo:

active = false
    ↓
login bloqueado

A regra deve ocorrer antes da emissão de um token válido.

8. Usuário excluído logicamente

Usuários que utilizarem deleted_at devem ser considerados inativos para autenticação quando:

deleted_at IS NOT NULL

Uma conta logicamente excluída não deve receber um novo token de autenticação.

9. Login

O endpoint de login deve receber as credenciais necessárias.

Fluxo:

POST /auth/login
        ↓
Validar request
        ↓
Localizar usuário
        ↓
Verificar senha
        ↓
Verificar status
        ↓
Obter tenant
        ↓
Emitir token

O login não deve conter regras extensas diretamente no router.

10. JWT

O backend utilizará JWT para autenticação de requisições.

Conceito:

Login
  ↓
JWT
  ↓
Authorization Header
  ↓
Authenticated Request

Formato esperado:

Authorization: Bearer <token>
11. JWT Secret

A chave utilizada para assinar JWT deve ser fornecida por variável de ambiente.

Exemplo:

JWT_SECRET_KEY=change-me

Nunca colocar a chave diretamente no código.

Nunca versionar uma chave real.

12. JWT Algorithm

O algoritmo utilizado pelo JWT deve ser configurado explicitamente.

Exemplo:

JWT_ALGORITHM=HS256

A aplicação não deve aceitar algoritmos arbitrários provenientes do token.

O algoritmo esperado deve ser definido pelo backend.

13. Expiração

Tokens de acesso devem possuir expiração.

Exemplo de configuração:

JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

A duração definitiva deve ser determinada pela configuração da aplicação.

Não criar tokens sem expiração.

14. Claims

O JWT deve carregar somente as informações necessárias para identificar e processar a autenticação.

Exemplos possíveis:

sub
tenant_id
iat
exp

Claims adicionais somente devem ser adicionadas quando houver necessidade real.

Evitar colocar no token grandes quantidades de dados de negócio.

15. Subject

O sub deve representar de forma consistente a identidade autenticada.

Exemplo:

sub = user_id

O backend deve possuir uma convenção única para esse campo.

Não utilizar significados diferentes de sub em diferentes endpoints.

16. Tenant no JWT

O JWT poderá carregar informações necessárias para identificar o contexto do tenant, conforme a estratégia de autenticação implementada.

Entretanto:

JWT
≠
autorização automática

O backend deve validar se a identidade autenticada possui acesso válido ao tenant.

Não confiar cegamente em um tenant_id fornecido no payload.

17. Token validation

Cada endpoint protegido deve validar:

token presente
token bem formado
assinatura válida
algoritmo esperado
token não expirado
identidade válida

Depois disso, a aplicação deve obter o contexto autenticado.

18. Token inválido

Tokens inválidos devem resultar em:

401 Unauthorized

Exemplos:

token ausente
token malformado
assinatura inválida
token expirado
token incompatível

Não retornar detalhes criptográficos desnecessários ao cliente.

19. Authentication Dependency

A validação da identidade deve ser centralizada.

Conceito:

async def get_current_user(...):
    ...

Routers protegidos podem depender dessa resolução.

Exemplo conceitual:

@router.get("/customers")
async def list_customers(
    current_user: User = Depends(get_current_user),
):
    ...

A implementação definitiva deve seguir a organização de dependencies do backend.

20. Current User

Depois da validação do token, a aplicação deve obter a identidade do usuário.

Fluxo:

JWT
 ↓
Decode
 ↓
user_id
 ↓
Database
 ↓
User

Sempre que necessário, verificar se o usuário ainda existe e está ativo.

Não assumir que um token válido significa que o usuário continua habilitado.

21. Tenant Context

Depois de identificar o usuário:

User
 ↓
Tenant
 ↓
Tenant Context

O contexto do tenant deve ser resolvido de forma confiável.

Esse contexto será utilizado posteriormente por:

repositories
services
authorization
logs
audit
background jobs
22. Relação User → Tenant

Na primeira versão do sistema, a estrutura pode considerar um usuário associado a um tenant.

Conceito:

Tenant
  └── Users

Caso o domínio evolua para usuários pertencentes a múltiplos tenants, essa estrutura deverá ser revisada para utilizar uma relação própria de associação.

Não implementar multi-tenant membership complexo antes de existir necessidade real.

23. Conta pertencente a tenant

Um usuário não deve conseguir autenticar ou operar dados fora do contexto permitido pela sua associação.

Exemplo:

Tenant A
 └── User A

Tenant B
 └── User B

User A:

→ Tenant A
→ dados de Tenant A

Não deve possuir acesso aos dados de Tenant B.

24. Autenticação ≠ Autorização

Possuir um JWT válido significa:

usuário autenticado

Não significa:

pode executar qualquer operação

Exemplo:

JWT válido
+
customer.read
→ GET /customers permitido

Mas:

JWT válido
+
sem customer.delete
→ DELETE /customers/{id} bloqueado
25. Roles e Permissions

O sistema utilizará posteriormente:

User
 ↓
Role
 ↓
Permission

A autenticação identifica o usuário.

A autorização avalia as permissões desse usuário.

Não colocar toda a lógica de RBAC dentro da geração do JWT.

26. Permissões no JWT

Permissões podem eventualmente ser incluídas no token, mas isso deve ser avaliado conforme o comportamento de revogação e atualização de permissões.

Não assumir que um token antigo passa automaticamente a refletir alterações de RBAC.

Quando a aplicação exigir mudanças imediatas de permissão, considerar validação adicional no servidor.

27. Logout

JWTs de acesso são stateless por natureza.

O logout deve ser tratado conforme a estratégia de sessão adotada.

Possibilidades futuras incluem:

token curto
refresh token
token revocation
Redis denylist

Não implementar uma estratégia de revogação complexa sem requisito real.

28. Refresh Token

Refresh tokens poderão ser adicionados posteriormente.

Quando forem implementados, devem possuir:

expiração
rotação quando apropriado
armazenamento seguro
revogação
rastreabilidade

Não tratar refresh token simplesmente como um JWT de acesso com validade maior sem considerar os riscos do ciclo de vida.

29. Armazenamento no cliente

O backend é responsável por definir o contrato de autenticação.

A estratégia de armazenamento do token no frontend deve considerar o risco de exposição a:

XSS
roubo de sessão
acesso indevido

A decisão final deve ser documentada na skill de frontend e segurança.

30. Brute Force

Tentativas repetidas de login devem ser consideradas uma preocupação de segurança.

Futuramente poderão ser implementados controles utilizando Redis, como:

rate limiting
login attempt tracking
temporary lock

Não bloquear contas permanentemente com base somente em falhas de senha sem uma estratégia adequada.

31. Rate Limiting de Login

O endpoint:

POST /auth/login

poderá possuir rate limiting específico.

Esse controle deve considerar adequadamente:

IP
identidade informada
tenant

conforme a estratégia escolhida.

O mecanismo não deve permitir que um atacante utilize tentativas ilimitadas.

32. Enumeração de usuários

Mensagens de login devem evitar diferenças desnecessárias entre:

usuário inexistente
senha incorreta

O sistema deve possuir uma resposta externa consistente para falha de credenciais.

Detalhes internos podem ser utilizados nos logs sem serem expostos ao usuário.

33. Logs de autenticação

Eventos relevantes podem ser registrados:

login_success
login_failed
user_disabled
token_invalid
logout

Quando apropriado, registrar:

request_id
user_id
tenant_id
event
timestamp

Nunca registrar:

password
password_hash
JWT completo
secret
refresh token
34. Auditoria de autenticação

Eventos importantes de segurança podem também ser registrados na auditoria.

Exemplos:

login
logout
alteração de senha
alteração de permissões
desativação de usuário

Logs técnicos e audit logs permanecem responsabilidades distintas.

35. Alteração de senha

A alteração de senha deve:

verificar autorização
validar senha atual quando aplicável
validar nova senha
gerar novo hash
persistir hash

Nunca armazenar a senha anterior ou nova em texto puro.

36. Política de senha

A aplicação deverá definir regras mínimas de senha.

Exemplos possíveis:

comprimento mínimo

Outras regras somente devem ser adicionadas quando houver justificativa de segurança ou requisito do sistema.

Evitar políticas extremamente complexas que não forneçam benefício proporcional.

37. Recuperação de senha

A recuperação de senha poderá ser implementada futuramente.

A implementação deverá utilizar um mecanismo temporário e seguro.

Não utilizar o próprio JWT de acesso como mecanismo de recuperação de senha.

Tokens de recuperação devem:

possuir expiração
ser difíceis de adivinhar
ser de uso controlado
não revelar informações sensíveis
38. Sessão e Redis

Redis poderá ser utilizado futuramente para:

refresh tokens
revogação
rate limiting
sessões
login attempts

Redis não substitui a identidade persistida no PostgreSQL.

39. Segurança dos secrets

Secrets relacionados à autenticação devem permanecer fora do código:

JWT_SECRET_KEY
API credentials
refresh token secrets
external integration secrets

Consultar:

skills/infrastructure/environment.md

para regras de configuração.

40. Testes

A autenticação deve possuir testes específicos.

Cobrir pelo menos:

login válido
senha inválida
usuário inexistente
usuário inativo
token válido
token expirado
token inválido
token ausente

Também testar:

tenant correto
tenant incorreto
usuário excluído logicamente

quando esses cenários fizerem parte da implementação.

41. Testes de isolamento

Exemplo:

Tenant A
 └── User A

Tenant B
 └── User B

Validar:

User A → Tenant A
✓
User A → Tenant B
✗

O teste deve garantir que autenticação e contexto de tenant permanecem corretamente vinculados.

42. Testes de autorização

Autenticação e RBAC devem ser testados separadamente quando possível.

Exemplo:

JWT válido
+
permission correta
→ permitido
JWT válido
+
permission ausente
→ 403
JWT inválido
→ 401
43. Erros

A autenticação deve utilizar respostas HTTP consistentes:

401 Unauthorized

para falha de autenticação.

403 Forbidden

para usuário autenticado sem autorização suficiente.

Não confundir os dois casos.

44. Performance

A autenticação deve evitar consultas desnecessárias.

Entretanto, otimizações não devem comprometer:

segurança
revogação
status da conta
tenant isolation

Qualquer cache relacionado à identidade deve possuir invalidação adequada.

45. Dependências

A implementação deve utilizar as dependências já definidas no projeto:

PyJWT
pwdlib
FastAPI
SQLAlchemy
Pydantic

Novas bibliotecas de autenticação somente devem ser adicionadas quando houver necessidade concreta.

Não implementar criptografia própria.

46. Arquitetura conceitual

O fluxo completo deve ser:

                    ┌──────────────┐
                    │    Login     │
                    └──────┬───────┘
                           ↓
                    ┌──────────────┐
                    │ Verificar    │
                    │   senha      │
                    └──────┬───────┘
                           ↓
                    ┌──────────────┐
                    │    User      │
                    └──────┬───────┘
                           ↓
                    ┌──────────────┐
                    │    Tenant    │
                    └──────┬───────┘
                           ↓
                    ┌──────────────┐
                    │     JWT      │
                    └──────┬───────┘
                           ↓
                    HTTP Request
                           ↓
                    ┌──────────────┐
                    │ JWT Validate │
                    └──────┬───────┘
                           ↓
                    ┌──────────────┐
                    │ Current User │
                    └──────┬───────┘
                           ↓
                    ┌──────────────┐
                    │ Tenant       │
                    │ Context      │
                    └──────┬───────┘
                           ↓
                    ┌──────────────┐
                    │ Authorization│
                    └──────┬───────┘
                           ↓
                    Business Logic
47. Ordem de implementação

Ao implementar autenticação:

1. User model
2. Password hashing
3. Authentication configuration
4. Login schema
5. Login service
6. JWT generation
7. Authentication dependency
8. Current user
9. Tenant context
10. Authorization
11. Tests
12. Documentation

A ordem pode ser ajustada conforme as dependências reais da implementação.

48. Checklist

Antes de finalizar uma alteração de autenticação:

 Senhas nunca são armazenadas em texto puro;
 Password hash utiliza pwdlib;
 JWT possui assinatura válida;
 Algoritmo JWT é controlado pelo backend;
 JWT possui expiração;
 Secret está em variável de ambiente;
 Token inválido retorna 401;
 Usuário sem permissão retorna 403;
 Usuário inativo não autentica;
 Usuário excluído logicamente não autentica;
 Tenant é obtido de contexto confiável;
 Dados de outro tenant não podem ser acessados;
 Secrets não aparecem nos logs;
 JWT completo não aparece nos logs;
 Testes de autenticação existem;
 Testes de isolamento existem.
49. Regra principal

A autenticação deve estabelecer uma identidade confiável para o restante da aplicação.

O fluxo deve manter uma separação clara:

Autenticar
    ↓
Identificar
    ↓
Contextualizar tenant
    ↓
Autorizar
    ↓
Executar operação

Nenhuma funcionalidade protegida deve depender somente de informações fornecidas diretamente pelo cliente.