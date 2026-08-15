import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
from flask_jwt_extended import create_access_token

from app.exceptions.base import (
    ValidationError,
    UnauthenticatedError,
    BusinessRuleViolationError,
    NotFoundError,
)
from app.models.company import Company
from app.models.user import User, RefreshToken


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def _hash_token(raw_token: str) -> str:
    # Refresh tokens are stored hashed, never in plaintext (Phase 12.1) —
    # same principle as password storage. SHA-256 is sufficient here
    # (unlike passwords, refresh tokens are already high-entropy random
    # values, not low-entropy user-chosen secrets, so bcrypt's slow-hash
    # property isn't needed).
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


class AuthService:
    def __init__(self, user_repo, refresh_token_repo, login_history_repo, company_repo, role_repo, config):
        self.user_repo = user_repo
        self.refresh_token_repo = refresh_token_repo
        self.login_history_repo = login_history_repo
        self.company_repo = company_repo
        self.role_repo = role_repo
        self.config = config

    def signup_company(self, company_name, company_slug, email, password, first_name, last_name):
        
        if self.company_repo.get_by_slug(company_slug) is not None:
            raise ValidationError(
                "That organization URL is already taken",
                details=[{"field": "company_slug", "message": "Already in use"}],
            )

        org_admin_role = self.role_repo.get_system_role_by_name("org_admin")
        if org_admin_role is None:
            raise BusinessRuleViolationError(
                "System roles are not seeded yet — run `flask seed-roles` before signing up"
            )

        company = Company(name=company_name, slug=company_slug, plan="trial", status="active")
        self.company_repo.add(company)
        self.company_repo.commit()

        user = User(
            company_id=company.id,
            email=email,
            password_hash=_hash_password(password),
            first_name=first_name,
            last_name=last_name,
            role_id=org_admin_role.id,
            status="active",
        )
        self.user_repo.add(user)
        self.user_repo.commit()

        return company, user

    def admin_create_user(self, tenant_id, email, first_name, last_name, role_id):
        
        role = self.role_repo.get_visible_or_404(role_id, tenant_id)

        existing = self.user_repo.get_by_email(email, tenant_id)
        if existing is not None:
            raise ValidationError(
                "A user with this email already exists in this organization",
                details=[{"field": "email", "message": "Already registered"}],
            )

        raw_temp_password = secrets.token_urlsafe(18)  # ~24 chars, well above the 10-char min
        user = User(
            company_id=tenant_id,
            email=email,
            password_hash=_hash_password(raw_temp_password),
            first_name=first_name,
            last_name=last_name,
            role_id=role_id,
            status="active",
            must_change_password=True,
            temp_password_expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        self.user_repo.add(user)
        self.user_repo.commit()
        # Raw temp password is returned to the caller for exactly one
        # response and never persisted or logged anywhere — same
        # discipline as a refresh token, just shown once instead of
        # sent as a cookie.
        return user, raw_temp_password

    def change_password(self, user_id, current_password, new_password, ip_address=None, device_info=None):
    
        user = self.user_repo.get_by_id_untenanted(user_id)
        if user is None:
            raise UnauthenticatedError("Invalid session")

        if user.must_change_password and user.temp_password_expires_at is not None:
            if datetime.now(timezone.utc) > user.temp_password_expires_at:
                raise BusinessRuleViolationError(
                    "This temporary password has expired. Ask an admin to reset your account."
                )

        if not _verify_password(current_password, user.password_hash):
            raise UnauthenticatedError("Current password is incorrect")

        if _verify_password(new_password, user.password_hash):
            raise ValidationError("New password must be different from the current password")

        user.password_hash = _hash_password(new_password)
        user.must_change_password = False
        user.temp_password_expires_at = None
        self.user_repo.commit()

        # Revoke every other refresh token: a temp password may have
        # been visible to more than one person (admin + the user during
        # handoff) — changing it should end any session started with it
        # everywhere except the one making this request.
        self.refresh_token_repo.revoke_all_for_user(user.id)

        access_token = self._issue_access_token(user)
        raw_refresh_token, refresh_token_row = self._issue_refresh_token(
            user, ip_address, device_info, remember_me=False
        )
        return {
            "access_token": access_token,
            "refresh_token": raw_refresh_token,
            "refresh_token_expires_at": refresh_token_row.expires_at,
        }

    def login(self, company_slug, email, password, ip_address=None, device_info=None, remember_me=False):
        company = self.company_repo.get_by_slug(company_slug)
        if company is None:
            # Same generic error as "wrong password" below — an unknown
            # organization slug shouldn't be distinguishable from a
            # known one with a bad password, for the same reason emails
            # aren't distinguishable (avoid enumeration).
            raise UnauthenticatedError("Invalid organization, email, or password")

        user = self.user_repo.get_by_email(email, company.id)

        if user is None:
            raise UnauthenticatedError("Invalid organization, email, or password")

        self._assert_not_locked(user)

        if not _verify_password(password, user.password_hash):
            self._record_failed_attempt(user)
            self._log_login(user.id, ip_address, device_info, success=False)
            raise UnauthenticatedError("Invalid organization, email, or password")

        if user.status != "active":
            raise UnauthenticatedError("Account is not active")

        if user.must_change_password and user.temp_password_expires_at is not None:
            if datetime.now(timezone.utc) > user.temp_password_expires_at:
                # Distinct from a normal expired-password state: this
                # tells the user *why* login worked (correct temp
                # password) but access is still refused, rather than a
                # generic invalid-credentials message that would leave
                # them retrying the same password indefinitely.
                raise BusinessRuleViolationError(
                    "This temporary password has expired. Ask an admin to reset your account."
                )

        self._reset_failed_attempts(user)
        self._log_login(user.id, ip_address, device_info, success=True)

        access_token = self._issue_access_token(user)
        raw_refresh_token, refresh_token_row = self._issue_refresh_token(
            user, ip_address, device_info, remember_me
        )
        return {
            "access_token": access_token,
            "refresh_token": raw_refresh_token,  # caller sets this as an HttpOnly cookie, never in JSON body to a browser client
            "refresh_token_expires_at": refresh_token_row.expires_at,
            "must_change_password": user.must_change_password,
        }

    def refresh(self, raw_refresh_token, ip_address=None, device_info=None):
        
        if not raw_refresh_token:
            # No cookie and no JSON body token — a real client state (e.g.
            # right after logout-all deletes the cookie), not a server
            # error. hashlib would otherwise blow up on None with a 500.
            raise UnauthenticatedError("Invalid refresh token")

        token_hash = _hash_token(raw_refresh_token)
        stored = self.refresh_token_repo.get_by_hash(token_hash)

        if stored is None:
            raise UnauthenticatedError("Invalid refresh token")

        if stored.revoked_at is not None:
            # Reuse of a revoked token: possible theft. Nuke every active
            # session for this user rather than just rejecting the request.
            self.refresh_token_repo.revoke_all_for_user(stored.user_id)
            self.refresh_token_repo.commit()
            raise UnauthenticatedError(
                "Refresh token reuse detected — all sessions have been revoked. Please log in again."
            )

        if stored.expires_at < datetime.now(timezone.utc):
            raise UnauthenticatedError("Refresh token expired")

        user = self.user_repo.get_by_id_untenanted(stored.user_id)
        if user is None or user.status != "active":
            raise UnauthenticatedError("Account is no longer active")

        stored.revoked_at = datetime.now(timezone.utc)
        self.refresh_token_repo.commit()

        access_token = self._issue_access_token_from_claims(stored.user_id)
        raw_new_token, new_row = self._issue_refresh_token_for_user_id(
            stored.user_id, ip_address, device_info
        )
        return {"access_token": access_token, "refresh_token": raw_new_token}

    def logout(self, raw_refresh_token):
        token_hash = _hash_token(raw_refresh_token)
        stored = self.refresh_token_repo.get_by_hash(token_hash)
        if stored is not None and stored.revoked_at is None:
            stored.revoked_at = datetime.now(timezone.utc)
            self.refresh_token_repo.commit()

    def logout_all(self, user_id):
        self.refresh_token_repo.revoke_all_for_user(user_id)
        self.refresh_token_repo.commit()

    # --- internal helpers -------------------------------------------------

    def _assert_not_locked(self, user: User):
        if user.locked_until and user.locked_until > datetime.now(timezone.utc):
            raise BusinessRuleViolationError(
                "Account temporarily locked due to repeated failed login attempts"
            )

    def _record_failed_attempt(self, user: User):
        user.failed_login_count += 1
        if user.failed_login_count >= self.config["LOGIN_LOCKOUT_THRESHOLD"]:
            user.locked_until = datetime.now(timezone.utc) + timedelta(
                minutes=self.config["LOGIN_LOCKOUT_DURATION_MINUTES"]
            )
        self.user_repo.commit()

    def _reset_failed_attempts(self, user: User):
        user.failed_login_count = 0
        user.locked_until = None
        self.user_repo.commit()

    def _log_login(self, user_id, ip_address, device_info, success):
        self.login_history_repo.add(
            self.login_history_repo.model(
                user_id=user_id, ip_address=ip_address, device_info=device_info, success=success
            )
        )
        self.login_history_repo.commit()

    def _issue_access_token(self, user: User):
        return create_access_token(
            identity=str(user.id),
            additional_claims={
                "tenant_id": str(user.company_id),
                "role_id": str(user.role_id),
                "must_change_password": user.must_change_password,
            },
        )

    def _issue_access_token_from_claims(self, user_id):
        user = self.user_repo.get_by_id_untenanted(user_id)
        return create_access_token(
            identity=str(user_id),
            additional_claims={
                "tenant_id": str(user.company_id),
                "role_id": str(user.role_id),
                "must_change_password": user.must_change_password,
            },
        )

    def _issue_refresh_token(self, user: User, ip_address, device_info, remember_me):
        raw_token = secrets.token_urlsafe(64)
        expires_delta = (
            self.config["JWT_REFRESH_TOKEN_EXPIRES_REMEMBER_ME"]
            if remember_me
            else self.config["JWT_REFRESH_TOKEN_EXPIRES"]
        )
        row = RefreshToken(
            user_id=user.id,
            token_hash=_hash_token(raw_token),
            device_info=device_info,
            ip_address=ip_address,
            expires_at=datetime.now(timezone.utc) + expires_delta,
        )
        self.refresh_token_repo.add(row)
        self.refresh_token_repo.commit()
        return raw_token, row

    def _issue_refresh_token_for_user_id(self, user_id, ip_address, device_info):
        raw_token = secrets.token_urlsafe(64)
        row = RefreshToken(
            user_id=user_id,
            token_hash=_hash_token(raw_token),
            device_info=device_info,
            ip_address=ip_address,
            expires_at=datetime.now(timezone.utc) + self.config["JWT_REFRESH_TOKEN_EXPIRES"],
        )
        self.refresh_token_repo.add(row)
        self.refresh_token_repo.commit()
        return raw_token, row
