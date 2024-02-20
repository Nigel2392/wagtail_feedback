from django.apps import apps as django_apps
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings
from typing import TYPE_CHECKING, Type
from .options import FEEDBACK_MODEL_NAME

if TYPE_CHECKING:
    from feedback.models import AbstractFeedback

def get_feedback_model() -> Type["AbstractFeedback"]:
    """
    Return the User model that is active in this project.
    """
    try:
        return django_apps.get_model(FEEDBACK_MODEL_NAME, require_ready=False)
    except ValueError:
        raise ImproperlyConfigured(
            "FEEDBACK_MODEL must be of the form 'app_label.model_name'"
        )
    except LookupError:
        raise ImproperlyConfigured(
            "FEEDBACK_MODEL refers to model '%s' that has not been installed"
            % FEEDBACK_MODEL_NAME
        )

__version__ = "1.1.7"
VERSION = __version__