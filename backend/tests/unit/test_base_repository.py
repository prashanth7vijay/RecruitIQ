
import pytest

from app.repositories.base_repository import TenantScopedRepository


class _FakeModel:
    company_id = None
    id = None


class _FakeRepo(TenantScopedRepository):
    model = _FakeModel


def test_base_query_raises_without_tenant_id():
    repo = _FakeRepo(session=object())
    with pytest.raises(ValueError, match="tenant_id is required"):
        repo._base_query(tenant_id=None)


def test_repository_requires_model_to_be_set():
    class _IncompleteRepo(TenantScopedRepository):
        pass  # forgot to set `model`

    with pytest.raises(NotImplementedError):
        _IncompleteRepo(session=object())
