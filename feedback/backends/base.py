from typing import TYPE_CHECKING
from django.http import HttpRequest
from django.utils.module_loading import import_string
from wagtail.models import Page
from ..options import (
    FEEDBACK_BACKEND,
)


if TYPE_CHECKING:
    from feedback.models import AbstractFeedback
    from feedback.forms import AbstractFeedbackForm



def get_feedback_backend(klass: type = None, options: dict = None) -> "Feedbackend":

    if not klass:
        klass = FEEDBACK_BACKEND.get("CLASS", Feedbackend)

    if not options:
        options = FEEDBACK_BACKEND.get("OPTIONS", {})

    if not klass:
        raise RuntimeError("No feedback backend class specified.")
    
    if isinstance(klass, str):
        klass = import_string(klass)

    return klass(options)

    
class Feedbackend:
    def __init__(self, options: dict = None):
        if callable(options):
            options = options(self)
        self.options = options or {}

    def is_duplicate(self, request: HttpRequest, page: Page, form: "AbstractFeedbackForm", exists: bool = False) -> bool:
        return False

    def end_check(self, request: HttpRequest, page: Page, form: "AbstractFeedbackForm", instance: "AbstractFeedback", exists: bool = False) -> None:
        pass
