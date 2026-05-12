from flask import Blueprint, request, jsonify
import bcrypt
from ..services.auth_service import AuthService
from ..services.db import db
from ..models.user import User

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
    try:
        data = request.get_json() or {}

        # Step 1: Validate request body
        username = data.get("username", "").strip()
        email = data.get("email", "").strip()
        password = data.get("password", "").strip()

        if not username or not email or not password:
            return jsonify({"error": "Username, email e senha são obrigatórios."}), 400

        if len(password) < 6:
            return jsonify({"error": "Senha deve ter pelo menos 6 caracteres."}), 400

        # Step 2: Check if user already exists
        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing_user:
            return jsonify({"error": "Username ou email já cadastrado."}), 409

        # Step 3: Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Step 4: Save to database
        new_user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            roles=[]
        )
        db.session.add(new_user)
        db.session.commit()

        # Step 5: Generate JWT tokens
        access_token, refresh_token = auth_service.login({
            "email": email,
            "password": password
        })

        return jsonify({
            "message": "Usuário registrado com sucesso.",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": new_user.to_dict()
        }), 201
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    except Exception as error:
        db.session.rollback()
        return jsonify({"error": "Erro ao registrar usuário."}), 500



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
    try:
        data = request.get_json() or {}
        auth_service.logout(data)
        return jsonify({"message": "Logout realizado com sucesso."}), 200
    except ValueError as error:
        return jsonify({"error": str(error)}), 400


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
    try:
        data = request.get_json() or {}
        access_token = auth_service.refresh(data)
        return jsonify({"access_token": access_token}), 200
    except ValueError as error:
        return jsonify({"error": str(error)}), 400


@auth.route("/me", methods=["GET"])
def get_me():
    """
    Rota para obter o perfil completo do usuário autenticado.

    Passos necessários:
    1. Verificar autenticação: usar decorator @jwt_required para garantir que o usuário está logado
       e extrair o user_id do token JWT.

    2. Buscar no banco: consultar o banco de dados para obter todas as informações do usuário
       (como username, email, role, status, data de criação, etc.) baseado no user_id extraído.

    3. Retornar perfil completo: devolver um JSON com todos os campos do usuário, exceto a senha
       hasheada.

    Retornar: dados do usuário em JSON, ou erro se não autenticado ou usuário não encontrado.
    """
    try:
        user = auth_service.get_current_user(request)
        return jsonify(user), 200
    except ValueError as error:
        return jsonify({"error": str(error)}), 401


@auth.route("/users", methods=["GET"])
def get_users():
    """
    Rota para listar todos os usuários (provavelmente para administradores).

    Passos necessários:
    1. Verificar autenticação e autorização: usar @jwt_required e verificar se o usuário tem
       role de admin (ex: checar claim 'role' no token).

    2. Buscar no banco: consultar todos os usuários no banco de dados, possivelmente com paginação
       (parâmetros query como limit, offset).

    3. Filtrar dados: retornar apenas campos públicos (sem senhas), talvez com opções de filtro
       por status ou role.

    Retornar: lista de usuários em JSON, ou erro se não autorizado.
    """
    try:
        # Step 1: Verify authentication and authorization
        current_user = auth_service.get_current_user(request)
        if "admin" not in current_user.get("roles", []):
            return jsonify({"error": "Acesso negado. Apenas administradores podem listar usuários."}), 403

        # Step 2: Fetch users from database with pagination
        limit = request.args.get("limit", default=10, type=int)
        offset = request.args.get("offset", default=0, type=int)

        users = User.query.limit(limit).offset(offset).all()
        total = User.query.count()

        # Step 3: Filter data and return only public fields
        users_list = [user.to_dict() for user in users]

        return jsonify({
            "users": users_list,
            "total": total,
            "limit": limit,
            "offset": offset
        }), 200
    except ValueError as error:
        return jsonify({"error": str(error)}), 401
    except Exception as error:
        return jsonify({"error": "Erro ao listar usuários."}), 500


@auth.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    """
    Rota para obter detalhes de um usuário específico por ID.

    Passos necessários:
    1. Verificar autenticação: usar @jwt_required.

    2. Verificar autorização: permitir apenas se o usuário é o próprio (user_id == token user_id)
       ou se é admin.

    3. Buscar no banco: consultar o usuário pelo user_id fornecido.

    4. Retornar dados: devolver JSON com detalhes do usuário (sem senha).

    Retornar: dados do usuário, ou erro se não encontrado ou não autorizado.
    """
    try:
        # Step 1: Verify authentication
        current_user = auth_service.get_current_user(request)
        current_user_id = current_user.get("id")

        # Step 2: Verify authorization
        is_admin = "admin" in current_user.get("roles", [])
        if current_user_id != user_id and not is_admin:
            return jsonify({"error": "Acesso negado. Você não tem permissão para acessar este usuário."}), 403

        # Step 3: Fetch user from database
        user = User.query.get(user_id)
        if user is None:
            return jsonify({"error": "Usuário não encontrado."}), 404

        # Step 4: Return user data
        return jsonify(user.to_dict()), 200
    except ValueError as error:
        return jsonify({"error": str(error)}), 401
    except Exception as error:
        return jsonify({"error": "Erro ao buscar usuário."}), 500


@auth.route("/users/<int:user_id>/role", methods=["PATCH"])
def update_user_role(user_id):
    """
    Rota para atualizar o role de um usuário (apenas administradores).

    Passos necessários:
    1. Verificar autenticação e autorização: @jwt_required e verificar se é admin.

    2. Validar corpo da requisição: verificar campo 'role' no body, validar se é um role válido
       (ex: 'user', 'admin').

    3. Buscar usuário: verificar se o user_id existe no banco.

    4. Atualizar no banco: alterar o campo 'role' do usuário.

    5. Retornar sucesso: confirmar a atualização.

    Retornar: mensagem de sucesso, ou erro se não autorizado, usuário não encontrado, etc.
    """
    try:
        # Step 1: Verify authentication and authorization
        current_user = auth_service.get_current_user(request)
        if "admin" not in current_user.get("roles", []):
            return jsonify({"error": "Acesso negado. Apenas administradores podem atualizar roles."}), 403

        # Step 2: Validate request body
        data = request.get_json() or {}
        role = data.get("role", "").strip()

        if not role:
            return jsonify({"error": "Campo 'role' é obrigatório."}), 400

        valid_roles = ["user", "admin"]
        if role not in valid_roles:
            return jsonify({"error": f"Role inválido. Valores permitidos: {', '.join(valid_roles)}"}), 400

        # Step 3: Fetch user
        user = User.query.get(user_id)
        if user is None:
            return jsonify({"error": "Usuário não encontrado."}), 404

        # Step 4: Update in database
        if role not in user.roles:
            user.roles.append(role)
            db.session.commit()

        # Step 5: Return success
        return jsonify({
            "message": "Role do usuário atualizado com sucesso.",
            "user": user.to_dict()
        }), 200
    except ValueError as error:
        return jsonify({"error": str(error)}), 401
    except Exception as error:
        db.session.rollback()
        return jsonify({"error": "Erro ao atualizar role do usuário."}), 500


@auth.route("/users/<int:user_id>/status", methods=["PATCH"])
def update_user_status(user_id):
    """
    Rota para atualizar o status de um usuário (apenas administradores).

    Passos necessários:
    1. Verificar autenticação e autorização: @jwt_required e verificar se é admin.

    2. Validar corpo da requisição: verificar campo 'status' no body, validar se é um status válido
       (ex: 'active', 'inactive', 'banned').

    3. Buscar usuário: verificar se o user_id existe no banco.

    4. Atualizar no banco: alterar o campo 'status' do usuário.

    5. Retornar sucesso: confirmar a atualização.

    Retornar: mensagem de sucesso, ou erro se não autorizado, usuário não encontrado, etc.
    """
    try:
        # Step 1: Verify authentication and authorization
        current_user = auth_service.get_current_user(request)
        if "admin" not in current_user.get("roles", []):
            return jsonify({"error": "Acesso negado. Apenas administradores podem atualizar status."}), 403

        # Step 2: Validate request body
        data = request.get_json() or {}
        status = data.get("status", "").strip()

        if not status:
            return jsonify({"error": "Campo 'status' é obrigatório."}), 400

        valid_statuses = ["active", "inactive", "banned"]
        if status not in valid_statuses:
            return jsonify({"error": f"Status inválido. Valores permitidos: {', '.join(valid_statuses)}"}), 400

        # Step 3: Fetch user
        user = User.query.get(user_id)
        if user is None:
            return jsonify({"error": "Usuário não encontrado."}), 404

        # Step 4: Update in database
        user.status = status
        db.session.commit()

        # Step 5: Return success
        return jsonify({
            "message": "Status do usuário atualizado com sucesso.",
            "user": user.to_dict()
        }), 200
    except ValueError as error:
        return jsonify({"error": str(error)}), 401
    except Exception as error:
        db.session.rollback()
        return jsonify({"error": "Erro ao atualizar status do usuário."}), 500
