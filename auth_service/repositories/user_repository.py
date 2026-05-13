import logging
from ..models.user import User
from ..services.db import db

logger = logging.getLogger(__name__)

class UserRepository:
    def get_by_id(self, user_id):
        return User.query.get(user_id)

    def get_by_email(self, email):
        return User.query.filter_by(email=email).first()

    def get_by_username_or_email(self, username, email):
        return User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()

    def create(self, username, email, password_hash, roles=None):
        if roles is None:
            roles = []
        new_user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            roles=roles
        )
        db.session.add(new_user)
        return new_user

    def list_all(self, limit=10, offset=0):
        return User.query.limit(limit).offset(offset).all()

    def count_all(self):
        return User.query.count()

    def commit(self):
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Database commit failed: {str(e)}", exc_info=True)
            raise

    def rollback(self):
        db.session.rollback()
