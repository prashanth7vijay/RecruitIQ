from sqlalchemy import Column, String, Boolean, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.extensions import db
from app.models.base import Base, UUIDPrimaryKeyMixin

role_permissions = Table(
    "role_permissions",
    db.metadata,
    Column("role_id", UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "permission_id",
        UUID(as_uuid=True),
        ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Role(Base, UUIDPrimaryKeyMixin, db.Model):

    __tablename__ = "roles"

    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=True)
    name = Column(String(100), nullable=False)
    is_system_role = Column(Boolean, nullable=False, default=True)

    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")


class Permission(Base, UUIDPrimaryKeyMixin, db.Model):
    __tablename__ = "permissions"

    code = Column(String(100), nullable=False, unique=True)  # e.g. 'job.create'

    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")


SYSTEM_ROLES = [
    "org_admin",
    "recruiter",
    "hiring_manager",
    "interviewer",
    "hr",
    "employee",
]

SYSTEM_PERMISSIONS = [
    "job.create", "job.approve", "job.publish", "job.close",
    "candidate.view_all", "candidate.reject", "candidate.manage",
    "interview.schedule", "interview.feedback.submit",
    "offer.create", "offer.approve",
    "referral.submit",
    "analytics.view_org",
    "admin.manage_users",
    "org.manage_structure",  # departments/teams CRUD — Sprint 2
    "company.manage_settings",  # company name/branding/settings — Sprint 3 gap-fix
    "application.manage",  # move candidates through the pipeline — Sprint 5
    "onboarding.manage",  # assign buddy/manager, complete tasks — Sprint 8
    "role.manage",  # create/edit/delete custom roles — Branding Center iteration, RBAC module
    "pipeline.manage",  # design/edit/delete recruitment pipeline templates — Pipeline Builder module.
    # Deliberately separate from job.create: a recruiter creating a job
    # only ever *selects* an existing template (see jobs/schemas.py
    # pipeline_template_id), never designs one — matches the Priority-1
    # requirement that pipeline design is admin-only, using pipelines is not.
    "approval.manage_chains",  # configure who must approve Jobs/Offers, and in what order — Approval Workflows module.
]
