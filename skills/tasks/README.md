# Tasks

## Objetivo

Definir como tarefas de desenvolvimento devem ser interpretadas, planejadas, executadas e validadas dentro do SaaS ERP Platform.

Este documento também define as regras para utilização de IA no desenvolvimento do projeto.

O agente de IA utilizado no desenvolvimento será o:

```text
OpenCode

O OpenCode será utilizado integrado ao ambiente de desenvolvimento, incluindo o VS Code.

As instruções deste diretório devem orientar o agente durante tarefas de:

criação
alteração
correção
refatoração
testes
database
infraestrutura
frontend
backend
1. Princípios

Toda tarefa deve seguir:

Entender
↓
Investigar
↓
Planejar
↓
Implementar
↓
Validar
↓
Relatar

O agente não deve começar modificando arquivos antes de compreender o objetivo e o contexto necessário.

2. Papel da IA

O OpenCode deve atuar como:

Assistente de desenvolvimento
Analista técnico
Implementador
Auxiliar de investigação
Revisor técnico

A IA não deve tomar decisões arquiteturais importantes sem considerar as regras existentes do projeto.

3. Fonte de verdade

Antes de implementar uma tarefa, consultar primeiro:

skills/AGENTS.md

Depois consultar as skills específicas da área envolvida.

Exemplo:

Backend
→ skills/backend/

Database
→ skills/database/

Frontend
→ skills/frontend/

Infrastructure
→ skills/infrastructure/

Security
→ skills/security/

Testing
→ skills/testing/

As skills do projeto devem ser tratadas como instruções de desenvolvimento.

4. Hierarquia de instruções

Durante uma tarefa, considerar esta ordem:

1. Requisitos explícitos da tarefa
2. skills/AGENTS.md
3. Skills específicas da área
4. Arquitetura existente
5. Código existente
6. Testes existentes

Quando houver conflito, identificar o conflito antes de implementar.

Não ignorar silenciosamente regras existentes.

5. Contexto da tarefa

Uma tarefa deve possuir, quando possível:

Problema
Arquivo
Classe
Método
Comportamento atual
Comportamento esperado
Restrições

Exemplo:

Problema:
clientes de outro tenant podem aparecer na listagem.

Arquivo:
backend/app/repositories/customer.py

Método:
list()

Comportamento atual:
consulta sem filtro de tenant.

Comportamento esperado:
retornar somente clientes do tenant autenticado.

Restrições:
manter arquitetura existente e adicionar testes.
6. Tarefas claras

O agente deve procurar identificar:

o que está errado
o que precisa mudar
o que não deve mudar

Não ampliar o escopo sem necessidade.

7. Escopo

O OpenCode deve modificar somente os arquivos necessários para cumprir a tarefa.

Evitar alterações não relacionadas.

Exemplo:

Tarefa:
corrigir endpoint de clientes.

Não alterar automaticamente:

layout do frontend
Docker
dependências
arquitetura
outros módulos

sem necessidade.

8. Investigação antes da implementação

Antes de modificar código:

1. localizar arquivos relevantes;
2. localizar classes e métodos;
3. procurar implementações semelhantes;
4. verificar dependencies;
5. verificar testes;
6. consultar skills relacionadas;
7. entender fluxo completo.
9. Buscar padrões existentes

Antes de criar uma solução nova, procurar código semelhante.

Exemplo:

CustomerRepository

pode ser referência para:

ProductRepository

quando a estrutura for equivalente.

Seguir o padrão existente antes de criar um novo.

10. Não inventar arquitetura

A IA não deve criar uma arquitetura diferente somente porque conhece outra abordagem.

Exemplo:

Projeto utiliza:
Router → Service → Repository

Não substituir automaticamente por:

Controller → UseCase → Port → Adapter → Repository

sem uma decisão arquitetural explícita.

11. Menor mudança correta

Priorizar:

menor mudança
+
comportamento correto
+
testes

Evitar grandes refatorações para resolver problemas pequenos.

12. Refatoração

Quando uma tarefa pedir correção:

corrigir primeiro

Não realizar uma grande refatoração automaticamente.

Quando uma refatoração for necessária para a solução:

explicar motivo
limitar escopo
preservar comportamento
testar
13. Dependências

Não adicionar bibliotecas automaticamente.

Antes de adicionar uma dependência:

1. verificar se já existe solução;
2. verificar biblioteca padrão;
3. verificar dependências existentes;
4. avaliar manutenção;
5. avaliar impacto.
14. Database

Quando a tarefa envolver banco:

consultar skills/database/

Verificar:

model
migration
tenant_id
constraints
indexes
soft delete
transactions

Não modificar o banco manualmente como substituto de migration.

15. Security

Quando uma tarefa envolver:

authentication
authorization
tenant
permissions
tokens
secrets
external API
uploads

consultar:

skills/security/README.md

A IA não deve remover proteções apenas para fazer a funcionalidade funcionar.

16. Multi-tenancy

Qualquer operação que trabalhe com dados de tenant deve considerar:

tenant context
tenant_id
ownership
authorization
cache
jobs
logs

O OpenCode deve verificar explicitamente esse ponto antes de concluir uma tarefa multi-tenant.

17. Backend

Para tarefas de backend, seguir:

Router
↓
Schema
↓
Service
↓
Repository
↓
Database

A IA deve colocar cada responsabilidade na camada apropriada.

18. Frontend

Para tarefas de frontend:

Component
↓
Hook / Service
↓
API Client
↓
Backend API

Não acessar diretamente:

PostgreSQL
Redis
SQLAlchemy
19. API

Alterações na API devem considerar:

request
response
status codes
authentication
authorization
tenant
OpenAPI
tests

Não quebrar o contrato sem avaliar impacto.

20. Tests

Toda tarefa relevante deve avaliar:

unit test
integration test
API test
security test
E2E

quando aplicável.

A IA deve criar ou atualizar testes relacionados ao comportamento alterado.

21. Não remover testes

O OpenCode não deve remover testes somente porque:

estão falhando
ficaram inconvenientes
a implementação mudou

Primeiro investigar a causa.

22. Falhas de testes

Quando um teste falhar:

1. entender o erro;
2. verificar comportamento esperado;
3. verificar implementação;
4. corrigir causa;
5. executar novamente.

Não alterar a assertion somente para obter sucesso.

23. Validação

Ao finalizar uma tarefa, executar as validações apropriadas.

Backend:

uv run pytest
uv run ruff check .
uv run ruff format --check .

Frontend:

type checking
lint
tests
build

conforme os scripts reais do projeto.

24. Database Validation

Depois de alteração de banco:

migration
↓
apply
↓
test

quando aplicável.

25. Docker Validation

Depois de alteração em Docker:

build
↓
start
↓
health check

quando aplicável.

26. OpenCode e terminal

O OpenCode deve executar comandos no ambiente do projeto quando necessário para:

investigação
testes
lint
formatação
build
migrations

Antes de comandos destrutivos, avaliar cuidadosamente o impacto.

27. Comandos destrutivos

Não executar automaticamente comandos potencialmente destrutivos.

Exemplos:

DROP DATABASE
DROP TABLE
rm -rf
git reset --hard
git clean
force push

Esses comandos exigem confirmação ou justificativa explícita e contexto seguro.

28. Git

O OpenCode pode analisar:

git status
git diff
git log

para compreender o estado do projeto.

Antes de modificar arquivos, considerar alterações existentes.

29. Alterações existentes

Não sobrescrever alterações que já estavam presentes.

Antes de alterar arquivos:

verificar git status

quando apropriado.

Separar:

alteração da tarefa

de:

alteração pré-existente
30. Git Commit

A IA não deve fazer commit automaticamente sem necessidade.

Quando solicitado, revisar:

git status
git diff

antes do commit.

31. Git Push

O OpenCode não deve executar push automaticamente apenas porque terminou uma tarefa.

Push deve ocorrer somente quando fizer parte explicitamente do fluxo solicitado.

32. Secrets

A IA nunca deve pedir ou criar secrets reais somente para executar uma tarefa.

Utilizar placeholders:

CHANGE_ME
example-token
dummy-secret

quando apropriado.

Nunca colocar credenciais reais no código.

33. Environment

Quando precisar de uma nova variável:

1. adicionar ao código;
2. adicionar ao .env.example;
3. verificar documentação;
4. verificar Docker;
5. verificar testes.

Nunca depender somente do .env pessoal do desenvolvedor.

34. Logs

Ao adicionar logs:

utilizar logging estruturado

Considerar:

request_id
tenant_id
user_id
event

Nunca registrar:

password
JWT
token
secret
API key
35. Exceptions

Erros de negócio devem utilizar exceptions apropriadas.

Evitar:

raise Exception("erro")

quando uma exception específica fizer sentido.

Não colocar HTTPException dentro de regras de negócio sem necessidade.

36. Performance

Não otimizar prematuramente.

Antes de afirmar que algo precisa ser otimizado:

identificar
medir
alterar
medir novamente

Não adicionar cache ou índices somente por hipótese.

37. Segurança de Queries

Queries devem utilizar os mecanismos de parametrização do SQLAlchemy.

Nunca concatenar entrada do usuário em SQL.

Ordenações e filtros dinâmicos devem utilizar valores controlados.

38. AI-generated Code Review

Todo código criado pelo OpenCode deve ser tratado como código comum.

O agente deve verificar:

correção
arquitetura
segurança
multi-tenancy
performance
testes

antes de considerar a tarefa concluída.

39. Não assumir que a IA está correta

A implementação gerada deve ser validada por:

código existente
testes
lint
execução
requisitos
skills

O OpenCode não deve justificar uma decisão simplesmente com:

"essa é a melhor prática"

sem verificar se ela é compatível com o projeto.

40. Explicações da implementação

Quando uma decisão não for óbvia, o agente deve explicar de forma objetiva:

o que foi alterado
por que foi alterado
qual impacto possui

Não produzir explicações longas sobre detalhes irrelevantes.

41. Bloqueios

Se uma tarefa estiver bloqueada por falta de informação essencial:

identificar exatamente o que está faltando

Não inventar:

endpoint
campo
tabela
regra
credential
42. Ambiguidades

Quando existirem múltiplas interpretações plausíveis:

identificar a ambiguidade
consultar código existente
consultar documentação

Utilizar a interpretação mais consistente com o projeto quando houver evidência suficiente.

43. External Information

Não substituir regras do projeto por informações genéricas encontradas na documentação de uma ferramenta.

Exemplo:

FastAPI recomenda X

não significa automaticamente:

projeto deve utilizar X

A decisão deve considerar a arquitetura existente.

44. Código experimental

Código experimental deve ser explicitamente identificado.

Não misturar:

prototype

com:

production implementation

sem validação.

45. Temporary Changes

Alterações temporárias utilizadas para debugging devem ser removidas ou claramente identificadas antes da conclusão.

Exemplos:

debug logs
temporary bypass
temporary mock
hardcoded test value
46. Security Bypass

Nunca criar bypass temporário de segurança e esquecer de removê-lo.

Exemplos:

desabilitar autenticação
ignorar permission
ignorar tenant
aceitar qualquer token
47. API Contract

Antes de alterar um endpoint existente:

verificar consumers
verificar frontend
verificar testes
verificar Integration Hub quando existir
48. Background Jobs

Ao criar ou alterar jobs:

tenant
idempotência
retry
timeout
logs
job_id

devem ser avaliados.

Consultar:

skills/backend/background-jobs.md
49. Integrations

Ao alterar uma integração:

authentication
timeout
retry
idempotency
payload
response
logging
tenant

devem ser avaliados.

Consultar:

skills/backend/integrations.md
50. Migration Safety

Antes de criar migration:

verificar impacto

Especialmente para:

drop
rename
not null
unique
foreign key

Não assumir que uma migration destrutiva é segura somente porque o Alembic a gerou.

51. Data Loss

Alterações que possam causar perda de dados exigem atenção especial.

Exemplos:

DROP COLUMN
DROP TABLE
DELETE
overwrite

Avaliar:

backup
migration strategy
existing data
rollback
52. Rollback

Toda alteração relevante deve possuir uma forma clara de recuperação quando possível.

Para migrations, considerar:

upgrade
downgrade

Para aplicação:

git revert
rollback deployment

conforme a infraestrutura.

53. Reporting

Ao finalizar uma tarefa, o OpenCode deve informar:

Alterações realizadas
Testes executados
Validações executadas
Arquivos alterados
Possíveis pontos pendentes

Exemplo:

Alterado:
backend/app/services/customer.py

Testes:
uv run pytest

Lint:
uv run ruff check .

Resultado:
passou

Pendente:
nenhum.
54. Não declarar sucesso sem validar

O OpenCode não deve afirmar:

"está funcionando"

sem ter evidência suficiente.

Preferir:

"Os testes X e Y passaram."

quando isso for o que realmente foi verificado.

55. Warnings

Warnings não devem ser ocultados somente para produzir saída limpa.

Quando relevante:

identificar
avaliar
documentar
corrigir
56. Scope Report

Quando uma tarefa envolver arquivos adicionais por necessidade técnica, informar:

arquivo
motivo
impacto

Isso torna a expansão de escopo explícita.

57. Documentation Changes

Atualizar documentação quando o comportamento ou arquitetura realmente mudar.

Não modificar toda a documentação para pequenas alterações internas.

58. Task Completion

Uma tarefa é considerada concluída quando:

requisito atendido
+
código implementado
+
testes relevantes executados
+
validações executadas
+
alterações revisadas

quando aplicável.

59. Ordem de decisão

Quando precisar decidir como implementar algo:

1. Requisito da tarefa
2. Segurança
3. Arquitetura existente
4. Padrões das skills
5. Código existente
6. Testes existentes
7. Simplicidade
8. Extensibilidade futura

Não priorizar extensibilidade futura sobre o requisito atual sem necessidade.

60. Regra principal

O OpenCode deve agir como parte do processo de desenvolvimento, não como uma ferramenta que modifica o projeto sem contexto.

Fluxo obrigatório:

Entender
   ↓
Consultar skills
   ↓
Investigar código
   ↓
Planejar
   ↓
Implementar
   ↓
Testar
   ↓
Revisar diff
   ↓
Relatar

A prioridade é:

Correção
+
Segurança
+
Consistência
+
Testabilidade
+
Simplicidade

Toda alteração deve respeitar a arquitetura e as regras existentes do SaaS ERP Platform.