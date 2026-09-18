# Backend Schemas

## Objetivo

Definir os padrões para criação, organização, validação e evolução dos schemas Pydantic utilizados pelo backend do SaaS ERP Platform.

Schemas representam os contratos de dados da API.

Este documento complementa:

```text
skills/02-architecture.md
skills/backend/README.md
skills/backend/architecture.md
skills/backend/api.md
skills/backend/services.md
skills/backend/repositories.md

A responsabilidade principal dos schemas é definir:

Formato
Tipos
Validação estrutural
Contrato de entrada
Contrato de saída

Regras de negócio devem permanecer no service.

1. Localização

Os schemas ficam em:

backend/app/schemas/

Exemplo:

schemas/
├── auth.py
├── tenant.py
├── user.py
├── customer.py
├── product.py
├── category.py
├── inventory.py
├── order.py
└── common.py

A organização deve acompanhar os domínios da aplicação.

2. Responsabilidade

Um schema deve responder:

Quais dados entram?
Quais dados saem?
Quais são os tipos?
Quais regras estruturais devem ser validadas?

Exemplos de validação apropriada:

campo obrigatório
tipo correto
formato de e-mail
UUID válido
valor mínimo
valor máximo
string vazia
formato de data
3. Schema não é Model

Pydantic schema e SQLAlchemy model possuem responsabilidades diferentes.

Pydantic
→ contrato da API

SQLAlchemy
→ persistência no banco

Não utilizar o model SQLAlchemy como substituto automático do contrato da API.

4. Separação

Quando necessário, separar schemas por finalidade:

Create
Update
Response
List
Filter

Exemplo:

CustomerCreate
CustomerUpdate
CustomerResponse
CustomerList
CustomerFilter

Nem todo recurso obrigatoriamente precisará de todos eles.

5. Create

Schemas Create representam os dados necessários para criar um recurso.

Exemplo:

class CustomerCreate(BaseModel):
    name: str
    email: str | None = None

Não incluir normalmente campos controlados pelo backend:

id
tenant_id
created_at
updated_at
deleted_at

quando esses valores forem definidos internamente.

6. Update

Schemas Update representam alterações parciais ou completas conforme o contrato da API.

Exemplo:

class CustomerUpdate(BaseModel):
    name: str | None = None
    email: str | None = None

Para PATCH, os campos normalmente devem ser opcionais.

O service deve distinguir:

campo não enviado

de:

campo enviado explicitamente como null

quando essa diferença tiver significado no domínio.

7. Response

Schemas Response representam os dados que podem ser expostos pela API.

Exemplo:

class CustomerResponse(BaseModel):
    id: UUID
    name: str
    email: str | None
    created_at: datetime
    updated_at: datetime

Não retornar automaticamente todos os campos existentes no model.

O response deve representar o contrato público do recurso.

8. Campos internos

Campos internos não devem aparecer no response simplesmente porque existem no banco.

Exemplos:

password_hash
internal_notes
technical_flags
internal_tokens
security_metadata

Esses campos devem permanecer fora do schema de resposta quando não fizerem parte do contrato público.

9. Read-only

Campos normalmente controlados pelo backend:

id
created_at
updated_at
deleted_at

não devem ser aceitos em schemas de criação ou atualização sem uma necessidade explícita.

10. UUID

IDs devem utilizar UUID em vez de str genérico quando o contrato representar um UUID.

Exemplo:

from uuid import UUID

class CustomerResponse(BaseModel):
    id: UUID

Isso permite validação estrutural automática.

11. Datetime

Timestamps devem utilizar tipos apropriados.

Exemplo:

from datetime import datetime

created_at: datetime

O backend deve trabalhar com timestamps timezone-aware.

A representação da API deve utilizar formato compatível com ISO 8601.

Exemplo:

2026-09-17T18:30:00Z
12. Decimal

Valores monetários não devem utilizar float.

Preferir:

from decimal import Decimal

price: Decimal

Isso mantém compatibilidade com NUMERIC no PostgreSQL.

13. Quantidades

Quantidades devem utilizar tipos coerentes com o domínio.

Exemplo:

quantity: int

ou:

quantity: Decimal

quando a regra exigir precisão decimal.

Não utilizar float sem uma justificativa específica.

14. Strings

Strings devem possuir validações apropriadas quando houver limites definidos.

Exemplo:

name: str = Field(min_length=1, max_length=255)

Não adicionar limites arbitrários somente por conveniência.

Os limites devem refletir:

regra do domínio
banco de dados
contrato da API
15. Campos obrigatórios

Um campo deve ser obrigatório quando o domínio exigir sua presença.

Exemplo:

name: str

Campo opcional:

description: str | None = None

Não transformar campos obrigatórios em opcionais apenas para facilitar o frontend.

16. Null

Diferenciar:

campo opcional

de:

campo que aceita null

Esses conceitos podem possuir significados diferentes dependendo do contrato.

Exemplo:

email: str | None = None

significa que o campo pode estar ausente conforme o comportamento do schema e também representar None.

A semântica definitiva deve ser definida conforme o endpoint.

17. Default

Valores padrão podem ser utilizados quando o padrão fizer sentido no contrato.

Exemplo:

page: int = 1
page_size: int = 20

Não utilizar defaults para esconder ausência de informações obrigatórias.

Evitar:

status: str = "active"

quando o valor deveria ser explicitamente decidido pelo backend.

18. Field

Utilizar Field quando forem necessários:

limites;
exemplos;
descrições;
aliases;
valores padrão controlados;
metadados relevantes.

Exemplo:

name: str = Field(
    min_length=1,
    max_length=255,
    description="Nome do cliente",
)

Não adicionar metadata excessiva somente para preencher documentação.

19. Email

Campos de e-mail podem utilizar o tipo apropriado do Pydantic quando isso melhorar a validação.

Exemplo:

from pydantic import EmailStr

email: EmailStr

A validação estrutural não substitui as regras de unicidade e negócio.

Por exemplo:

formato válido
≠
e-mail disponível

A segunda verificação pertence à aplicação e ao banco.

20. Enum

Quando o domínio possuir um conjunto fechado de valores, considerar Enum.

Exemplo:

class OrderStatus(str, Enum):
    draft = "draft"
    confirmed = "confirmed"
    cancelled = "cancelled"

Isso evita aceitar valores arbitrários.

Não utilizar strings livres quando o domínio realmente possuir estados fechados.

21. Status de negócio

Enums podem representar estados conhecidos.

Exemplo:

draft
confirmed
completed
cancelled

O schema valida que o valor pertence ao conjunto esperado.

A transição entre estados continua sendo responsabilidade do service.

22. Regras de negócio

Schemas não devem consultar banco para validar regras de negócio.

Evitar:

class CustomerCreate(BaseModel):

    def validate_email_unique(self):
        ...

O schema pode validar:

e-mail possui formato válido

O service/repository pode validar:

e-mail ainda não está cadastrado
23. Cross-field validation

Validações que dependem somente dos campos presentes no próprio payload podem permanecer no schema.

Exemplo:

start_date <= end_date

ou:

password_confirmation == password

quando fizer parte do contrato de entrada.

Quando a validação depender do banco ou do estado do domínio, utilizar o service.

24. Validators

Validators do Pydantic podem ser utilizados quando a regra for estrutural.

Exemplos:

normalização
formatação
validação de campos relacionados

Evitar colocar chamadas externas ou consultas SQL em validators.

25. Normalização

Schemas podem normalizar valores quando isso fizer parte do contrato.

Exemplo:

remover espaços externos
normalizar formato conhecido

A normalização deve ser previsível.

Não alterar silenciosamente valores de negócio importantes.

26. Segurança

Schemas devem rejeitar ou ignorar campos que o cliente não deve controlar, conforme a configuração apropriada.

Exemplo:

tenant_id
user_id
role
permissions
created_at

não devem ser utilizados como forma de conceder privilégios ou alterar contexto.

A segurança não pode depender somente da configuração do Pydantic; services e banco também devem proteger o sistema.

27. Mass Assignment

Não permitir que um payload genérico atualize campos arbitrários da entidade.

Evitar:

for field, value in payload.items():
    setattr(entity, field, value)

quando o payload puder conter campos que o cliente não deveria alterar.

Preferir schemas Update explícitos.

28. Create x Update

Não assumir que o mesmo schema serve para criação e atualização.

Exemplo:

Create
→ name obrigatório

Update
→ name opcional

Isso permite representar corretamente a diferença entre:

criar recurso

e:

alterar recurso existente
29. Response x Database

O response schema não precisa reproduzir exatamente o model.

Um recurso pode possuir:

20 campos no banco

e:

8 campos na API

quando somente esses 8 forem necessários.

Essa separação ajuda a reduzir acoplamento.

30. Nested Schemas

Respostas podem conter estruturas aninhadas quando isso representar o contrato da API.

Exemplo:

class OrderItemResponse(BaseModel):
    product_id: UUID
    quantity: int


class OrderResponse(BaseModel):
    id: UUID
    items: list[OrderItemResponse]

Evitar aninhamentos excessivamente profundos.

31. List Schemas

Para endpoints de listagem, considerar um schema específico.

Exemplo:

class CustomerListResponse(BaseModel):
    items: list[CustomerResponse]
    page: int
    page_size: int
    total: int

A estrutura deve ser consistente entre endpoints semelhantes.

32. Filter Schemas

Filtros complexos podem utilizar schemas próprios.

Exemplo:

class CustomerFilter(BaseModel):
    search: str | None = None
    active: bool | None = None

Isso facilita:

validação
documentação
reutilização
testes
33. Query Parameters

Nem todo filtro precisa ser transformado em schema.

Para filtros simples, FastAPI pode receber parâmetros diretamente.

Exemplo:

async def list_customers(
    search: str | None = None,
    page: int = 1,
):
    ...

A decisão deve considerar a complexidade do contrato.

34. Paginação

Schemas de paginação devem possuir limites apropriados.

Exemplo:

page: int = Field(default=1, ge=1)
page_size: int = Field(default=20, ge=1, le=100)

Os limites devem refletir o comportamento esperado da aplicação.

Não permitir tamanhos arbitrariamente grandes.

35. Ordenação

Valores de ordenação podem ser representados por enum quando o conjunto for conhecido.

Exemplo:

class CustomerSortField(str, Enum):
    name = "name"
    created_at = "created_at"

Isso reduz a possibilidade de parâmetros inválidos chegarem ao repository.

36. Sort Direction

Também pode existir um enum:

class SortDirection(str, Enum):
    asc = "asc"
    desc = "desc"

A camada de persistência deve converter esses valores para as colunas e expressões SQL apropriadas.

37. Schema compartilhado

Schemas comuns podem ser definidos em:

schemas/common.py

Exemplos possíveis:

Pagination
SortDirection
ErrorResponse
PageResponse

Não criar abstrações genéricas antes de existir reutilização real.

38. Error Schemas

Quando o formato de erro da API estiver definido, poderá existir um schema específico.

Exemplo:

class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    detail: ErrorDetail

Isso ajuda a manter respostas de erro consistentes.

39. Auth Schemas

Schemas de autenticação devem representar somente os dados necessários.

Exemplo:

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

Response:

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

Não retornar informações sensíveis desnecessárias.

40. Password Fields

Schemas que recebem senhas podem conter:

password
current_password
new_password

Esses campos nunca devem ser retornados por schemas de response.

Também não devem aparecer em logs.

41. Configuração ORM

Quando um response schema precisar ser criado a partir de um objeto SQLAlchemy, utilizar a configuração Pydantic apropriada para leitura de atributos do objeto.

Exemplo conceitual:

class CustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

Isso deve ser utilizado somente quando fizer sentido para o padrão adotado.

42. Serialization

A serialização deve ser controlada pelo schema.

Não depender de:

repr()
str()
__dict__

do model SQLAlchemy para formar respostas da API.

Isso pode expor campos internos e criar contratos instáveis.

43. Decimal Serialization

Valores monetários devem possuir uma representação consistente.

Exemplo:

{
  "price": "199.90"
}

A estratégia definitiva de serialização deve permanecer consistente entre os endpoints.

Não alternar arbitrariamente entre:

199.9
199.90
"199.90"

sem uma decisão de contrato.

44. Dates Serialization

Timestamps devem ser serializados de forma consistente.

Exemplo:

{
  "created_at": "2026-09-17T18:30:00Z"
}

Não retornar timestamps em múltiplos formatos diferentes na mesma API.

45. Campos calculados

Response schemas podem representar informações calculadas pelo service.

Exemplo:

subtotal
total
stock_available
display_name

Esses campos não precisam necessariamente existir como colunas no banco.

O contrato deve deixar clara sua origem quando necessário.

46. Dados sensíveis

Response schemas devem filtrar informações sensíveis.

Exemplos:

password_hash
tokens
secret keys
internal credentials

Nunca incluir esses campos somente porque o model possui a coluna.

47. Compatibilidade

Alterar um response schema pode quebrar consumidores.

Mudanças que exigem atenção:

remover campo
alterar tipo
alterar formato
renomear campo
alterar semântica

Adicionar campos pode também exigir avaliação dependendo do consumidor.

A API deve evoluir de forma consciente.

48. Versionamento

Schemas fazem parte da versão da API.

Exemplo:

api/v1

Uma alteração incompatível pode exigir:

api/v2

quando não existir estratégia adequada de compatibilidade.

49. Testes

Schemas devem possuir testes quando sua validação for relevante.

Testar:

entrada válida
entrada inválida
campo obrigatório
limites
enum
UUID
e-mail
datas
valores monetários
campos proibidos
50. Testes de segurança

Testar tentativas de enviar campos que o cliente não deve controlar.

Exemplo:

{
  "name": "Cliente",
  "tenant_id": "tenant-de-outro-contexto",
  "role": "Administrator"
}

O backend não deve utilizar esses campos para conceder acesso.

51. Schemas e Tenant

Normalmente tenant_id não precisa fazer parte dos schemas públicos de criação de entidades quando ele é determinado pelo contexto autenticado.

Exemplo:

POST /customers

Request:

{
  "name": "Cliente"
}

O backend determina:

tenant_id

através do contexto autenticado.

52. Schemas e User ID

Da mesma forma, user_id relacionado ao usuário autenticado não deve ser aceito do frontend quando deveria ser derivado do contexto autenticado.

Evitar:

{
  "user_id": "outro-usuario"
}

como mecanismo de identidade.

53. PATCH

Para endpoints PATCH, considerar cuidadosamente a distinção entre:

não enviado

e:

enviado como null

Exemplo:

{}

pode significar:

nenhuma alteração

enquanto:

{
  "email": null
}

pode significar:

remover email

A implementação deve respeitar a semântica definida para o campo.

54. Extra Fields

A política para campos extras deve ser definida conscientemente.

Quando o contrato exigir payload estrito, considerar rejeitar campos desconhecidos.

Isso reduz:

erros de digitação
mass assignment
contratos ambíguos

Não escolher uma estratégia global sem considerar compatibilidade e necessidade do projeto.

55. OpenAPI

Schemas devem produzir documentação adequada no OpenAPI.

Utilizar descrições e exemplos quando eles melhorarem a compreensão do contrato.

Evitar documentação excessiva que fique desatualizada em relação ao código.

56. Dependências

Schemas devem utilizar preferencialmente:

Pydantic
FastAPI
Python standard library

Evitar adicionar dependências externas somente para validações simples já suportadas pelo ecossistema existente.

57. Clareza

Um schema deve ser fácil de ler.

Preferir:

class CustomerCreate(BaseModel):
    name: str
    email: EmailStr | None = None

a uma definição excessivamente abstrata.

O contrato deve ser evidente no código.

58. Abstrações genéricas

Evitar criar um sistema genérico para gerar automaticamente:

CreateSchema
UpdateSchema
ResponseSchema

para todas as entidades.

Domínios diferentes possuem contratos diferentes.

Reutilizar somente o que realmente for comum.

59. Ordem de implementação

Ao criar schemas para um recurso:

1. Definir contrato da API
2. Definir Create
3. Definir Update
4. Definir Response
5. Definir filtros quando necessário
6. Definir paginação quando necessário
7. Definir enums quando necessário
8. Adicionar validações estruturais
9. Criar testes
10. Validar OpenAPI
60. Checklist

Antes de finalizar um schema:

 O contrato está claro;
 Tipos estão corretos;
 Campos obrigatórios estão definidos;
 Campos opcionais estão definidos;
 UUIDs utilizam UUID;
 Datas utilizam datetime quando apropriado;
 Valores monetários utilizam Decimal;
 Enums foram considerados;
 Validações estruturais estão no schema;
 Regras de negócio estão fora do schema;
 Campos internos não são expostos;
 tenant_id não pode ser utilizado indevidamente;
 user_id não pode ser utilizado indevidamente;
 Create e Update foram separados quando necessário;
 Response não reproduz automaticamente o model;
 Paginação possui limites;
 Ordenação possui valores controlados;
 Testes existem;
 OpenAPI está correto.
61. Regra principal

Schemas representam contratos, não regras de negócio.

A separação deve permanecer:

Schema
→ formato e validação estrutural

Service
→ regra e comportamento do negócio

Repository
→ persistência

Model
→ estrutura do banco

Um schema bem definido protege o contrato da API, reduz ambiguidades e evita que detalhes internos do banco sejam expostos aos consumidores.