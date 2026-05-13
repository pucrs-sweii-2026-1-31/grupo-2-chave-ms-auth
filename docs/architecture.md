# Arquitetura do MS Auth

## 1. Objetivo

O MS Auth é o microsserviço responsável pela autenticação e autorização da plataforma de gerenciamento de competências.

Esse serviço deve controlar:

* cadastro de usuários;
* login;
* geração e validação de tokens JWT;
* renovação de sessão;
* logout;
* controle de permissões;
* autenticação para acesso às funcionalidades protegidas da plataforma.

O microsserviço serve como camada de segurança para os demais módulos do sistema, como:

* gerenciamento de competências;
* questionários;
* relatórios;
* grupos;
* painel administrativo.

---

## 2. Estrutura Atual do Projeto

Estrutura identificada no projeto:

```text
auth_service/
├── models/       # Definição das tabelas e esquemas (SQLAlchemy)
├── repositories/ # Camada de acesso a dados (Abstração do DB)
├── routes/       # Endpoints e Blueprints (Interface REST)
├── services/     # Regras de negócio e lógica de segurança
├── config.py     # Variáveis de ambiente (DB_URL, JWT_SECRET)
├── __init__.py   # Fábrica do App (Application Factory)

tests/            # Testes unitários e de integração
bruno/            # Coleção de requisições para teste de API (Bruno)
db/               # Scripts de inicialização e Dockerfile do banco
run.py
requirements.txt
Dockerfile
Makefile          # Comandos para automação (testes, setup)
```
---


## 3. Responsabilidade das Camadas

models/: Define a estrutura da tabela no banco. A senha é armazenada como um hash bcrypt (string). Utiliza o SQLAlchemy para representar as entidades.

repositories/: Camada responsável por realizar as operações de persistência e consulta no banco de dados. Isola a lógica de busca (SQLAlchemy/Query) das regras de negócio.

routes/: Recebe os dados do Frontend (JSON). Sua função é validar a estrutura básica da requisição e encaminhar para os serviços.

services/: Camada onde reside a inteligência e regras de negócio. Aqui é feita a verificação de hash com bcrypt, a criação do payload do JWT e a lógica de expiração dos tokens. Utiliza os repositórios para persistência.

config.py: Centraliza o uso de variáveis de ambiente, garantindo que chaves de segurança não fiquem expostas diretamente no código.


## 4. Documentação da API (Swagger)

A lista completa de endpoints, parâmetros e formatos de resposta está documentada utilizando Swagger (OpenAPI).

A documentação interativa pode ser acessada em:

```text
/apidocs
```

---

## 5. Observabilidade e Logs

O sistema utiliza o módulo nativo de `logging` do Python.

* **Development:** Nível `DEBUG` ativado, exibindo payloads de requisições e detalhes internos.
* **Production:** Nível `INFO` por padrão.
* Logs estruturados para facilitar a depuração de erros de banco, falhas de autenticação e validação de tokens.

---

## 6. Fluxo de Cadastro

Fluxo esperado:

1. O frontend envia os dados de cadastro.
2. O backend valida os campos obrigatórios.
3. O sistema verifica se o usuário já existe.
4. A senha é criptografada utilizando bcrypt.
5. O usuário é salvo no banco de dados.
6. Tokens JWT podem ser gerados automaticamente após o cadastro.
7. O sistema retorna sucesso ou erro.

---

## 7. Fluxo de Login

Fluxo esperado:

1. O usuário informa e-mail e senha.
2. O frontend envia os dados para o backend.
3. O backend valida os dados recebidos.
4. O sistema busca o usuário pelo e-mail.
5. A senha informada é comparada com a senha criptografada.
6. Caso as credenciais estejam corretas:

   * access token é gerado;
   * refresh token é gerado.
7. Os tokens são retornados para o frontend.
8. O frontend armazena os tokens para autenticação futura.

---

## 8. Fluxo de Rotas Protegidas

Fluxo esperado:

1. O frontend envia o token JWT no cabeçalho da requisição.
2. O backend valida o token.
3. O sistema verifica permissões do usuário.
4. O acesso é permitido ou negado.

Formato do header:

```text
Authorization: Bearer <access_token>
```

Possíveis respostas:

```text
200 OK
401 Unauthorized
403 Forbidden
```

---

## 9. Fluxo de Refresh Token

Fluxo esperado:

1. O frontend envia o refresh token.
2. O backend valida o token.
3. Um novo access token é gerado.
4. O sistema retorna o novo token.

---

## 10. Fluxo de Logout

Fluxo esperado:

1. O usuário solicita logout.
2. O frontend remove os tokens armazenados.
3. Opcionalmente o backend pode invalidar o refresh token.
4. O usuário é redirecionado para a tela de login.

Como JWT é stateless, o logout pode ser tratado principalmente pelo frontend removendo os tokens locais.

---

## 11. Fluxo de Usuário Atual

Fluxo esperado:

1. O frontend envia o access token.
2. O backend valida o token.
3. O backend identifica o usuário autenticado.
4. Os dados do usuário são retornados.

---

## 12. JWT

O sistema utiliza autenticação baseada em JWT.

Dois tipos de token devem ser utilizados:

### Access Token

Responsável por autenticar requisições protegidas.

Características:

* tempo de expiração curto;
* enviado no Authorization Header.

---

### Refresh Token

Responsável por renovar sessões sem exigir novo login.

Características:

* tempo de expiração maior;
* utilizado no endpoint `/refresh`.

---

## 13. RBAC (Role-Based Access Control)

O sistema deve utilizar controle de acesso baseado em papéis.

Papéis sugeridos:

```text
ADMIN
USER
```

---

### ADMIN

Permissões administrativas:

* gerenciar usuários;
* alterar permissões;
* acessar relatórios administrativos;
* gerenciar grupos;
* acessar painel administrativo.

---

### USER

Permissões comuns:

* autenticar-se no sistema;
* acessar funcionalidades permitidas;
* responder questionários;
* acessar dados do próprio perfil.

---

## 14. Integração com o Frontend

A tela de autenticação deve se comunicar diretamente com o MS Auth.

Fluxo esperado:

```text
Tela de Login
        ↓
POST /login
        ↓
MS Auth valida credenciais
        ↓
JWT é gerado
        ↓
Frontend armazena tokens
        ↓
Usuário acessa área protegida
```

Fluxo de erro:

```text
Credenciais inválidas
        ↓
Backend retorna erro
        ↓
Frontend exibe mensagem
```

---

## 15. Integração com Outros Microsserviços

O MS Auth deve atuar como camada central de segurança da plataforma.

Outros microsserviços poderão validar tokens JWT antes de permitir acesso às funcionalidades do sistema.

Exemplos:

* competências;
* questionários;
* relatórios;
* grupos;
* painel administrativo.

---

## 16. Tecnologias Utilizadas

Linguagem: Python 
Framework: Flask (Leve e modular para microsserviços)
Segurança: Bcrypt (Hash de senha) e PyJWT (Gerenciamento de tokens)
API Doc: Flasgger (Swagger/OpenAPI)
Banco de Dados: PostgreSQL (via SQLAlchemy)
Infraestrutura: Docker e Docker Compose

---

## 17. Resumo da Arquitetura

O microsserviço segue arquitetura em camadas:

```text
Frontend
   ↓
routes/
   ↓
services/
   ↓
repositories/
   ↓
models/
   ↓
database
```

Responsabilidades:

* routes/: recebe requisições HTTP;
* services/: executa regras de negócio;
* repositories/: abstrai o acesso ao banco;
* models/: representa entidades;
* JWT: autentica requisições;
* RBAC: controla permissões.

---

## 18. Escopo da Primeira Entrega (P1)


* integração com tela de autenticação;
* fluxo de login;
* geração de access token;
* geração de refresh token;
* estrutura de cadastro;
* estrutura de logout;
* validação de rotas protegidas;
* base para RBAC;
* documentação Swagger;
