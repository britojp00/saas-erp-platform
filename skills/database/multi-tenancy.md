# Multi-Tenancy

## Objetivo

Este documento define as regras oficiais de implementação
do multi-tenancy no SaaS ERP Platform.

O isolamento entre tenants é um requisito obrigatório
do sistema.

Nenhum usuário, processo ou endpoint deve conseguir acessar,
alterar ou remover dados pertencentes a outro tenant sem uma
regra explícita que permita essa operação.

---

# 1. Estratégia adotada

O projeto utilizará:

```text
PostgreSQL
    |
    └── Database compartilhado
          |
          └── Schema compartilhado
                |
                ├── tenants
                ├── users
                ├── customers
                ├── products
                ├── orders
                └── inventory

O isolamento lógico será realizado através do campo:

tenant_id

nas entidades que pertencem a uma empresa.

2. Conceito de Tenant

Um tenant representa uma empresa que utiliza a plataforma.

Exemplo:

Tenant A
Empresa ABC

Tenant B
Empresa XYZ

Tenant C
Empresa 123

Cada tenant possui seu próprio contexto de dados.

3. Entidade Tenant

A entidade principal é:

tenants

Estrutura conceitual:

tenants

id
name
status
created_at
updated_at
deleted_at

A tabela tenants é a raiz do isolamento entre empresas.

A tabela tenants não possui tenant_id.

4. Relacionamento com Tenant

Toda entidade de negócio que pertence a uma empresa
deve possuir:

tenant_id

Exemplo:

customers

id
tenant_id
name
email
created_at
updated_at
deleted_at
products

id
tenant_id
sku
name
price
created_at
updated_at
deleted_at
orders

id
tenant_id
customer_id
status
total_amount
created_at
updated_at
deleted_at
5. Entidades que não possuem tenant_id

Nem toda entidade precisa possuir tenant_id.

A decisão deve considerar a propriedade dos dados.

Exemplos que podem existir como entidades globais:

permissions

porque uma permission pode representar uma definição
da própria plataforma.

Exemplos que normalmente pertencem a um tenant:

customers
products
orders
inventory

A ausência de tenant_id deve ser uma decisão explícita.

Não adicionar tenant_id automaticamente a toda tabela.

6. Regra de propriedade

Antes de criar uma tabela, responder:

Quem é o proprietário desses dados?

A informação pertence:
    |
    +---- à plataforma?
    |
    +---- a um tenant?
    |
    +---- a uma relação entre tenants?

Se os dados pertencem a um tenant, utilizar:

tenant_id
7. Foreign Key

O campo:

tenant_id

deve possuir relacionamento com:

tenants.id

quando aplicável.

Conceito:

customers.tenant_id
        |
        v
   tenants.id

Isso garante a integridade do relacionamento no banco.

8. Contexto do Tenant

O tenant atual deve ser determinado a partir de
uma fonte confiável da aplicação.

O sistema não deve confiar exclusivamente em:

tenant_id

enviado pelo cliente.

Exemplo incorreto:

POST /api/v1/customers

{
    "tenant_id": "tenant-da-empresa-B",
    "name": "João"
}

e a aplicação aceitar esse valor como fonte de autorização.

O tenant deve ser obtido do contexto autenticado
e validado pela aplicação.

9. Autenticação e Tenant

O usuário autenticado deve possuir uma associação
com o tenant correspondente.

Conceito:

User
 |
 +---- Tenant

Exemplo:

User:
João

Tenant:
Empresa ABC

Quando João realizar uma operação, a aplicação deve conhecer
o contexto do tenant associado à sua sessão/autenticação.

10. Usuário e Tenant

A estrutura inicial prevista será:

users

id
tenant_id
name
email
password_hash
created_at
updated_at
deleted_at

Um usuário de negócio pertence a um tenant.

O modelo final de associação pode evoluir caso o sistema
precise suportar usuários pertencentes a múltiplos tenants.

Essa mudança não deve ser introduzida sem uma necessidade real.

11. Acesso aos dados

Uma operação de leitura deve considerar:

recurso
+
tenant atual

Exemplo conceitual:

SELECT *
FROM customers
WHERE id = :customer_id
  AND tenant_id = :tenant_id
  AND deleted_at IS NULL

A aplicação não deve buscar somente:

WHERE id = :customer_id

quando o recurso pertence a um tenant.

12. Listagens

Toda listagem de uma entidade multi-tenant deve
considerar o tenant atual.

Exemplo:

GET /api/v1/customers

deve resultar conceitualmente em:

Tenant atual
    |
    v
clientes daquele tenant

e não:

todos os clientes da plataforma
13. Busca por ID

Uma busca por ID deve respeitar o tenant.

Exemplo:

GET /api/v1/customers/{id}

A aplicação deve validar:

customer.id
+
customer.tenant_id

O fato de o usuário conhecer o ID de outro tenant
não deve conceder acesso ao registro.

14. Atualização

Atualizações devem validar o tenant do registro.

Exemplo:

PUT /api/v1/products/{id}

A operação deve localizar o produto dentro do contexto
do tenant atual.

Conceito:

product.id
+
product.tenant_id

Não realizar alteração somente utilizando o ID quando
a entidade for multi-tenant.

15. Exclusão lógica

O sistema utilizará:

deleted_at

para exclusão lógica das entidades de negócio.

Registro ativo:

deleted_at = NULL

Registro excluído:

deleted_at = data da exclusão

A exclusão lógica também deve respeitar o tenant atual.

16. Consultas de registros ativos

Consultas normais devem considerar:

deleted_at IS NULL

além do:

tenant_id = tenant atual

Conceito:

WHERE tenant_id = :tenant_id
  AND deleted_at IS NULL
17. Registros excluídos

Consultas que precisarem visualizar registros
logicamente excluídos devem declarar explicitamente
essa intenção.

Uma consulta padrão de dados ativos não deve retornar
registros com:

deleted_at IS NOT NULL
18. Criação de registros

Ao criar uma entidade pertencente a um tenant,
o tenant_id deve ser derivado do contexto autenticado
da operação.

Não confiar no tenant_id fornecido pelo cliente
quando ele representar autorização.

Exemplo:

Usuário autenticado
        |
        v
Tenant = A
        |
        v
POST /customers
        |
        v
customer.tenant_id = A
19. Relações entre entidades multi-tenant

Ao trabalhar com duas ou mais entidades multi-tenant,
as relações também devem respeitar o tenant.

Exemplo:

Order
   |
   v
Customer

Ao criar um pedido:

order.tenant_id
customer.tenant_id

devem representar o mesmo tenant.

Não permitir:

Order
Tenant A

Customer
Tenant B

como uma relação válida.

20. Exemplo de validação de relacionamento

Conceito:

Criar Order para Customer
        |
        v
Customer existe?
        |
        v
Customer pertence ao tenant atual?
        |
        +---- NÃO → rejeitar
        |
        +---- SIM → continuar

A existência do registro não é suficiente.

Também é necessário validar sua propriedade.

21. Produtos e estoque

Produtos e estoques são dados pertencentes ao tenant.

Exemplo:

products

id
tenant_id
sku
name
price
created_at
updated_at
deleted_at
inventory

id
tenant_id
product_id
quantity
created_at
updated_at
deleted_at

O produto relacionado ao estoque deve pertencer
ao mesmo tenant.

22. Pedidos

Pedidos pertencem ao tenant.

Exemplo:

orders

id
tenant_id
customer_id
status
total_amount
created_at
updated_at
deleted_at

Ao criar um pedido:

Order Tenant
      =
Customer Tenant

Os itens do pedido também devem pertencer ao contexto
do pedido.

23. Unique por Tenant

Regras de unicidade devem considerar o escopo do tenant
quando o dado não precisa ser globalmente único.

Exemplo:

products

tenant_id
sku

A regra pode ser:

UNIQUE (
    tenant_id,
    sku
)

Assim:

Tenant A + SKU 001
Tenant B + SKU 001

podem coexistir.

Mas:

Tenant A + SKU 001
Tenant A + SKU 001

não podem coexistir.

24. Soft Delete e Unicidade

Quando uma entidade possuir:

deleted_at

a regra de unicidade deve considerar o comportamento
esperado para registros logicamente excluídos.

Antes de definir a constraint, responder:

Um registro excluído deve continuar ocupando o valor único?

Exemplo:

Tenant A
SKU 001

foi excluído logicamente.

Devemos permitir criar outro:

Tenant A
SKU 001

ou não?

A decisão deve ser definida de acordo com o domínio.

Não assumir automaticamente uma estratégia.

25. Índices

Consultas multi-tenant frequentemente utilizam:

tenant_id

como filtro.

Quando apropriado, criar índices considerando
os padrões reais de consulta.

Exemplo conceitual:

INDEX (
    tenant_id,
    created_at
)

ou:

INDEX (
    tenant_id,
    status
)

A definição final deve considerar as consultas reais
da aplicação.

26. Tenant e índices

Não criar índices somente porque uma tabela possui
tenant_id.

Avaliar:

frequência das consultas;
filtros;
ordenação;
cardinalidade;
volume de dados.

O objetivo é atender os padrões reais de acesso.

27. Repositories

Repositories devem receber ou utilizar o contexto
de tenant de forma consistente.

Uma operação como:

get_customer(customer_id)

não deve ignorar o tenant quando estiver sendo utilizada
para dados multi-tenant.

O padrão concreto será definido na skill de backend
e aplicado de maneira consistente.

28. Services

Services são responsáveis por aplicar regras de negócio
relacionadas ao tenant.

Exemplo:

OrderService
    |
    +---- validar cliente
    +---- validar tenant
    +---- validar estoque
    +---- criar pedido

O service não deve permitir uma operação que viole
o isolamento entre tenants.

29. Routers

Routers não devem confiar em um tenant enviado
diretamente pelo cliente.

O router deve utilizar as dependências e serviços
responsáveis por obter o contexto autenticado.

A lógica de negócio de isolamento deve permanecer
na arquitetura apropriada.

30. Segurança contra acesso cruzado

O sistema deve tratar como cenário obrigatório
o seguinte teste:

Tenant A
   |
   +---- tenta acessar recurso do Tenant B
                     |
                     v
                  BLOQUEAR

Esse comportamento deve possuir testes automatizados.

31. Teste de isolamento

Exemplo conceitual:

Criar:

Tenant A
Customer A

Tenant B
Customer B

Depois:

Autenticar como Tenant A

GET Customer A
→ permitido

GET Customer B
→ bloqueado

O teste deve validar explicitamente o isolamento.

32. Teste de atualização

Exemplo:

Tenant A
Product A

Tenant B
Product B

Usuário do Tenant A tenta:

PUT Product B

Resultado esperado:

operação bloqueada

O produto do Tenant B não deve ser alterado.

33. Teste de exclusão

Exemplo:

Tenant A
Customer A

Tenant B
Customer B

Usuário do Tenant A tenta excluir logicamente
o Customer B.

Resultado:

operação bloqueada

O deleted_at do Customer B não deve ser alterado.

34. Background Jobs e Tenant

Processos executados em background também devem conhecer
o contexto do tenant quando trabalharem com dados
multi-tenant.

Exemplo:

Queue Message
    |
    +---- tenant_id
    |
    +---- entity_id
    |
    +---- operation

Um worker não deve executar uma operação de negócio
sem conhecer o contexto do tenant quando ele for necessário.

35. Cache e Tenant

Dados armazenados em cache também devem respeitar
o isolamento entre tenants.

Chaves de cache relacionadas a dados de negócio devem
considerar o tenant quando necessário.

Exemplo:

tenant:{tenant_id}:products:{product_id}

Evitar chaves genéricas que possam causar colisão
ou exposição de dados entre tenants.

36. Logs e Tenant

Logs de operações multi-tenant devem permitir
identificar o contexto do tenant quando aplicável.

Exemplo:

{
  "event": "customer_created",
  "tenant_id": "...",
  "user_id": "...",
  "request_id": "..."
}

Não registrar informações sensíveis desnecessariamente.

37. APIs públicas e Tenant

Endpoints públicos ou de integração devem possuir
uma estratégia explícita para determinar o tenant.

Não assumir que o primeiro tenant encontrado no banco
é o tenant da requisição.

O contexto deve ser estabelecido através de um mecanismo
de autenticação ou identificação confiável.

38. Integrações futuras

O futuro integration-hub consumirá a API do ERP.

As integrações deverão possuir contexto de tenant
quando representarem operações de uma empresa específica.

Exemplo conceitual:

Integration Hub
       |
       v
API do ERP
       |
       v
Tenant A

O sistema não deve permitir que uma credencial de integração
destinada ao Tenant A manipule dados do Tenant B.

39. Regra para novas tabelas

Ao criar uma nova tabela, responder:

1. Essa entidade pertence a um tenant?
2. Se sim, possui tenant_id?
3. tenant_id possui foreign key?
4. As consultas considerarão o tenant?
5. Os relacionamentos respeitam o tenant?
6. A unicidade é global ou por tenant?
7. Os índices consideram os padrões de consulta?
8. O soft delete está sendo considerado?
9. Existem testes de isolamento?
40. Regra para novas APIs

Ao criar um endpoint que trabalha com dados de negócio:

1. Identificar o tenant atual.
2. Validar autenticação.
3. Validar autorização.
4. Consultar dados dentro do tenant.
5. Validar relacionamentos.
6. Garantir que atualizações respeitem o tenant.
7. Garantir que exclusões respeitem o tenant.
8. Criar testes de isolamento.
41. Regra para novas queries

Antes de criar uma query sobre entidade multi-tenant,
verificar se ela precisa considerar:

tenant_id
deleted_at

Exemplo:

tenant_id = tenant atual
AND
deleted_at IS NULL

quando a operação estiver trabalhando com registros ativos.

42. Regra para acesso por ID

Conhecer o ID de um registro nunca deve ser considerado
uma autorização suficiente.

Exemplo:

/customer/{id}

deve considerar o contexto do tenant quando o recurso
for multi-tenant.

43. Regra para dados administrativos

Dados administrativos da plataforma podem possuir
escopo diferente dos dados do tenant.

Exemplos:

tenants
permissions

A estratégia de acesso deve ser definida explicitamente.

Não misturar dados da plataforma com dados de negócio
sem definir seu escopo.

44. Regra final

O isolamento multi-tenant deve ser tratado como
uma propriedade do sistema inteiro.

Não é responsabilidade exclusiva do banco ou do router.

Deve ser respeitado por:

Authentication
Authorization
API
Services
Repositories
Database
Cache
Workers
Logs
Tests
Integrations

Fluxo esperado:

Request
   |
   v
Authenticated User
   |
   v
Tenant Context
   |
   v
Business Operation
   |
   v
Tenant-aware Query
   |
   v
Database

O princípio fundamental é:

Um tenant só pode acessar e modificar dados
que pertencem ao seu próprio contexto.

Qualquer exceção deve possuir uma justificativa
explícita de negócio ou arquitetura e ser documentada.


### Local exato

```text
C:\Users\joao\Projetos\saas-erp-platform\skills\database\multi-tenancy.md