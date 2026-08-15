from datetime import timedelta

from flask_jwt_extended import create_access_token

from app.exceptions.base import ValidationError, UnauthenticatedError
from app.models.candidate import Candidate
from app.services.auth_service import _hash_password, _verify_password

# Candidates have no refresh-token flow yet (see module docstring scope
# notes) — a 15-minute token, appropriate for a staff member mid-shift,
# would log a candidate out mid-read of their own application status.
# A longer-lived token is the standard trade-off consumer-facing portals
# make when there's no silent-refresh yet; this is deliberately
# independent of JWT_ACCESS_TOKEN_EXPIRES; staff config changes should
# never accidentally also change candidate session length.
CANDIDATE_TOKEN_LIFETIME = timedelta(days=7)


class CandidateAuthService:
    def __init__(self, candidate_repo):
        self.candidate_repo = candidate_repo

    def signup(self, email, password, first_name, last_name, phone=None):
        existing = self.candidate_repo.get_by_email(email)

        if existing is not None and existing.password_hash is not None:
            raise ValidationError(
                "An account with this email already exists — log in instead.",
                details=[{"field": "email", "message": "Already registered"}],
            )

        if existing is not None:
            # Guest identity from a prior application (see module
            # docstring) — claim it rather than creating a duplicate
            # Candidate row, which would silently split their
            # application history across two identities.
            existing.password_hash = _hash_password(password)
            existing.first_name = first_name
            existing.last_name = last_name
            if phone:
                existing.phone = phone
            self.candidate_repo.commit()
            candidate = existing
        else:
            candidate = Candidate(
                email=email,
                password_hash=_hash_password(password),
                first_name=first_name,
                last_name=last_name,
                phone=phone,
            )
            self.candidate_repo.add(candidate)
            self.candidate_repo.commit()

        return {"access_token": self._issue_access_token(candidate)}

    def login(self, email, password):
        candidate = self.candidate_repo.get_by_email(email)
        # Same shape as staff login's timing-safe-ish handling: run
        # verify_password against a placeholder hash when the account
        # doesn't exist / has no password, so a mistyped email and a
        # correct email + wrong password don't visibly differ in
        # behavior beyond a constant-ish amount of work.
        if candidate is None or candidate.password_hash is None:
            _verify_password(password, _hash_password("placeholder-no-such-account"))
            raise UnauthenticatedError("Invalid email or password")

        if not _verify_password(password, candidate.password_hash):
            raise UnauthenticatedError("Invalid email or password")

        return {"access_token": self._issue_access_token(candidate)}

    def _issue_access_token(self, candidate: Candidate):
        return create_access_token(
            identity=str(candidate.id),
            additional_claims={"actor_type": "candidate"},
            expires_delta=CANDIDATE_TOKEN_LIFETIME,
        )
