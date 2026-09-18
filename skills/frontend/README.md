# Frontend

## Objetivo

Definir as regras gerais para desenvolvimento, organização e evolução do frontend do SaaS ERP Platform.

O frontend será responsável pela interface do usuário e consumirá o backend exclusivamente através da API HTTP.

Stack planejada:

```text
React
TypeScript
Vite

O frontend não deve acessar diretamente:

PostgreSQL
Redis
SQLAlchemy
Repositories
Services do backend

A comunicação deve ocorrer através da API.

1. Princípios

O frontend deve ser:

organizado;
previsível;
responsivo;
reutilizável;
acessível;
seguro;
tipado;
desacoplado do backend interno.

A interface deve consumir somente os contratos públicos da API.

2. Estrutura

O frontend fica em:

frontend/

A estrutura inicial poderá seguir:

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   ├── layouts/
│   ├── hooks/
│   ├── services/
│   ├── types/
│   ├── contexts/
│   ├── utils/
│   ├── assets/
│   ├── routes/
│   └── main.tsx
├── public/
├── package.json
├── tsconfig.json
└── vite.config.ts

A estrutura poderá evoluir conforme o sistema crescer.

Não criar diretórios sem necessidade real.

3. Separação Frontend / Backend

O frontend deve conhecer:

HTTP
JSON
API Contract
Authentication Contract

O frontend não deve conhecer detalhes internos como:

SQLAlchemy
PostgreSQL tables
Repository
Service implementation
Database queries
4. API Client

A comunicação com o backend deve ser centralizada.

Exemplo conceitual:

src/
└── services/
    └── api/

ou estrutura equivalente.

Evitar chamadas HTTP espalhadas diretamente por componentes.

Preferir:

Component
   ↓
Hook / Service
   ↓
API Client
   ↓
Backend
5. HTTP Client

A aplicação deve possuir uma estratégia consistente para chamadas HTTP.

Responsabilidades do client podem incluir:

base URL
headers
authentication
serialization
error handling
timeouts

Não criar um client diferente para cada tela.

6. API Base URL

A URL da API deve vir de configuração de ambiente.

Exemplo conceitual:

VITE_API_URL

Não colocar:

http://localhost:8000

diretamente em componentes.

O mesmo código deve poder utilizar diferentes ambientes.

7. Environment

Configurações do frontend devem utilizar o mecanismo de ambiente do Vite.

Exemplo:

VITE_API_URL=http://localhost:8000

Somente configurações que podem ser expostas ao navegador devem possuir prefixo:

VITE_

Nunca colocar secrets de backend em variáveis expostas ao frontend.

8. Secrets

O frontend não é um ambiente seguro para armazenar secrets.

Nunca colocar no frontend:

JWT secret
database password
API private key
backend credentials
external private tokens

Qualquer variável enviada ao navegador deve ser tratada como pública.

9. Authentication

O frontend deve consumir o contrato de autenticação fornecido pelo backend.

Fluxo conceitual:

Login Form
   ↓
POST /auth/login
   ↓
Authentication Response
   ↓
Authenticated Application

A lógica de validação da identidade permanece no backend.

10. Token

A estratégia de armazenamento do token deve ser definida conscientemente.

Considerar:

XSS
session theft
CSRF
token lifetime
logout
refresh

A implementação definitiva deve seguir:

skills/backend/authentication.md
skills/security/README.md
11. Authorization no Frontend

O frontend pode utilizar permissions para melhorar a experiência.

Exemplo:

customer.delete

pode controlar:

mostrar botão "Excluir"

Mas isso não representa segurança.

O backend sempre deve validar a permission.

12. Permission-Based UI

A interface pode condicionar componentes:

User has permission
    ↓
show action

ou:

User lacks permission
    ↓
hide / disable action

Essa lógica existe para UX.

Nunca confiar nela para impedir operações.

13. Tenant Context

O frontend poderá exibir informações relacionadas ao tenant atual.

Entretanto, não deve utilizar um tenant_id enviado pela interface como mecanismo de segurança.

O backend continua responsável por determinar e validar o contexto.

14. API Responses

O frontend deve consumir os schemas públicos da API.

Não assumir a existência de campos internos do banco.

Exemplo:

API Response
↓
TypeScript Type
↓
Component
15. TypeScript Types

Dados relevantes da API devem possuir tipos TypeScript.

Exemplo conceitual:

interface Customer {
  id: string;
  name: string;
  email: string | null;
}

Evitar utilizar:

any

quando o formato for conhecido.

16. API Types

Os tipos devem refletir o contrato real da API.

Evitar criar tipos arbitrariamente diferentes.

Exemplo:

Backend:
created_at

Frontend:
created_at

Não mudar silenciosamente para:

createdAt

sem uma estratégia clara de transformação.

17. DTO / Transformation

Quando o frontend precisar adaptar o formato da API para a interface, a transformação deve ser explícita.

Exemplo:

API Response
   ↓
Mapper
   ↓
UI Model

Não espalhar transformações diferentes por vários componentes.

18. Components

Componentes devem possuir responsabilidade clara.

Evitar componentes gigantes contendo:

API calls
business logic
routing
forms
tables
modals
permission checks

tudo no mesmo arquivo.

Separar responsabilidades quando isso melhorar a manutenção.

19. Pages

Pages representam telas ou áreas de navegação.

Exemplo:

pages/
├── Login
├── Dashboard
├── Customers
├── Products
├── Inventory
└── Orders

Pages podem coordenar componentes, hooks e services.

20. Components

Componentes reutilizáveis devem ficar em:

components/

Exemplos:

Button
Modal
Table
Input
Select
Pagination
LoadingState
ErrorState

Não criar componentes genéricos excessivamente abstratos.

21. Layouts

Layouts representam estruturas reutilizáveis de página.

Exemplos:

AuthLayout
DashboardLayout

Um layout pode controlar:

navigation
sidebar
header
content area
22. Hooks

Hooks devem encapsular lógica reutilizável do frontend.

Exemplos:

useAuth()
useCustomers()
useProducts()
usePagination()

Evitar transformar hooks em arquivos gigantes.

23. API Hooks

Quando uma funcionalidade exigir:

fetch
loading
error
data
refetch

um hook pode ser utilizado para centralizar esse comportamento.

A estratégia definitiva deve permanecer consistente entre as telas.

24. State Management

Não introduzir uma biblioteca global de estado sem necessidade.

Começar com:

React state
Context
Hooks

quando forem suficientes.

Adicionar uma solução dedicada somente quando a complexidade justificar.

25. Global State

Estado global pode ser apropriado para:

authenticated user
tenant context
theme
application settings

Não armazenar globalmente todo estado de cada tela.

26. Server State

Dados vindos da API possuem características diferentes do estado local da interface.

Exemplos:

customers
products
orders
inventory

Quando a aplicação crescer, poderá ser considerada uma biblioteca específica para server state.

Não adicionar prematuramente.

27. Forms

Formulários devem possuir:

validation
loading state
error state
success feedback

A validação do frontend melhora UX.

A validação do backend continua obrigatória.

28. Form Validation

Validar no frontend:

required fields
format
length
basic constraints

Isso não substitui:

backend validation
business rules
authorization
29. Error Handling

Erros da API devem possuir tratamento consistente.

Exemplo:

401
→ sessão inválida

403
→ sem permissão

404
→ recurso não encontrado

409
→ conflito

422
→ dados inválidos

500
→ erro interno

A interface deve apresentar uma mensagem apropriada ao usuário.

30. API Error Structure

O frontend deve consumir a estrutura de erro definida pela API.

Exemplo:

{
  "detail": {
    "code": "INSUFFICIENT_STOCK",
    "message": "Estoque insuficiente."
  }
}

Não depender somente do texto da mensagem quando um código está disponível.

31. Authentication Errors

Quando a API retornar:

401 Unauthorized

o frontend deve tratar como falha de autenticação.

Possíveis comportamentos:

session expired
redirect to login
clear authentication state

A estratégia final deve seguir o ciclo de autenticação do backend.

32. Authorization Errors

Quando retornar:

403 Forbidden

o frontend deve apresentar uma resposta adequada.

Não tratar 403 como:

usuário deslogado

porque o usuário pode estar autenticado e simplesmente não possuir a permission.

33. Loading States

Operações assíncronas devem possuir estados visuais apropriados.

Exemplos:

loading
success
error
empty

Evitar deixar a interface aparentemente congelada durante chamadas de API.

34. Empty States

Listagens sem dados devem possuir estado específico.

Exemplo:

Nenhum cliente cadastrado.

Não confundir:

lista vazia

com:

erro de carregamento
35. Error States

Quando uma API falhar, mostrar estado de erro adequado.

Exemplo:

Não foi possível carregar os clientes.

Não exibir:

stack trace
SQL
database error
internal exception

para o usuário final.

36. Retry na Interface

Retry pode ser disponibilizado para erros transitórios.

Exemplo:

Falha ao carregar dados.
[ Tentar novamente ]

Não repetir automaticamente toda operação de escrita sem avaliar idempotência.

37. Mutations

Operações como:

create
update
delete
cancel
confirm

devem possuir feedback adequado.

Exemplo:

saving
success
error
38. Duplicate Submission

A interface deve evitar submissões acidentais repetidas.

Exemplos:

usuário clica duas vezes

Pode resultar em:

duplicidade

Utilizar:

disable while loading
request state
idempotency support

quando apropriado.

39. Tables

Tabelas devem considerar:

loading
empty
error
pagination
sorting
filtering

Evitar carregar quantidades arbitrariamente grandes de dados.

40. Pagination

A paginação deve utilizar a paginação fornecida pela API.

Não buscar todos os registros para paginar somente no navegador quando o volume puder ser grande.

41. Filtering

Filtros devem ser enviados para a API quando forem filtros de dados persistidos.

Exemplo:

GET /customers?search=joao

Evitar:

GET /customers
↓
baixar milhares
↓
filtrar no frontend

sem necessidade.

42. Sorting

Ordenação de grandes conjuntos deve ocorrer no backend quando possível.

O frontend deve enviar os parâmetros aceitos pela API.

Exemplo:

sort=created_at
order=desc
43. Debounce

Busca textual pode utilizar debounce para evitar muitas requisições consecutivas.

Exemplo:

digitou "cam"
↓
aguarda
↓
GET /products?search=cam

Usar quando melhorar performance e experiência.

44. Routing

As rotas do frontend devem ser organizadas de forma previsível.

Exemplo:

/login
/dashboard
/customers
/products
/inventory
/orders

Rotas protegidas devem exigir autenticação.

45. Protected Routes

O frontend pode bloquear visualmente uma rota para usuários não autenticados.

Porém:

frontend route guard
≠
backend authorization

O backend continua sendo a autoridade de segurança.

46. Navigation

Menus e navegação podem ser condicionados por permissions.

Exemplo:

user.permissions
↓
render menu

Isso melhora UX, mas não substitui o controle da API.

47. Accessibility

A interface deve considerar acessibilidade.

Exemplos:

labels
keyboard navigation
focus
contrast
semantic HTML
screen reader support

Não criar componentes visualmente corretos que sejam difíceis de utilizar por teclado ou tecnologias assistivas.

48. Responsive Design

A interface deve funcionar adequadamente em diferentes tamanhos de tela.

Considerar:

desktop
tablet
mobile

O ERP deve priorizar a experiência de uso das telas reais do sistema.

49. Styling

A estratégia visual deve ser consistente.

Definir e reutilizar:

spacing
typography
buttons
forms
tables
colors
states

Evitar estilos completamente diferentes para cada página.

50. UI Consistency

A mesma ação deve possuir aparência e comportamento semelhantes em diferentes telas.

Exemplo:

Salvar
Cancelar
Excluir
Editar
Pesquisar

devem seguir padrões consistentes.

51. Notifications

Notificações visuais podem informar:

success
warning
error
info

Não utilizar mensagens de sucesso para operações que realmente falharam.

52. Destructive Actions

Operações como:

delete
cancel
reset

devem possuir confirmação quando o risco justificar.

O backend continua responsável por validar a operação.

53. Confirmation Dialogs

Confirmações devem explicar claramente:

ação
recurso
consequência

Evitar:

"Tem certeza?"

sem explicar o que acontecerá.

54. Security UI

O frontend não deve exibir informações sensíveis desnecessariamente.

Evitar exibir:

tokens
secrets
password hashes
internal credentials
55. Sensitive Forms

Campos de senha devem utilizar controles apropriados.

Exemplo:

<input type="password">

Não exibir senhas em texto puro por padrão.

56. Browser Storage

Não armazenar secrets de backend no navegador.

Qualquer dado persistido no navegador deve ser avaliado considerando:

XSS
session theft
privacy
57. API Calls

Chamadas à API devem possuir comportamento centralizado para:

401
403
network failure
timeout
JSON parsing errors

Evitar repetir o mesmo tratamento em todos os componentes.

58. Request Cancellation

Chamadas de busca ou navegação que possam ficar obsoletas podem utilizar cancelamento.

Exemplo:

search request A
↓
usuário digita novamente
↓
cancel / ignore A
↓
request B

Isso reduz respostas fora de ordem.

59. Race Conditions

A interface deve considerar respostas assíncronas fora de ordem.

Exemplo:

Request A
Request B

B termina primeiro
A termina depois

O estado final não deve ser sobrescrito incorretamente por uma resposta antiga.

60. Frontend Logging

O frontend pode registrar erros técnicos, mas não deve expor informações sensíveis.

Nunca registrar:

password
token
secret
credentials
61. Error Reporting

Ferramentas de monitoramento de frontend podem futuramente ser adicionadas.

Elas devem ser configuradas para evitar:

tokens
passwords
personal data
62. Performance

Considerar:

bundle size
rendering
API requests
images
lists
lazy loading

Não otimizar prematuramente.

Primeiro identificar gargalos reais.

63. Code Splitting

Rotas grandes podem futuramente utilizar lazy loading.

Exemplo conceitual:

Login
Dashboard
Customers
Products
Orders

Não é necessário dividir componentes pequenos artificialmente.

64. API Caching

Dados de leitura que forem estáveis ou frequentemente reutilizados podem utilizar cache de server state.

Quando implementado, considerar:

stale data
invalidation
tenant
permissions

Nunca retornar dados de tenant incorreto através de cache.

65. Tenant-aware Cache

Qualquer cache no frontend que possa conter dados específicos de tenant deve considerar o contexto.

Ao trocar de tenant:

cache anterior
→ invalidar / separar

quando aplicável.

66. Tenant Switching

Caso o sistema futuramente permita que um usuário pertença a múltiplos tenants, a troca de tenant deverá:

validar contexto no backend
atualizar sessão
invalidar dados antigos
carregar dados do novo tenant

Não realizar a troca apenas no estado local do frontend.

67. API Versioning

O frontend deve consumir uma versão conhecida da API.

Exemplo:

/api/v1

Mudanças incompatíveis devem ser tratadas de forma consciente.

68. Backend Contract

O frontend não deve depender de detalhes não documentados do backend.

Exemplos de comportamentos que não devem ser assumidos:

ordenação implícita
campos não documentados
mensagens de erro específicas sem contrato
69. Frontend Types

Quando possível, tipos podem ser derivados ou mantidos próximos do contrato da API.

O objetivo é reduzir divergências entre:

Backend
+
Frontend

Não gerar código automaticamente sem avaliar a complexidade e manutenção.

70. API Client Errors

Erros de rede devem ser diferenciados de erros HTTP.

Exemplo:

Network Error

é diferente de:

HTTP 500

A interface pode oferecer comportamentos diferentes para cada caso.

71. Offline

Não implementar suporte offline completo sem requisito.

Quando necessário, definir explicitamente:

offline
reconnection
pending mutations
conflict resolution
72. Internationalization

Internacionalização poderá ser adicionada futuramente.

Não criar uma infraestrutura completa de múltiplos idiomas antes de existir necessidade.

Quando necessário, evitar hardcode indiscriminado de textos de interface.

73. Testing

O frontend deverá possuir testes apropriados.

Considerar:

component tests
hook tests
form tests
API interaction tests
routing tests
E2E

A estratégia geral está em:

skills/testing/README.md
74. Security Tests

Testar quando aplicável:

protected routes
permission-based UI
sensitive data exposure
authentication flow
tenant switching

Mas lembrar:

frontend security tests
≠
backend authorization
75. Environment Tests

Testar configurações importantes:

API URL
environment
feature flags

Não incluir secrets reais.

76. Build

O frontend deve possuir build reproduzível.

Exemplo conceitual:

npm run build

O comando definitivo dependerá da configuração do projeto.

Builds devem falhar quando existirem:

TypeScript errors
build errors
invalid imports

conforme a configuração escolhida.

77. Type Checking

O projeto deve executar verificação de tipos TypeScript.

Evitar utilizar:

any

como solução padrão para eliminar erros de compilação.

Corrigir o tipo na origem.

78. Linting

O frontend deverá possuir linting configurado.

A ferramenta poderá ser definida durante a implementação.

Lint deve verificar principalmente:

unused code
unsafe patterns
consistency
React rules
TypeScript rules
79. Formatting

A formatação deve ser consistente.

A ferramenta escolhida deverá ser única e aplicada ao projeto inteiro.

Não misturar múltiplos formatadores com regras conflitantes.

80. Dependencies

Novas bibliotecas devem ser adicionadas somente quando necessárias.

Antes de adicionar:

verificar solução existente
avaliar manutenção
avaliar bundle
avaliar segurança
avaliar complexidade
81. Avoid Overengineering

Não adicionar automaticamente:

Redux
global event bus
state machine
design system completo
microfrontend
form framework
data fetching framework

sem necessidade real.

Começar simples e evoluir conforme o produto exigir.

82. Component Reuse

Reutilizar componentes quando existir comportamento realmente comum.

Não transformar todo elemento em componente separado somente para reduzir tamanho dos arquivos.

83. Business Logic

Regras importantes não devem existir somente na interface.

Exemplos:

calculation
authorization
stock rules
order state
financial rules

O backend deve permanecer a autoridade.

O frontend pode antecipar validações para UX.

84. Calculations

Valores financeiros devem ser tratados cuidadosamente.

Evitar confiar em number para lógica financeira crítica sem entender a precisão envolvida.

O valor oficial deve ser determinado pelo backend.

85. Dates

O frontend deve respeitar o formato definido pela API.

Exemplo:

2026-09-17T18:30:00Z

Conversões para o horário local devem ocorrer somente na camada de apresentação quando apropriado.

86. API Data Refresh

Depois de uma mutation:

create
update
delete

o frontend deve atualizar ou invalidar os dados relacionados conforme a estratégia adotada.

Evitar manter dados visivelmente obsoletos sem indicação.

87. Optimistic Updates

Atualizações otimistas podem ser utilizadas quando:

operação simples
risco baixo
rollback claro

Não utilizar para qualquer operação crítica.

Para operações financeiras ou de estoque, avaliar cuidadosamente.

88. Error Recovery

A interface deve permitir recuperação quando possível.

Exemplos:

retry request
reload data
cancel form
return to previous state

Não esconder o erro silenciosamente.

89. Navigation Guards

Quando existirem formulários com alterações não salvas, considerar avisar antes de sair.

Isso deve ser implementado somente quando houver benefício claro para a experiência.

90. Accessibility Testing

Componentes importantes devem ser testados para:

keyboard navigation
focus
labels
ARIA when necessary
screen readers
91. Responsive Testing

Telas importantes devem ser verificadas em:

desktop
tablet
mobile

especialmente:

login
dashboard
forms
tables
menus
modals
92. Frontend Documentation

Decisões importantes devem ser documentadas.

Exemplos:

authentication storage
state management
API client
component architecture
styling
routing

Documentação adicional pode ficar em:

docs/
93. Development

A execução do frontend dependerá do package.json criado durante a implementação.

O padrão esperado será semelhante a:

npm install
npm run dev
npm run build
npm run test

Os comandos definitivos devem refletir o projeto real.

94. Pull Requests

Alterações significativas de frontend devem incluir:

implementation
tests
type checking
lint
build validation

quando aplicável.

95. Checklist

Antes de finalizar uma alteração no frontend:

 API contract foi respeitado;
 TypeScript types estão corretos;
 Não existe any desnecessário;
 API calls estão centralizadas;
 Authentication foi considerada;
 Authorization foi considerada;
 Tenant isolation foi considerada;
 Backend continua sendo a autoridade de segurança;
 Loading state foi tratado;
 Error state foi tratado;
 Empty state foi tratado;
 Form validation foi considerada;
 Dados sensíveis não aparecem na interface;
 Secrets não estão no frontend;
 Componentes possuem responsabilidades claras;
 Estado global foi utilizado somente quando necessário;
 Não existe lógica de negócio crítica somente no frontend;
 Responsividade foi considerada;
 Acessibilidade foi considerada;
 Testes foram atualizados;
 Type checking passa;
 Lint passa;
 Build passa.
96. Regra principal

O frontend deve ser uma camada de apresentação e interação com o usuário, consumindo o backend através de contratos claros.

A separação principal deve permanecer:

Frontend
→ interface e experiência

API
→ contrato

Backend
→ regra de negócio e segurança

Database
→ persistência e integridade

O frontend deve ser independente dos detalhes internos do backend e nunca assumir responsabilidades críticas que pertencem ao servidor.