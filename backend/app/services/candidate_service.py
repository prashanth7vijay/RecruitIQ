"""
CandidateService implements the get-or-create-by-email pattern for the
global Candidate identity (Phase 9a): if a recruiter adds a candidate
whose email already exists globally (they applied to a different
tenant previously), we reuse that Candidate row and just create a new,
isolated CandidateProfile for this tenant — never a duplicate global
identity, and never leaking the fact that another tenant has profiled
them.
"""

from app.exceptions.base import BusinessRuleViolationError
from app.models.candidate import Candidate, CandidateProfile
from app.models.resume import Resume


class CandidateService:
    def __init__(self, candidate_repo, profile_repo, resume_repo, event_bus=None, note_repo=None, tag_repo=None):
        self.candidate_repo = candidate_repo
        self.profile_repo = profile_repo
        self.resume_repo = resume_repo
        self.event_bus = event_bus
        self.note_repo = note_repo
        self.tag_repo = tag_repo

    def add_candidate(self, tenant_id, email, first_name, last_name, phone=None, source=None):
        candidate = self.candidate_repo.get_by_email(email)
        if candidate is None:
            candidate = Candidate(email=email, first_name=first_name, last_name=last_name, phone=phone)
            self.candidate_repo.add(candidate)
            self.candidate_repo.commit()

        existing_profile = self.profile_repo.get_by_candidate(tenant_id, candidate.id)
        if existing_profile is not None:
            raise BusinessRuleViolationError(
                "This candidate already has a profile in your organization"
            )

        profile = CandidateProfile(company_id=tenant_id, candidate_id=candidate.id, source=source)
        self.profile_repo.add(profile)
        self.profile_repo.commit()
        return candidate, profile

    def get_or_create_profile(self, tenant_id, email, first_name, last_name, phone=None, source=None):
        """
        Unlike add_candidate (which errors if a profile already exists —
        the recruiter-initiated "add to my pool" case), this is for the
        public apply flow: a candidate applying to a second job at the
        same company should reuse their existing profile, not error.
        """
        candidate = self.candidate_repo.get_by_email(email)
        if candidate is None:
            candidate = Candidate(email=email, first_name=first_name, last_name=last_name, phone=phone)
            self.candidate_repo.add(candidate)
            self.candidate_repo.commit()

        profile = self.profile_repo.get_by_candidate(tenant_id, candidate.id)
        if profile is None:
            profile = CandidateProfile(company_id=tenant_id, candidate_id=candidate.id, source=source)
            self.profile_repo.add(profile)
            self.profile_repo.commit()
        return candidate, profile

    def find_or_create_identity(self, email):
        email = email.strip().lower()

        candidate = self.candidate_repo.get_by_email(email)
        if candidate is not None:
            return candidate

        candidate = Candidate(
            email=email,
            first_name="",
            last_name="",
        )

        self.candidate_repo.add(candidate)
        self.candidate_repo.commit()

        return candidate



    def get_profile(self, tenant_id, profile_id):
        return self.profile_repo.get_or_404(profile_id, tenant_id)

    def list_profiles(self, tenant_id):
        return self.profile_repo.list(tenant_id).all()

    def update_profile(self, tenant_id, profile_id, **fields):
        profile = self.profile_repo.get_or_404(profile_id, tenant_id)
        for key, value in fields.items():
            if value is not None:
                setattr(profile, key, value)
        self.profile_repo.commit()
        return profile

    def attach_resume(self, tenant_id, profile_id, storage_key, original_filename):
        profile = self.profile_repo.get_or_404(profile_id, tenant_id)

        existing = self.resume_repo.list_for_candidate(profile.candidate_id).first()
        next_version = (existing.version + 1) if existing else 1

        resume = Resume(
            candidate_id=profile.candidate_id,
            storage_key=storage_key,
            original_filename=original_filename,
            version=next_version,
            parse_status="pending",
        )
        self.resume_repo.add(resume)
        self.resume_repo.commit()

        profile.resume_id = resume.id
        self.profile_repo.commit()

        if self.event_bus is not None:
            self.event_bus.publish("resume.uploaded", {"resume_id": str(resume.id)})

        return resume

    # --- Notes & tags (Sprint 10 CRM) ---------------------------------

    def add_note(self, tenant_id, profile_id, author_id, body):
        from app.models.candidate_crm import CandidateNote

        self.profile_repo.get_or_404(profile_id, tenant_id)  # confirms profile belongs to this tenant
        note = CandidateNote(company_id=tenant_id, candidate_profile_id=profile_id, author_id=author_id, body=body)
        self.note_repo.add(note)
        self.note_repo.commit()
        return note

    def list_notes(self, tenant_id, profile_id):
        self.profile_repo.get_or_404(profile_id, tenant_id)
        return self.note_repo.list_for_profile(tenant_id, profile_id)

    def add_tag(self, tenant_id, profile_id, label):
        from app.models.candidate_crm import CandidateTag

        self.profile_repo.get_or_404(profile_id, tenant_id)
        existing = self.tag_repo.get_by_label(tenant_id, profile_id, label)
        if existing is not None:
            return existing  # idempotent — adding the same tag twice is a no-op, not an error

        tag = CandidateTag(company_id=tenant_id, candidate_profile_id=profile_id, label=label)
        self.tag_repo.add(tag)
        self.tag_repo.commit()
        return tag

    def list_tags(self, tenant_id, profile_id):
        self.profile_repo.get_or_404(profile_id, tenant_id)
        return self.tag_repo.list_for_profile(tenant_id, profile_id)
