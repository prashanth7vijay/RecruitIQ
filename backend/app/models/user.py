from sqlalchemy import Column, String, ForeignKey, Integer, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, CITEXT
from sqlalchemy.orm import relationship

from app.extensions import db
from app.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin, db.Model):
    """
    Staff identity: recruiters, hiring managers, interviewers, HR, admins.
    Deliberately tenant-scoped (UNIQUE(company_id, email), not a global
    unique email) — the mirror-image decision to Candidate being global.
    See Phase 9a for why.
    """

    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("company_id", "email", name="uq_users_company_email"),)

    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    email = Column(CITEXT, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=False)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="SET NULL"), nullable=True)
    manager_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="SET NULL"), nullable=True)

    status = Column(String(20), nullable=False, default="pending")  # pending/active/locked/disabled
    email_verified_at = Column(DateTime(timezone=True), nullable=True)
    failed_login_count = Column(Integer, nullable=False, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)

    # Admin-created-user lifecycle (temp password, no email dependency —
    # see auth_service.admin_create_user). must_change_password is
    # enforced server-side in tenant_context middleware, not just left to
    # the frontend to redirect on — a client that ignores the flag still
    # can't reach any other endpoint.
    must_change_password = Column(db.Boolean, nullable=False, default=False)
    temp_password_expires_at = Column(DateTime(timezone=True), nullable=True)

    role = relationship("Role")
    manager = relationship("User", remote_side="User.id", foreign_keys=[manager_id])

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class RefreshToken(Base, UUIDPrimaryKeyMixin, db.Model):

    __tablename__ = "refresh_tokens"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(255), nullable=False, index=True)
    device_info = Column(db.JSON, nullable=True)
    ip_address = Column(String(64), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=db.func.now(), nullable=False)


class LoginHistory(Base, UUIDPrimaryKeyMixin, db.Model):
    __tablename__ = "login_history"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    ip_address = Column(String(64), nullable=True)
    device_info = Column(db.JSON, nullable=True)
    geo_location = Column(String(255), nullable=True)
    success = Column(db.Boolean, nullable=False)
    risk_flag = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=db.func.now(), nullable=False)
