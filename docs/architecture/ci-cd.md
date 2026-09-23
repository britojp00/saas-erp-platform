# CI/CD

## Objetivo

Definir a pipeline de Continuous Integration (CI) e Continuous Deployment (CD)
do SaaS ERP Platform utilizando GitHub Actions, Azure Container Registry (ACR)
e Azure VM.

---

# 1. Visão geral

```text
Push para master
       |
       v
  GitHub Actions
       |
       +---- CI (validação completa)
       |
       +---- Build & Push (imagem Docker para o ACR)
       |
       +---- Deploy (Azure VM via Run Command)
              |
              somente após CI e Build passarem
              somente push para master
```

Fluxo completo:

```text
CI:
GitHub Actions
       |
       v
Validação (lint, format, alembic, testes, docker build)

CD:
GitHub Actions
       |
       v
Docker build
       |
       v
Docker push (Azure Container Registry)
       |
       v
Azure VM Run Command
       |
       v
docker pull na VM
       |
       v
migration (alembic upgrade head)
       |
       v
recria somente o backend
       |
       v
health check (GET /health)
```

A pipeline é composta por três jobs encadeados, onde cada etapa
depende exclusivamente da conclusão bem-sucedida da anterior.

# 2. Diferença entre CI e CD

| Conceito | O que faz | Quando executa |
|---|---|---|
| CI | Valida o código (lint, format, testes, build) | Push e Pull Request para master |
| CD | Publica a imagem no ACR e faz deploy na Azure VM | Somente push para master, após CI passar |

CI protege o código contra regressões.

CD automatiza a implantação em produção.

Pull Requests NÃO publicam imagem nem disparam deploy de produção.

# 3. Arquivo de workflow

Localização:

```text
.github/workflows/ci.yml
```

O workflow possui três jobs:

| Job | Responsabilidade |
|---|---|
| `ci` | Todas as validações |
| `build_and_push` | Build da imagem Docker e push para o ACR |
| `deploy` | Deploy remoto na Azure VM via Run Command |

Dependências:

```text
ci
 |
 v
build_and_push
 |
 v
deploy
```

Condição de execução dos jobs de build/push e deploy:

```text
if: github.event_name == 'push' && github.ref == 'refs/heads/master'
```

# 4. Job: CI

O job `ci` é executado em:

- push para `master`
- pull request para `master`

Etapas do CI (ordem preservada):

1. Checkout do código
2. Configuração do Python 3.13
3. Instalação do uv
4. Instalação de dependências (`uv sync --frozen`)
5. Ruff check
6. Ruff format check
7. Alembic upgrade head
8. Alembic check
9. Pytest (269 testes)
10. Docker build

Todas as etapas devem passar para que o pipeline seja considerado válido.

O job `ci` executa apenas validações. Ele não publica imagem
e não faz deploy.

# 5. Job: build_and_push

Características:

- Depende do job `ci` (através de `needs: ci`)
- Executa somente quando:
  - o evento é `push` (não pull request)
  - a branch é `master`
- Executa em `ubuntu-24.04`

Permissões do job:

```text
contents: read
id-token: write
```

`id-token: write` é obrigatório para a autenticação OIDC na Azure.

Etapas:

1. Checkout do código
2. Azure Login via OIDC (`azure/login@v2`)
3. Login no ACR com Azure CLI (`az acr login --name saaserpplatforma`)
4. Docker build da imagem
5. Docker push da imagem

Imagem publicada:

```text
saaserpplatforma-e6gtb8bqbgesdxgr.azurecr.io/saas-erp-backend:<git-sha>
```

A tag é o `${{ github.sha }}` do commit que disparou o workflow.

Regras da tag:

- tag imutável (cada commit gera uma imagem distinta)
- NÃO depende de `latest`
- NÃO utiliza senha do ACR, admin user, client secret
  nem docker username/password hardcoded

Login no ACR é feito exclusivamente via Azure CLI após o
Azure Login OIDC.

# 6. Job: deploy

Características:

- Depende do job `build_and_push` (através de `needs: build_and_push`)
- Executa somente quando:
  - o evento é `push` (não pull request)
  - a branch é `master`
- Executa em `ubuntu-24.04`

Permissões do job:

```text
contents: read
id-token: write
```

Etapas:

1. Azure Login via OIDC (`azure/login@v2`)
   com os três secrets do GitHub
2. Execução remota do deployment na VM via:

```text
az vm run-command invoke
  --resource-group rg-saas-erp-platform
  --name vm-saas-erp
  --command-id RunShellScript
```

## 6.1 Usuário de execução na VM

O Run Command executa o script como usuário elevado por padrão.

Para evitar problemas de ownership do repositório e manter o
deployment executando como o usuário `azureuser`, o bloco
principal de comandos é executado com:

```bash
sudo -u azureuser -H bash -lc
```

## 6.2 Script remoto de deployment

O script remoto executa exatamente as seguintes etapas:

1. Entrar em:

```text
/home/azureuser/saas-erp-platform
```

2. Atualizar o repositório:

```bash
git fetch origin master
git reset --hard origin/master
```

O `.env.prod` não é removido nem alterado por esse processo.

3. Autenticar a VM no Azure usando a Managed Identity:

```bash
az login --identity
```

4. Autenticar no ACR:

```bash
az acr login --name saaserpplatforma
```

5. Definir a imagem do backend somente para este deployment:

```bash
export BACKEND_IMAGE=saaserpplatforma-e6gtb8bqbgesdxgr.azurecr.io/saas-erp-backend:<git-sha>
```

A tag recebe o `${{ github.sha }}` do workflow.

O `.env.prod` NÃO é alterado permanentemente. A variável
`BACKEND_IMAGE` é exportada no processo e sobrescreve o valor
do `.env.prod` somente durante aquele deployment
(a variável de ambiente do shell tem precedência sobre o env-file).

6. Baixar a nova imagem:

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod pull backend
```

7. Executar a migration usando a nova imagem, sem alterar o
   backend atual:

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod \
  run --rm --no-deps backend alembic upgrade head
```

Se a migration falhar:

- o workflow falha
- o backend NÃO é recriado

8. Somente depois da migration, recriar o backend:

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod \
  up -d --no-deps backend
```

9. Health check local na VM:

```bash
curl --fail --silent --show-error http://127.0.0.1:8000/health
```

Retry configurado:

| Parâmetro | Valor |
|---|---|
| Máximo de tentativas | 30 |
| Intervalo entre tentativas | 2 segundos |
| Falha | após exceder o limite |

10. Se o health check falhar:

- o script retorna exit code diferente de zero
- o job `deploy` falha

Rollback automático NÃO é implementado nesta etapa.

## 6.3 Detecção de falha no workflow

O script remoto imprime o marcador `DEPLOY_SUCCESS` somente
depois do health check passar.

O step do workflow verifica:

1. o exit code do `az vm run-command invoke`
2. a presença do marcador `DEPLOY_SUCCESS` na saída do script

Se qualquer um dos dois falhar, o job `deploy` falha.

# 7. Autenticação e permissões

## 7.1 OIDC (GitHub Actions → Azure)

| Componente | Valor |
|---|---|
| App Registration | `saas-erp-platform-github-actions` |
| Federated credential | repo `britojp00/saas-erp-platform` |
| Branch | `master` |
| Ação usada | `azure/login@v2` |

Não existe client secret. A autenticação é feita por token OIDC
(`id-token: write`), emitido somente para o repositório e branch
corretos.

## 7.2 GitHub Secrets

| Secret | Uso |
|---|---|
| `AZURE_CLIENT_ID` | client-id do `azure/login@v2` |
| `AZURE_TENANT_ID` | tenant-id do `azure/login@v2` |
| `AZURE_SUBSCRIPTION_ID` | subscription-id do `azure/login@v2` |

Os três secrets são usados pelos jobs `build_and_push` e `deploy`.

NUNCA:

- imprimir `AZURE_CLIENT_ID`
- imprimir `AZURE_TENANT_ID`
- imprimir qualquer token
- imprimir qualquer conteúdo do `.env.prod`
- colocar secrets em YAML ou em logs

## 7.3 Permissões da identidade do GitHub

| Permissão | Escopo |
|---|---|
| Container Registry Repository Writer | ACR `saaserpplatforma` |
| Container Registry Configuration Reader and Data Access Configuration Reader | ACR `saaserpplatforma` |
| Virtual Machine Contributor | somente na VM `vm-saas-erp` |

`Repository Writer` permite o push da imagem no job
`build_and_push`.

`Virtual Machine Contributor` limitado à VM permite o
`az vm run-command invoke` no job `deploy`.

## 7.4 Managed Identity da VM

| Componente | Valor |
|---|---|
| VM | `vm-saas-erp` |
| Resource Group | `rg-saas-erp-platform` |
| Autenticação | `az login --identity` |
| Permissão no ACR | Container Registry Repository Reader |

A VM autentica-se no ACR com a própria Managed Identity.
Não existem senhas de ACR, docker login manual ou
credenciais estáticas na VM.

# 8. Fluxo completo

## Push para master

```text
git push origin master
       |
       v
GitHub Actions inicia
       |
       v
Job: ci
  ├── Checkout
  ├── Python + uv
  ├── uv sync --frozen
  ├── Ruff check
  ├── Ruff format check
  ├── Alembic upgrade head
  ├── Alembic check
  ├── Pytest (269 testes)
  └── Docker build
       |
       | (todos passaram)
       v
Job: build_and_push
  ├── Checkout
  ├── Azure Login (OIDC)
  ├── az acr login
  ├── docker build (tag = git sha)
  └── docker push para o ACR
       |
       | (push OK)
       v
Job: deploy
  ├── Azure Login (OIDC)
  └── az vm run-command invoke
        ├── git fetch/reset (como azureuser)
        ├── az login --identity (Managed Identity)
        ├── az acr login
        ├── export BACKEND_IMAGE (somente neste processo)
        ├── docker compose pull backend
        ├── docker compose run --no-deps backend alembic upgrade head
        ├── docker compose up -d --no-deps backend
        └── health check (30 tentativas, 2s)
```

## Pull Request para master

```text
Pull Request para master
       |
       v
GitHub Actions inicia
       |
       v
Job: ci
  └── executa todas as validações
       |
       v
Job: build_and_push
  └── NÃO executa (condição: push only)

Job: deploy
  └── NÃO executa (condição: push only)
```

Pull Requests NÃO publicam imagem no ACR e NÃO fazem deploy.

# 9. Segurança

## Nunca

- hardcode de tokens
- ACR admin user
- ACR password
- client secret
- SSH private key
- secrets no YAML
- secrets em logs

## Não imprimir em logs

- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- qualquer token
- qualquer conteúdo do `.env.prod`

## Mecanismos

- O workflow utiliza `${{ secrets.* }}`, que é mascarado pelo GitHub
- O login no ACR é feito via Azure CLI/OIDC, sem senha
- A VM autentica no ACR via Managed Identity, sem credenciais locais
- O `.env.prod` permanece intacto: `BACKEND_IMAGE` é sobrescrito
  apenas por exportação de variável no processo do deployment
- Os jobs de build/push e deploy possuem `permissions` mínimas
  (`contents: read`, `id-token: write`)

## Secrets antigos do Coolify

Os secrets `COOLIFY_TOKEN` e `COOLIFY_WEBHOOK` não são mais
utilizados por nenhum arquivo do repositório.

Eles ainda NÃO devem ser apagados manualmente nesta etapa.
Somente o uso deles foi removido do código e da documentação.
A remoção pode ser feita depois, em:

```text
Settings > Secrets and variables > Actions
```

# 10. Imagem Docker

O build utiliza o Dockerfile existente em `backend/Dockerfile`:

```text
backend/Dockerfile
```

Características:

- Imagem base: `python:3.13-slim`
- Gerenciador de dependências: uv
- Lockfile: `uv.lock` (reprodutibilidade)
- Porta interna: 8000
- Comando: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
- Healthcheck endpoint: `GET /health` (definido na aplicação)

Registro:

```text
saaserpplatforma-e6gtb8bqbgesdxgr.azurecr.io
```

Imagem:

```text
saas-erp-backend
```

Tag: `${{ github.sha }}` (imutável, versionada por Git SHA).

O `latest` não é utilizado.

# 11. Migrations em produção

As migrations são executadas pelo Alembic durante o deploy,
na VM, usando a NOVA imagem:

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod \
  run --rm --no-deps backend alembic upgrade head
```

Ordem do deploy:

```text
pull da nova imagem
       |
       v
alembic upgrade head (nova imagem, --no-deps)
       |
       | (migration OK)
       v
recria somente o backend (up -d --no-deps backend)
       |
       v
health check
```

Se a migration falhar:

- o job `deploy` falha
- o backend atual NÃO é recriado
- a aplicação continua no backend anterior

### Compatibilidade das migrations

As migrations devem ser planejadas de forma compatível com o backend
anterior durante o processo de deployment.

O deployment não implementa rollback automático do banco de dados.
Portanto, uma migration aplicada com sucesso não é revertida caso
o novo backend apresente falha posteriormente.

Alterações incompatíveis de schema devem utilizar estratégia de
migração em etapas (expand/contract) quando necessário.

# 12. PostgreSQL e Redis

O deployment NÃO recria PostgreSQL nem Redis.

Todas as etapas do deploy utilizam `--no-deps`:

```text
docker compose ... run --rm --no-deps backend ...
docker compose ... up -d --no-deps backend
```

PostgreSQL e Redis já estão rodando na VM e seus volumes
(`postgres_data`, `redis_data`) são persistentes.

# 13. Observabilidade pós-deploy

## GitHub Actions

- Logs completos de cada step disponíveis em Actions > Run
- Saída do `az vm run-command invoke` (stdout e stderr remotos)
- Código de retorno de cada comando verificável
- Marcador `DEPLOY_SUCCESS` confirma o fim do script remoto

## Azure VM

- Saída do Run Command no output do step de deploy
- Logs do container: `docker compose -f docker-compose.prod.yml logs backend`
- Healthcheck `GET /health` em `127.0.0.1:8000`

## Aplicação

- Logs estruturados (JSON/text) em stdout
- Eventos: `application_started`, `application_shutdown`
- Request ID para correlação
- Middleware de logging HTTP

# 14. Troubleshooting

## Deploy não executa

Verificar:

1. O evento foi um push (não pull request)?
2. A branch é master?
3. O job `ci` passou completamente?
4. O job `build_and_push` passou?
5. Os secrets `AZURE_CLIENT_ID`, `AZURE_TENANT_ID` e
   `AZURE_SUBSCRIPTION_ID` estão configurados?

## build_and_push falha no Azure Login

- Verificar a federated credential do App Registration
  (repositório `britojp00/saas-erp-platform`, branch `master`)
- Verificar os três secrets do GitHub

## build_and_push falha no push para o ACR

- Verificar a permissão Container Registry Repository Writer
  na identidade do GitHub
- Verificar o step `az acr login` no log

## deploy falha no az vm run-command invoke

- Verificar a permissão Virtual Machine Contributor
  (escopo: somente `vm-saas-erp`)
- Verificar se o Azure CLI da VM e o VM agent estão funcionando
- Verificar conectividade da VM com o Azure

## deploy falha na migration

- Ler a saída do Run Command no log do step
- O backend atual continua rodando (não foi recriado)
- Corrigir a migration e fazer um novo push

## deploy falha no health check

- Verificar quantas tentativas apareceram no log (limite: 30)
- Na VM: `docker compose -f docker-compose.prod.yml logs backend`
- Verificar se a porta 8000 está publicada
- Verificar se PostgreSQL e Redis estão healthy

## Marcador DEPLOY_SUCCESS não encontrado

- O script remoto falhou antes do health check
- Ler a saída completa do Run Command para localizar a etapa

# 15. Checklist de configuração

Antes de ativar o deploy:

- [ ] Secret `AZURE_CLIENT_ID` configurado no GitHub
- [ ] Secret `AZURE_TENANT_ID` configurado no GitHub
- [ ] Secret `AZURE_SUBSCRIPTION_ID` configurado no GitHub
- [ ] App Registration `saas-erp-platform-github-actions` existe
- [ ] Federated credential aponta para o repo/branch corretos
- [ ] Identidade do GitHub com Repository Writer no ACR
- [ ] Identidade do GitHub com Virtual Machine Contributor
      somente na VM `vm-saas-erp`
- [ ] Managed Identity da VM habilitada
- [ ] VM com Container Registry Repository Reader no ACR
- [ ] Repositório clonado na VM em `/home/azureuser/saas-erp-platform`
- [ ] `.env.prod` presente na VM (não versionado)
- [ ] `docker-compose.prod.yml` presente na VM
- [ ] PostgreSQL e Redis rodando na VM
- [ ] Primeiro push para master testado
- [ ] Secrets antigos do Coolify removidos (etapa posterior,
      somente após confirmar que não são mais usados)

# 16. Referências

- Workflow: `.github/workflows/ci.yml`
- Dockerfile: `backend/Dockerfile`
- Compose produção: `docker-compose.prod.yml`
- Health endpoint: `backend/app/main.py` (`GET /health`)
- Deployment: `docs/architecture/deployment.md`
- Skills: `skills/infrastructure/README.md`,
  `skills/infrastructure/docker.md`,
  `skills/infrastructure/docker-compose.md`
