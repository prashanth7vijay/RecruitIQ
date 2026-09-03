import uuid
import io

import pytest
from flask_sqlalchemy.session import Session as _FlaskSQLASession

from app import create_app
from app.extensions import db as _db
from app.models.company import Company
from app.models.role import Role, Permission
from app.models.user import User
from app.seeds.system_roles import run as seed_system_roles
from app.services.auth_service import _hash_password


class _TestSession(_FlaskSQLASession):
    def get_bind(self, mapper=None, clause=None, bind=None, **kwargs):
        if bind is None and self.bind is not None:
            return self.bind
        return super().get_bind(mapper=mapper, clause=clause, bind=bind, **kwargs)


@pytest.fixture(scope="session")
def app():
    application = create_app("testing")
    with application.app_context():
        _db.create_all()
        seed_system_roles()
        _db.session.remove()
        yield application
        _db.drop_all()


@pytest.fixture
def db_session(app):
    connection = _db.engine.connect()
    transaction = connection.begin()
    _db.session.session_factory.class_ = _TestSession
    _db.session.configure(bind=connection, join_transaction_mode="create_savepoint")

    yield _db.session

    _db.session.remove()
    transaction.rollback()
    connection.close()
    _db.session.session_factory.class_ = _FlaskSQLASession
    _db.session.configure(bind=None, join_transaction_mode="conditional_savepoint")


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def test_company(db_session):
    company = Company(name="Acme Test Co", slug=f"acme-{uuid.uuid4().hex[:8]}")
    db_session.add(company)
    db_session.commit()
    return company


@pytest.fixture
def recruiter_role(db_session):
    role = Role(company_id=None, name="recruiter", is_system_role=True)
    perm = Permission.query.filter_by(code="job.create").first()
    if perm is None:
        perm = Permission(code="job.create")
        db_session.add(perm)
    role.permissions.append(perm)
    db_session.add(role)
    db_session.commit()
    return role


@pytest.fixture
def test_user(db_session, test_company, recruiter_role):
    user = User(
        company_id=test_company.id,
        email="recruiter@acme-test.com",
        password_hash=_hash_password("correct-horse-battery-staple"),
        first_name="Test",
        last_name="Recruiter",
        role_id=recruiter_role.id,
        status="active",
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def auth_client(client, test_user, test_company):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "company_slug": test_company.slug,
            "email": test_user.email,
            "password": "correct-horse-battery-staple",
        },
    )
    access_token = response.get_json()["data"]["access_token"]
    client.environ_base["HTTP_AUTHORIZATION"] = f"Bearer {access_token}"
    return client


def dummy_resume(filename="resume.pdf"):
    return (io.BytesIO(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\ntest resume content"), filename)