from flask import Blueprint, request, jsonify
from ..services.auth_service import AuthService

auth = Blueprint("auth", __name__)
auth_service = AuthService()


@auth.route("/register", methods=["POST"])
def register():
    """
    Rota para registrar um novo usuário.

    Passos necessários:
    1. Validar o corpo da requisição (body): verificar se os campos obrigatórios estão presentes,
       como 'username', 'password', 'email' (se aplicável). Usar validação para garantir que
       os dados são strings não vazias e que a senha tem comprimento mínimo.

    2. Verificar se o usuário já existe no banco: fazer uma consulta no banco de dados para
       checar se o username ou email já está cadastrado. Se existir, retornar erro.

    3. Hash da senha: usar bcrypt para gerar um hash seguro da senha antes de armazenar.

    4. Salvar no banco: inserir o novo usuário no banco de dados com os dados validados e
       a senha hasheada.

    5. Gerar JWT: após o registro bem-sucedido, gerar um token JWT (access e refresh) para
       autenticar o usuário imediatamente.

    Retornar: access_token, refresh_token e mensagem de sucesso, ou erro se falhar.
    """
    # TODO: Implementar a lógica acima
    pass


@auth.route("/login", methods=["POST"])
def login():
    """
    Rota para fazer login de um usuário existente.

    Passos necessários:
    1. Validar o corpo da requisição (body): verificar se os campos 'email' e 'password'
       estão presentes e são válidos (strings não vazias).

    2. Buscar no banco: consultar o banco de dados para encontrar o usuário pelo email.
       Se não encontrado, retornar erro de credenciais inválidas.

    3. Verificar senha com bcrypt: comparar a senha fornecida com o hash armazenado no banco
       usando bcrypt.checkpw(). Se não corresponder, retornar erro.

    4. Gerar JWT: se a senha estiver correta, gerar tokens JWT (access e refresh) contendo
       informações do usuário (como user_id).

    Retornar: access_token e refresh_token, ou erro se falhar.
    """
    try:
        data = request.get_json() or {}
        access_token, refresh_token = auth_service.login(data)
        return jsonify({"access_token": access_token, "refresh_token": refresh_token}), 200
    except ValueError as error:
        return jsonify({"error": str(error)}), 400


@auth.route("/logout", methods=["POST"])
def logout():
    """
    Rota para fazer logout do usuário.

    Como JWT é stateless, o logout pode ser simples: apenas confirmar que o token foi
    "invalidado" (embora na prática, o cliente deve descartar o token).

    Passos necessários:
    1. Validar o corpo da requisição (body): opcionalmente, aceitar o refresh_token para
       invalidá-lo (se houver uma lista negra de tokens).

    2. Se implementar invalidação: adicionar o token a uma lista negra no banco ou cache.

    3. Retornar mensagem de sucesso.

    Nota: Em sistemas stateless, o logout é mais do lado do cliente.
    """
    # TODO: Implementar a lógica acima
    pass


@auth.route("/refresh", methods=["POST"])
def refresh():
    """
    Rota para renovar o access token usando o refresh token.

    Passos necessários:
    1. Validar o corpo da requisição (body): verificar se o campo 'refresh_token' está presente.

    2. Verificar o refresh token: decodificar e validar o JWT refresh token. Verificar se não
       expirou e se é válido (usar a chave secreta).

    3. Buscar no banco: opcionalmente, verificar se o usuário associado ao token ainda existe
       e está ativo.

    4. Gerar novo JWT: se válido, gerar um novo access_token (e opcionalmente um novo
       refresh_token).

    Retornar: novo access_token (e refresh_token se renovado), ou erro se falhar.
    """
    # TODO: Implementar a lógica acima
    pass
