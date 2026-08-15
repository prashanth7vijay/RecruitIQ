from app import create_app
from app.utils.pagination import paginate_query, DEFAULT_PER_PAGE, MAX_PER_PAGE


class _FakeQuery:

    def __init__(self, total):
        self._total = total
        self._offset = 0
        self._limit = None

    def count(self):
        return self._total

    def offset(self, n):
        self._offset = n
        return self

    def limit(self, n):
        self._limit = n
        return self

    def all(self):
        # Simulate returning `limit` items starting at `offset`, capped at total.
        remaining = max(0, self._total - self._offset)
        return list(range(min(self._limit or remaining, remaining)))


def test_default_pagination_uses_page_1_and_default_per_page():
    app = create_app("testing")
    with app.test_request_context("/?"):
        items, meta = paginate_query(_FakeQuery(total=45))
    assert meta["pagination"]["page"] == 1
    assert meta["pagination"]["per_page"] == DEFAULT_PER_PAGE
    assert meta["pagination"]["total_items"] == 45
    assert meta["pagination"]["total_pages"] == 3  # ceil(45/20)
    assert len(items) == DEFAULT_PER_PAGE


def test_per_page_is_capped_at_max():
    app = create_app("testing")
    with app.test_request_context("/?per_page=99999"):
        _, meta = paginate_query(_FakeQuery(total=500))
    assert meta["pagination"]["per_page"] == MAX_PER_PAGE


def test_page_below_one_is_clamped_to_one():
    app = create_app("testing")
    with app.test_request_context("/?page=0"):
        _, meta = paginate_query(_FakeQuery(total=10))
    assert meta["pagination"]["page"] == 1


def test_last_page_returns_partial_results():
    app = create_app("testing")
    with app.test_request_context("/?page=3&per_page=20"):
        items, meta = paginate_query(_FakeQuery(total=45))
    assert meta["pagination"]["total_pages"] == 3
    assert len(items) == 5  # 45 - 2*20 = 5 remaining on the last page
