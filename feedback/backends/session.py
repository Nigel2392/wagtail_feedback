from typing import TYPE_CHECKING
from django.http import HttpRequest
from wagtail.models import Page

from .base import Feedbackend

if TYPE_CHECKING:
    from feedback.models import AbstractFeedback
    from feedback.forms import FeedbackForm



class SessionBasedFeedbackend(Feedbackend):
    def __init__(self, options: dict = None):
        super().__init__(options)
        self.format_key: str = self.options.get("FORMAT_KEY", "user-feedback-{page.pk}")
        self.format_exists_key: str = self.options.get("FORMAT_EXISTS_KEY", "user-feedback-has-message-{page.pk}")
        

    def is_duplicate(self, request: HttpRequest, page: Page, form: "FeedbackForm", exists: bool = False) -> bool:
        if not request:
            raise RuntimeError("A request must be passed to the form when the instance does not have an IP address.")

        if exists:
            key = self.format_exists_key.format(page=page)
        else:
            key = self.format_key.format(page=page)

        return key in request.session

    def end_check(self, request: HttpRequest, page: Page, form: "FeedbackForm", instance: "AbstractFeedback", exists: bool = False) -> None:
        if exists:
            key = self.format_exists_key.format(page=page)
        else:
            key = self.format_key.format(page=page)
        request.session[key] = True
        request.session.modified = True


