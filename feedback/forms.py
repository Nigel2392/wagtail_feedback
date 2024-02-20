from typing import Any
from django import forms
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

from wagtail.models import Page

from . import get_feedback_model
from .backends import IPBasedFeedbackend

class AbstractFeedbackForm(forms.ModelForm):
    class Meta:
        model = get_feedback_model()
        fields = [
            "positive",
            "message",
        ]

        widgets = {
            "message": forms.Textarea(attrs={
                "placeholder": _("Message"),
                "rows": 3,
            }),
        }

        help_texts = {
            "message": _("What would you like to see improved?"),
        }
    
    def __init__(self, *args, request: HttpRequest = None, page: Page = None, requires_message: bool = True, **kwargs):
        self.request = request
        self.page = page
        self.requires_message = requires_message
        super().__init__(*args, **kwargs)
        if self.requires_message:
            del self.fields["positive"]
            self.fields["message"].required = True
        else:
            del self.fields["message"]
    
    def clean(self):
        cleaned = super().clean()
        if self.requires_message:
            message = cleaned.get("message", "")
            if not message.strip():
                raise ValidationError(_("You must provide a message."))
        
        return cleaned

class FeedbackForm(AbstractFeedbackForm):
    def save(self, commit: bool = True) -> Any:
        instance = super().save(False)
        if not self.request and not instance.ip_address:
            raise RuntimeError("A request must be passed to the form when the instance does not have an IP address.")

        elif self.request and not instance.ip_address:
            instance.ip_address = IPBasedFeedbackend.ip_address(self.request)

        if commit:
            instance.save()

        return instance
    


