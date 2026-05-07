from ..services.db import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    refresh_token = db.Column(db.String(512), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
        }
