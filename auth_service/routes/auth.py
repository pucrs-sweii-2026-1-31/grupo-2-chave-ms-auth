import logging
from flask import Blueprint, jsonify, request

from ..services.auth_service import AuthService
from ..repositories.user_repository import UserRepository
from ..services.exceptions import AuthenticationError, ConflictError

logger = logging.getLogger(__name__)
auth = Blueprint("auth", __name__)

user_repository = UserRepository()
auth_service = AuthService(user_repository)


@auth.route("/register", methods=["POST"])
def register():
    """
    Registrar um novo usuário.

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
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            username:
              type: string
              example: johndoe
            email:
              type: string
              example: john@example.com
            password:
              type: string
              example: secret123
            role:
              type: string
              example: aluno
              description: Role opcional do usuário. Se não informado, será atribuída a role padrão 'aluno'.
    responses:
      201:
        description: Usuário registrado com sucesso.
        schema:
          type: object
          properties:
            access_token:
              type: string
            refresh_token:
              type: string
            message:
              type: string
      400:
        description: Dados inválidos.
      409:
        description: Usuário ou email já existe.
    """
    try:
        data = request.get_json() or {}
        result = auth_service.register(data)
        return jsonify(result), 201
    except ConflictError as error:
        logger.warning(f"Registration conflict: {str(error)}")
        return jsonify({"error": str(error)}), 409
    except ValueError as error:
        logger.warning(f"Invalid registration data: {str(error)}")
        return jsonify({"error": str(error)}), 400
    except AuthenticationError as error:
        logger.warning(f"Authentication error during registration: {str(error)}")
        return jsonify({"error": str(error)}), 401
    except Exception as error:
        logger.error(f"Unexpected error during registration: {str(error)}", exc_info=True)
        return jsonify({"error": "Erro ao registrar usuário."}), 500


@auth.route("/login", methods=["POST"])
def login():
    """
    Autenticar um usuário.

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
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            email:
              type: string
              example: john@example.com
            password:
              type: string
              example: secret123
    responses:
      200:
        description: Login realizado com sucesso.
        schema:
          type: object
          properties:
            access_token:
              type: string
            refresh_token:
              type: string
      400:
        description: Dados inválidos.
      401:
        description: Credenciais inválidas.
    """
    try:
        data = request.get_json() or {}
        access_token, refresh_token = auth_service.login(data)
        return jsonify(
            {"access_token": access_token, "refresh_token": refresh_token}
        ), 200
    except AuthenticationError as error:
        logger.warning(f"Login failed: {str(error)}")
        return jsonify({"error": str(error)}), 401
    except ValueError as error:
        logger.warning(f"Invalid login data: {str(error)}")
        return jsonify({"error": str(error)}), 400
    except Exception as error:
        logger.error(f"Unexpected error during login: {str(error)}", exc_info=True)
        return jsonify({"error": "Erro ao realizar login."}), 500


@auth.route("/logout", methods=["POST"])
def logout():
    """
    Logout do usuário.

    Como JWT é stateless, o logout pode ser simples: apenas confirmar que o token foi
    "invalidado" (embora na prática, o cliente deve descartar o token).

    Passos necessários:
    1. Validar o corpo da requisição (body): opcionalmente, aceitar o refresh_token para
       invalidá-lo (se houver uma lista negra de tokens).

    2. Se implementar invalidação: adicionar o token a uma lista negra no banco ou cache.

    3. Retornar mensagem de sucesso.

    Nota: Em sistemas stateless, o logout é mais do lado do cliente.
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        schema:
          type: object
          properties:
            refresh_token:
              type: string
    responses:
      200:
        description: Logout realizado com sucesso.
      400:
        description: Dados inválidos.
    """
    try:
        data = request.get_json() or {}
        auth_service.logout(data)
        return jsonify({"message": "Logout realizado com sucesso."}), 200
    except ValueError as error:
        logger.warning(f"Invalid logout data: {str(error)}")
        return jsonify({"error": str(error)}), 400
    except Exception as error:
        logger.error(f"Unexpected error during logout: {str(error)}", exc_info=True)
        return jsonify({"error": "Erro ao realizar logout."}), 500


@auth.route("/refresh", methods=["POST"])
def refresh():
    """
    Renovar access token.

    Passos necessários:
    1. Validar o corpo da requisição (body): verificar se o campo 'refresh_token' está presente.

    2. Verificar o refresh token: decodificar e validar o JWT refresh token. Verificar se não
       expirou e se é válido (usar a chave secreta).

    3. Buscar no banco: opcionalmente, verificar se o usuário associado ao token ainda existe
       e está ativo.

    4. Gerar novo JWT: se válido, gerar um novo access_token (e opcionalmente um novo
       refresh_token).

    Retornar: novo access_token (e refresh_token se renovado), ou erro se falhar.
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            refresh_token:
              type: string
    responses:
      200:
        description: Token renovado com sucesso.
        schema:
          type: object
          properties:
            access_token:
              type: string
      401:
        description: Token inválido ou expirado.
      400:
        description: Dados inválidos.
    """
    try:
        data = request.get_json() or {}
        access_token = auth_service.refresh(data)
        return jsonify({"access_token": access_token}), 200
    except AuthenticationError as error:
        logger.warning(f"Token refresh failed: {str(error)}")
        return jsonify({"error": str(error)}), 401
    except ValueError as error:
        logger.warning(f"Invalid refresh data: {str(error)}")
        return jsonify({"error": str(error)}), 400
    except Exception as error:
        logger.error(f"Unexpected error during token refresh: {str(error)}", exc_info=True)
        return jsonify({"error": "Erro ao renovar token."}), 500


@auth.route("/me", methods=["GET"])
def get_me():
    """
    Obter perfil do usuário logado.

    Passos necessários:
    1. Verificar autenticação: usar decorator @jwt_required para garantir que o usuário está logado
       e extrair o user_id do token JWT.

    2. Buscar no banco: consultar o banco de dados para obter todas as informações do usuário
       (como username, email, role, status, data de criação, etc.) baseado no user_id extraído.

    3. Retornar perfil completo: devolver um JSON com todos os campos do usuário, exceto a senha
       hasheada.

    Retornar: dados do usuário em JSON, ou erro se não autenticado ou usuário não encontrado.
    ---
    tags:
      - Users
    security:
      - Bearer: []
    responses:
      200:
        description: Perfil do usuário.
      401:
        description: Não autenticado.
    """
    try:
        auth_header = request.headers.get("Authorization", "")
        user = auth_service.get_current_user(auth_header)
        return jsonify(user), 200
    except AuthenticationError as error:
        logger.warning(f"Failed to get current user: {str(error)}")
        return jsonify({"error": str(error)}), 401
    except ValueError as error:
        logger.warning(f"Invalid request for current user: {str(error)}")
        return jsonify({"error": str(error)}), 400
    except Exception as error:
        logger.error(f"Unexpected error getting current user: {str(error)}", exc_info=True)
        return jsonify({"error": "Erro ao obter perfil do usuário."}), 500


@auth.route("/users", methods=["GET"])
def get_users():
    """
    Listar todos os usuários (Admin).

    Passos necessários:
    1. Verificar autenticação e autorização: usar @jwt_required e verificar se o usuário tem
       role de admin (ex: checar claim 'role' no token).

    2. Buscar no banco: consultar todos os usuários no banco de dados, possivelmente com paginação
       (parâmetros query como limit, offset).

    3. Filtrar dados: retornar apenas campos públicos (sem senhas), talvez com opções de filtro
       por status ou role.

    Retornar: lista de usuários em JSON, ou erro se não autorizado.
    ---
    tags:
      - Users
    security:
      - Bearer: []
    parameters:
      - name: limit
        in: query
        type: integer
        default: 10
      - name: offset
        in: query
        type: integer
        default: 0
    responses:
      200:
        description: Lista de usuários.
      401:
        description: Não autenticado.
      403:
        description: Não autorizado (apenas Admin).
    """
    try:
        auth_header = request.headers.get("Authorization", "")
        limit = request.args.get("limit", default=10, type=int)
        offset = request.args.get("offset", default=0, type=int)
        
        result = auth_service.get_all_users(auth_header, limit, offset)
        return jsonify(result), 200
    except AuthenticationError as error:
        logger.warning(f"Authentication failed for listing users: {str(error)}")
        return jsonify({"error": str(error)}), 401
    except PermissionError as error:
        logger.warning(f"Permission denied for listing users: {str(error)}")
        return jsonify({"error": str(error)}), 403
    except ValueError as error:
        logger.warning(f"Invalid request for listing users: {str(error)}")
        return jsonify({"error": str(error)}), 400
    except Exception as error:
        logger.error(f"Unexpected error listing users: {str(error)}", exc_info=True)
        return jsonify({"error": "Erro ao listar usuários."}), 500


@auth.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    """
    Obter detalhes de um usuário.

    Passos necessários:
    1. Verificar autenticação: usar @jwt_required.

    2. Verificar autorização: permitir apenas se o usuário é o próprio (user_id == token user_id)
       ou se é admin.

    3. Buscar no banco: consultar o usuário pelo user_id fornecido.

    4. Retornar dados: devolver JSON com detalhes do usuário (sem senha).

    Retornar: dados do usuário, ou erro se não encontrado ou não autorizado.
    ---
    tags:
      - Users
    security:
      - Bearer: []
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Detalhes do usuário.
      401:
        description: Não autenticado.
      403:
        description: Não autorizado.
      404:
        description: Usuário não encontrado.
    """
    try:
        auth_header = request.headers.get("Authorization", "")
        result = auth_service.get_user_by_id(user_id, auth_header)
        return jsonify(result), 200
    except AuthenticationError as error:
        logger.warning(f"Authentication failed for user {user_id}: {str(error)}")
        return jsonify({"error": str(error)}), 401
    except PermissionError as error:
        logger.warning(f"Permission denied for user {user_id}: {str(error)}")
        return jsonify({"error": str(error)}), 403
    except LookupError as error:
        logger.warning(f"User {user_id} not found: {str(error)}")
        return jsonify({"error": str(error)}), 404
    except ValueError as error:
        logger.warning(f"Invalid request for user {user_id}: {str(error)}")
        return jsonify({"error": str(error)}), 400
    except Exception as error:
        logger.error(f"Unexpected error fetching user {user_id}: {str(error)}", exc_info=True)
        return jsonify({"error": "Erro ao buscar usuário."}), 500


@auth.route("/users/<int:user_id>/role", methods=["PATCH"])
def update_user_role(user_id):
    """
    Atualizar role de um usuário (Admin).

    Passos necessários:
    1. Verificar autenticação e autorização: @jwt_required e verificar se é admin.

    2. Validar corpo da requisição: verificar campo 'role' no body, validar se é um role válido
       (ex: 'user', 'admin').

    3. Buscar usuário: verificar se o user_id existe no banco.

    4. Atualizar no banco: alterar o campo 'role' do usuário.

    5. Retornar sucesso: confirmar a atualização.

    Retornar: mensagem de sucesso, ou erro se não autorizado, usuário não encontrado, etc.
    ---
    tags:
      - Users
    security:
      - Bearer: []
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            role:
              type: string
              example: admin
    responses:
      200:
        description: Role atualizado com sucesso.
      401:
        description: Não autenticado.
      403:
        description: Não autorizado.
      404:
        description: Usuário não encontrado.
    """
    try:
        data = request.get_json() or {}
        auth_header = request.headers.get("Authorization", "")
        result = auth_service.update_user_role(user_id, data, auth_header)
        return jsonify(result), 200
    except AuthenticationError as error:
        logger.warning(f"Authentication failed for role update on user {user_id}: {str(error)}")
        return jsonify({"error": str(error)}), 401
    except PermissionError as error:
        logger.warning(f"Permission denied for role update on user {user_id}: {str(error)}")
        return jsonify({"error": str(error)}), 403
    except LookupError as error:
        logger.warning(f"User {user_id} not found for role update: {str(error)}")
        return jsonify({"error": str(error)}), 404
    except ValueError as error:
        logger.warning(f"Invalid role update data for user {user_id}: {str(error)}")
        return jsonify({"error": str(error)}), 400
    except Exception as error:
        logger.error(f"Unexpected error updating role for user {user_id}: {str(error)}", exc_info=True)
        return jsonify({"error": "Erro ao atualizar role do usuário."}), 500


@auth.route("/users/<int:user_id>/status", methods=["PATCH"])
def update_user_status(user_id):
    """
    Atualizar status de um usuário (Admin).

    Passos necessários:
    1. Verificar autenticação e autorização: @jwt_required e verificar se é admin.

    2. Validar corpo da requisição: verificar campo 'status' no body, validar se é um status válido
       (ex: 'active', 'blocked').

    3. Buscar usuário: verificar se o user_id existe no banco.

    4. Atualizar no banco: alterar o campo 'status' do usuário.

    5. Retornar sucesso: confirmar a atualização.

    Retornar: mensagem de sucesso, ou erro se não autorizado, usuário não encontrado, etc.
    ---
    tags:
      - Users
    security:
      - Bearer: []
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            status:
              type: string
              example: active
    responses:
      200:
        description: Status atualizado com sucesso.
      401:
        description: Não autenticado.
      403:
        description: Não autorizado.
      404:
        description: Usuário não encontrado.
    """
    try:
        data = request.get_json() or {}
        auth_header = request.headers.get("Authorization", "")
        result = auth_service.update_user_status(user_id, data, auth_header)
        return jsonify(result), 200
    except AuthenticationError as error:
        logger.warning(f"Authentication failed for status update on user {user_id}: {str(error)}")
        return jsonify({"error": str(error)}), 401
    except PermissionError as error:
        logger.warning(f"Permission denied for status update on user {user_id}: {str(error)}")
        return jsonify({"error": str(error)}), 403
    except LookupError as error:
        logger.warning(f"User {user_id} not found for status update: {str(error)}")
        return jsonify({"error": str(error)}), 404
    except ValueError as error:
        logger.warning(f"Invalid status update data for user {user_id}: {str(error)}")
        return jsonify({"error": str(error)}), 400
    except Exception as error:
        logger.error(f"Unexpected error updating status for user {user_id}: {str(error)}", exc_info=True)
        return jsonify({"error": "Erro ao atualizar status do usuário."}), 500
