# Deployment

## Objetivo

Definir como o SaaS ERP Platform é implantado em produção.

---

# 1. Ambientes

| Ambiente | Arquivo Compose | Propósito |
|---|---|---|
| Local | `docker-compose.yml` | Desenvolvimento (postgres + redis) |
| Produção | `docker-compose.prod.yml` | Deployment (backend + postgres + redis) |

O `docker-compose.yml` local NÃO deve ser utilizado em produção.

O `docker-compose.prod.yml` NÃO deve ser utilizado em desenvolvimento.

# 2. Infraestrutura de produção

## Serviços

```text
                    ┌─────────────────┐
                    │    Internet     │
                    └────────┬────────┘
                             |
                           HTTP
                             |
                             v
                    ┌─────────────────┐
                    │     Backend     │
                    │    FastAPI      │
                    │   porta 8000    │
                    └────────┬────────┘
                             |
                ┌────────────┴────────────┐
                |                         |
                v                         v
         ┌─────────────┐          ┌─────────────┐
         │ PostgreSQL  │          │    Redis    │
         │  interna    │          │   interna   │
         └─────────────┘          └─────────────┘
```

## Serviços do docker-compose.prod.yml

| Serviço | Imagem | Porta exposta | Volume |
|---|---|---|---|
| postgres | postgres:17-alpine | nenhuma | postgres_data |
| redis | redis:7-alpine | nenhuma | redis_data |
| backend | ${BACKEND_IMAGE} | 8000:8000 | nenhuma |

## Portas

| Serviço | Host | Container | Exposta publicamente |
|---|---|---|---|
| backend | 8000 | 8000 | sim |
| postgres | - | 5432 | não |
| redis | - | 6379 | não |

PostgreSQL e Redis somente são acessíveis internamente
pela rede do Docker Compose.

# 3. Variáveis de ambiente

## Arquivo de referência

```text
.env.prod.example
```

## Arquivo de produção (na VM)

```text
.env.prod
```

O `.env.prod` NUNCA deve ser versionado.

## Variáveis obrigatórias

| Variável | Descrição | Exemplo |
|---|---|---|
| `BACKEND_IMAGE` | Imagem do backend | `saas-erp-backend:local` |
| `POSTGRES_DB` | Nome do banco | `saas_erp` |
| `POSTGRES_USER` | Usuário do banco | `postgres` |
| `POSTGRES_PASSWORD` | Senha do banco | (secret) |
| `JWT_SECRET_KEY` | Chave JWT | (secret) |
| `JWT_ALGORITHM` | Algoritmo JWT | `HS256` |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Expiração do token | `30` |
| `CORS_ALLOWED_ORIGINS` | Origens permitidas | `https://app.example.com` |

## Variáveis com valor padrão

| Variável | Padrão |
|---|---|
| `LOG_LEVEL` | `INFO` |
| `LOG_JSON` | `true` |

## Variáveis sobrescritas pelo Compose

O `docker-compose.prod.yml` sobrescreve `DATABASE_URL` e `REDIS_URL`
para utilizar nomes dos serviços Docker internos:

```text
DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/dbname
REDIS_URL=redis://redis:6379/0
```

Isso é necessário porque o backend roda dentro da rede Docker
e não deve utilizar `localhost`.

# 4. BACKEND_IMAGE

A variável `BACKEND_IMAGE` permite trocar a imagem do backend
sem alterar o compose.

## Build local na VM

```bash
BACKEND_IMAGE=saas-erp-backend:local
```

Build:

```bash
docker build -t saas-erp-backend:local ./backend
```

## Azure Container Registry (futuro)

```bash
BACKEND_IMAGE=<registry>.azurecr.io/saas-erp-backend:<tag>
```

A estrutura do compose permanece a mesma.

# 5. Volumes

| Volume | Serviço | Conteúdo |
|---|---|---|
| postgres_data | postgres | Dados do banco PostgreSQL |
| redis_data | redis | Dados do Redis (AOF) |

Volumes são persistentes e sobrevivem à recriação dos containers.

Para remover dados (DESTRUTIVO):

```bash
docker compose -f docker-compose.prod.yml down -v
```

# 6. Healthchecks

| Serviço | Comando | Intervalo |
|---|---|---|
| postgres | `pg_isready -U user -d db` | 5s |
| redis | `redis-cli ping` | 5s |

O backend depende de ambos via `depends_on` com `condition: service_healthy`.

O backend possui `GET /health` disponível para uso externo.

# 7. Migrations

Migrations NÃO são executadas automaticamente pelo compose.

Executar manualmente após cada deploy:

```bash
docker compose -f docker-compose.prod.yml exec -T backend alembic upgrade head
```

Fluxo de deploy:

```bash
# 1. Parar containers antigos
docker compose -f docker-compose.prod.yml down

# 2. Atualizar imagem (se necessário)
docker pull <nova-imagem>
# ou: docker build -t saas-erp-backend:local ./backend

# 3. Iniciar containers
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d

# 4. Executar migrations
docker compose -f docker-compose.prod.yml exec -T backend alembic upgrade head

# 5. Verificar status
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs backend
```

# 8. Comandos principais

## Iniciar

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d
```

## Parar

```bash
docker compose -f docker-compose.prod.yml down
```

## Ver status

```bash
docker compose -f docker-compose.prod.yml ps
```

## Ver logs

```bash
docker compose -f docker-compose.prod.yml logs backend
docker compose -f docker-compose.prod.yml logs postgres
```

## Reconstruir

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
```

# 9. localhost vs nomes de serviços

| Contexto | Host correto |
|---|---|
| Desenvolvimento local (Windows) | `localhost` |
| Docker Compose (interno) | nome do serviço |

```text
Backend no Windows → localhost:5432 (PostgreSQL)
Docker Compose     → postgres:5432  (PostgreSQL)
```

O `docker-compose.prod.yml` já configura `DATABASE_URL` e `REDIS_URL`
com os nomes corretos dos serviços.

# 10. Segurança

## Portas

- Apenas a porta 8000 (backend) é exposta
- PostgreSQL e Redis ficam internos à rede Docker
- Nenhuma porta de dados deve ser publicada

## Secrets

- `.env.prod` nunca é versionado
- `.env.prod.example` contém apenas exemplos
- Secrets não aparecem no `docker-compose.prod.yml`
- Docker Compose usa `${VARIAVEL}` que é resolvida do `.env.prod`

## TLS/HTTPS

HTTPS não é configurado neste estágio.

Será adicionado em etapa posterior (reverse proxy).

# 11. Observabilidade

## Logs

- Backend escreve em stdout (JSON ou texto)
- PostgreSQL escreve em stdout
- Redis escreve em stdout

## Health

- `GET /health` — healthcheck da aplicação
- PostgreSQL: `pg_isready`
- Redis: `redis-cli ping`

## Restart

Todos os serviços utilizam `restart: unless-stopped`.

# 12. Troubleshooting

## Backend não inicia

```bash
docker compose -f docker-compose.prod.yml logs backend
```

Verificar:

- PostgreSQL e Redis estão healthy?
- Variáveis de ambiente estão configuradas?
- Imagem do backend existe?

## Backend não conecta ao banco

Verificar:

- `DATABASE_URL` usa `postgres:5432` (não `localhost`)?
- PostgreSQL está healthy?
- Senha está correta?

## Migrations falham

```bash
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

Verificar:

- Conexão com banco está funcionando?
- Migrations estão no código fonte?
- Alembic consegue acessar `alembic.ini`?

# 13. Checklist de deploy

- [ ] `.env.prod` criado na VM com valores reais
- [ ] Imagem do backend construída ou baixada
- [ ] `docker compose -f docker-compose.prod.yml --env-file .env.prod up -d`
- [ ] Containers estão healthy
- [ ] Migrations executadas: `alembic upgrade head`
- [ ] `GET /health` retorna 200
- [ ] Logs não contêm erros
- [ ] PostgreSQL e Redis não estão expostos publicamente

# 14. Referências

- Compose local: `docker-compose.yml`
- Compose produção: `docker-compose.prod.yml`
- Env exemplo produção: `.env.prod.example`
- Dockerfile: `backend/Dockerfile`
- Skills: `skills/infrastructure/docker.md`, `skills/infrastructure/docker-compose.md`
