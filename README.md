# chave-ms-auth

Microsserviço de autenticação e autorização do projeto **Chave**.

Responsável pelo gerenciamento de usuários, geração de tokens JWT e controle de acesso (RBAC). Construído com Python + Flask e PostgreSQL.

---

## Tecnologias

- Python 3.12
- Flask (Application Factory Pattern)
- SQLAlchemy (ORM)
- PyJWT (Tokens)
- Bcrypt (Hash de senhas)
- Pytest (Testes unitários)
- Flasgger (Swagger/OpenAPI documentation)

---

## Variáveis de Ambiente

O serviço utiliza as seguintes variáveis de ambiente (podem ser configuradas no arquivo `.env`):

| Variável | Descrição | Valor Padrão |
|---|---|---|
| `PORT` | Porta onde o serviço será exposto | `3001` |
| `JWT_SECRET` | Chave secreta para assinatura dos tokens JWT | `change-me` |
| `ACCESS_TOKEN_EXPIRES` | Tempo de expiração do access token (segundos) | `900` |
| `REFRESH_TOKEN_EXPIRES` | Tempo de expiração do refresh token (segundos) | `86400` |
| `DB_HOST` | Host do banco de dados PostgreSQL | `localhost` |
| `DB_PORT` | Porta do banco de dados PostgreSQL | `5432` |
| `DB_USER` | Usuário do banco de dados | `chave` |
| `DB_PASSWORD` | Senha do banco de dados | `chave_secret` |
| `DB_NAME` | Nome do banco de dados | `chave_auth` |
| `AWS_ENDPOINT` | Endpoint para serviços AWS (LocalStack/Ministack) | `http://localhost:4566` |

---

## Desenvolvimento Local

### Executando com a stack completa (Docker)

Este serviço é orquestrado pelo `chave-infra`. Para subir toda a stack:

```bash
cd ../chave-infra
make setup
```

### Reconstruindo a imagem após mudanças de código

Sempre que houver alterações no código fonte e você desejar vê-las refletidas no container Docker, utilize o comando:

```bash
make rebuild-service
```

Este comando irá derrubar a stack, remover a imagem atual do serviço e subir tudo novamente através do `chave-infra`.

---

## Testes

Os testes unitários estão localizados em `tests/unit/`.

### Preparação do ambiente de testes

```bash
make setup-tests
```

### Execução dos testes

```bash
make test
```

### Limpeza do ambiente de testes

```bash
make clean-tests
```

---

## API Documentation

Com o serviço rodando, a documentação interativa da API (Swagger) pode ser acessada em:

`http://localhost:3001/apidocs/`

Uma collection para o Bruno pode ser encontrada em:

`./bruno/`

---

## Arquitetura

Para detalhes sobre a organização de pastas e fluxos de dados, consulte [docs/architecture.md](./docs/architecture.md).
