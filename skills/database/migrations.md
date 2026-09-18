# Database Migrations

## Objetivo

Este documento define as regras oficiais para criação,
alteração, revisão e execução de migrations do banco de
dados do SaaS ERP Platform.

O projeto utiliza:

```text
Alembic

para controlar a evolução do schema do PostgreSQL.

Toda alteração estrutural do banco deve ser rastreável
através de uma migration.

1. Princípio

O banco de dados deve evoluir através de migrations
versionadas.

Fluxo:

Model / Schema Change
        |
        v
Alembic Migration
        |
        v
PostgreSQL

Não utilizar alterações manuais no banco como substituição
do fluxo normal de migrations.

2. Localização

As migrations do backend ficam em:

backend/migrations/

A configuração do Alembic ficará associada ao backend.

3. Responsabilidade

Uma migration representa uma alteração estrutural
específica no banco.

Exemplos:

criar tabela
adicionar coluna
remover coluna
alterar tipo
criar índice
remover índice
criar constraint
remover constraint
criar relacionamento
alterar relacionamento
4. Antes de criar uma migration

Antes de gerar uma migration:

entender a alteração;
verificar o model atual;
verificar o estado atual do banco;
verificar migrations anteriores;
verificar relacionamentos;
verificar índices;
verificar constraints;
verificar impacto no multi-tenancy;
verificar impacto no soft delete;
verificar testes relacionados.

Não gerar uma migration automaticamente sem revisar
o resultado.

5. Model primeiro

Quando uma alteração representar uma mudança permanente
na estrutura da entidade, o model SQLAlchemy deve ser
atualizado de forma coerente com o banco.

Fluxo esperado:

Alterar Model
      |
      v
Gerar Migration
      |
      v
Revisar Migration
      |
      v
Testar Migration
      |
      v
Aplicar Migration

Não considerar concluída uma alteração estrutural
somente porque o model foi modificado.

6. Autogenerate

O Alembic pode ser utilizado para gerar migrations
automaticamente através da comparação entre o metadata
da aplicação e o schema do banco.

Exemplo:

alembic revision --autogenerate -m "create customers table"

A migration gerada deve ser sempre revisada manualmente.

Nunca assumir que o autogenerate capturou corretamente
toda a intenção da alteração.

7. Revisão da migration

Depois de gerar uma migration, verificar:

Tabela
Coluna
Tipo
Nullable
Default
Primary Key
Foreign Key
Unique
Check
Index

Também verificar:

tenant_id
created_at
updated_at
deleted_at

quando aplicável.

8. Nome da migration

As mensagens das migrations devem ser claras e descrever
a alteração realizada.

Exemplos:

create tenants table
create users table
add tenant_id to customers
create orders table
add order status constraint
create customer email index

Evitar mensagens genéricas como:

update
changes
fix
migration
test
stuff
9. Uma alteração por migration

Preferir migrations focadas em uma alteração lógica.

Exemplo:

add products table

em vez de uma migration que cria simultaneamente
dezenas de entidades sem necessidade.

Alterações que fazem parte da mesma mudança lógica
podem permanecer na mesma migration.

10. Ordem das migrations

Migrations possuem ordem de execução.

Uma migration deve respeitar as dependências das estruturas
que utiliza.

Exemplo:

tenants
   |
   v
users
   |
   v
customers
   |
   v
orders

Uma tabela que possui foreign key para outra tabela
não deve ser criada antes da existência da tabela referenciada.

11. Foreign Keys

Ao adicionar uma foreign key:

verificar se a tabela referenciada existe;
verificar se os dados existentes são compatíveis;
criar a constraint apropriada;
verificar estratégia de exclusão;
validar o relacionamento.

Não adicionar uma foreign key sem considerar
os dados existentes.

12. Multi-tenancy

Alterações em entidades multi-tenant devem verificar:

tenant_id
Foreign Key
Indexes
Unique Constraints
Queries
Existing Data

Exemplo:

Adicionar tenant_id em customers

não deve ser tratado apenas como:

ALTER TABLE customers
ADD COLUMN tenant_id ...

É necessário considerar:

dados existentes
nullable
preenchimento inicial
foreign key
index
constraints

A estratégia concreta depende da situação da tabela.

Consultar:

skills/database/multi-tenancy.md
13. Adding a required column

Adicionar uma coluna NOT NULL em uma tabela
que já possui dados exige cuidado.

Exemplo conceitual:

customers

já possui registros.

Adicionar:

tenant_id NOT NULL

sem definir como os registros existentes receberão
um tenant pode quebrar a migration.

A alteração deve possuir uma estratégia explícita
para os dados existentes.

14. Defaults

Não adicionar DEFAULT automaticamente.

Antes de definir um default, avaliar:

regra de negócio;
dados existentes;
comportamento de novos registros;
necessidade de manter o default após a migration.

O default deve existir quando representar uma regra real.

15. Remoção de coluna

Remover uma coluna é uma alteração potencialmente destrutiva.

Antes de remover:

verificar uso no backend;
verificar uso no frontend;
verificar queries;
verificar repositories;
verificar serviços;
verificar integrações;
verificar migrations dependentes;
verificar necessidade de preservação dos dados.

Não remover uma coluna somente porque ela deixou
de ser utilizada em um único arquivo.

16. Remoção de tabela

A remoção de tabela é uma operação destrutiva.

Antes de remover:

Verificar referências
Verificar Foreign Keys
Verificar código
Verificar dados
Verificar integrações
Verificar histórico

A operação deve possuir justificativa clara.

17. Alteração de tipo

Alterações de tipo devem considerar os dados
já existentes.

Exemplo:

VARCHAR
   ↓
INTEGER

pode falhar se existirem valores incompatíveis.

Uma migration desse tipo deve considerar:

conversão
validação
dados inválidos
rollback
18. Índices

Ao criar ou remover índices, avaliar:

consultas existentes;
volume de dados;
frequência da operação;
filtros;
ordenação;
impacto em INSERT/UPDATE/DELETE.

Não criar índices automaticamente para todas as colunas.

19. Unique Constraints

Ao criar uma constraint UNIQUE, verificar se os dados
existentes já atendem à regra.

Exemplo:

UNIQUE (
    tenant_id,
    sku
)

Antes de aplicar, verificar se existem registros duplicados
dentro do mesmo tenant.

20. Soft Delete

Entidades de negócio utilizam:

deleted_at

como padrão de exclusão lógica.

Uma migration que adicionar deleted_at deve definir
adequadamente:

tipo
nullable
default

O comportamento esperado é:

NULL
→ ativo

data preenchida
→ excluído logicamente

A migration não deve transformar automaticamente
registros existentes em excluídos sem uma regra de negócio
explícita.

21. Timestamps

Entidades de negócio normalmente possuem:

created_at
updated_at
deleted_at

Timestamps devem ser compatíveis com o padrão
definido em:

skills/database/modeling.md

O armazenamento deve considerar timezone e UTC.

22. Dados existentes

Migrations devem considerar se a tabela já contém dados.

Existem dois cenários:

Banco vazio

e:

Banco com dados

Uma migration válida deve considerar ambos quando
a estrutura puder ser aplicada em ambientes existentes.

23. Data migrations

Quando uma alteração estrutural exigir transformação
dos dados existentes, a migration pode precisar realizar
uma operação de dados.

Exemplo:

preencher novo campo
normalizar valores
migrar informação

Essas operações devem ser:

determinísticas;
seguras;
justificadas;
revisadas;
testadas quando possível.
24. Separar schema change e data change

Quando uma alteração de dados for complexa, considerar
separar em migrations diferentes.

Exemplo:

Migration 1
Adicionar nova coluna

Migration 2
Migrar dados

Migration 3
Tornar coluna NOT NULL

Essa abordagem pode ser necessária para manter
compatibilidade durante uma transição.

25. Downgrade

Cada migration deve possuir uma estratégia de downgrade
quando isso for tecnicamente possível e seguro.

Exemplo:

upgrade
→ cria tabela

downgrade
→ remove tabela

Para alterações destrutivas, o downgrade pode exigir
cuidados adicionais.

Nunca assumir que um downgrade pode recuperar dados
que foram fisicamente removidos.

26. Migrations destrutivas

São consideradas potencialmente destrutivas:

DROP TABLE
DROP COLUMN
ALTER TYPE
remoção de constraint essencial

Essas alterações devem ser revisadas com atenção.

Quando houver risco de perda de dados, documentar
claramente a operação.

27. Ordem de execução

Antes de aplicar migrations:

1. Verificar migration atual
2. Verificar banco
3. Verificar dependências
4. Executar testes
5. Aplicar migration
6. Validar schema
7. Executar testes novamente quando necessário
28. Verificação

Após aplicar uma migration, verificar:

Tabela existe?
Colunas corretas?
Tipos corretos?
Nullable correto?
Foreign Keys corretas?
Indexes presentes?
Constraints presentes?

Também verificar se a aplicação continua funcionando.

29. Desenvolvimento local

Durante desenvolvimento local, o banco será executado
conforme a infraestrutura definida em:

skills/infrastructure/

As migrations devem poder ser executadas
de maneira reproduzível no ambiente do projeto.

30. Git

Migrations devem ser versionadas no Git.

Não adicionar migrations ao .gitignore.

Exemplo:

backend/migrations/

deve fazer parte do repositório.

31. Pull Requests

Uma alteração que modifica o banco deve incluir:

Model alterado
Migration criada
Testes atualizados
Documentação atualizada quando necessário

O autor deve verificar o conteúdo da migration
antes do commit.

32. Testes de migrations

Quando aplicável, testar:

upgrade
schema resultante
dados migrados
constraints
relacionamentos
downgrade

Alterações relacionadas ao multi-tenancy devem
ser acompanhadas por testes que garantam o isolamento.

33. Não editar migrations aplicadas

Depois que uma migration já tiver sido aplicada
em um ambiente compartilhado, não alterar seu conteúdo
para corrigir o histórico.

Criar uma nova migration para a correção.

Exemplo:

Migration 001
Migration 002
Migration 003

Se a Migration 002 já foi aplicada, uma alteração
posterior deve ser feita através de uma nova migration.

34. Revisão antes do commit

Antes de criar o commit:

1. Verificar migration
2. Verificar model
3. Verificar testes
4. Verificar git diff
5. Verificar se não existem alterações não relacionadas
35. Fluxo oficial

O fluxo recomendado é:

Requisito
   |
   v
Alterar Model
   |
   v
Gerar Migration
   |
   v
Revisar Migration
   |
   v
Testar
   |
   v
Aplicar Migration
   |
   v
Validar Banco
   |
   v
Commit
36. Regra final

A migration deve representar exatamente
a alteração estrutural necessária.

Antes de considerar uma migration pronta,
responder:

O que mudou?
Por que mudou?
Existem dados existentes?
Há risco de perda?
Os relacionamentos estão corretos?
O tenant foi considerado?
O soft delete foi considerado?
Os índices foram considerados?
Os testes foram atualizados?

Migrations devem ser claras, rastreáveis,
revisáveis e reproduzíveis.


### Local exato

```text
C:\Users\joao\Projetos\saas-erp-platform\skills\database\migrations.md