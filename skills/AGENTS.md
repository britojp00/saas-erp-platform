# AGENTS.md

## 1. Objetivo

Este arquivo define as regras gerais para desenvolvimento
assistido por IA no projeto SaaS ERP Platform.

A IA deve utilizar este documento junto com as skills
localizadas em:

```text
skills/

As skills representam os padrões técnicos e arquiteturais
adotados pelo projeto.

2. Regra principal

Antes de modificar qualquer código:

Entender claramente o objetivo da tarefa.
Identificar os arquivos e componentes envolvidos.
Consultar as skills relevantes.
Verificar a implementação existente.
Identificar padrões já utilizados no projeto.
Implementar somente o necessário.
Criar ou atualizar os testes necessários.
Executar as validações de qualidade.
Verificar alterações fora do escopo.
Informar o resultado da alteração.
3. Skills

A pasta:

skills/

contém a documentação oficial dos padrões do projeto.

Antes de implementar uma funcionalidade, consultar as
skills relacionadas à área da alteração.

Skills fundamentais
skills/00-project-overview.md
skills/01-project-structure.md
skills/02-architecture.md
Skills especializadas
skills/backend/
skills/frontend/
skills/database/
skills/infrastructure/
skills/testing/
skills/observability/
skills/security/
skills/development/
skills/tasks/
4. Como escolher as skills

A IA deve identificar quais áreas são afetadas pela tarefa.

Exemplo:

Criar endpoint
    ↓
backend/
testing/
Criar tabela
    ↓
database/
testing/
Alterar autenticação
    ↓
security/
backend/
testing/
Alterar Docker
    ↓
infrastructure/
Alterar logs
    ↓
observability/

Quando uma tarefa envolver várias áreas, consultar todas
as skills relevantes.

5. Verificar antes de criar

Antes de criar um novo arquivo, classe, função ou componente:

procurar uma implementação existente;
verificar se existe um padrão equivalente;
consultar a skill correspondente;
reutilizar a solução existente quando apropriado.

Não criar uma segunda implementação da mesma responsabilidade
sem necessidade.

6. Consistência

A consistência com o código existente é prioridade.

Quando já existir um padrão para determinado problema,
preferir esse padrão em vez de criar uma nova abordagem.

A IA não deve introduzir uma nova arquitetura, padrão ou
convenção apenas por preferência pessoal.

7. Escopo

Implementar somente o que foi solicitado ou o que for
estritamente necessário para concluir a tarefa.

Não:

reestruturar o projeto sem necessidade;
renomear arquivos não relacionados;
alterar funcionalidades não relacionadas;
modificar configurações sem necessidade;
refatorar partes não envolvidas na tarefa;
criar abstrações desnecessárias.

Uma alteração pequena deve continuar sendo uma alteração pequena.

8. Arquitetura

A arquitetura oficial está definida em:

skills/02-architecture.md

A IA deve respeitar a separação das responsabilidades.

Fluxo principal:

Router
   ↓
Schema
   ↓
Service
   ↓
Repository
   ↓
Database

Regras principais:

routers não devem conter regras de negócio complexas;
routers não devem executar SQL diretamente;
schemas não devem acessar o banco;
services devem concentrar regras de negócio;
repositories devem concentrar persistência;
frontend não deve acessar o banco diretamente.
9. Backend

O backend utiliza:

Python 3.13
FastAPI
SQLAlchemy
Alembic
PostgreSQL
Redis
Pytest
Ruff

Localização:

backend/

A estrutura do backend deve seguir:

backend/app/
├── api/
├── core/
├── models/
├── schemas/
├── repositories/
├── services/
└── main.py

Consultar também:

skills/backend/

antes de alterações relacionadas ao backend.

10. Frontend

O frontend será uma aplicação separada.

Localização:

frontend/

Tecnologias planejadas:

React
TypeScript
Vite

O frontend deve consumir a API do backend.

Nunca acessar diretamente:

PostgreSQL
Redis

Consultar:

skills/frontend/

antes de alterações no frontend.

11. Banco de dados

O banco principal é:

PostgreSQL

A aplicação utiliza:

SQLAlchemy
asyncpg
Alembic

Alterações estruturais do banco devem utilizar migrations.

Antes de alterar o banco, consultar:

skills/database/
12. Multi-tenancy

O projeto utiliza arquitetura multi-tenant.

O isolamento entre empresas é requisito obrigatório.

Antes de implementar funcionalidades que trabalhem com
dados de negócio, verificar a skill de multi-tenancy.

Regra geral:

Tenant A
   ↓
somente dados do Tenant A

Tenant B
   ↓
somente dados do Tenant B

A IA nunca deve assumir que um identificador fornecido pelo
cliente é suficiente para autorizar acesso a um recurso.

O contexto do tenant deve ser respeitado nas operações
correspondentes.

13. Segurança

Antes de realizar alterações relacionadas a:

autenticação;
autorização;
JWT;
RBAC;
permissões;
secrets;

consultar:

skills/security/

Nunca colocar no código:

password
JWT
API key
secret
database credentials

Nunca registrar credenciais ou tokens nos logs.

14. Logs e observabilidade

Antes de implementar ou alterar logs, consultar:

skills/observability/

Logs devem ser úteis para investigação.

Quando aplicável, utilizar:

request_id
tenant_id
user_id
event
timestamp
level

Nunca registrar secrets, tokens ou senhas.

15. Testes

Toda nova funcionalidade relevante deve possuir testes
adequados.

Consultar:

skills/testing/

Tipos de testes utilizados:

Unit Tests
API Tests
Integration Tests
Security Tests
Multi-Tenant Tests

Não:

remover testes para contornar erros;
desabilitar testes;
ignorar falhas;
alterar expectativas sem motivo técnico.
16. Validação obrigatória

Quando aplicável, antes de concluir uma tarefa no backend,
executar:

uv run ruff check .
uv run ruff format --check .
uv run pytest

A IA não deve afirmar que os testes passaram sem executá-los.

Da mesma forma, não deve afirmar que uma funcionalidade foi
validada quando não houve validação correspondente.

17. Dependências

Não adicionar bibliotecas automaticamente.

Antes de adicionar uma nova dependência:

verificar se o projeto já possui uma solução equivalente;
verificar se a biblioteca existente pode resolver o problema;
avaliar a necessidade da nova dependência;
verificar compatibilidade com a stack;
adicionar somente quando houver justificativa técnica.
18. Docker

O projeto utiliza Docker para infraestrutura.

Antes de alterar:

Dockerfile
docker-compose.yml
containers
volumes
services

consultar:

skills/infrastructure/

Não adicionar serviços ou infraestrutura sem necessidade.

19. Migrations

Alterações estruturais no banco devem utilizar Alembic.

Fluxo esperado:

Model
   ↓
Migration
   ↓
PostgreSQL

A IA não deve substituir migrations por alterações manuais
no banco como parte do desenvolvimento normal.

20. Documentação

Alterações relevantes devem atualizar a documentação
correspondente quando necessário.

Áreas principais:

docs/architecture/
docs/api/
docs/database/
skills/

Se uma decisão alterar significativamente a arquitetura,
registrar a decisão na documentação apropriada.

21. Refatoração

Refatorações são permitidas quando necessárias para a tarefa.

Entretanto:

não refatorar código não relacionado;
não reestruturar o projeto apenas por preferência;
não alterar múltiplas camadas sem necessidade;
não criar complexidade adicional sem justificativa.
22. Código gerado por IA

Todo código gerado por IA deve seguir os mesmos padrões
do restante do projeto.

O fato de uma implementação ter sido gerada por IA
não altera os requisitos de:

segurança;
testes;
arquitetura;
qualidade;
legibilidade;
manutenção.

A IA deve verificar seu próprio código antes de considerá-lo
concluído.

23. Solução existente

Antes de criar uma nova abstração:

Existe algo semelhante?
        |
        +---- SIM → reutilizar ou adaptar
        |
        +---- NÃO → avaliar nova implementação

Evitar:

helpers genéricos sem necessidade;
abstrações prematuras;
frameworks adicionais;
camadas duplicadas;
código excessivamente genérico.
24. Alterações fora do escopo

Depois da implementação, verificar o diff do Git.

A IA deve identificar alterações não relacionadas
à tarefa solicitada.

Não considerar concluída uma tarefa se alterações
não intencionais tiverem sido introduzidas sem justificativa.

25. Resultado da tarefa

Ao finalizar uma tarefa, informar:

Alterações realizadas
Arquivos alterados
Testes executados
Resultado dos testes
Validações executadas
Possíveis pontos de atenção

Exemplo:

Alterações:
- criado endpoint de clientes;
- criado CustomerService;
- criado CustomerRepository.

Testes:
- pytest: 12 passed

Qualidade:
- ruff check: passed
- ruff format: passed

Não informar como realizado algo que não foi executado.

26. Ordem de decisão

Em caso de dúvida, seguir esta ordem:

1. Código existente
2. AGENTS.md
3. Skills específicas
4. Skills gerais
5. Arquitetura documentada
6. Decisão técnica necessária

Se uma decisão nova for necessária e alterar a arquitetura
existente, documentá-la antes de aplicá-la quando apropriado.

27. Princípio final

O objetivo não é produzir a maior quantidade de código.

O objetivo é produzir código:

simples
+
consistente
+
seguro
+
testável
+
manutenível
+
documentado

A IA deve priorizar a qualidade e a consistência do projeto
em vez de introduzir complexidade desnecessária.


### Onde fica

```text
saas-erp-platform/
└── AGENTS.md