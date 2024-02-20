from typing import Literal as L
from django.conf import settings


FEEDBACK_MODEL_NAME = getattr(settings, "FEEDBACK_MODEL_NAME", "feedback.Feedback")
FEEDBACK_FORM_CLASS = getattr(settings, "FEEDBACK_FORM_CLASS", "feedback.forms.FeedbackForm")
FEEDBACK_FILTER_CLASS = getattr(settings, "FEEDBACK_FILTER_CLASS", "feedback.filters.AbstractFeedbackFilter")
FEEDBACK_BACKEND = getattr(settings, "FEEDBACK_BACKEND", {
    "CLASS": "feedback.backends.IPBasedFeedbackend",
    "OPTIONS": {
        # ...
    }
})
IS_PROXIED = getattr(settings, "USE_X_FORWARDED_HOST", False)
