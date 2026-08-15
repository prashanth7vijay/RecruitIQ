import pytest

from app.exceptions.base import InvalidTransitionError
from app.validators.state_transitions import assert_valid_offer_transition


def test_draft_to_pending_approval_is_valid():
    assert_valid_offer_transition("draft", "pending_approval")


def test_pending_approval_to_sent_is_valid():
    assert_valid_offer_transition("pending_approval", "sent")


def test_pending_approval_rejection_back_to_draft_is_valid():
    assert_valid_offer_transition("pending_approval", "draft")


def test_sent_to_accepted_is_valid():
    assert_valid_offer_transition("sent", "accepted")


def test_sent_to_withdrawn_is_valid():
    assert_valid_offer_transition("sent", "withdrawn")


def test_draft_to_sent_is_invalid():
    with pytest.raises(InvalidTransitionError, match="Cannot move offer from 'draft' to 'sent'"):
        assert_valid_offer_transition("draft", "sent")


def test_accepted_has_no_further_transitions():
    with pytest.raises(InvalidTransitionError):
        assert_valid_offer_transition("accepted", "withdrawn")
