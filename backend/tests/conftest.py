"""
Shared pytest fixtures.

`app` builds a fresh TestingConfig instance per test session; `db_session`
wraps each test in a transaction that's rolled back afterward, so tests
never leak data into one another. `auth_client` is the fixture most
domain tests will actually use — it gives a Flask test client that's
already carrying a valid access token for a seeded test user, so
feature tests don't each have to re-implement login.
"""

import uuid

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
    """Only used by the db_session fixture below.

    Flask-SQLAlchemy's own Session.get_bind() ignores this session's
    configured `bind` for any ORM operation on a mapped class — it always
    resolves through db.engines by the table's bind_key first, and falls
    back to the app's single default engine whenever no bind_key is set
    (the normal case here, since this app has no SQLALCHEMY_BINDS). That
    silently defeats "join session into an external transaction" for
    tests: every INSERT/UPDATE went straight to the real engine regardless
    of the connection/transaction this fixture set up, so nothing was
    actually rolled back at teardown — rows leaked between tests and
    collided on unique constraints (surfaced as permissions_code_key
    duplicates). Preferring an explicitly-configured `self.bind` first is
    exactly what plain SQLAlchemy's Session.get_bind() already does.
    """

    def get_bind(self, mapper=None, clause=None, bind=None, **kwargs):
        if bind is None and self.bind is not None:
            return self.bind
        return super().get_bind(mapper=mapper, clause=clause, bind=bind, **kwargs)


@pytest.fixture(scope="session")
def app():
    application = create_app("testing")
    with application.app_context():
        _db.create_all()
        # Signup (POST /api/v1/auth/signup) depends on system roles/
        # permissions already existing (company_id=NULL rows) — in a real
        # deploy that's `flask seed-roles`, run once at bootstrap. Tests
        # need the same seed, once per session, or signup 422s.
        seed_system_roles()
        # Clear the session instance seed_system_roles() just created —
        # otherwise it stays cached in the scoped_session registry, and
        # every db_session fixture's later .configure()/class_ swap below
        # silently no-ops against a session that already exists.
        _db.session.remove()
        yield application
        _db.drop_all()


@pytest.fixture
def db_session(app):
    connection = _db.engine.connect()
    transaction = connection.begin()
    # `configure(class_=...)` doesn't work here — sessionmaker.configure()
    # just merges into its kwargs dict without popping `class_` the way
    # __init__ does, so it ends up double-passed and raises. Setting it
    # directly on the underlying sessionmaker (`.session_factory`) is what
    # actually changes which Session subclass gets instantiated.
    _db.session.session_factory.class_ = _TestSession
    _db.session.configure(bind=connection, join_transaction_mode="create_savepoint")

    yield _db.session

    _db.session.remove()
    transaction.rollback()
    connection.close()
    _db.session.session_factory.class_ = _FlaskSQLASession
    # Reset to the engine-level default so any code path that touches
    # db.session without going through this fixture doesn't inherit a
    # connection that's already closed.
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
    # get-or-create by code, not a bare Permission(code=...): system_roles
    # seeding (see the `app` fixture) already created "job.create" for
    # real, once, outside any per-test transaction — a second unconditional
    # insert here collides with that row's unique constraint.
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
