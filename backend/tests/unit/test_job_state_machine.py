import pytest

from app.exceptions.base import InvalidTransitionError
from app.validators.state_transitions import assert_valid_job_transition


def test_draft_to_pending_approval_is_valid():
    assert_valid_job_transition("draft", "pending_approval")  # should not raise


def test_pending_approval_to_published_is_valid():
    assert_valid_job_transition("pending_approval", "published")


def test_pending_approval_to_draft_rejection_is_valid():
    assert_valid_job_transition("pending_approval", "draft")


def test_draft_to_closed_is_invalid():
    with pytest.raises(InvalidTransitionError, match="Cannot move job from 'draft' to 'closed'"):
        assert_valid_job_transition("draft", "closed")


def test_published_to_draft_is_invalid():
    with pytest.raises(InvalidTransitionError):
        assert_valid_job_transition("published", "draft")


def test_archived_has_no_valid_transitions():
    with pytest.raises(InvalidTransitionError):
        assert_valid_job_transition("archived", "published")
