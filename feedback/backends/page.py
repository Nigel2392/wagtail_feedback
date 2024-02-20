from typing import TYPE_CHECKING, Union
from django.http import HttpRequest
from django.utils.module_loading import import_string
from wagtail.models import Page

from .base import Feedbackend, get_feedback_backend

if TYPE_CHECKING:
    from feedback.models import AbstractFeedback
    from feedback.forms import FeedbackForm
    from feedback.mixins import FeedbackendPageMixin



class PageBasedFeedbackend(Feedbackend):
    def __init__(self, options: dict = None):
        super().__init__(options)
        backup_backend = self.options.get("BACKUP_BACKEND", None)
        backup_backend_options = self.options.get("BACKUP_BACKEND_OPTIONS", {})

        if backup_backend:
            self.backup = get_feedback_backend(
                klass=backup_backend,
                options=backup_backend_options,
            )
        else:
            self.backup = None


    def is_duplicate(self, request: HttpRequest, page: Union[Page, FeedbackendPageMixin], form: "FeedbackForm", exists: bool = False) -> bool:
        if hasattr(page, "check_for_feedback_duplicate"):
            return page.check_for_feedback_duplicate(request, form, exists=exists)
        
        if self.backup:
            return self.backup.is_duplicate(request, page, form, exists=exists)
        
        return False


    def end_check(self, request: HttpRequest, page: Union[Page, FeedbackendPageMixin], form: "FeedbackForm", instance: "AbstractFeedback", exists: bool = False) -> None:
        if hasattr(page, "end_feedback_check"):
            page.end_feedback_check(request, form, instance, exists=exists)
            return

        if self.backup:
            self.backup.end_check(request, page, form, instance, exists=exists)
            return

