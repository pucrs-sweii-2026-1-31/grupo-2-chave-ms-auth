from ..services.db import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    roles = db.Column(db.ARRAY(db.String), nullable=False, default=[])
    status = db.Column(db.String(50), nullable=False, default="active")
    refresh_token = db.Column(db.String(512), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, server_default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "roles": self.roles,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
