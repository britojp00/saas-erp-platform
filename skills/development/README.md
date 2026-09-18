# Development

## Objetivo

Definir o fluxo geral de desenvolvimento do SaaS ERP Platform.

Este documento estabelece como novas funcionalidades, correções, refatorações e alterações de infraestrutura devem ser planejadas, implementadas, testadas e versionadas.

Este documento complementa:

```text
skills/00-project-overview.md
skills/01-project-structure.md
skills/02-architecture.md
skills/AGENTS.md
skills/tasks/README.md
skills/testing/README.md
skills/security/README.md
1. Princípios

O desenvolvimento deve priorizar:

Clareza
Consistência
Simplicidade
Segurança
Testabilidade
Manutenibilidade

Toda alteração deve resolver o problema solicitado sem ampliar desnecessariamente o escopo.

2. Antes de alterar código

Antes de modificar qualquer arquivo:

1. Entender o problema
2. Localizar a implementação
3. Consultar as skills relevantes
4. Verificar código relacionado
5. Verificar testes existentes
6. Definir a menor alteração necessária

Não começar alterando arquivos sem entender a responsabilidade deles.

3. Skills

As skills existentes devem ser consultadas conforme a natureza da tarefa.

Exemplo:

Backend
→ skills/backend/

Banco
→ skills/database/

Docker
→ skills/infrastructure/

Segurança
→ skills/security/

Testes
→ skills/testing/

Frontend
→ skills/frontend/

Não é necessário carregar todas as skills para qualquer tarefa.

4. Escopo

Uma tarefa deve alterar somente o necessário para atingir o objetivo.

Evitar:

feature solicitada
+
refatoração não relacionada
+
mudança visual não solicitada
+
atualização de dependências sem necessidade

Isso dificulta revisão e aumenta o risco de regressões.

5. Regra da menor mudança

Preferir:

menor alteração correta

em vez de:

maior refatoração possível

Exemplo:

problema em uma query
→ corrigir a query

Não transformar automaticamente em:

problema em uma query
→ reestruturar todo o repository

sem necessidade.

6. Consistência

Antes de criar uma implementação nova, procurar implementações existentes do mesmo padrão.

Exemplo:

Customer
→ observar padrão

Product
→ seguir padrão quando aplicável

Order
→ seguir padrão quando aplicável

Não criar abordagens diferentes para problemas equivalentes sem justificativa técnica.

7. Código existente

Código existente deve ser tratado como contexto arquitetural.

Antes de criar:

helper
service
repository
component
utility
factory

verificar se já existe algo equivalente.

Evitar duplicar funcionalidades.

8. Abstração

Não abstrair prematuramente.

Primeiro implementar corretamente.

Depois avaliar se existe:

repetição real
padrão consolidado
benefício de manutenção

Somente então criar abstração.

9. Overengineering

Evitar introduzir tecnologias ou padrões somente porque são populares.

Exemplos que não devem ser adicionados automaticamente:

CQRS
Event Sourcing
Microservices
Generic Repository
Dependency Injection Framework
Message Bus
Advanced State Management

A complexidade deve ser justificada pelo problema.

10. Dependências

Antes de adicionar uma biblioteca:

1. Verificar se já existe solução no projeto
2. Avaliar biblioteca padrão da linguagem
3. Avaliar dependências existentes
4. Verificar manutenção
5. Verificar compatibilidade
6. Avaliar impacto arquitetural

Adicionar somente quando houver necessidade real.

11. Backend Dependencies

Backend deve utilizar:

uv
pyproject.toml
uv.lock

Não instalar pacotes manualmente fora do gerenciamento do projeto.

Preferir:

uv add pacote

ou:

uv add --dev pacote

quando apropriado.

12. Frontend Dependencies

O frontend deverá utilizar o gerenciador de pacotes definido no projeto.

As dependências devem permanecer registradas no:

package.json

e lockfile correspondente.

Não instalar bibliotecas somente globalmente na máquina do desenvolvedor.

13. Database Changes

Alterações no banco devem seguir:

Model
↓
Migration
↓
Review
↓
Test

Não alterar tabelas manualmente como fluxo normal.

Consultar:

skills/database/migrations.md
14. Migration

Nunca editar uma migration já aplicada em ambientes compartilhados.

Quando existir necessidade de corrigir o schema:

migration existente
↓
nova migration

Isso preserva o histórico.

15. Environment

Configurações específicas de ambiente devem permanecer fora do código.

Utilizar:

.env
.env.example
environment variables

Consultar:

skills/infrastructure/environment.md
16. Secrets

Nunca adicionar ao Git:

password
token
API key
private key
JWT secret
database credentials
.env

Antes do commit, verificar alterações novas e arquivos gerados.

17. Docker

Alterações relacionadas a containers devem seguir:

skills/infrastructure/docker.md
skills/infrastructure/docker-compose.md

Evitar modificar infraestrutura somente para resolver um problema que pertence à aplicação.

18. Local Development

O projeto deve ser executável localmente com o mínimo de configuração manual possível.

O desenvolvedor deve seguir os comandos documentados no:

README.md

e nas skills correspondentes.

19. Desenvolvimento incremental

Preferir construir o projeto em etapas pequenas.

Exemplo:

Infraestrutura
↓
Database
↓
Authentication
↓
Tenant
↓
Customer
↓
Product
↓
Inventory
↓
Order

Cada etapa deve ser validada antes de avançar.

20. Vertical Slices

Quando possível, implementar funcionalidades completas por domínio.

Exemplo:

Customer
├── Model
├── Migration
├── Schema
├── Repository
├── Service
├── Router
└── Tests

Isso permite validar uma funcionalidade inteira antes de espalhar código incompleto por várias áreas.

21. Commit pequeno

Commits devem representar alterações coerentes.

Preferir:

feat: add customer model

e depois:

feat: add customer API

quando essas forem mudanças distintas.

Evitar um commit que misture:

feature
refactor
docker
frontend
migration

sem necessidade.

22. Commit Message

Utilizar mensagens claras.

Formato recomendado:

type: description

Exemplos:

feat: add customer management
fix: prevent cross-tenant access
test: add order service tests
refactor: simplify customer repository
docs: update database guidelines
chore: update dependencies
23. Types de Commit

Tipos comuns:

feat
fix
refactor
test
docs
chore
build
ci

Utilizar o tipo que melhor representa a mudança.

24. Git Status

Antes de realizar commit:

git status

Verificar:

arquivos alterados
arquivos novos
arquivos removidos

Não fazer commit automaticamente de tudo sem revisar.

25. Git Diff

Antes do commit:

git diff

Também verificar arquivos novos quando necessário.

O objetivo é confirmar que somente as alterações pretendidas serão versionadas.

26. Arquivos Não Relacionados

Se houver alterações pré-existentes ou não relacionadas à tarefa:

não sobrescrever
não apagar
não incluir automaticamente

Revisar antes de modificar.

27. Branches

O projeto poderá utilizar branches para separar trabalho.

Estrutura conceitual:

main
feature/*
fix/*
refactor/*

A estratégia definitiva pode evoluir conforme o projeto e o fluxo de contribuição.

28. Main

A branch principal deve permanecer estável.

Evitar desenvolver diretamente nela quando a alteração possuir risco relevante.

Antes de integrar uma mudança, executar as validações apropriadas.

29. Feature Branch

Uma funcionalidade relevante pode utilizar:

feature/nome-da-feature

Exemplo:

feature/customer-management
30. Fix Branch

Correções podem utilizar:

fix/nome-do-problema

Exemplo:

fix/cross-tenant-access
31. Refactor Branch

Refatorações independentes podem utilizar:

refactor/nome-da-refatoracao

Não misturar refatoração extensa com feature sem necessidade.

32. Pull Request

Pull Requests devem possuir contexto suficiente para revisão.

Incluir quando apropriado:

problema
solução
impacto
testes
alterações de banco
alterações de infraestrutura
33. Pull Request Scope

Um Pull Request deve possuir escopo coerente.

Evitar PRs contendo:

feature A
+
feature B
+
refactor C
+
mudança visual D

sem relação clara entre eles.

34. Review

Durante revisão, verificar:

correção
arquitetura
segurança
testes
performance
legibilidade

Não avaliar somente se o código "funciona".

35. Definition of Done

Uma tarefa somente deve ser considerada concluída quando:

implementação
↓
testes
↓
lint
↓
format
↓
review

estiverem adequadamente validados quando aplicáveis.

36. Testes obrigatórios

Toda alteração relevante deve avaliar se necessita:

unit test
integration test
API test
security test
E2E test

Não adicionar testes artificiais somente para aumentar coverage.

37. Lint

Backend:

uv run ruff check .

O comando deve passar antes da conclusão da tarefa, quando houver alterações no backend.

38. Format

Backend:

uv run ruff format --check .

Quando necessário, corrigir com:

uv run ruff format .
39. Tests

Backend:

uv run pytest

Testes relevantes devem passar antes de finalizar a alteração.

40. Coverage

Quando uma alteração possuir regras relevantes:

uv run coverage run -m pytest
uv run coverage report

Coverage deve ser usada como indicador.

41. Frontend Validation

O frontend deverá possuir comandos próprios para:

type checking
lint
tests
build

Esses comandos serão definidos quando a aplicação frontend for implementada.

42. Database Validation

Após alterações relacionadas ao banco:

migration
↓
apply
↓
tests

quando aplicável.

43. Docker Validation

Após alterações em Docker:

build
↓
start
↓
health check

quando aplicável.

44. API Validation

Após alterações na API, verificar:

endpoint
request
response
status code
authentication
authorization
OpenAPI
tests
45. Breaking Changes

Antes de realizar mudança incompatível:

1. Identificar consumidores
2. Verificar frontend
3. Verificar testes
4. Verificar integrações
5. Avaliar versionamento
6. Documentar impacto

Não quebrar contratos silenciosamente.

46. Refactoring

Refatorações devem preservar comportamento quando esse for o objetivo.

Fluxo recomendado:

estado atual
↓
testes
↓
refactor
↓
testes

Não misturar mudança de comportamento com refatoração sem necessidade.

47. Bug Fix

Correção de bug deve, quando possível:

reproduzir
↓
criar teste
↓
corrigir
↓
executar teste

Isso transforma o bug corrigido em proteção contra regressão.

48. Investigation

Quando o problema não estiver claro:

1. Reproduzir
2. Coletar evidências
3. Consultar logs
4. Verificar estado
5. Identificar causa
6. Alterar
7. Validar

Evitar alterar vários componentes simultaneamente sem saber qual é a causa.

49. Debugging

Durante debugging, é aceitável adicionar:

temporary logs
debug configuration
diagnostic commands

Mas esses recursos devem ser removidos ou controlados antes da conclusão.

Nunca adicionar secrets aos logs para facilitar debugging.

50. Production Debugging

Evitar alterações experimentais diretamente em produção.

Quando possível:

reproduzir
↓
corrigir
↓
testar
↓
deploy

Logs e observabilidade devem ser utilizados para investigar produção.

51. Performance

Não otimizar somente por percepção.

Fluxo recomendado:

identificar gargalo
↓
medir
↓
alterar
↓
medir novamente

Evitar micro-otimizações sem impacto real.

52. Database Performance

Para queries lentas:

identificar query
↓
avaliar filtros
↓
avaliar índices
↓
analisar plano quando necessário
↓
otimizar
↓
validar

Não adicionar índices indiscriminadamente.

53. API Performance

Para endpoints lentos, investigar:

database
serialization
external API
network
CPU
caching
N+1

Não resolver todo problema de performance com cache.

54. Cache

Cache deve ser utilizado quando existir benefício mensurável.

Antes de adicionar cache:

identificar custo
avaliar frequência
definir invalidação
considerar tenant

Um cache incorreto pode causar problemas de consistência.

55. Security Review

Alterações que afetem:

authentication
authorization
tenant
database
external integrations
secrets
uploads

devem receber revisão adicional de segurança.

56. Multi-tenancy Review

Toda funcionalidade que acessar dados de tenant deve verificar:

tenant context
tenant filter
ownership
cache
jobs
logs
integrations

quando aplicável.

57. Dependency Changes

Alterações de dependência devem verificar:

compatibilidade
lockfile
tests
build
security

Não atualizar dependências somente por estarem desatualizadas sem avaliar impacto.

58. Generated Code

Código gerado automaticamente deve ser tratado como código normal.

Antes de aceitar:

revisar
testar
formatar
validar

Não confiar no código apenas porque foi produzido por uma ferramenta de IA.

59. AI-assisted Development

Quando utilizar IA no desenvolvimento:

1. Fornecer contexto preciso
2. Indicar arquivos relevantes
3. Definir objetivo
4. Limitar escopo
5. Revisar alterações
6. Executar testes
7. Verificar segurança

A IA deve seguir as skills do projeto.

60. Contexto para IA

Um bom contexto deve incluir:

problema
arquivo
classe
método
comportamento atual
comportamento esperado
restrições

Evitar enviar contexto gigante sem relação com a tarefa.

61. AI Scope

Não solicitar à IA:

"melhore todo o projeto"

quando o problema for:

"corrija este endpoint"

Preferir tarefas específicas.

62. AI-generated Dependencies

A IA não deve adicionar uma dependência automaticamente somente porque ela conhece uma biblioteca que resolve o problema.

Qualquer dependência nova deve seguir as mesmas regras aplicadas a código escrito manualmente.

63. AI Security

Código gerado por IA deve ser especialmente revisado em:

authentication
authorization
tenant isolation
SQL
secrets
validation
external integrations
logging
64. Não remover proteções

A IA não deve remover:

authentication
authorization
validation
tenant filters
constraints
tests

somente para resolver erros de implementação.

Quando uma proteção impedir uma funcionalidade legítima, investigar a causa antes de removê-la.

65. Documentação

Alterações de comportamento importantes devem atualizar documentação relevante.

Exemplos:

API
architecture
environment
database
deployment
development

Não atualizar documentação somente para registrar mudanças internas irrelevantes.

66. README

O README.md da raiz deve explicar pelo menos:

objetivo
stack
estrutura
como executar
testes
roadmap

Ele deve permanecer coerente com o estado real do projeto.

67. Changelog

Um changelog poderá ser adicionado futuramente quando o projeto possuir releases relevantes.

Não é necessário manter um changelog detalhado para cada commit durante o desenvolvimento inicial.

68. Releases

Quando o projeto possuir releases:

version
release notes
migration notes
breaking changes

devem ser documentados quando aplicável.

69. Backward Compatibility

Ao alterar uma funcionalidade existente, avaliar:

frontend
API consumers
database
jobs
integrations
tests

Não considerar somente o arquivo modificado.

70. Cleanup

Após uma implementação:

remover código temporário
remover logs de debug
remover imports inúteis
remover arquivos temporários

Não deixar artefatos de investigação no repositório.

71. Temporary Files

Arquivos temporários devem permanecer fora do repositório.

Exemplos:

debug.log
dump.sql
response.json
screenshots temporários

quando não fizerem parte do projeto.

72. Generated Artifacts

Arquivos gerados automaticamente devem ser versionados somente quando isso fizer parte da estratégia do projeto.

Evitar commitar:

build output
cache
coverage
temporary generated files

quando estiverem corretamente ignorados pelo Git.

73. File Naming

Seguir os padrões definidos em:

skills/01-project-structure.md

Preferir nomes previsíveis e consistentes.

74. Naming Code

Nomes devem comunicar intenção.

Preferir:

get_current_user
create_customer
cancel_order
reserve_stock

Evitar:

do_it
process_data
handle_stuff

quando não explicarem o comportamento.

75. Comments

Comentários devem explicar:

por que

e não simplesmente:

o que o código já deixa evidente

Exemplo útil:

# Use tenant_id here to prevent cross-tenant access.

Evitar comentários óbvios como:

# Add customer
customer = ...
76. TODO

TODOs devem representar trabalho real futuro.

Evitar deixar:

TODO: melhorar isso

sem contexto.

Quando possível:

TODO: replace temporary polling with webhook once provider supports it
77. Error Handling

Nunca ignorar erros silenciosamente.

Evitar:

try:
    ...
except Exception:
    pass

Tratar ou propagar de maneira apropriada.

78. Logging

Logs devem seguir:

skills/backend/logging.md
skills/observability/README.md

Não adicionar logs indiscriminadamente.

79. Security

Toda implementação deve respeitar:

skills/security/README.md

Em caso de conflito entre conveniência e segurança, a implementação deve manter as proteções necessárias e revisar a solução.

80. Tests

Toda alteração deve considerar o impacto sobre testes existentes.

Não remover testes somente porque ficaram inconvenientes após uma implementação.

Quando o comportamento mudou deliberadamente, atualizar o teste para refletir o novo contrato.

81. Final Validation

Antes de considerar uma tarefa concluída:

1. Revisar diff
2. Executar testes
3. Executar lint
4. Verificar formatação
5. Verificar segurança
6. Verificar migrations quando aplicável
7. Verificar documentação quando aplicável
82. Git Commit

Depois das validações:

git status
git diff
git add .
git commit -m "type: description"

Não realizar push automaticamente sem verificar o conteúdo do commit.

83. Push

Antes do push:

git status

e verificar:

branch correta
commit correto
arquivos corretos

Depois:

git push
84. Pull

Antes de iniciar trabalho em uma branch compartilhada:

git pull

Resolver conflitos conscientemente.

Não sobrescrever alterações de outras pessoas.

85. Merge Conflicts

Em conflitos:

1. Identificar origem das alterações
2. Entender ambas as versões
3. Preservar comportamento necessário
4. Resolver
5. Executar testes

Nunca escolher automaticamente um lado sem compreender o impacto.

86. Revert

Quando uma alteração causar problema, preferir utilizar mecanismos do Git de forma controlada.

Não apagar arquivos manualmente como substituto de uma estratégia de versionamento.

87. Scope Creep

Durante uma tarefa, podem surgir problemas relacionados.

Separar:

problema necessário para concluir tarefa

de:

melhoria futura

Registrar a melhoria futura sem necessariamente implementá-la naquele momento.

88. Future Improvements

Melhorias não necessárias para a tarefa podem ser registradas em:

docs/
issues
roadmap

conforme o mecanismo escolhido pelo projeto.

89. Simplicidade

Quando duas soluções forem tecnicamente adequadas, preferir a que possuir:

menos complexidade
menos dependências
menos código
menos pontos de falha

desde que preserve os requisitos.

90. Consistency over Creativity

No projeto, consistência é mais importante que criatividade arquitetural.

Quando já existir um padrão funcional:

seguir o padrão

antes de criar uma abordagem nova.

Uma nova abordagem deve possuir justificativa técnica clara.

91. Não alterar padrões sem necessidade

Não modificar simultaneamente:

naming
architecture
folder structure
database strategy
testing strategy

durante uma feature comum.

Mudanças arquiteturais devem ser tratadas como alterações próprias.

92. Production Readiness

Uma funcionalidade não deve ser considerada pronta somente porque funciona localmente.

Quando aplicável, verificar:

tests
security
logging
configuration
database migration
Docker
error handling
observability
93. Developer Experience

O projeto deve permanecer fácil de executar e entender.

Evitar soluções que exijam conhecimento implícito não documentado.

Quando uma configuração for necessária, documentá-la.

94. Onboarding

Um novo desenvolvedor deve conseguir:

clonar
configurar
instalar dependências
iniciar infraestrutura
executar aplicação
executar testes

seguindo a documentação existente.

95. Quality Gate

Uma alteração importante deve passar pelos seguintes pontos:

Código
↓
Tests
↓
Lint
↓
Format
↓
Security
↓
Architecture
↓
Documentation

Nem todos os pontos serão necessários em toda alteração, mas devem ser avaliados.

96. Regra principal

O desenvolvimento deve seguir:

Entender
↓
Planejar
↓
Implementar
↓
Testar
↓
Revisar
↓
Versionar

Não:

Alterar
↓
Executar
↓
Esperar funcionar

A qualidade do projeto depende mais da consistência do processo do que da velocidade de uma alteração isolada.