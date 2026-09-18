# Database Modeling

## Objetivo

Este documento define os padrões oficiais para modelagem
das entidades persistidas no PostgreSQL do SaaS ERP Platform.

Toda nova tabela ou alteração estrutural deve seguir estas
regras, juntamente com:

```text
skills/database/README.md
skills/database/multi-tenancy.md
skills/database/migrations.md
skills/02-architecture.md
1. Princípios

A modelagem deve priorizar:

integridade dos dados;
consistência;
clareza;
manutenção;
desempenho;
segurança;
isolamento entre tenants.

Não criar estruturas genéricas apenas para evitar criar
tabelas ou entidades específicas.

O modelo deve representar claramente o domínio do sistema.

2. Nomenclatura
Tabelas

Utilizar:

snake_case

e nomes no plural.

Exemplos:

tenants
users
roles
permissions
customers
products
categories
orders
order_items
inventory
audit_logs

Não utilizar:

Customers
Customer
tbl_customers
TB_CUSTOMERS
customerTable
Colunas

Utilizar:

snake_case

Exemplos:

first_name
created_at
updated_at
deleted_at
tenant_id
product_id
unit_price

Não utilizar:

firstName
CreatedAt
DeletedAt
TenantId
3. Primary Key

As entidades principais devem possuir uma chave primária
chamada:

id

Padrão definido para o projeto:

UUID

Exemplo conceitual:

id UUID PRIMARY KEY

A escolha de UUID permite identificar entidades sem depender
de sequências numéricas facilmente previsíveis em APIs.

IDs devem ser gerados pela aplicação ou por mecanismo
explicitamente definido pela arquitetura.

4. Foreign Keys

Relacionamentos devem utilizar foreign keys reais no banco.

Exemplo:

customer_id
product_id
tenant_id
user_id
order_id

Uma foreign key deve apontar para uma primary key ou outra
chave única apropriada.

Não utilizar somente convenções de nomenclatura para
representar relacionamentos sem constraint no banco quando
uma foreign key for aplicável.

5. Tenant ID

Entidades de negócio que pertencem a uma empresa devem possuir:

tenant_id

Exemplo:

customers
products
orders
inventory

Estrutura conceitual:

id
tenant_id
name
created_at
updated_at
deleted_at

O tenant_id deve possuir foreign key para:

tenants.id

quando aplicável.

A ausência ou presença de tenant_id deve ser uma decisão
consciente baseada no relacionamento da entidade com o tenant.

6. Tenant como entidade raiz

A tabela:

tenants

representa as empresas que utilizam a plataforma.

Ela é uma entidade raiz do modelo multi-tenant.

A própria tabela tenants não deve possuir tenant_id
referenciando a si mesma.

Exemplo conceitual:

tenants

id
name
status
created_at
updated_at
deleted_at
7. Campos obrigatórios

Campos que são essenciais para a existência ou integridade
da entidade devem utilizar NOT NULL.

Exemplo:

products

id
tenant_id
name
created_at
updated_at
deleted_at

Campos opcionais devem ser nullable somente quando existir
uma justificativa de negócio.

Não utilizar NULL como padrão para todos os campos.

8. Timestamps

As entidades de negócio devem utilizar, quando aplicável,
os seguintes campos:

created_at
updated_at
deleted_at

Padrão:

created_at → momento de criação
updated_at → momento da última alteração
deleted_at → momento da exclusão lógica

Os timestamps devem ser armazenados com informação de fuso
horário.

Padrão recomendado:

TIMESTAMP WITH TIME ZONE

ou equivalente no SQLAlchemy:

DateTime(timezone=True)

Os horários persistidos devem utilizar UTC.

9. Created At

created_at representa o momento em que o registro foi criado.

Depois de criado, esse valor normalmente não deve ser
alterado pela aplicação.

Exemplo:

created_at = 2026-09-17T23:15:00Z
10. Updated At

updated_at representa o momento da última alteração
do registro.

Quando uma entidade for modificada, esse campo deve ser
atualizado.

Tabelas imutáveis ou append-only não precisam possuir
updated_at quando não houver alteração do registro.

11. Soft Delete

As entidades de negócio do sistema devem utilizar exclusão
lógica através do campo:

deleted_at

Padrão:

NULL
→ registro ativo

data preenchida
→ registro logicamente removido

O campo deve utilizar um tipo compatível com timestamp
com informação de fuso horário.

Exemplo:

deleted_at TIMESTAMP WITH TIME ZONE NULL

Quando um registro for removido logicamente:

deleted_at = momento da exclusão

O registro não deve ser fisicamente removido do banco
quando a operação prevista for uma exclusão lógica.

As consultas padrão da aplicação devem considerar
somente registros com:

deleted_at IS NULL

quando a operação estiver trabalhando com registros ativos.

Consultas que precisarem visualizar registros excluídos
devem declarar essa intenção explicitamente.

O padrão oficial do projeto é:

deleted_at

Não criar simultaneamente campos como:

deleted
is_deleted
deleted_at
12. Status

Quando uma entidade possuir diferentes estados de negócio,
o campo deve possuir valores claramente definidos.

Exemplo:

orders.status

com valores previamente documentados.

O banco deve possuir uma constraint apropriada quando isso
for útil para garantir integridade.

Não permitir valores arbitrários quando o domínio possuir
um conjunto fechado e conhecido de estados.

13. Enums

Não utilizar PostgreSQL ENUM automaticamente para todos
os campos de status.

Antes de utilizar ENUM, avaliar:

frequência de alteração dos valores;
impacto de migrations;
necessidade real de constraint específica;
compatibilidade com a aplicação.

Quando o conjunto de valores puder mudar frequentemente,
considerar VARCHAR com CHECK ou outra estratégia
apropriada.

A decisão deve ser consistente dentro do mesmo domínio.

14. Valores monetários

Nunca utilizar:

FLOAT
REAL
DOUBLE PRECISION

para valores monetários do ERP.

Utilizar:

NUMERIC

com precisão e escala definidas de acordo com a necessidade.

Exemplo:

NUMERIC(15,2)

para valores monetários.

Exemplos de campos:

unit_price
total_amount
discount_amount
tax_amount

A precisão deve ser definida de acordo com o domínio
e não arbitrariamente.

15. Quantidades

Quantidades de estoque ou itens devem utilizar um tipo
numérico adequado ao domínio.

Exemplo:

INTEGER

quando somente quantidades inteiras forem permitidas.

Para produtos que permitam quantidades fracionadas,
utilizar:

NUMERIC

com precisão definida.

16. Texto

Utilizar tipos de texto de acordo com o domínio.

Exemplos:

VARCHAR
TEXT

Não limitar arbitrariamente o tamanho de textos que não
possuem uma regra real de tamanho.

Campos que representam códigos, documentos ou identificadores
externos devem possuir tamanho definido quando o domínio
estabelecer esse limite.

17. Booleanos

Utilizar:

BOOLEAN

para valores verdadeiros ou falsos.

Evitar representar booleanos como:

VARCHAR
INTEGER
CHAR

quando não houver necessidade específica.

18. Relacionamentos

Relacionamentos devem ser representados explicitamente.

Exemplo:

orders
    |
    +---- order_items

e:

products
    |
    +---- order_items

Um relacionamento deve possuir foreign keys e constraints
apropriadas.

19. One-to-Many

Exemplo:

Customer
   |
   +---- Orders
   +---- Orders
   +---- Orders

No banco:

orders.customer_id

referencia:

customers.id
20. Many-to-Many

Relacionamentos muitos-para-muitos devem utilizar uma
tabela associativa.

Exemplo:

users
   |
   +---- user_roles ----+
                        |
                       roles

Não armazenar múltiplos IDs em uma única coluna para
representar relacionamentos.

Evitar estruturas como:

role_ids = "1,2,3"

ou:

role_ids = [1,2,3]

quando o relacionamento for estrutural e puder ser
representado por tabela associativa.

21. Foreign Key e exclusão

A estratégia de ON DELETE deve ser definida de acordo
com o significado do relacionamento.

Usar CASCADE somente quando os registros dependentes
devem obrigatoriamente ser removidos junto com o registro pai.

Usar RESTRICT ou equivalente quando a exclusão do pai
deve ser impedida enquanto existirem dependências.

Não utilizar CASCADE indiscriminadamente.

Quando existir soft delete, avaliar se a exclusão física
do registro pai sequer deve ser permitida.

22. Unique Constraints

Campos que precisam ser únicos devem possuir uma
constraint apropriada.

Exemplo global:

email

ou exemplo relacionado a um tenant:

tenant_id + sku

No modelo multi-tenant, avaliar se a unicidade deve ser:

global

ou:

por tenant

Exemplo:

tenant_id + email

permite o mesmo e-mail em tenants diferentes.

23. Unique composto

Quando a regra de negócio exigir unicidade dentro
de um tenant, utilizar uma constraint composta.

Exemplo:

UNIQUE (
    tenant_id,
    sku
)

Isso significa:

Tenant A + SKU 001

e:

Tenant B + SKU 001

podem existir simultaneamente.

Mas:

Tenant A + SKU 001
Tenant A + SKU 001

não podem coexistir.

Quando uma tabela utiliza soft delete, a estratégia
de unicidade deverá considerar se registros logicamente
excluídos devem continuar ocupando a chave única.

24. Índices

Índices devem existir para necessidades reais.

Avaliar índices para:

foreign keys;
campos frequentemente utilizados em filtros;
campos frequentemente utilizados em buscas;
campos utilizados em ordenação;
combinações frequentes de filtros.

Não criar índices em todas as colunas automaticamente.

25. Índices relacionados ao tenant

Entidades multi-tenant frequentemente possuem consultas
que filtram por:

tenant_id

Quando apropriado, avaliar índices iniciados por tenant_id.

Exemplo:

INDEX (
    tenant_id,
    created_at
)

pode ser apropriado quando o sistema realiza frequentemente
consultas por tenant ordenadas por data.

O índice deve refletir os padrões reais de consulta.

26. Índices e UNIQUE

Quando houver uma regra de unicidade por tenant,
a constraint pode também produzir o índice necessário.

Evitar criar um índice duplicado que represente
exatamente a mesma regra.

27. JSON / JSONB

JSONB pode ser utilizado quando os dados forem realmente
semiestruturados ou variáveis.

Exemplos possíveis:

metadata
external_data
integration_payload

Não utilizar JSONB para substituir tabelas relacionais
quando os dados possuem estrutura conhecida e relações
importantes no domínio.

Evitar armazenar entidades inteiras dentro de uma coluna JSONB.

28. Dados externos

Quando uma entidade precisar armazenar um identificador
proveniente de outro sistema, utilizar um campo explícito.

Exemplo:

external_id
source_system

Quando a combinação precisar ser única por tenant,
utilizar uma constraint apropriada.

Exemplo:

UNIQUE (
    tenant_id,
    source_system,
    external_id
)

Esse padrão será especialmente importante para o futuro
projeto integration-hub.

29. Auditoria

Dados de auditoria devem possuir estrutura adequada
para registrar alterações relevantes.

Exemplo conceitual:

audit_logs

id
tenant_id
user_id
action
entity
entity_id
old_data
new_data
created_at

A modelagem detalhada de auditoria deve permanecer
consistente com a skill de observabilidade.

30. Tabelas de histórico

Quando o domínio exigir histórico de alterações,
preferir uma estrutura própria de histórico em vez de
sobrescrever dados importantes sem rastreabilidade.

Exemplo:

product
product_price_history

A decisão deve ser baseada no requisito real de negócio.

Não criar histórico para toda tabela automaticamente.

31. Integridade no banco

Sempre que uma regra puder ser garantida de forma segura
pelo banco, avaliar a criação de uma constraint.

Exemplos:

PRIMARY KEY
FOREIGN KEY
UNIQUE
NOT NULL
CHECK

A aplicação continua responsável pelas regras de negócio,
mas o banco também deve proteger sua própria integridade.

32. Normalização

O modelo deve evitar duplicação desnecessária de dados.

Quando uma informação representa uma entidade própria
ou possui relacionamentos importantes, avaliar a criação
de uma tabela específica.

Não desnormalizar apenas por conveniência de implementação.

Desnormalizações devem possuir justificativa técnica
relacionada a desempenho ou necessidade real do domínio.

33. Regra para novas entidades

Antes de criar uma tabela, definir:

Nome
Responsabilidade
Primary Key
Tenant
Foreign Keys
Campos obrigatórios
Campos opcionais
Constraints
Índices
Timestamps
Soft Delete
Relacionamentos

O padrão de timestamps para entidades de negócio é:

created_at
updated_at
deleted_at

Exemplo:

products

id
tenant_id
category_id
sku
name
description
price
created_at
updated_at
deleted_at

Depois avaliar:

PK
FK
UNIQUE
INDEX
NOT NULL
CHECK
34. Modelagem multi-tenant

Exemplo conceitual:

tenants
---------
id
name
created_at
updated_at
deleted_at


customers
---------
id
tenant_id
name
email
created_at
updated_at
deleted_at


products
--------
id
tenant_id
sku
name
price
created_at
updated_at
deleted_at


orders
------
id
tenant_id
customer_id
status
total_amount
created_at
updated_at
deleted_at

Relacionamentos:

tenants
   |
   +---- customers
   |
   +---- products
   |
   +---- orders

E:

orders.customer_id
        |
        v
customers.id

O relacionamento também deve ser validado dentro
das regras de multi-tenancy.

35. Ordem de definição

Para uma nova entidade:

1. Identificar a entidade
2. Definir responsabilidade
3. Definir relacionamento com tenant
4. Definir primary key
5. Definir foreign keys
6. Definir campos
7. Definir tipos
8. Definir NOT NULL
9. Definir UNIQUE
10. Definir CHECK quando aplicável
11. Definir índices
12. Definir created_at
13. Definir updated_at
14. Definir deleted_at
15. Avaliar auditoria
36. Modelagem no SQLAlchemy

Os models devem representar fielmente o schema
definido para o banco.

Localização:

backend/app/models/

A modelagem do SQLAlchemy não deve divergir
intencionalmente do schema do PostgreSQL.

Quando houver uma diferença necessária, ela deve possuir
justificativa técnica.

Os campos padrão de entidades de negócio devem ser
representados de forma consistente:

created_at
updated_at
deleted_at
37. Alterações de modelagem

Quando uma entidade existente for alterada:

verificar dependências;
verificar relacionamentos;
verificar índices;
verificar constraints;
verificar impacto no tenant;
verificar comportamento do soft delete;
verificar migrations;
atualizar testes.

Não alterar somente o model ORM e considerar a alteração
concluída.

38. Regra final

Uma boa modelagem deve responder:

O que representa essa tabela?
Quem é o dono desses dados?
Qual é sua chave?
Com quem ela se relaciona?
Como sua integridade é garantida?
Como ela será consultada?
Como será isolada por tenant?
Como será alterada no futuro?
Como será logicamente removida?

A modelagem deve ser clara, consistente e orientada
ao domínio real do ERP.


Agora o padrão oficial das entidades de negócio fica:

```text
id
tenant_id          ← quando aplicável
...
created_at
updated_at
deleted_at

com deleted_at = NULL significando ativo e uma data preenchida significando excluído logicamente.