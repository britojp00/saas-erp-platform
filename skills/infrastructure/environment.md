# Environment & Configuration

## Objetivo

Definir como configurações e variáveis de ambiente devem ser utilizadas no projeto SaaS ERP Platform.

A configuração da aplicação deve ser separada do código-fonte.

Nenhum segredo, credencial ou configuração específica de ambiente deve ser armazenado diretamente no código.

---

# 1. Princípios

As configurações devem:

- utilizar variáveis de ambiente;
- possuir valores padrão somente quando forem seguros;
- evitar segredos no código;
- permitir ambientes diferentes sem alterar a aplicação;
- ser centralizadas na camada de configuração;
- funcionar de forma consistente localmente, em Docker e em produção.

A aplicação não deve depender de valores fixos específicos da máquina do desenvolvedor.

---

# 2. Arquivos de Ambiente

O projeto utiliza como referência:

```text
.env
.env.example
.env

Contém as configurações reais utilizadas no ambiente local.

Esse arquivo pode conter:

senhas;
tokens;
chaves secretas;
URLs internas;
credenciais de banco;
configurações específicas da máquina.

O .env nunca deve ser versionado.

Ele deve estar incluído no .gitignore.

.env.example

Contém somente as variáveis necessárias para executar o projeto, com valores de exemplo ou placeholders.

Exemplo:

APP_ENV=development
APP_DEBUG=true

DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/saas_erp

REDIS_URL=redis://localhost:6379/0

JWT_SECRET_KEY=change-me
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

Nunca colocar credenciais reais no .env.example.

3. Nunca versionar secrets

Nunca adicionar ao Git:

.env
*.pem
*.key
*.crt
credentials.json
secrets.json

Também não devem ser armazenados diretamente no código:

DATABASE_PASSWORD = "123456"

ou:

JWT_SECRET_KEY = "minha-chave-secreta"

Segredos devem ser fornecidos pelo ambiente.

4. Configuração centralizada

A aplicação deve possuir uma camada central responsável por carregar e validar as configurações.

No backend, essa responsabilidade deve ficar em:

backend/app/core/

A configuração deve ser acessada pela aplicação através dessa camada, evitando chamadas diretas e espalhadas para leitura de variáveis de ambiente.

Exemplo conceitual:

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "development"
    app_debug: bool = False

    database_url: str
    redis_url: str

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30

A implementação definitiva deve seguir os padrões definidos na arquitetura do projeto.

5. Tipos de configuração

As configurações devem ser organizadas por responsabilidade.

Exemplos:

Aplicação
APP_ENV
APP_DEBUG
APP_NAME
APP_VERSION
Banco de dados
DATABASE_URL
Redis
REDIS_URL
Autenticação
JWT_SECRET_KEY
JWT_ALGORITHM
JWT_ACCESS_TOKEN_EXPIRE_MINUTES
CORS
CORS_ALLOWED_ORIGINS
Integrações externas
EXTERNAL_API_URL
EXTERNAL_API_TOKEN

As variáveis devem utilizar nomes claros e consistentes.

6. Ambientes

O projeto deve considerar pelo menos:

development
test
production
Development

Utilizado durante o desenvolvimento local.

Pode possuir:

debug habilitado;
serviços Docker locais;
logs mais detalhados;
ferramentas auxiliares de desenvolvimento.
Test

Utilizado pelos testes automatizados.

Deve evitar dependência de recursos reais de produção.

Quando necessário, deve utilizar:

banco de teste;
Redis de teste;
dados isolados;
configurações específicas para testes.
Production

Utilizado no ambiente real.

Deve:

desabilitar debug;
utilizar secrets seguros;
utilizar credenciais reais fornecidas pelo ambiente;
evitar exposição desnecessária de informações;
possuir configurações específicas de infraestrutura.
7. Docker

Quando a aplicação for executada através do Docker Compose, as variáveis de ambiente devem ser fornecidas através da configuração do Compose ou do ambiente de execução.

Exemplo conceitual:

services:
  backend:
    environment:
      DATABASE_URL: ${DATABASE_URL}
      REDIS_URL: ${REDIS_URL}
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}

Não colocar secrets diretamente no docker-compose.yml.

8. PostgreSQL

As credenciais do PostgreSQL devem ser configuradas através de variáveis de ambiente.

Exemplo:

POSTGRES_DB=saas_erp
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

A URL utilizada pela aplicação pode ser construída ou fornecida diretamente:

DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/saas_erp

A estratégia final deve permanecer consistente entre Docker Compose e execução local.

9. Redis

A conexão com Redis deve utilizar variável de ambiente:

REDIS_URL=redis://redis:6379/0

Em execução fora do Docker, o host pode ser diferente, por exemplo:

REDIS_URL=redis://localhost:6379/0

O código da aplicação não deve precisar ser alterado entre esses ambientes.

10. Frontend

O frontend também deve separar configurações de ambiente do código.

Exemplos de configurações:

API base URL
environment
feature flags

Segredos nunca devem ser enviados ao frontend.

Qualquer variável disponível no navegador deve ser considerada pública.

Tokens secretos, senhas e chaves privadas nunca devem ser armazenados em variáveis de ambiente expostas ao frontend.

11. Configuração local

Um novo desenvolvedor deve conseguir configurar o ambiente seguindo um fluxo previsível.

Fluxo esperado:

.env.example
      ↓
copiar para .env
      ↓
preencher configurações locais
      ↓
iniciar infraestrutura
      ↓
iniciar aplicação

Exemplo:

Copy-Item .env.example .env

Depois disso, o desenvolvedor deve preencher os valores necessários.

12. Valores padrão

Valores padrão podem ser utilizados quando não representam risco.

Exemplo aceitável:

app_env: str = "development"

Valores padrão não devem ser utilizados para esconder secrets ou credenciais obrigatórias.

Evitar:

jwt_secret_key: str = "secret123"

Quando uma variável for obrigatória, a aplicação deve falhar de forma clara durante a inicialização caso ela não esteja configurada.

13. Validação

Configurações devem ser validadas na inicialização da aplicação.

Problemas como:

variável obrigatória ausente;
URL inválida;
valor incompatível com o tipo esperado;
configuração inválida;

devem gerar erro claro.

É preferível falhar durante o startup do que executar parcialmente com uma configuração incorreta.

14. Segurança

Nunca registrar em logs:

JWT_SECRET_KEY
DATABASE_PASSWORD
API_TOKEN
ACCESS_TOKEN
REFRESH_TOKEN

Também não devem aparecer em:

mensagens de erro;
responses da API;
testes;
commits;
documentação pública.

Ao depurar configurações, registrar somente informações não sensíveis.

15. Testes

Os testes não devem depender do .env pessoal do desenvolvedor.

O ambiente de testes deve possuir configurações próprias.

Quando uma configuração for necessária para um teste, ela deve ser definida de maneira explícita no ambiente de teste.

Os testes devem permanecer reproduzíveis em:

máquina local
CI
Docker
16. CI/CD

No GitHub Actions, secrets e configurações sensíveis devem ser fornecidos através dos mecanismos de secrets e variables da plataforma.

Nunca colocar tokens diretamente no workflow:

env:
  API_TOKEN: "token-real"

Utilizar os secrets configurados no repositório ou ambiente.

17. Alterações de configuração

Ao adicionar uma nova variável de ambiente:

adicionar a configuração ao código;
adicionar a variável ao .env.example;
documentar sua finalidade quando necessário;
verificar o Docker Compose;
verificar testes;
verificar CI/CD quando aplicável.

Uma variável utilizada pelo sistema não deve existir somente no .env pessoal de um desenvolvedor.

18. Checklist

Antes de finalizar uma alteração relacionada a configuração:

 Nenhum secret foi colocado no código;
 .env continua fora do Git;
 .env.example foi atualizado;
 Configuração está centralizada;
 Variáveis obrigatórias são validadas;
 Docker utiliza as variáveis corretamente;
 Testes não dependem do .env pessoal;
 Secrets não aparecem em logs;
 Frontend não expõe informações sensíveis.
19. Ordem de consulta

Ao trabalhar com configurações, consultar nesta ordem:

skills/00-project-overview.md
skills/01-project-structure.md
skills/02-architecture.md
skills/infrastructure/README.md
skills/infrastructure/docker-compose.md
skills/infrastructure/docker.md
skills/infrastructure/environment.md

Em caso de conflito, seguir as regras mais específicas da tarefa sem quebrar os princípios gerais de segurança e arquitetura.