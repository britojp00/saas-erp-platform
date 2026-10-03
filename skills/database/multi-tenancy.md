# Multi-Tenancy

## Objetivo

Este documento define as regras oficiais de implementação
do multi-tenancy no SaaS ERP Platform.

O isolamento entre tenants é um requisito obrigatório
do sistema.

Nenhum usuário, processo ou endpoint deve conseguir acessar,
alterar ou remover dados pertencentes a outra empresa sem uma
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
                ├── empresas
                ├── users
                ├── clientes
                ├── produtos
                ├── pedidos
                └── estoque

O isolamento lógico será realizado através do campo:

empresa_id

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

3. Entidade Empresa

A entidade principal é:

empresas

Estrutura conceitual:

empresas

id
name
status
created_at
updated_at
deleted_at

A tabela empresas é a raiz do isolamento entre empresas.

A tabela empresas não possui empresa_id.

4. Relacionamento com Empresa

Toda entidade de negócio que pertence a uma empresa
deve possuir:

empresa_id

Exemplo:

clientes

id
empresa_id
name
email
created_at
updated_at
deleted_at
produtos

id
empresa_id
sku
name
price
created_at
updated_at
deleted_at
pedidos

id
empresa_id
cliente_id
status
total_amount
created_at
updated_at
deleted_at
5. Entidades que não possuem empresa_id

Nem toda entidade precisa possuir empresa_id.

A decisão deve considerar a propriedade dos dados.

Exemplos que podem existir como entidades globais:

permissions

porque uma permission pode representar uma definição
da própria plataforma.

Exemplos que normalmente pertencem a uma empresa:

clientes
produtos
pedidos
estoque

A ausência de empresa_id deve ser uma decisão explícita.

Não adicionar empresa_id automaticamente a toda tabela.

6. Regra de propriedade

Antes de criar uma tabela, responder:

Quem é o proprietário desses dados?

A informação pertence:
    |
    +---- à plataforma?
    |
    +---- a uma empresa?
    |
    +---- a uma relação entre empresas?

Se os dados pertencem a uma empresa, utilizar:

empresa_id
7. Foreign Key

O campo:

empresa_id

deve possuir relacionamento com:

empresas.id

quando aplicável.

Conceito:

clientes.empresa_id
        |
        v
   empresas.id

Isso garante a integridade do relacionamento no banco.

8. Contexto de Empresa

A empresa atual deve ser determinada a partir de
uma fonte confiável da aplicação.

O sistema não deve confiar exclusivamente em:

empresa_id

enviado pelo cliente.

Exemplo incorreto:

POST /api/v1/clientes

{
    "empresa_id": "empresa-B",
    "name": "João"
}

e a aplicação aceitar esse valor como fonte de autorização.

A empresa deve ser obtida do contexto autenticado
e validada pela aplicação.

9. Autenticação e Empresa

O usuário autenticado deve possuir uma associação
com a empresa correspondente.

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
o contexto da empresa associada à sua sessão/autenticação.

10. Usuário e Empresa

A estrutura inicial prevista será:

users

id
empresa_id
name
email
password_hash
created_at
updated_at
deleted_at

Um usuário de negócio pertence a uma empresa.

O modelo final de associação pode evoluir caso o sistema
precise suportar usuários pertencentes a múltiplos tenants.

Essa mudança não deve ser introduzida sem uma necessidade real.

11. Acesso aos dados

Uma operação de leitura deve considerar:

recurso
+
empresa atual

Exemplo conceitual:

SELECT *
FROM clientes
WHERE id = :cliente_id
  AND empresa_id = :empresa_id
  AND deleted_at IS NULL

A aplicação não deve buscar somente:

WHERE id = :cliente_id

quando o recurso pertence a uma empresa.

12. Listagens

Toda listagem de uma entidade multi-tenant deve
considerar a empresa atual.

Exemplo:

GET /api/v1/clientes

deve resultar conceitualmente em:

Empresa atual
    |
    v
clientes daquela empresa

e não:

todos os clientes da plataforma
13. Busca por ID

Uma busca por ID deve respeitar a empresa.

Exemplo:

GET /api/v1/clientes/{id}

A aplicação deve validar:

cliente.id
+
cliente.empresa_id

O fato de o usuário conhecer o ID de outra empresa
não deve conceder acesso ao registro.

14. Atualização

Atualizações devem validar a empresa do registro.

Exemplo:

PUT /api/v1/produtos/{id}

A operação deve localizar o produto dentro do contexto
da empresa atual.

Conceito:

produto.id
+
produto.empresa_id

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

A exclusão lógica também deve respeitar a empresa atual.

16. Consultas de registros ativos

Consultas normais devem considerar:

deleted_at IS NULL

além do:

empresa_id = empresa atual

Conceito:

WHERE empresa_id = :empresa_id
  AND deleted_at IS NULL
17. Registros excluídos

Consultas que precisarem visualizar registros
logicamente excluídos devem declarar explicitamente
essa intenção.

Uma consulta padrão de dados ativos não deve retornar
registros com:

deleted_at IS NOT NULL
18. Criação de registros

Ao criar uma entidade pertencente a uma empresa,
o empresa_id deve ser derivado do contexto autenticado
da operação.

Não confiar no empresa_id fornecido pelo cliente
quando ele representar autorização.

Exemplo:

Usuário autenticado
        |
        v
Empresa = A
        |
        v
POST /clientes
        |
        v
cliente.empresa_id = A
19. Relações entre entidades multi-tenant

Ao trabalhar com duas ou mais entidades multi-tenant,
as relações também devem respeitar a empresa.

Exemplo:

Pedido
   |
   v
Cliente

Ao criar um pedido:

pedido.empresa_id
cliente.empresa_id

devem representar a mesma empresa.

Não permitir:

Pedido
Tenant A

Cliente
Tenant B

como uma relação válida.

20. Exemplo de validação de relacionamento

Conceito:

Criar Pedido para Cliente
        |
        v
Cliente existe?
        |
        v
Cliente pertence à empresa atual?
        |
        +---- NÃO → rejeitar
        |
        +---- SIM → continuar

A existência do registro não é suficiente.

Também é necessário validar sua propriedade.

21. Produtos e estoque

Produtos e estoques são dados pertencentes à empresa.

Exemplo:

produtos

id
empresa_id
sku
name
price
created_at
updated_at
deleted_at
estoque

id
empresa_id
produto_id
quantity
created_at
updated_at
deleted_at

O produto relacionado ao estoque deve pertencer
à mesma empresa.

22. Pedidos

Pedidos pertencem à empresa.

Exemplo:

pedidos

id
empresa_id
cliente_id
status
total_amount
created_at
updated_at
deleted_at

Ao criar um pedido:

Empresa do pedido
      =
Empresa do cliente

Os itens do pedido também devem pertencer ao contexto
do pedido.

23. Unicidade por Empresa

Regras de unicidade devem considerar o escopo da empresa
quando o dado não precisa ser globalmente único.

Exemplo:

produtos

empresa_id
sku

A regra pode ser:

UNIQUE (
    empresa_id,
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

empresa_id

como filtro.

Quando apropriado, criar índices considerando
os padrões reais de consulta.

Exemplo conceitual:

INDEX (
    empresa_id,
    created_at
)

ou:

INDEX (
    empresa_id,
    status
)

A definição final deve considerar as consultas reais
da aplicação.

26. Empresa e índices

Não criar índices somente porque uma tabela possui
empresa_id.

Avaliar:

frequência das consultas;
filtros;
ordenação;
cardinalidade;
volume de dados.

O objetivo é atender os padrões reais de acesso.

27. Repositories

Repositories devem receber ou utilizar o contexto
de empresa de forma consistente.

Uma operação como:

get_cliente(cliente_id)

não deve ignorar a empresa quando estiver sendo utilizada
para dados multi-tenant.

O padrão concreto será definido na skill de backend
e aplicado de maneira consistente.

28. Services

Services são responsáveis por aplicar regras de negócio
relacionadas à empresa.

Exemplo:

PedidoService
    |
    +---- validar cliente
    +---- validar empresa
    +---- validar estoque
    +---- criar pedido

O service não deve permitir uma operação que viole
o isolamento entre tenants.

29. Routers

Routers não devem confiar em uma empresa enviada
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
Cliente A

Tenant B
Cliente B

Depois:

Autenticar como Tenant A

GET Cliente A
→ permitido

GET Cliente B
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
Cliente A

Tenant B
Cliente B

Usuário do Tenant A tenta excluir logicamente
o Cliente B.

Resultado:

operação bloqueada

O deleted_at do Cliente B não deve ser alterado.

34. Background Jobs e Empresa

Processos executados em background também devem conhecer
o contexto da empresa quando trabalharem com dados
multi-tenant.

Exemplo:

Queue Message
    |
    +---- empresa_id
    |
    +---- entity_id
    |
    +---- operation

Um worker não deve executar uma operação de negócio
sem conhecer o contexto da empresa quando ele for necessário.

35. Cache e Empresa

Dados armazenados em cache também devem respeitar
o isolamento entre tenants.

Chaves de cache relacionadas a dados de negócio devem
considerar a empresa quando necessário.

Exemplo:

empresa:{empresa_id}:produtos:{produto_id}

Evitar chaves genéricas que possam causar colisão
ou exposição de dados entre tenants.

36. Logs e Empresa

Logs de operações multi-tenant devem permitir
identificar o contexto da empresa quando aplicável.

Exemplo:

{
  "event": "cliente_created",
  "empresa_id": "...",
  "user_id": "...",
  "request_id": "..."
}

Não registrar informações sensíveis desnecessariamente.

37. APIs públicas e Empresa

Endpoints públicos ou de integração devem possuir
uma estratégia explícita para determinar a empresa.

Não assumir que a primeira empresa encontrada no banco
é a empresa da requisição.

O contexto deve ser estabelecido através de um mecanismo
de autenticação ou identificação confiável.

38. Integrações futuras

O futuro integration-hub consumirá a API do ERP.

As integrações deverão possuir contexto de empresa
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

1. Essa entidade pertence a uma empresa?
2. Se sim, possui empresa_id?
3. empresa_id possui foreign key?
4. As consultas considerarão a empresa?
5. Os relacionamentos respeitam a empresa?
6. A unicidade é global ou por empresa?
7. Os índices consideram os padrões de consulta?
8. O soft delete está sendo considerado?
9. Existem testes de isolamento?
40. Regra para novas APIs

Ao criar um endpoint que trabalha com dados de negócio:

1. Identificar a empresa atual.
2. Validar autenticação.
3. Validar autorização.
4. Consultar dados dentro da empresa.
5. Validar relacionamentos.
6. Garantir que atualizações respeitem a empresa.
7. Garantir que exclusões respeitem a empresa.
8. Criar testes de isolamento.
41. Regra para novas queries

Antes de criar uma query sobre entidade multi-tenant,
verificar se ela precisa considerar:

empresa_id
deleted_at

Exemplo:

empresa_id = empresa atual
AND
deleted_at IS NULL

quando a operação estiver trabalhando com registros ativos.

42. Regra para acesso por ID

Conhecer o ID de um registro nunca deve ser considerado
uma autorização suficiente.

Exemplo:

/cliente/{id}

deve considerar o contexto da empresa quando o recurso
for multi-tenant.

43. Regra para dados administrativos

Dados administrativos da plataforma podem possuir
escopo diferente dos dados da empresa.

Exemplos:

empresas
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
Contexto de Empresa
   |
   v
Business Operation
   |
   v
Query com escopo de empresa
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