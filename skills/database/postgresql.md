# PostgreSQL

## Objetivo

Este documento define os padrões específicos de PostgreSQL
utilizados no SaaS ERP Platform.

Estas regras complementam:

```text
skills/database/README.md
skills/database/modeling.md
skills/database/multi-tenancy.md
skills/database/migrations.md
skills/02-architecture.md

Antes de criar ou alterar estruturas no PostgreSQL,
consultar estas regras.

1. Banco principal

O banco de dados principal da aplicação é:

PostgreSQL

O PostgreSQL será a fonte principal dos dados transacionais
do ERP.

Redis não substitui o PostgreSQL como banco principal.

2. Schema

O projeto utilizará inicialmente um schema compartilhado
para as entidades da aplicação.

Estrutura conceitual:

PostgreSQL
    |
    └── database
          |
          └── public
                |
                ├── tenants
                ├── users
                ├── customers
                ├── products
                ├── orders
                └── inventory

Não criar schemas PostgreSQL separados por tenant.

O isolamento entre tenants será realizado através do
modelo definido em:

skills/database/multi-tenancy.md
3. Nomenclatura

Utilizar snake_case.

Tabelas

Utilizar nomes no plural.

Exemplos:

tenants
users
roles
permissions
customers
products
orders
order_items
audit_logs
Colunas

Utilizar nomes descritivos em snake_case.

Exemplos:

tenant_id
customer_id
created_at
updated_at
deleted_at
unit_price
total_amount
4. Primary Keys

O padrão de chave primária do projeto é:

UUID

Nome:

id

Exemplo:

id UUID PRIMARY KEY

Toda entidade principal deve utilizar sua própria chave
primária.

As chaves devem possuir geração consistente entre a
aplicação e o banco.

Não misturar estratégias diferentes de geração de ID
sem justificativa técnica.

5. Foreign Keys

Relacionamentos devem utilizar foreign keys reais.

Exemplo:

customer_id UUID REFERENCES customers(id)

Quando a tabela pertencer a um tenant:

tenant_id UUID REFERENCES tenants(id)

Foreign keys devem possuir nomes claros e consistentes.

6. UUID como tipo

Quando uma coluna representar uma referência a uma entidade
cujo ID é UUID, utilizar:

UUID

Não armazenar UUID como:

TEXT
VARCHAR

quando a coluna representar uma chave estrutural.

Exemplo correto:

customer_id UUID

Exemplo a evitar:

customer_id VARCHAR(36)
7. Timestamps

O padrão temporal do projeto é:

TIMESTAMP WITH TIME ZONE

No PostgreSQL, esse tipo deve ser utilizado para campos
temporais das entidades de negócio quando aplicável.

Campos padrão:

created_at
updated_at
deleted_at

Os valores persistidos devem utilizar UTC.

8. Created At

Padrão:

created_at TIMESTAMP WITH TIME ZONE

Representa o momento em que o registro foi criado.

Depois de criado, o valor não deve ser alterado
normalmente pela aplicação.

9. Updated At

Padrão:

updated_at TIMESTAMP WITH TIME ZONE

Representa o momento da última alteração do registro.

Quando o registro for atualizado, o valor deve acompanhar
a alteração.

10. Deleted At

Padrão:

deleted_at TIMESTAMP WITH TIME ZONE NULL

Representa o momento da exclusão lógica.

Regra:

deleted_at IS NULL
→ registro ativo

deleted_at IS NOT NULL
→ registro logicamente excluído

O padrão deve seguir:

skills/database/modeling.md
11. Valores monetários

Valores financeiros devem utilizar:

NUMERIC

Nunca utilizar:

FLOAT
REAL
DOUBLE PRECISION

para armazenar valores monetários.

Exemplo:

unit_price NUMERIC(15,2)
total_amount NUMERIC(15,2)
discount_amount NUMERIC(15,2)
tax_amount NUMERIC(15,2)

A precisão deve ser definida de acordo com o domínio.

12. Quantidades

Para quantidades inteiras:

INTEGER

Exemplo:

quantity INTEGER

Para quantidades fracionadas:

NUMERIC

Exemplo:

quantity NUMERIC(15,4)

A precisão deve ser definida pelo domínio.

13. Percentuais

Percentuais devem utilizar NUMERIC.

Exemplo:

discount_percent NUMERIC(7,4)
tax_percent NUMERIC(7,4)

Nunca utilizar tipos de ponto flutuante para cálculos
financeiros ou percentuais que exigem precisão controlada.

14. Texto

Utilizar VARCHAR ou TEXT de acordo com o domínio.

Usar VARCHAR(n) quando existir uma regra real de tamanho.

Usar TEXT quando não existir necessidade real de limitar
o comprimento.

Não adicionar limites arbitrários.

15. Códigos

Campos de código podem utilizar VARCHAR quando possuírem
um tamanho conhecido no domínio.

Exemplos:

sku
external_id
country_code
postal_code

O tamanho deve ser definido de acordo com a necessidade
real do domínio.

16. Documentos e identificadores

Informações como documentos, inscrições ou identificadores
externos não devem ser armazenadas como tipos numéricos
quando puderem possuir:

zeros à esquerda;
caracteres;
formatação;
tamanho variável.

Exemplo:

cnpj VARCHAR(...)
cpf VARCHAR(...)
external_id VARCHAR(...)

A escolha final deve seguir a regra do domínio.

17. Boolean

Valores binários devem utilizar:

BOOLEAN

Exemplo:

is_active BOOLEAN

Evitar representar booleanos como:

0 / 1
S / N
Y / N
TRUE / FALSE em texto

quando o tipo booleano for suficiente.

18. JSONB

JSONB pode ser utilizado para dados realmente
semiestruturados.

Exemplos:

metadata
external_data
integration_payload
settings

Usar JSONB quando:

a estrutura puder variar;
os dados forem complementares;
o conteúdo não precisar de relacionamento relacional
próprio;
não houver necessidade de transformar cada propriedade
em uma coluna.
19. Quando não utilizar JSONB

Não utilizar JSONB para esconder entidades estruturadas.

Evitar:

customer_data JSONB

quando o sistema precisar consultar, relacionar ou validar
individualmente informações que deveriam ser colunas
relacionais.

Não armazenar uma entidade inteira em JSONB quando uma
tabela normalizada for apropriada.

20. Default

Defaults devem representar regras reais do domínio.

Não adicionar defaults automaticamente.

Exemplos aceitáveis quando fizerem sentido:

quantity = 0
deleted_at = NULL

Defaults relacionados a timestamps devem ser definidos
de forma consistente no projeto.

A decisão sobre onde o valor será gerado:

aplicação

ou:

banco

deve ser consistente para cada padrão.

21. NOT NULL

Utilizar:

NOT NULL

quando a ausência do valor for inválida para a entidade.

Exemplo:

name NOT NULL
tenant_id NOT NULL
created_at NOT NULL

Não utilizar NULL apenas porque a coluna poderia ficar vazia.

22. Unique

Utilizar UNIQUE quando existir uma regra de unicidade.

Exemplo:

email

ou:

tenant_id + sku

A estratégia deve respeitar o escopo do dado.

Uma informação que é única dentro de um tenant
não deve receber automaticamente uma constraint global.

23. Unique composto

Para unicidade por tenant, preferir constraints compostas.

Exemplo:

UNIQUE (
    tenant_id,
    sku
)

Exemplo:

Tenant A + SKU 001

e:

Tenant B + SKU 001

podem existir.

Mas:

Tenant A + SKU 001
Tenant A + SKU 001

não podem coexistir.

24. Soft Delete e Unique

Quando uma tabela possuir:

deleted_at

avaliar explicitamente como a unicidade deverá funcionar
para registros logicamente excluídos.

Pergunta obrigatória:

Um registro com deleted_at preenchido
continua ocupando o valor único?

A resposta depende do domínio.

A estratégia escolhida deve ser aplicada de forma consistente
com a modelagem e com as migrations.

25. Primary Key Constraints

Toda tabela de entidade deve possuir uma primary key.

Exemplo:

CONSTRAINT pk_customers
PRIMARY KEY (id)

A nomenclatura de constraints deve ser consistente
com o restante do banco.

26. Foreign Key Constraints

Foreign keys devem possuir constraints explícitas.

Exemplo conceitual:

CONSTRAINT fk_orders_customer
FOREIGN KEY (customer_id)
REFERENCES customers(id)
27. Foreign Key e Tenant

Relacionamentos entre entidades multi-tenant devem respeitar
as regras de multi-tenancy.

Exemplo:

orders
    |
    +---- customer_id
    |
    +---- tenant_id

A aplicação deve garantir que:

Order Tenant
=
Customer Tenant

A foreign key simples entre:

orders.customer_id
→ customers.id

não substitui a validação de contexto de tenant.

28. ON DELETE

A estratégia de exclusão de foreign keys deve ser escolhida
de acordo com o domínio.

Possibilidades:

CASCADE
RESTRICT
SET NULL

Não utilizar CASCADE indiscriminadamente.

Antes de escolher uma estratégia, avaliar:

dependência do registro;
histórico;
soft delete;
integridade;
risco de exclusão em cadeia.
29. CHECK Constraints

Utilizar CHECK quando o banco puder garantir uma regra
simples de integridade.

Exemplo:

quantity >= 0

ou:

price >= 0

quando essas regras fizerem parte do domínio.

Não utilizar CHECK para substituir regras de negócio
complexas.

30. Status

Quando uma coluna representar um conjunto conhecido
de estados, a integridade deve ser avaliada.

Exemplo:

order.status

Poderá utilizar uma constraint apropriada, como:

CHECK (
    status IN (
        'pending',
        'confirmed',
        'cancelled'
    )
)

A estratégia final deve permanecer consistente com
a skill de modelagem.

31. Índices

Índices devem ser criados com base em padrões reais
de consulta.

Avaliar índices para:

foreign keys;
filtros frequentes;
buscas;
ordenação;
combinações frequentes de filtros;
consultas multi-tenant.

Não criar índices indiscriminadamente.

32. Índices multi-tenant

Quando uma tabela for multi-tenant e as consultas
frequentemente utilizarem o tenant como filtro,
avaliar índices iniciados por:

tenant_id

Exemplo:

INDEX (
    tenant_id,
    created_at
)

ou:

INDEX (
    tenant_id,
    status
)

A definição deve refletir as consultas reais.

33. Foreign Keys e índices

Foreign keys não devem ser consideradas automaticamente
como motivo suficiente para criar qualquer índice.

Verificar os padrões de consulta e o plano de acesso
antes de adicionar índices.

Quando uma foreign key for frequentemente utilizada
como filtro, considerar um índice apropriado.

34. Índices compostos

A ordem das colunas de um índice composto deve refletir
os padrões de consulta.

Exemplo:

INDEX (
    tenant_id,
    status,
    created_at
)

não deve ser criado apenas por conveniência.

Avaliar:

WHERE
tenant_id = ...

AND status = ...

ORDER BY
created_at

como um exemplo de consulta que pode justificar
essa estrutura.

35. Índices parciais

Índices parciais podem ser utilizados quando somente
uma parte dos registros for frequentemente consultada.

Exemplo conceitual:

WHERE deleted_at IS NULL

Essa estratégia deve ser utilizada somente quando houver
necessidade real e benefício comprovado.

36. Case sensitivity

Não depender de comportamento implícito de maiúsculas
e minúsculas para regras de unicidade.

Quando a regra exigir:

email

sem distinção entre maiúsculas e minúsculas, definir
uma estratégia explícita.

A implementação deve ser consistente com a aplicação.

37. Ordenação

Não assumir que consultas possuem uma ordem determinística
sem utilizar ORDER BY.

Quando a aplicação precisar de ordem específica,
a ordenação deve ser explícita.

Exemplo:

ORDER BY created_at DESC

Quando houver possibilidade de empate, considerar
um segundo campo para desempate.

Exemplo:

ORDER BY created_at DESC, id DESC
38. Paginação

Listagens potencialmente grandes devem possuir paginação.

Evitar retornar grandes volumes de registros
em uma única requisição.

A estratégia de paginação deve ser definida na camada
da API e compatibilizada com os padrões de consulta
do PostgreSQL.

39. Seleção de colunas

Não buscar todas as colunas automaticamente quando
somente parte dos dados for necessária.

Avaliar a projeção necessária para:

listagens;
dashboards;
consultas;
integrações.

Isso é especialmente importante para tabelas
com colunas JSONB ou grandes volumes de dados.

40. Pesquisa textual

Consultas textuais devem utilizar mecanismos adequados
ao tipo de busca.

Não utilizar:

LIKE '%texto%'

indiscriminadamente em tabelas grandes.

Quando pesquisas textuais crescerem em volume,
avaliar índices e mecanismos apropriados.

41. Dados externos

Para dados vindos de outros sistemas, preferir campos
explícitos como:

external_id
source_system

Quando necessário:

UNIQUE (
    tenant_id,
    source_system,
    external_id
)

Esse padrão será utilizado futuramente pelo projeto
integration-hub.

42. Auditoria

Quando uma tabela precisar de rastreabilidade de negócio,
avaliar sua relação com:

audit_logs

Não adicionar campos de auditoria específicos em todas
as tabelas sem necessidade.

Os padrões de auditoria serão definidos em:

skills/observability/
43. Performance

Não otimizar prematuramente.

Antes de adicionar:

índices;
estruturas auxiliares;
desnormalizações;
views;
materialized views;

identificar o problema real e medir quando possível.

A otimização deve ser orientada pelo comportamento
da aplicação e pelas consultas reais.

44. Desnormalização

Desnormalização é permitida quando houver justificativa técnica.

Exemplos:

performance
relatórios
consultas muito frequentes

A decisão deve ser documentada quando alterar
significativamente o modelo normalizado.

Não duplicar dados apenas para tornar o código
mais conveniente.

45. Views

Views podem ser utilizadas para necessidades específicas
de leitura quando houver benefício real.

Não criar uma view somente para substituir uma consulta
simples.

A necessidade deve estar relacionada ao domínio ou
à manutenção de consultas complexas.

46. Materialized Views

Materialized views devem ser utilizadas somente quando
houver uma necessidade real de desempenho ou processamento
de consultas específicas.

Sua atualização deve ser planejada.

Não adicionar materialized views como parte da modelagem
inicial sem necessidade.

47. Extensões

Extensões PostgreSQL não devem ser adicionadas
automaticamente.

Antes de utilizar uma extensão:

identificar o problema que ela resolve;
verificar se o PostgreSQL nativo já resolve o problema;
avaliar impacto no ambiente;
avaliar manutenção;
documentar a necessidade.
48. Configuração do banco

Informações de conexão não devem ficar no código.

Utilizar variáveis de ambiente.

Exemplo conceitual:

DATABASE_URL

Credenciais não devem ser versionadas.

49. Ambiente de desenvolvimento

O PostgreSQL do projeto será executado através
da infraestrutura definida em:

skills/infrastructure/

O ambiente deve ser reproduzível.

Não depender de configurações manuais específicas
da máquina do desenvolvedor.

50. Regra para nova tabela

Antes de criar uma tabela PostgreSQL:

1. Definir entidade
2. Definir primary key
3. Definir tenant
4. Definir colunas
5. Definir tipos
6. Definir NOT NULL
7. Definir foreign keys
8. Definir UNIQUE
9. Definir CHECK
10. Definir índices
11. Definir created_at
12. Definir updated_at
13. Definir deleted_at
14. Avaliar JSONB
15. Avaliar soft delete
16. Avaliar auditoria
17. Criar migration
18. Criar testes
51. Regra para alteração

Antes de alterar uma tabela existente:

1. Verificar model
2. Verificar migrations
3. Verificar código dependente
4. Verificar dados existentes
5. Verificar índices
6. Verificar constraints
7. Verificar tenant
8. Verificar soft delete
9. Verificar impacto na API
10. Criar migration
11. Atualizar testes
52. Regra de consistência

Uma mesma regra deve possuir representação consistente
em toda a aplicação.

Exemplo:

created_at
updated_at
deleted_at

devem seguir o mesmo padrão nas entidades equivalentes.

Não utilizar:

created
created_at
creation_date

para representar o mesmo conceito em tabelas diferentes
sem uma justificativa arquitetural.

53. Regra final

O PostgreSQL deve ser tratado como parte da arquitetura
do sistema e não apenas como armazenamento.

Toda decisão deve considerar:

integridade
+
consistência
+
segurança
+
desempenho
+
multi-tenancy
+
manutenção

Alterações estruturais devem passar por modelagem,
migration e validação.

As decisões específicas devem permanecer alinhadas
com as demais skills da pasta:

skills/database/

### Local exato

```text
C:\Users\joao\Projetos\saas-erp-platform\skills\database\postgresql.md