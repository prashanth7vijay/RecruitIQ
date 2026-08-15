from sqlalchemy import func

from app.models.user import User, RefreshToken, LoginHistory
from app.repositories.base_repository import TenantScopedRepository


class UserRepository(TenantScopedRepository):
    model = User

    def get_by_email(self, email, tenant_id):
        return self._base_query(tenant_id).filter(User.email == email).first()

    def get_by_id_untenanted(self, user_id):
        return self.session.query(User).filter(User.id == user_id).first()


class RefreshTokenRepository:

    model = RefreshToken

    def __init__(self, session):
        self.session = session

    def get_by_hash(self, token_hash):
        return self.session.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()

    def list_active_for_user(self, user_id):
        return self.session.query(RefreshToken).filter(
            RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None)
        )

    def revoke_all_for_user(self, user_id):
        # `self.session.func` doesn't exist — `func` is a plain SQLAlchemy
        # import, not something exposed off a Session/scoped_session.
        self.list_active_for_user(user_id).update({"revoked_at": func.now()})

    def add(self, obj):
        self.session.add(obj)
        return obj

    def commit(self):
        self.session.commit()


class LoginHistoryRepository:
    model = LoginHistory

    def __init__(self, session):
        self.session = session

    def add(self, obj):
        self.session.add(obj)
        return obj

    def commit(self):
        self.session.commit()

    def recent_for_user(self, user_id, limit=20):
        return (
            self.session.query(LoginHistory)
            .filter(LoginHistory.user_id == user_id)
            .order_by(LoginHistory.created_at.desc())
            .limit(limit)
        )
