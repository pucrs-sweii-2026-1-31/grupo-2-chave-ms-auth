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
