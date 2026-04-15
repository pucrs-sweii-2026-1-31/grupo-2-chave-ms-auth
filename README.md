# chave-ms-auth

Microsserviço de autenticação do projeto **Chave**.

Expõe uma API REST com JWT para login, refresh, logout e consulta do usuário autenticado. Persiste usuários em PostgreSQL (provisionado pelo Ministack via `chave-infra`).

---

## Tecnologias

- Node.js + Express
- JWT (`jsonwebtoken`) — access token (15 min) + refresh token (7 dias)
- bcryptjs — hash de senhas
- PostgreSQL (`pg`)

---

## Endpoints

| Método | Rota | Descrição |
|---|---|---|
| POST | `/auth/login` | Autentica com email e senha; retorna `token` e `refresh` |
| POST | `/auth/refresh` | Troca um refresh token válido por um novo access token |
| POST | `/auth/logout` | Encerra a sessão (stateless) |
| GET | `/auth/me` | Retorna os dados do usuário autenticado (`Authorization: Bearer <token>`) |

---

## Variáveis de ambiente

Copie `.env.example` e ajuste conforme necessário:

```bash
cp .env.example .env
```

| Variável | Padrão | Descrição |
|---|---|---|
| `PORT` | `3001` | Porta do servidor |
| `JWT_SECRET` | `change-me` | Segredo para assinar os tokens |
| `DB_HOST` | `localhost` | Host do PostgreSQL |
| `DB_PORT` | `5432` | Porta do PostgreSQL |
| `DB_USER` | `chave` | Usuário do banco |
| `DB_PASSWORD` | `chave_secret` | Senha do banco |
| `DB_NAME` | `chave_auth` | Nome do banco |
| `AWS_ENDPOINT` | `http://localhost:4566` | Endpoint do Ministack |

---

## Desenvolvimento local (sem Docker)

```bash
npm install
npm run dev
```

> Para rodar isolado, é necessário ter o PostgreSQL disponível na porta configurada em `.env`.
> Em ambiente completo, use `make setup` no `chave-infra`.

---

## Executando com a stack completa

Este serviço é orquestrado pelo `chave-infra`. Consulte o [README do chave-infra](https://github.com/pucrs-sweii-2026-1-30/chave-infra).
