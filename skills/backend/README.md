# Backend

## Objetivo

Definir as regras gerais para desenvolvimento, manutenção e evolução do backend do SaaS ERP Platform.

O backend é responsável pela API, regras de negócio, persistência, autenticação, autorização, integrações e processamento das operações do sistema.

---

# 1. Stack

O backend utiliza:

- Python 3.13
- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL
- Redis
- Pydantic
- PyJWT
- pwdlib
- Uvicorn
- Pytest
- pytest-asyncio
- HTTPX
- Coverage
- Ruff
- uv

A aplicação deve permanecer compatível com a versão de Python definida pelo projeto.

---

# 2. Estrutura

O backend segue a estrutura:

```text
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   ├── core/
│   ├── models/
│   ├── schemas/
│   ├── repositories/
│   ├── services/
│   └── main.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── api/
├── migrations/
├── .python-version
├── pyproject.toml
└── uv.lock

Cada camada possui uma responsabilidade específica.

Não colocar lógica de negócio aleatoriamente em qualquer arquivo somente para resolver rapidamente uma tarefa.

3. Arquitetura

O fluxo principal esperado é:

Router
   ↓
Schema
   ↓
Service
   ↓
Repository
   ↓
SQLAlchemy
   ↓
PostgreSQL

Cada camada deve possuir uma responsabilidade clara.

Router

Responsável por:

receber requisições HTTP;
validar entrada através dos schemas;
resolver dependências;
chamar services;
retornar respostas HTTP.

O router não deve concentrar regras complexas de negócio.

Schema

Responsável por:

validação de entrada;
representação dos dados da API;
validação de saída;
contratos HTTP.

Schemas não devem executar operações de banco de dados.

Service

Responsável pela lógica de negócio.

Exemplos:

validar regras de negócio;
coordenar operações;
controlar fluxos;
executar transações quando necessário;
chamar repositories;
coordenar integrações e outros serviços.
Repository

Responsável pelo acesso aos dados.

Exemplos:

consultas;
inserções;
atualizações;
exclusões;
filtros;
paginação.

Regras de negócio devem permanecer nos services sempre que possível.

4. Modelos

Os models representam entidades persistidas no PostgreSQL.

Os padrões de modelagem devem seguir:

skills/database/modeling.md
skills/database/postgresql.md
skills/database/multi-tenancy.md

Regras importantes:

UUID para identificadores;
foreign keys reais;
tenant_id quando aplicável;
timestamps timezone-aware;
created_at;
updated_at;
deleted_at para entidades de negócio;
valores monetários com NUMERIC;
constraints e índices apropriados.

Não criar estruturas diferentes sem justificativa técnica.

5. Multi-tenancy

O backend utiliza:

Database compartilhado
Schema compartilhado
tenant_id nas entidades pertencentes ao tenant

Toda operação envolvendo dados de tenant deve respeitar o contexto autenticado.

O tenant_id não deve ser tratado como informação confiável simplesmente porque veio da requisição HTTP.

O contexto do tenant deve ser determinado a partir da identidade autenticada e das regras de autorização.

Nunca permitir acesso de um tenant aos dados de outro tenant.

Essa regra deve ser validada também por testes.

6. Autenticação

A autenticação utilizará tokens JWT.

Responsabilidades:

Authentication
    ↓
Identity
    ↓
Authorization
    ↓
Business operation

O backend deve distinguir:

autenticação;
autorização;
permissões;
contexto do tenant.

Não considerar apenas a existência de um usuário autenticado como autorização suficiente para qualquer operação.

7. RBAC

O sistema utilizará controle de acesso baseado em:

User
Role
Permission

Permissões devem representar ações do sistema.

Exemplos conceituais:

customer.read
customer.create
customer.update
customer.delete

As verificações de autorização devem ocorrer em local consistente da aplicação e não serem duplicadas arbitrariamente em cada endpoint.

8. Banco de dados

O acesso ao PostgreSQL deve utilizar SQLAlchemy.

As alterações estruturais do banco devem ser realizadas através do Alembic.

Fluxo esperado:

Model
   ↓
Migration
   ↓
Review
   ↓
Apply
   ↓
Test

Não alterar a estrutura do banco manualmente como fluxo normal de desenvolvimento.

Consultar:

skills/database/README.md
skills/database/migrations.md

antes de alterações relacionadas ao banco.

9. Transações

Operações que alteram múltiplos registros relacionados devem possuir controle transacional adequado.

Exemplo:

Criar pedido
   ↓
Criar itens
   ↓
Atualizar estoque

Essas operações não devem resultar em estado parcialmente persistido quando uma etapa obrigatória falhar.

A estratégia de transação deve permanecer clara e previsível.

10. Async

O backend utiliza FastAPI e componentes assíncronos quando apropriado.

Operações de I/O que utilizam bibliotecas assíncronas devem respeitar o modelo async do projeto.

Não misturar operações bloqueantes em endpoints assíncronos sem uma justificativa técnica.

Quando uma biblioteca síncrona for necessária, avaliar corretamente seu impacto.

11. Redis

Redis poderá ser utilizado para:

cache;
sessões ou dados temporários;
rate limiting;
filas;
coordenação de workers;
outras necessidades de infraestrutura.

Redis não deve ser tratado como substituto do PostgreSQL para dados persistentes de negócio.

A estratégia de cache deve considerar:

tenant;
invalidação;
expiração;
consistência;
isolamento.
12. Background Jobs

Operações demoradas ou que não precisam bloquear a resposta HTTP poderão utilizar workers.

Exemplos:

processamento de integrações;
tarefas de sincronização;
envio de notificações;
processamento em massa;
rotinas assíncronas.

O processamento deve ser projetado considerando:

retry;
idempotência;
falhas;
observabilidade;
isolamento por tenant.
13. API

A API deve ser organizada por versão.

Estrutura esperada:

app/api/v1/

Os endpoints devem:

possuir nomes consistentes;
utilizar métodos HTTP apropriados;
validar entradas;
retornar status HTTP corretos;
utilizar schemas;
respeitar autenticação e autorização;
não expor detalhes internos desnecessários.

A API deve ser pensada como contrato consumido pelo frontend e por futuras integrações externas.

14. Tratamento de erros

Erros devem possuir comportamento previsível.

Diferenciar:

Erro de validação
Erro de autenticação
Erro de autorização
Recurso não encontrado
Conflito de negócio
Erro interno

Não retornar stack traces ou informações internas para o cliente em produção.

Erros inesperados devem ser registrados nos logs apropriados.

15. Logging

O backend deve utilizar logs estruturados.

Quando relevante, registrar:

request_id
tenant_id
user_id
event
level
timestamp

Nunca registrar:

senhas;
tokens;
secrets;
credenciais;
dados sensíveis desnecessários.

Logs técnicos e auditoria de ações de negócio são conceitos diferentes.

A auditoria deve utilizar estrutura própria quando necessária.

Consultar:

skills/observability/README.md
16. Testes

Toda funcionalidade relevante deve possuir testes apropriados.

Tipos principais:

tests/unit/
tests/integration/
tests/api/

Os testes devem cobrir principalmente:

regras de negócio;
endpoints;
validações;
autenticação;
autorização;
multi-tenancy;
persistência;
integrações;
cenários de erro.

Casos de segurança e isolamento entre tenants são obrigatórios quando a funcionalidade tocar dados multi-tenant.

17. Segurança

Toda implementação do backend deve considerar:

autenticação;
autorização;
isolamento de tenant;
validação de entrada;
proteção contra acesso indevido;
armazenamento seguro de credenciais;
secrets fora do código;
logs sem informações sensíveis;
respostas sem exposição de detalhes internos.

Nunca confiar exclusivamente em dados fornecidos pelo cliente.

18. Dependências

Novas dependências somente devem ser adicionadas quando existir necessidade real.

Antes de adicionar uma biblioteca:

verificar se o projeto já possui solução equivalente;
avaliar manutenção e compatibilidade;
avaliar impacto na arquitetura;
verificar necessidade de configuração adicional;
atualizar pyproject.toml;
atualizar uv.lock;
executar os testes.

Evitar dependências utilizadas apenas para resolver problemas simples que podem ser tratados pela stack existente.

19. Qualidade de código

O código deve seguir:

tipagem quando apropriado;
nomes claros;
funções com responsabilidade definida;
baixo acoplamento;
tratamento explícito de erros;
baixa duplicação;
formatação consistente.

Ferramentas principais:

Ruff
Pytest
Coverage

Antes de concluir uma alteração relevante, executar as verificações apropriadas.

20. Desenvolvimento

Comandos principais:

cd backend
uv sync

Executar API:

uv run uvicorn app.main:app --reload

Executar testes:

uv run pytest

Verificar lint:

uv run ruff check .

Formatar:

uv run ruff format .

Verificar formatação:

uv run ruff format --check .

As ferramentas devem ser executadas através do ambiente gerenciado pelo uv.

21. Alterações de código

Antes de modificar uma implementação:

localizar o arquivo correto;
entender a responsabilidade da camada;
verificar código relacionado;
consultar as skills relevantes;
identificar testes existentes;
implementar a menor mudança necessária;
executar validações.

Não criar abstrações genéricas sem necessidade real.

Não alterar partes não relacionadas à tarefa.

22. Novos módulos

Ao criar um novo módulo:

definir claramente sua responsabilidade;
colocá-lo na camada correta;
verificar necessidade de schema;
verificar necessidade de service;
verificar necessidade de repository;
criar testes;
considerar multi-tenancy;
considerar autorização;
documentar quando necessário.

A existência de uma entidade ou endpoint não significa automaticamente que todas as camadas precisam possuir lógica própria.

A arquitetura deve permanecer simples.

23. Integrações externas

Integrações externas devem ser isoladas da regra central do ERP sempre que possível.

Devem considerar:

autenticação;
timeout;
retry;
idempotência;
tratamento de erros;
logs;
rastreabilidade;
transformação de payload;
tenant;
limites da API externa.

Esses princípios serão importantes posteriormente no projeto Integration Hub.

24. Compatibilidade com o frontend

O backend fornece a API consumida pelo frontend.

O frontend não deve acessar diretamente:

PostgreSQL
Redis
SQLAlchemy
Repositories

A comunicação deve ocorrer através da API HTTP.

Alterações nos contratos da API devem considerar o impacto sobre os consumidores.

25. Documentação

A documentação da API deve permanecer coerente com a implementação.

FastAPI gera documentação OpenAPI automaticamente.

Quando houver comportamento importante que não seja evidente pelo contrato HTTP, documentar a regra de forma apropriada.

26. Ordem de consulta

Para tarefas de backend, consultar:

skills/00-project-overview.md
skills/01-project-structure.md
skills/02-architecture.md
skills/backend/README.md

Depois consultar as skills específicas da área:

skills/database/
skills/security/
skills/testing/
skills/observability/
skills/infrastructure/
skills/development/
skills/tasks/

Não carregar todas as skills desnecessariamente quando somente uma área estiver envolvida.

27. Regra principal

O backend deve evoluir de forma:

Consistente
Previsível
Testável
Segura
Multi-tenant
Observável

A prioridade é manter uma arquitetura compreensível e sustentável, evitando complexidade prematura.