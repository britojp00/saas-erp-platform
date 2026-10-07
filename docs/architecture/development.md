# Development Environment (staging publico)

## Objetivo

Disponibilizar o SaaS ERP Platform na web como **ambiente de
desenvolvimento publico (staging)** para validacao da infraestrutura
de aplicacao completa: frontend + backend + banco proprio.

Este ambiente **nao e producao**:

- nao usa dados reais;
- nao reutiliza banco, Redis, containers ou portas de producao;
- nao participa do pipeline de deploy de `master`;
- pode ser publicado por `http://<IP-da-VM>/` enquanto nao existir
  dominio e HTTPS.

---

# 1. Arquitetura

```text
Internet
   |
   v  host:${DEV_HTTP_PORT}  (padrao 80)
Frontend Nginx  (saas-erp-dev-frontend)
   |-- /         -> SPA (try_files -> index.html)
   |-- /api/*    -> backend:8000  (URI preservada)
   |-- /health   -> backend:8000/health
   +-- /healthz  -> 200 local (liveness do container)
            |
            v
Backend Development (saas-erp-dev-backend, sem porta publicada)
   |-- PostgreSQL Development (saas-erp-dev-postgres)
   +-- Redis Development (saas-erp-dev-redis)
```

Somente o frontend publica porta no host. Backend, PostgreSQL e Redis
ficam apenas na rede interna do projeto Compose `saas-erp-dev`.

# 2. Isolamento em relacao a producao

| Barreira | Producao | Development |
|---|---|---|
| Arquivo Compose | `docker-compose.prod.yml` | `docker-compose.dev.yml` |
| Projeto Compose | (diretorio) | `name: saas-erp-dev` |
| Containers | `saas-erp-*` | `saas-erp-dev-*` |
| Volumes | `postgres_data`, `redis_data` | `dev_postgres_data`, `dev_redis_data` |
| Banco | `saas_erp` | `saas_erp_dev` |
| Porta no host | `8000` (backend) | `${DEV_HTTP_PORT:-80}` (frontend) |
| Env | `.env.prod` | `.env.dev` |
| Deploy | GitHub Actions em push para `master` | manual, por este documento |

O projeto Compose proprio (`name: saas-erp-dev`) e obrigatorio: sem
ele, o Compose usaria o nome do diretorio e reaproveitaria os
containers de producao.

Nenhum destes arquivos de producao foi alterado nesta etapa:

- `docker-compose.prod.yml`
- `.env.prod` / `.env.prod.example`
- `.github/workflows/ci.yml`
- `backend/Dockerfile`
- migrations (nenhuma migration nova foi criada)

# 3. Arquivos novos

| Arquivo | Funcao |
|---|---|
| `docker-compose.dev.yml` | orquestracao do ambiente Development |
| `.env.dev.example` | variaveis de exemplo (secrets ficam fora do Git) |
| `frontend/Dockerfile` | build Node 22 + runtime nginx 1.27 |
| `frontend/nginx.conf` | SPA + proxy reverso |
| `frontend/.dockerignore` | mantem `node_modules`, `dist` e `.env` fora da imagem |
| `backend/scripts/bootstrap_dev.py` | empresa, permissions, roles e primeiro admin |
| `backend/app/core/permissions.py` | conjunto canonico de permissions (PT-BR) |

# 4. Variaveis de ambiente

O Compose le apenas `.env.dev` (ignorado pelo Git, `!.env.dev.example`
versionado).

| Variavel | Obrigatoria | Descricao |
|---|---|---|
| `DEV_HTTP_PORT` | nao | porta do frontend (padrao `80`) |
| `POSTGRES_DB` | sim | padrao `saas_erp_dev` |
| `POSTGRES_USER` | sim | padrao `erp_dev` |
| `POSTGRES_PASSWORD` | sim | gerada fora do Git |
| `JWT_SECRET_KEY` | sim | gerada fora do Git |
| `JWT_ALGORITHM` | nao | `HS256` |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | nao | `30` |
| `CORS_ALLOWED_ORIGINS` | sim | origem publica real do ambiente |
| `LOG_LEVEL` / `LOG_JSON` | nao | `INFO` / `true` |
| `BOOTSTRAP_DEV_EMPRESA_SLUG` | sim | slug da empresa Development |
| `BOOTSTRAP_DEV_EMPRESA_NAME` | nao | nome da empresa |
| `BOOTSTRAP_DEV_ADMIN_EMAIL` | sim na 1a subida | email do primeiro administrador |
| `BOOTSTRAP_DEV_ADMIN_PASSWORD` | sim na 1a subida | senha do primeiro administrador |
| `BOOTSTRAP_DEV_ADMIN_NAME` | nao | nome completo do administrador |

Geracao de segredos (executar na VM, fora do Git):

```bash
openssl rand -hex 32   # JWT_SECRET_KEY e POSTGRES_PASSWORD
```

Nenhuma credencial versionada. O bootstrap nunca imprime a senha e
nunca possui valor padrao.

# 5. Pre-requisito de rede

Antes de considerar o acesso externo concluido:

1. verificar se a porta `80` (ou a definida em `DEV_HTTP_PORT`)
   esta liberada no NSG da VM `vm-saas-erp`;
2. se nao estiver, **nao abrir automaticamente** - relatar a
   necessidade e aguardar a decisao;
3. nao alterar nenhuma porta utilizada pela producao.

# 6. Como iniciar

Executar a partir da raiz do repositorio:

```bash
cp .env.dev.example .env.dev
# preencher .env.dev fora do Git

docker compose -f docker-compose.dev.yml --env-file .env.dev build

docker compose -f docker-compose.dev.yml --env-file .env.dev up -d postgres redis

docker compose -f docker-compose.dev.yml --env-file .env.dev \
  run --rm --no-deps backend alembic upgrade head

docker compose -f docker-compose.dev.yml --env-file .env.dev \
  run --rm --no-deps backend python -m scripts.bootstrap_dev

docker compose -f docker-compose.dev.yml --env-file .env.dev up -d
```

Se a porta `80` nao estiver disponivel, usar outra sem editar o
compose:

```bash
DEV_HTTP_PORT=8080 docker compose -f docker-compose.dev.yml \
  --env-file .env.dev up -d
```

# 7. Bootstrap Development

`scripts/bootstrap_dev.py` opera somente no banco do ambiente
Development e e idempotente:

1. renomeia permissions legadas em ingles para PT-BR preservando os
   vinculos de role (`role.read` -> `role.ler` e demais permissoes de
   governanca);
2. cria a empresa Development se nao existir;
3. garante o conjunto completo de permissions;
4. garante os perfis `admin`, `manager` e `viewer` com as vinculacoes;
5. cria o primeiro administrador apenas quando nao ha nenhum usuario
   no banco, exige `BOOTSTRAP_DEV_ADMIN_EMAIL` e
   `BOOTSTRAP_DEV_ADMIN_PASSWORD`, nunca sobrescreve usuario
   existente e nunca imprime a senha.

Execucoes posteriores apenas confirmam o estado ja existente.

# 8. Nomenclatura de permissions

Conjunto canonico em `backend/app/core/permissions.py`:

```text
cliente.ler      cliente.criar      cliente.atualizar      cliente.excluir
produto.ler      produto.criar      produto.atualizar      produto.excluir
categoria.ler    categoria.criar    categoria.atualizar    categoria.excluir
pedido.ler       pedido.criar       pedido.atualizar       pedido.cancelar
estoque.ler      estoque.atualizar
user.ler         user.criar         user.atualizar         user.excluir
role.ler         role.criar         role.atualizar         role.excluir
permission.ler
```

`/api/v1/audit-logs` e `/api/v1/auth/roles` exigem `role.ler`,
coerente com o padrao PT-BR dos demais modulos.

# 9. Comandos operacionais

```bash
# status
docker compose -f docker-compose.dev.yml --env-file .env.dev ps

# logs
docker compose -f docker-compose.dev.yml --env-file .env.dev logs -f frontend backend

# parar (volumes preservados)
docker compose -f docker-compose.dev.yml --env-file .env.dev down

# parar e apagar os dados do ambiente Development
docker compose -f docker-compose.dev.yml --env-file .env.dev down -v
```

Nenhum desses comandos enxerga containers de producao.

# 10. Validacao

- [ ] `http://<IP>/` responde
- [ ] `http://<IP>/healthz` retorna `ok` (nginx)
- [ ] `http://<IP>/health` retorna o health do backend
- [ ] `/login` abre
- [ ] login com o administrador criado pelo bootstrap funciona
- [ ] `/dashboard`, `/clientes`, `/categorias`, `/produtos`,
      `/estoque` e `/pedidos` funcionam
- [ ] refresh direto em `/pedidos/criar` e `/pedidos/:id` funciona
- [ ] a API nao aponta para `localhost` (build usa `VITE_API_URL=/api`)
- [ ] PostgreSQL e Redis nao estao publicados
- [ ] containers de producao continuam intactos

# 11. Seguranca e limitacoes

- ambiente de Development: nao usar dados reais;
- acesso inicial por `http://<IP>/` e aceitavel apenas para validar
  a infraestrutura;
- backend, PostgreSQL e Redis nao publicam portas;
- o `.env.dev` nunca e versionado nem aparece em logs;
- a producao permanece inalterada.

# 12. Evolucao para dominio e HTTPS

Etapa posterior (fora do escopo atual), sem alterar o build do
frontend:

1. registrar o dominio (manual, sem automacao de DNS nesta etapa);
2. criar registro `A`/`AAAA` apontando para o IP da VM;
3. liberar a porta `443` no NSG;
4. obter certificado (certbot na VM, certs montados no container do
   nginx via volume, ou servico Azure com certificate managed);
5. adicionar `server { listen 443; ... }` em `frontend/nginx.conf`
   com os certificados montados por volume;
6. atualizar `CORS_ALLOWED_ORIGINS` no `.env.dev` para
   `https://<dominio>`.

`VITE_API_URL=/api` continua valido porque frontend e API continuam
na mesma origem; o nginx ja envia `X-Forwarded-Proto`.

# 13. Situacao do CI/CD

- `ci.yml` nao foi alterado;
- jobs `build_and_push` e `deploy` (producao) continuam identicos;
- este ambiente e iniciado manualmente (secao 6);
- validacao de build do frontend no CI ficou para uma etapa futura;
- esta branch nao deve ser mergeada em `master` sem revisao, pois o
  pipeline de `master` dispara deploy automatico de producao.
