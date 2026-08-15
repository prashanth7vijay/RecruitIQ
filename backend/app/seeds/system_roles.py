from app.extensions import db
from app.models.role import Role, Permission, SYSTEM_ROLES, SYSTEM_PERMISSIONS

# Full permission matrix from Phase 4 — coarser than the eventual UI-editable
# version, but complete enough for every route currently gated by
# @require_permission in Sprint 1/2.
ROLE_PERMISSION_MAP = {
    "org_admin": SYSTEM_PERMISSIONS,  # org_admin gets everything
    "recruiter": [
        "job.create", "job.publish", "job.close",
        "candidate.view_all", "candidate.reject", "candidate.manage",
        "interview.schedule",
        "offer.create",
        "application.manage",
        "onboarding.manage",
    ],
    "hiring_manager": [
        "job.approve",
        "candidate.view_all", "candidate.reject",
        "interview.schedule", "interview.feedback.submit",
        "offer.approve",
        "analytics.view_org",
        "application.manage",
    ],
    "interviewer": [
        "interview.feedback.submit",
    ],
    "hr": [
        "offer.create", "offer.approve",
        "analytics.view_org",
        "onboarding.manage",
    ],
    "employee": [
        "referral.submit",
    ],
}


def run():
    _seed_permissions()
    _seed_roles_and_assign_permissions()
    db.session.commit()
    print("System roles and permissions seeded.")


def _seed_permissions():
    existing_codes = {p.code for p in Permission.query.filter(Permission.code.in_(SYSTEM_PERMISSIONS))}
    for code in SYSTEM_PERMISSIONS:
        if code not in existing_codes:
            db.session.add(Permission(code=code))
    db.session.flush()


def _seed_roles_and_assign_permissions():
    existing_roles = {
        r.name: r for r in Role.query.filter(Role.company_id.is_(None), Role.name.in_(SYSTEM_ROLES))
    }
    all_permissions = {p.code: p for p in Permission.query.all()}

    for role_name in SYSTEM_ROLES:
        role = existing_roles.get(role_name)
        if role is None:
            role = Role(company_id=None, name=role_name, is_system_role=True)
            db.session.add(role)
            db.session.flush()

        wanted_codes = set(ROLE_PERMISSION_MAP.get(role_name, []))
        current_codes = {p.code for p in role.permissions}
        for code in wanted_codes - current_codes:
            permission = all_permissions.get(code)
            if permission is not None:
                role.permissions.append(permission)
