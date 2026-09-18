# Database Skills

## Objetivo

Esta pasta contém os padrões, regras e procedimentos relacionados
ao banco de dados do SaaS ERP Platform.

As definições desta área devem ser utilizadas sempre que uma
tarefa envolver:

- banco de dados;
- tabelas;
- colunas;
- relacionamentos;
- índices;
- constraints;
- consultas;
- SQLAlchemy;
- Alembic;
- migrations;
- transações;
- multi-tenancy;
- persistência de dados.

---

# 1. Banco principal

O banco de dados principal do projeto será:

```text
PostgreSQL

A aplicação utilizará:

SQLAlchemy
asyncpg
Alembic

O PostgreSQL será executado através da infraestrutura
definida pelo projeto.

2. Responsabilidade do banco

O banco de dados será responsável pela persistência dos dados
do sistema.

O PostgreSQL será a fonte principal dos dados transacionais
do ERP.

Redis não substitui o PostgreSQL como armazenamento principal
das informações de negócio.

3. Organização das skills

As regras específicas serão organizadas em arquivos separados.

skills/database/
│
├── README.md
├── postgresql.md
├── modeling.md
├── migrations.md
└── multi-tenancy.md
postgresql.md

Define padrões específicos relacionados ao PostgreSQL.

Exemplos:

tipos de dados;
uso de UUID ou IDs numéricos;
constraints;
índices;
recursos específicos do PostgreSQL;
consultas;
convenções relacionadas ao banco.
modeling.md

Define regras para modelagem das entidades.

Exemplos:

nomenclatura de tabelas;
nomenclatura de colunas;
primary keys;
foreign keys;
relacionamentos;
timestamps;
campos obrigatórios;
campos opcionais;
índices;
unique constraints.
migrations.md

Define como alterações estruturais do banco devem ser feitas.

A ferramenta utilizada será:

Alembic

Toda alteração estrutural deve possuir migration correspondente.

multi-tenancy.md

Define como o isolamento de dados entre tenants será
implementado no banco e na aplicação.

Esta será uma skill crítica do projeto.

Ela deverá definir:

quais entidades possuem tenant;
uso de tenant_id;
isolamento;
consultas;
relacionamentos;
índices;
constraints;
testes de isolamento.
4. Regra geral de modelagem

Antes de criar uma nova tabela:

verificar se a entidade já existe;
verificar relacionamentos existentes;
consultar a skill de modelagem;
consultar a skill de multi-tenancy quando aplicável;
definir constraints necessárias;
definir índices necessários;
definir a migration correspondente.

Não criar tabelas duplicadas para representar a mesma entidade.

5. Integridade dos dados

Sempre que uma regra puder ser garantida pelo banco de dados,
avaliar a utilização de:

primary keys;
foreign keys;
unique constraints;
check constraints;
not null;
índices apropriados.

A integridade dos dados não deve depender exclusivamente
da validação realizada pela aplicação quando uma garantia
no banco for apropriada.

6. Multi-tenancy

O projeto utiliza arquitetura multi-tenant.

Dados pertencentes a uma empresa devem ser associados
ao tenant correspondente quando aplicável.

Conceito:

Tenant
   |
   +---- Users
   +---- Customers
   +---- Products
   +---- Orders
   +---- Inventory

Entidades de negócio que pertencem a um tenant devem seguir
as regras definidas em:

skills/database/multi-tenancy.md

O isolamento entre tenants é requisito obrigatório.

7. SQLAlchemy

A aplicação utilizará SQLAlchemy como camada ORM.

Os models ficam em:

backend/app/models/

Os repositories ficam em:

backend/app/repositories/

A organização deve respeitar a arquitetura definida em:

skills/02-architecture.md

Acesso ao banco não deve ser implementado diretamente
nos routers quando a operação deveria passar pela camada
de persistência apropriada.

8. Migrations

Alterações estruturais do banco devem utilizar Alembic.

Fluxo:

Model
   |
   v
Migration
   |
   v
PostgreSQL

Não utilizar alterações manuais no banco como substituição
do fluxo normal de migrations.

Antes de criar ou alterar migrations, consultar:

skills/database/migrations.md
9. Alterações no banco

Quando uma tarefa modificar a estrutura do banco, verificar:

Model
Migration
Foreign Keys
Indexes
Constraints
Multi-tenancy
Tests

Não alterar somente o model e esquecer a migration.

Não criar migration sem verificar se a alteração do model
corresponde ao schema esperado.

10. Consultas

Consultas devem considerar:

desempenho;
índices;
relacionamentos;
integridade;
contexto do tenant;
necessidade de paginação;
quantidade de dados retornados.

Consultas não devem buscar dados desnecessários
quando a operação não precisar deles.

11. Transações

Operações que dependem de múltiplas alterações relacionadas
devem avaliar a necessidade de uma transação.

Exemplo:

Criar pedido
    |
    +---- criar Order
    |
    +---- criar OrderItem
    |
    +---- atualizar Inventory

Essas operações devem permanecer consistentes.

Se uma etapa crítica falhar, as alterações relacionadas
devem ser revertidas quando a operação exigir atomicidade.

12. Índices

Índices devem ser criados com base em necessidades reais.

Avaliar índices para:

foreign keys;
campos utilizados frequentemente em filtros;
campos utilizados em buscas;
campos utilizados em ordenação;
combinações de colunas utilizadas frequentemente.

Não criar índices indiscriminadamente.

Cada índice possui custo de armazenamento e manutenção.

13. Constraints

Quando apropriado, utilizar constraints para garantir
integridade dos dados.

Exemplos:

PRIMARY KEY
FOREIGN KEY
UNIQUE
NOT NULL
CHECK

Regras críticas de integridade devem ser avaliadas
tanto no nível da aplicação quanto no banco de dados.

14. Dados sensíveis

Não armazenar secrets diretamente no schema do banco
sem uma necessidade específica.

Não registrar em logs valores sensíveis desnecessariamente.

Exemplos de informações que exigem atenção:

password
tokens
API keys
credenciais
secrets
15. Testes relacionados ao banco

Alterações no banco devem ser acompanhadas pelos testes
adequados.

Quando aplicável:

Unit Tests
Integration Tests
API Tests
Multi-Tenant Tests

Alterações de multi-tenancy devem possuir testes que
demonstrem o isolamento entre tenants.

Exemplo:

Tenant A
   |
   +---- acessa próprios dados
   |
   +---- não acessa dados do Tenant B
16. Ambiente

O PostgreSQL não deve ser tratado como uma instalação manual
obrigatória no computador do desenvolvedor.

O ambiente do projeto será executado através da infraestrutura
definida em:

skills/infrastructure/

A configuração de conexão deve utilizar variáveis de ambiente.

17. Documentação

Alterações relevantes na estrutura do banco devem ser
documentadas quando necessário.

Documentação relacionada ao banco pode ser mantida em:

docs/database/

As decisões e padrões devem permanecer sincronizados
com as skills desta pasta.

18. Ordem de consulta

Quando uma tarefa envolver banco:

1. skills/00-project-overview.md
2. skills/01-project-structure.md
3. skills/02-architecture.md
4. skills/database/README.md
5. skill específica da tarefa

Exemplo:

Criar tabela
    |
    +---- modeling.md
    +---- multi-tenancy.md
    +---- migrations.md
19. Regra para novas tabelas

Antes de criar uma nova tabela, responder:

Qual entidade ela representa?

Quem é o proprietário dos dados?

Ela pertence a um tenant?

Quais relacionamentos possui?

Quais constraints são necessárias?

Quais índices são necessários?

Como será criada através do Alembic?

Como será testada?

Não criar uma tabela apenas para armazenar dados
sem definir claramente sua responsabilidade.

20. Regra para alterações

Antes de alterar uma tabela existente:

verificar código que utiliza a tabela;
verificar relacionamentos;
verificar migrations existentes;
verificar índices;
verificar constraints;
verificar impacto no multi-tenancy;
verificar testes;
criar ou atualizar a migration;
validar a alteração.
21. Princípio final

O banco de dados deve priorizar:

integridade
+
consistência
+
segurança
+
desempenho
+
manutenibilidade

As decisões específicas devem ser documentadas nas
skills correspondentes em vez de concentrar todas as
regras em um único arquivo.


## Onde fica

```text
C:\Users\joao\Projetos\saas-erp-platform\skills\database\README.md