from app.exceptions.base import InvalidTransitionError

JOB_STATUS_TRANSITIONS = {
    "draft": {"pending_approval"},
    "pending_approval": {"published", "draft"},  # draft = rejected back to draft
    "published": {"closed"},
    "closed": {"archived"},
    "archived": set(),
}


def assert_valid_job_transition(current_status: str, target_status: str) -> None:
    allowed = JOB_STATUS_TRANSITIONS.get(current_status, set())
    if target_status not in allowed:
        raise InvalidTransitionError(
            f"Cannot move job from '{current_status}' to '{target_status}'"
        )


OFFER_STATUS_TRANSITIONS = {
    "draft": {"pending_approval"},
    "pending_approval": {"sent", "draft"},
    "sent": {"accepted", "rejected", "expired", "withdrawn"},
    "accepted": set(),
    "rejected": set(),
    "expired": set(),
    "withdrawn": set(),
}


def assert_valid_offer_transition(current_status: str, target_status: str) -> None:
    allowed = OFFER_STATUS_TRANSITIONS.get(current_status, set())
    if target_status not in allowed:
        raise InvalidTransitionError(
            f"Cannot move offer from '{current_status}' to '{target_status}'"
        )
