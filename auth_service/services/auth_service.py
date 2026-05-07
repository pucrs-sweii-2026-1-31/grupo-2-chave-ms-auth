import datetime
from typing import Optional

from flask import current_app
from itsdangerous import BadSignature, SignatureExpired, TimedJSONWebSignatureSerializer as Serializer

from ..models.user import User
from ..extensions import db


class AuthService:
    @staticmethod
    def generate_token(payload: dict, expires_in: int) -> str:
        serializer = Serializer(current_app.config["SECRET_KEY"], expires_in)
        return serializer.dumps(payload).decode("utf-8")

    @staticmethod
    def decode_token(token: str) -> dict:
        serializer = Serializer(current_app.config["SECRET_KEY"])
        try:
            data = serializer.loads(token)
            return data
        except SignatureExpired:
            raise ValueError("Token expirado")
        except BadSignature:
            raise ValueError("Token inválido")

    @classmethod
    def authenticate_user(cls, email: str, password: str) -> Optional[User]:
        user = User.query.filter_by(email=email, is_active=True).first()
        if user and user.check_password(password):
            return user
        return None

    @classmethod
    def create_access_token(cls, user: User) -> str:
        payload = {
            "sub": user.id,
            "type": "access",
            "iat": int(datetime.datetime.utcnow().timestamp()),
        }
        return cls.generate_token(payload, current_app.config["ACCESS_TOKEN_EXPIRES"])

    @classmethod
    def create_refresh_token(cls, user: User) -> str:
        payload = {
            "sub": user.id,
            "type": "refresh",
            "iat": int(datetime.datetime.utcnow().timestamp()),
        }
        return cls.generate_token(payload, current_app.config["REFRESH_TOKEN_EXPIRES"])

    @classmethod
    def get_user_from_token(cls, token: str) -> User:
        data = cls.decode_token(token)
        if data.get("type") != "access":
            raise ValueError("Token deve ser do tipo access")

        user_id = data.get("sub")
        user = User.query.get(user_id)
        if not user or not user.is_active:
            raise ValueError("Usuário não encontrado")
        return user

    @classmethod
    def refresh_access_token(cls, refresh_token: str) -> str:
        data = cls.decode_token(refresh_token)
        if data.get("type") != "refresh":
            raise ValueError("Token deve ser do tipo refresh")

        user_id = data.get("sub")
        user = User.query.get(user_id)
        if not user or not user.is_active:
            raise ValueError("Usuário não encontrado")
        return cls.create_access_token(user)

    @classmethod
    def revoke_token(cls, token: str) -> None:
        # TODO: implementar blacklist de tokens em banco ou cache
        pass
