from typing import TYPE_CHECKING
from django.db import models
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import (
    FieldPanel,
)
from wagtail.models import Page

if TYPE_CHECKING:
    from feedback.models import AbstractFeedback
    from feedback.forms import FeedbackForm


class FeedbackendPageMixin:
    def check_for_feedback_duplicate(self, request: HttpRequest, form: "FeedbackForm", exists: bool = False):
        raise NotImplementedError("This method must be implemented by a subclass.")

    def end_feedback_check(self, request: HttpRequest, form: "FeedbackForm", instance: "AbstractFeedback", exists: bool = False):
        raise NotImplementedError("This method must be implemented by a subclass.")


class FeedbackPageMixin:

    class Meta:
        abstract = True

    def allow_feedback_message_on_positive(self):
        return True

    def get_feedback_title(self):
        return None

    def get_feedback_thanks(self):
        return None

    def get_feedback_explainer(self):
        return None

    def get_feedback_positive_text(self):
        return None

    def get_feedback_negative_text(self):
        return None


class CustomFeedbackPageMixin(FeedbackPageMixin, Page):
    class Meta:
        abstract = True

    feedback_title = models.CharField(
        max_length=255,
        blank=False,
        null=True,
        verbose_name=_("Feedback Title"),
        help_text=_("The title of the feedback form."),
    )
    feedback_thanks = models.CharField(
        max_length=255,
        blank=False,
        null=True,
        verbose_name=_("Feedback Thanks"),
        help_text=_("The message shown after submitting feedback."),
    )
    feedback_explainer = models.CharField(
        max_length=255,
        blank=False,
        null=True,
        verbose_name=_("Feedback Explainer"),
        help_text=_("The message shown before submitting feedback, explaining what the feedback should be about."),
    )
    feedback_positive_text = models.CharField(
        max_length=255,
        blank=False,
        null=True,
        verbose_name=_("Feedback Positive Text"),
        help_text=_("The text shown for positive feedback tooltip."),
    )
    feedback_negative_text = models.CharField(
        max_length=255,
        blank=False,
        null=True,
        verbose_name=_("Feedback Negative Text"),
        help_text=_("The text shown for negative feedback tooltip."),
    )
    message_if_positive = models.BooleanField(
        blank=False,
        null=False,
        default=False,
        verbose_name=_("Message If Positive"),
        help_text=_("Allow asking for explanation if the feedback is positive."),
    )

    feedback_panels = [
        FieldPanel("feedback_title"),
        FieldPanel("feedback_thanks"),
        FieldPanel("feedback_explainer"),
        FieldPanel("feedback_positive_text"),
        FieldPanel("feedback_negative_text"),
        FieldPanel("message_if_positive"),
    ]

    def allow_feedback_message_on_positive(self):
        return self.message_if_positive
    
    def get_feedback_title(self):
        return self.feedback_title
    
    def get_feedback_thanks(self):
        return self.feedback_thanks
    
    def get_feedback_explainer(self):
        return self.feedback_explainer
    
    def get_feedback_positive_text(self):
        return self.feedback_positive_text
    
    def get_feedback_negative_text(self):
        return self.feedback_negative_text
    