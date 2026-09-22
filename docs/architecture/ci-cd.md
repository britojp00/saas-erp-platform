# CI/CD

## Objetivo

Definir a pipeline de Continuous Integration (CI) e Continuous Deployment (CD)
do SaaS ERP Platform utilizando GitHub Actions e Coolify.

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
       +---- CD (deploy Coolify)
              |
              somente após CI passar
              somente push para master
```

A pipeline é composta por dois estágios independentes, onde o CD
depende exclusivamente da conclusão bem-sucedida do CI.

# 2. Diferença entre CI e CD

| Conceito | O que faz | Quando executa |
|---|---|---|
| CI | Valida o código (lint, format, testes, build) | Push e Pull Request para master |
| CD | Dispara o deploy em produção | Somente push para master, após CI passar |

CI protege o código contra regressões.

CD automaiza a implantação em produção.

Pull Requests NÃO disparam deploy de produção.

# 3. Arquivo de workflow

Localização:

```text
.github/workflows/ci.yml
```

O workflow possui dois jobs:

- `ci` — executa todas as validações
- `deploy` — dispara o webhook do Coolify

# 4. Job: CI

O job `ci` é executado em:

- push para `master`
- pull request para `master`

Etapas do CI:

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

# 5. Job: CD (Deploy)

O job `deploy` possui as seguintes características:

- Depende do job `ci` (através de `needs: ci`)
- Executa somente quando:
  - o evento é `push` (não pull request)
  - a branch é `master`
- Não possui dependências de infraestrutura (PostgreSQL, Redis)
- Executa em `ubuntu-24.04`

Condição de execução:

```text
if: github.event_name == 'push' && github.ref == 'refs/heads/master'
```

# 6. Coolify Deploy Webhook

O deploy utiliza o mecanismo de Deploy Webhook do Coolify.

Fluxo:

```text
GitHub Actions
       |
       | POST (autenticado)
       v
Coolify Webhook
       |
       v
Coolify build + deploy
       |
       v
Aplicação em produção
```

A chamada HTTP é realizada via `curl` com autenticação Bearer Token.

Autenticação:

```text
Authorization: Bearer ${{ secrets.COOLIFY_TOKEN }}
```

O endpoint do webhook é definido pelo secret:

```text
${{ secrets.COOLIFY_WEBHOOK }}
```

# 7. GitHub Secrets necessários

| Secret | Descrição | Uso |
|---|---|---|
| `COOLIFY_TOKEN` | Token de autenticação do Coolify | Header Authorization Bearer |
| `COOLIFY_WEBHOOK` | URL do Deploy Webhook do Coolify | Endpoint POST para trigger |

Ambos os secrets devem ser configurados no repositório GitHub:

Settings > Secrets and variables > Actions > New repository secret

NUNCA:

- colocar valores reais no código
- colocar valores reais no workflow
- imprimir tokens nos logs
- versionar secrets

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
Job: deploy
  └── Deploy to Coolify
        ├── curl POST autenticado
        ├── valida HTTP status
        └── falha se status não for 2xx
```

## Pull Request para master

```text
git push origin feature/xyz
       |
       v
Pull Request para master
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
       v
Job: deploy
  └── NÃO executa (condição: push only)
```

# 9. Segurança

## Secrets

- `COOLIFY_TOKEN` nunca aparece nos logs do GitHub Actions
- `COOLIFY_WEBHOOK` é uma URL e também não é exposta
- O workflow utiliza `${{ secrets.* }}` que é mascarado pelo GitHub

## Validação HTTP

O deploy verifica o código de resposta HTTP:

- 2xx: deploy disparado com sucesso
- Qualquer outro código: falha com exit 1

Isso garante que falhas de autenticação ou outros erros sejam
identificados imediatamente.

# 10. Dockerfile do backend

O Coolify utiliza o Dockerfile existente em `backend/Dockerfile`:

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

O Coolify será responsável por:

- build da imagem
- execução do container
- exposição da porta
- healthcheck
- restart automático

# 11. Migrations em produção

As migrations são executadas pelo Alembic.

Fluxo de deploy:

```text
Coolify deploy
       |
       v
Novo container é criado
       |
       v
Aplicação inicia
       |
       v
Alembic upgrade head (quando configurado no Coolify)
       |
       v
Aplicação pronta
```

O Coolify deve estar configurado para executar `alembic upgrade head`
antes de iniciar a aplicação, ou a aplicação deve ser configurada
para executar migrations durante o startup quando apropriado.

# 12. Observabilidade pós-deploy

## GitHub Actions

- Logs completos de cada step disponíveis em Actions > Run
- Tempo de execução de cada step registrado
- Código de retorno de cada comando verificável

## Coolify

- Logs do container disponíveis no painel do Coolify
- Healthcheck `GET /health` verifica disponibilidade
- Restart automático em caso de falha
- Status do deploy registrado

## Aplicação

- Logs estruturados (JSON/text) em stdout
- Eventos: `application_started`, `application_shutdown`
- Request ID para correlação
- Middleware de logging HTTP

# 13. Troubleshooting

## Deploy não executa

Verificar:

1. O evento foi um push (não pull request)?
2. A branch é master?
3. O job `ci` passou completamente?
4. Os secrets `COOLIFY_TOKEN` e `COOLIFY_WEBHOOK` estão configurados?

## Deploy falha com HTTP 401

- Verificar se `COOLIFY_TOKEN` está correto
- Verificar se o token não expirou
- Verificar se o token possui permissão de deploy

## Deploy falha com HTTP 404

- Verificar se `COOLIFY_WEBHOOK` está correto
- Verificar se o endpoint do webhook existe no Coolify

## Deploy falha com outro código HTTP

- Consultar a documentação do Coolify para o código específico
- Verificar logs do Coolify

# 14. Checklist de configuração

Antes de ativar o deploy:

- [ ] Secret `COOLIFY_TOKEN` configurado no GitHub
- [ ] Secret `COOLIFY_WEBHOOK` configurado no GitHub
- [ ] Aplicação criada no Coolify
- [ ] Deploy Webhook configurado no Coolify
- [ ] Coolify apontando para o repositório Git
- [ ] Coolify configurado para build a partir de `backend/Dockerfile`
- [ ] Variáveis de ambiente configuradas no Coolify (DATABASE_URL, etc.)
- [ ] Healthcheck configurado no Coolify (`GET /health`)
- [ ] Primeiro push para master testado

# 15. Referências

- Workflow: `.github/workflows/ci.yml`
- Dockerfile: `backend/Dockerfile`
- Health endpoint: `backend/app/main.py` (`GET /health`)
- Skills: `skills/infrastructure/docker.md`, `skills/infrastructure/environment.md`
