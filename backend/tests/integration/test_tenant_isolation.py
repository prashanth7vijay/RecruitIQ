import uuid

from app.extensions import db as _db
from app.models.company import Company
from app.models.department import Department
from app.models.role import Permission


def _grant(db_session, role, code):
    perm = db_session.query(Permission).filter_by(code=code).first()
    if perm is None:
        perm = Permission(code=code)
        db_session.add(perm)
        db_session.flush()
    if perm not in role.permissions:
        role.permissions.append(perm)
    db_session.commit()


def _make_company_with_department(db_session, name_suffix):
    company = Company(name=f"Company {name_suffix}", slug=f"company-{name_suffix}-{uuid.uuid4().hex[:6]}")
    db_session.add(company)
    db_session.flush()

    department = Department(company_id=company.id, name=f"Engineering {name_suffix}")
    db_session.add(department)
    db_session.commit()
    return company, department


def test_cross_tenant_department_access_returns_404(auth_client, db_session, test_company, test_user):
    _grant(db_session, test_user.role, "org.manage_structure")
    other_company, other_department = _make_company_with_department(db_session, "B")

    response = auth_client.get(f"/api/v1/departments/{other_department.id}")

    assert response.status_code == 404
    body = response.get_json()
    assert body["error"]["code"] == "not_found"

def test_same_tenant_department_access_succeeds(auth_client, db_session, test_company, test_user):
    _grant(db_session, test_user.role, "org.manage_structure")
    department = Department(company_id=test_company.id, name="Engineering A")
    db_session.add(department)
    db_session.commit()

    response = auth_client.get(f"/api/v1/departments/{department.id}")

    assert response.status_code == 200
    body = response.get_json()
    assert body["data"]["name"] == "Engineering A"


def test_recruiter_without_org_manage_permission_cannot_create_department(auth_client):
    response = auth_client.post("/api/v1/departments", json={"name": "New Dept"})

    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "permission_denied"