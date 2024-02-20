from typing import TYPE_CHECKING
from django.http import HttpRequest
from wagtail.models import Page
from ..options import (
    IS_PROXIED,
)
from .base import Feedbackend
from .. import get_feedback_model

if TYPE_CHECKING:
    from feedback.models import AbstractFeedback
    from feedback.forms import FeedbackForm



Feedback = get_feedback_model()


class IPBasedFeedbackend(Feedbackend):
    def is_duplicate(self, request: HttpRequest, page: Page, form: "FeedbackForm", exists: bool = False) -> bool:
        if not request:
            raise RuntimeError("A request must be passed to the form when the instance does not have an IP address.")

        ip_address = self.ip_address(request)
        feedback_qs = Feedback.objects.filter(
            ip_address=ip_address,
            page=page,
        )

        return feedback_qs.exists()

    
    def end_check(self, request: HttpRequest, page: Page, form: "FeedbackForm", instance: "AbstractFeedback", exists: bool = False) -> None:
        pass

    @staticmethod
    def ip_address(request: HttpRequest):
        if IS_PROXIED:
            addr: str = request.META.get('HTTP_X_FORWARDED_FOR', None)
            if addr:
                return addr.split(',')[-1].strip()
        else:
            return request.META.get('REMOTE_ADDR', None)

