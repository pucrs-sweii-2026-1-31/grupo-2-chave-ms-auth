import os
import datetime
import jwt
import bcrypt
from .db import db
from ..models.user import User
from ..config import Config


class AuthService:
    def __init__(self):
        self.secret_key = Config.JWT_SECRET
        self.access_expires = int(os.getenv("ACCESS_TOKEN_EXPIRES", 900))
        self.refresh_expires = int(os.getenv("REFRESH_TOKEN_EXPIRES", 86400))

    def login(self, data):
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            raise ValueError("Email e senha são obrigatórios.")

        user = User.query.filter_by(email=email).first()
        if user is None or not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            raise ValueError("Credenciais inválidas.")

        refresh_token = self._create_token({"sub": user.id, "type": "refresh"}, self.refresh_expires)
        access_token = self._create_token({"sub": user.id, "type": "access"}, self.access_expires)

        user.refresh_token = refresh_token
        db.session.commit()

        return access_token, refresh_token

    def refresh(self, data):
        refresh_token = data.get("refresh_token")
        if not refresh_token:
            raise ValueError("Refresh token é obrigatório.")

        payload = self._decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise ValueError("Token de refresh inválido.")

        user = User.query.get(payload.get("sub"))
        if user is None or user.refresh_token != refresh_token:
            raise ValueError("Token de refresh inválido.")

        return self._create_token({"sub": user.id, "type": "access"}, self.access_expires)

    def logout(self, data):
        refresh_token = data.get("refresh_token")
        if not refresh_token:
            raise ValueError("Refresh token é obrigatório.")

        payload = self._decode_token(refresh_token)
        user = User.query.get(payload.get("sub"))
        if user:
            user.refresh_token = None
            db.session.commit()

    def get_current_user(self, request):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise ValueError("Authorization header inválido.")

        token = auth_header.split(" ", 1)[1]
        payload = self._decode_token(token)
        if payload.get("type") != "access":
            raise ValueError("Token inválido.")

        user = User.query.get(payload.get("sub"))
        if user is None:
            raise ValueError("Usuário não encontrado.")

        return user.to_dict()

    def register(self, data):
        # Step 1: Validate request body
        username = data.get("username", "").strip()
        email = data.get("email", "").strip()
        password = data.get("password", "").strip()

        if not username or not email or not password:
            raise ValueError("Username, email e senha são obrigatórios.")

        if len(password) < 6:
            raise ValueError("Senha deve ter pelo menos 6 caracteres.")

        # Step 2: Check if user already exists
        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing_user:
            raise ValueError("Username ou email já cadastrado.")

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
        access_token, refresh_token = self.login({
            "email": email,
            "password": password
        })

        return {
            "message": "Usuário registrado com sucesso.",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": new_user.to_dict()
        }

    def get_all_users(self, request):
        # Step 1: Verify authentication and authorization
        current_user = self.get_current_user(request)
        if "admin" not in current_user.get("roles", []):
            raise PermissionError("Acesso negado. Apenas administradores podem listar usuários.")

        # Step 2: Fetch users from database with pagination
        limit = request.args.get("limit", default=10, type=int)
        offset = request.args.get("offset", default=0, type=int)

        users = User.query.limit(limit).offset(offset).all()
        total = User.query.count()

        # Step 3: Filter data and return only public fields
        users_list = [user.to_dict() for user in users]

        return {
            "users": users_list,
            "total": total,
            "limit": limit,
            "offset": offset
        }

    def get_user_by_id(self, user_id, request):
        # Step 1: Verify authentication
        current_user = self.get_current_user(request)
        current_user_id = current_user.get("id")

        # Step 2: Verify authorization
        is_admin = "admin" in current_user.get("roles", [])
        if current_user_id != user_id and not is_admin:
            raise PermissionError("Acesso negado. Você não tem permissão para acessar este usuário.")

        # Step 3: Fetch user from database
        user = User.query.get(user_id)
        if user is None:
            raise LookupError("Usuário não encontrado.")

        # Step 4: Return user data
        return user.to_dict()

    def update_user_role(self, user_id, data, request):
        # Step 1: Verify authentication and authorization
        current_user = self.get_current_user(request)
        if "admin" not in current_user.get("roles", []):
            raise PermissionError("Acesso negado. Apenas administradores podem atualizar roles.")

        # Step 2: Validate request body
        role = data.get("role", "").strip()

        if not role:
            raise ValueError("Campo 'role' é obrigatório.")

        valid_roles = ["user", "admin"]
        if role not in valid_roles:
            raise ValueError(f"Role inválido. Valores permitidos: {', '.join(valid_roles)}")

        # Step 3: Fetch user
        user = User.query.get(user_id)
        if user is None:
            raise LookupError("Usuário não encontrado.")

        # Step 4: Update in database
        if role not in user.roles:
            user.roles.append(role)
            db.session.commit()

        # Step 5: Return success
        return {
            "message": "Role do usuário atualizado com sucesso.",
            "user": user.to_dict()
        }

    def update_user_status(self, user_id, data, request):
        # Step 1: Verify authentication and authorization
        current_user = self.get_current_user(request)
        if "admin" not in current_user.get("roles", []):
            raise PermissionError("Acesso negado. Apenas administradores podem atualizar status.")

        # Step 2: Validate request body
        status = data.get("status", "").strip()

        if not status:
            raise ValueError("Campo 'status' é obrigatório.")

        valid_statuses = ["active", "inactive", "banned"]
        if status not in valid_statuses:
            raise ValueError(f"Status inválido. Valores permitidos: {', '.join(valid_statuses)}")

        # Step 3: Fetch user
        user = User.query.get(user_id)
        if user is None:
            raise LookupError("Usuário não encontrado.")

        # Step 4: Update in database
        user.status = status
        db.session.commit()

        # Step 5: Return success
        return {
            "message": "Status do usuário atualizado com sucesso.",
            "user": user.to_dict()
        }

    def _create_token(self, payload, expires_in):
        now = datetime.datetime.utcnow()
        payload.update({
            "exp": now + datetime.timedelta(seconds=expires_in),
            "iat": now,
        })
        return jwt.encode(payload, self.secret_key, algorithm="HS256")

    def _decode_token(self, token):
        try:
            return jwt.decode(token, self.secret_key, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise ValueError("Token expirado.")
        except jwt.InvalidTokenError:
            raise ValueError("Token inválido.")
