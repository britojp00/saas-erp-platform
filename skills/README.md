# Project Skills

## Objetivo

Este diretório contém as instruções de desenvolvimento do SaaS ERP Platform.

As skills existem para orientar o desenvolvimento humano e o uso de IA, especialmente o OpenCode integrado ao VS Code.

Elas definem:

```text
Arquitetura
Estrutura
Backend
Frontend
Database
Infrastructure
Security
Testing
Observability
Development
Tasks
1. Regra principal

Antes de modificar o projeto, consultar as skills relacionadas à tarefa.

Não é necessário carregar todas as skills para qualquer alteração.

Consultar somente o contexto necessário.

2. Agente de IA

O projeto utiliza:

OpenCode

como agente de IA para desenvolvimento.

O OpenCode deve utilizar este diretório como referência para:

entender arquitetura
localizar responsabilidades
implementar funcionalidades
corrigir problemas
criar testes
alterar banco
alterar infraestrutura
revisar código
3. Arquivo principal de instruções

Antes de qualquer tarefa, consultar:

skills/AGENTS.md

Esse arquivo contém as regras gerais de comportamento do agente no projeto.

As demais skills complementam essas regras.

4. Estrutura

A estrutura atual é:

skills/
├── AGENTS.md
├── README.md
├── 00-project-overview.md
├── 01-project-structure.md
├── 02-architecture.md
│
├── backend/
│   ├── README.md
│   ├── architecture.md
│   ├── api.md
│   ├── database.md
│   ├── authentication.md
│   ├── authorization.md
│   ├── services.md
│   ├── repositories.md
│   ├── schemas.md
│   ├── exceptions.md
│   ├── dependencies.md
│   ├── logging.md
│   ├── testing.md
│   ├── background-jobs.md
│   └── integrations.md
│
├── database/
│   ├── README.md
│   ├── modeling.md
│   ├── multi-tenancy.md
│   ├── migrations.md
│   └── postgresql.md
│
├── development/
│   └── README.md
│
├── frontend/
│   └── README.md
│
├── infrastructure/
│   ├── README.md
│   ├── docker-compose.md
│   ├── docker.md
│   └── environment.md
│
├── observability/
│   └── README.md
│
├── security/
│   └── README.md
│
├── tasks/
│   └── README.md
│
└── testing/
    └── README.md
5. Ordem de consulta geral

Quando o contexto da tarefa não for conhecido:

1. skills/AGENTS.md
2. skills/00-project-overview.md
3. skills/01-project-structure.md
4. skills/02-architecture.md

Depois consultar a skill específica.

6. Project Overview

Consultar:

skills/00-project-overview.md

quando for necessário entender:

objetivo do projeto
stack
visão geral
multi-tenancy
arquitetura conceitual
roadmap
princípios
7. Project Structure

Consultar:

skills/01-project-structure.md

quando for necessário decidir:

onde criar arquivo
onde colocar módulo
responsabilidade de diretórios
estrutura do monorepo
8. Architecture

Consultar:

skills/02-architecture.md

quando a tarefa envolver:

arquitetura
dependências entre camadas
fluxo de dados
separação frontend/backend
multi-tenancy
decisões estruturais
9. Backend

Para qualquer tarefa específica do backend, começar por:

skills/backend/README.md

Depois consultar conforme a tarefa.

Arquitetura
skills/backend/architecture.md
API
skills/backend/api.md
Banco
skills/backend/database.md
Autenticação
skills/backend/authentication.md
Autorização
skills/backend/authorization.md
Services
skills/backend/services.md
Repositories
skills/backend/repositories.md
Schemas
skills/backend/schemas.md
Exceptions
skills/backend/exceptions.md
Dependencies
skills/backend/dependencies.md
Logging
skills/backend/logging.md
Testes
skills/backend/testing.md
Background Jobs
skills/backend/background-jobs.md
Integrações
skills/backend/integrations.md
10. Database

Para alterações de banco:

skills/database/

Consultar principalmente:

skills/database/README.md
skills/database/modeling.md
skills/database/multi-tenancy.md
skills/database/migrations.md
skills/database/postgresql.md
11. Infrastructure

Para Docker, Compose ou ambiente:

skills/infrastructure/
Geral
skills/infrastructure/README.md
Docker Compose
skills/infrastructure/docker-compose.md
Dockerfile
skills/infrastructure/docker.md
Environment
skills/infrastructure/environment.md
12. Security

Para qualquer alteração relacionada à segurança:

skills/security/README.md

Consultar também as skills específicas relacionadas ao componente alterado.

Exemplo:

Authentication
+
Authorization
+
Multi-tenancy
13. Testing

Para estratégia geral de testes:

skills/testing/README.md

Para implementação de testes de backend:

skills/backend/testing.md

Quando ambos forem relevantes, a skill específica do backend complementa a geral.

14. Observability

Para:

logs
metrics
tracing
audit
health checks
monitoring
alerts

consultar:

skills/observability/README.md

Para logging especificamente no backend:

skills/backend/logging.md
15. Frontend

Para alterações no React/TypeScript:

skills/frontend/README.md

Quando a alteração envolver API:

skills/frontend/README.md
+
skills/backend/api.md

Quando envolver autenticação:

skills/frontend/README.md
+
skills/backend/authentication.md
+
skills/security/README.md
16. Development

Para fluxo de desenvolvimento:

skills/development/README.md

Consultar quando a tarefa envolver:

Git
branches
commits
pull requests
dependências
refatoração
processo de desenvolvimento
AI-assisted development
17. Tasks

Para entender como uma tarefa deve ser executada pelo agente:

skills/tasks/README.md

Essa skill define:

investigação
planejamento
escopo
implementação
validação
report
uso do OpenCode
18. Consulta mínima

Sempre que possível, utilizar a menor quantidade de documentação necessária.

Exemplo:

Alterar Dockerfile

Consultar:

skills/AGENTS.md
skills/01-project-structure.md
skills/infrastructure/docker.md

Não é necessário carregar todas as skills de backend.

19. Consulta cruzada

Algumas tarefas atravessam mais de uma área.

Exemplo:

Adicionar autenticação

Consultar:

skills/backend/authentication.md
skills/backend/authorization.md
skills/backend/dependencies.md
skills/security/README.md
skills/backend/testing.md

Outro exemplo:

Criar sincronização externa

Consultar:

skills/backend/integrations.md
skills/backend/background-jobs.md
skills/backend/logging.md
skills/security/README.md
skills/database/multi-tenancy.md
20. Prioridade das Skills

As skills mais específicas possuem prioridade contextual.

Exemplo:

skills/security/README.md

define princípios gerais de segurança.

Já:

skills/backend/authentication.md

define como esses princípios devem ser aplicados à autenticação do backend.

Portanto:

Regra geral
↓
Regra específica
21. Não duplicar regras

Evitar criar a mesma regra em muitos arquivos sem necessidade.

As skills devem:

definir princípios gerais
+
detalhar aplicação específica

Quando uma regra já estiver definida em uma skill mais apropriada, referenciá-la em vez de duplicar grandes blocos.

22. Atualização das Skills

As skills devem evoluir junto com o projeto.

Atualizar quando houver mudança real em:

arquitetura
stack
estrutura
segurança
infraestrutura
processo

Não alterar documentação apenas para refletir pequenas mudanças internas sem impacto arquitetural.

23. Código como fonte de contexto

As skills não substituem a análise do código existente.

O agente deve considerar:

skills
+
código
+
testes
+
configuração

antes de tomar decisões.

Uma skill descreve o padrão esperado.

O código mostra o estado atual.

24. Divergência entre Skill e Código

Se a documentação indicar uma arquitetura diferente do código atual:

não corrigir automaticamente tudo

Primeiro:

identificar divergência
avaliar impacto

Depois determinar se a tarefa atual realmente exige a correção.

Não transformar uma feature pequena em uma migração arquitetural sem necessidade.

25. Divergência entre Skills

Quando duas skills aparentemente entrarem em conflito:

1. verificar se uma é geral e outra específica;
2. verificar o contexto da tarefa;
3. consultar AGENTS.md;
4. analisar o código existente;
5. escolher a interpretação mais consistente.

Não ignorar o conflito silenciosamente.

26. Novas Skills

Não criar novos arquivos de skill automaticamente.

Criar uma nova skill somente quando existir:

responsabilidade claramente separada
+
necessidade recorrente
+
conteúdo suficiente para justificar o arquivo

Evitar fragmentar excessivamente a documentação.

27. Manutenção

Quando uma skill deixar de representar a arquitetura real:

atualizar

em vez de criar outra skill contraditória.

Evitar acumular documentação obsoleta.

28. AI Context Efficiency

As skills devem ser utilizadas também para reduzir o contexto enviado ao OpenCode.

Em uma tarefa específica:

carregar contexto relevante

em vez de:

carregar todo o projeto

Isso melhora:

clareza
velocidade
precisão
29. Task Context

O contexto fornecido ao OpenCode deve preferencialmente indicar:

Problema
Arquivo
Classe
Método
Comportamento atual
Comportamento esperado
Restrições

Consultar:

skills/tasks/README.md

para o fluxo detalhado.

30. Segurança do Contexto

Nunca inserir secrets reais no contexto fornecido à IA.

Evitar incluir:

passwords
API keys
JWT secrets
private keys
production credentials

Utilizar placeholders quando necessário.

31. Resultado esperado da IA

Ao concluir uma tarefa, o agente deve informar:

Arquivos alterados
O que foi alterado
Testes executados
Validações executadas
Problemas encontrados
Pendências

Não afirmar que uma alteração foi validada sem executar a validação correspondente.

32. Ordem recomendada por área
Backend
AGENTS
↓
Project Overview
↓
Project Structure
↓
Architecture
↓
Backend README
↓
Skill específica
Database
AGENTS
↓
Project Overview
↓
Project Structure
↓
Architecture
↓
Database README
↓
Skill específica
Frontend
AGENTS
↓
Project Overview
↓
Project Structure
↓
Architecture
↓
Frontend README
Infrastructure
AGENTS
↓
Project Overview
↓
Project Structure
↓
Infrastructure README
↓
Skill específica
33. Desenvolvimento de funcionalidades

Uma funcionalidade normalmente deve seguir:

Requisito
↓
Skills relevantes
↓
Código existente
↓
Planejamento
↓
Implementação
↓
Testes
↓
Validação
↓
Review
34. Regra para IA

O OpenCode deve evitar:

alterações amplas
refatorações não solicitadas
dependências desnecessárias
arquitetura prematura
bypasses de segurança
alterações destrutivas

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
35. Regra principal

As skills devem funcionar como o manual técnico do projeto.

A relação deve ser:

AGENTS.md
    ↓
Regras gerais do agente

README.md
    ↓
Mapa das skills

Project Skills
    ↓
Regras por área

Código
    ↓
Implementação real

Testes
    ↓
Comportamento verificado

O objetivo é permitir que qualquer desenvolvedor ou agente de IA compreenda rapidamente:

como o projeto funciona
onde cada responsabilidade pertence
como implementar uma mudança
como validar a mudança

sem depender de conhecimento implícito.