import logging
from abc import ABC, abstractmethod

logger = logging.getLogger("recruitiq.email")

TEMPLATES = {
    "application_stage_changed": "Hi {first_name}, your application for {job_title} has moved to the {stage_name} stage.",
    "resume_uploaded_confirmation": "Hi {first_name}, we've received your resume and it's being processed.",
    "interview_scheduled": "Hi {first_name}, your {round_name} interview for {job_title} has been scheduled.",
}


class BaseEmailSender(ABC):
    @abstractmethod
    def send(self, notification) -> None: ...


class ConsoleEmailSender(BaseEmailSender):
    def send(self, notification) -> None:
        template = TEMPLATES.get(notification.type, "{payload}")
        try:
            body = template.format(**notification.payload)
        except KeyError:
            body = str(notification.payload)  # fall back rather than crash on a template/payload mismatch
        logger.info("[EMAIL to notification %s] %s", notification.id, body)


def build_email_sender(config) -> BaseEmailSender:
    provider = config.get("EMAIL_PROVIDER", "console")
    if provider == "console":
        return ConsoleEmailSender()
    if provider == "ses":
        raise NotImplementedError(
            "SES provider not implemented in this sandbox build — set EMAIL_PROVIDER=console"
        )
    raise ValueError(f"Unknown EMAIL_PROVIDER: {provider}")
