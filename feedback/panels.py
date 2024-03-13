from django.urls import reverse
from wagtail.admin.panels import Panel

from .templatetags.feedback import (
    FEEDBACK_CSS,
    FEEDBACK_JS,
)

from . import get_feedback_model

Feedback = get_feedback_model()

class FeedbackPanel(Panel):

    def __init__(self, *args, visible_by_default = False, **kwargs):
        super().__init__(*args, **kwargs)
        self.visible_by_default = visible_by_default

    class BoundPanel(Panel.BoundPanel):
        template_name = "feedback/panels/feedback_panel.html"
        panel: "FeedbackPanel"

        class Media:
            js = [
                FEEDBACK_JS,
                "wagtailadmin/js/date-time-chooser.js"
            ]
            css = {
                "all": [
                    FEEDBACK_CSS,
                ]
            }

        def is_shown(self):
            shown = super().is_shown() and self.request.user.has_perm("feedback.view_feedback")
            if not shown:
                return False
            
            if self.instance is None:
                return False
            
            if not self.instance.pk:
                return False
            
            return Feedback.objects.filter(page=self.instance).exists()

        def get_context_data(self, parent_context=None):
            context = super().get_context_data(parent_context)
            context.update(
                self.panel.get_panel_context(self.instance)
            )
            return context
        
    @classmethod
    def get_panel_context(cls, instance, **kwargs):
        return {
            "page": instance,
            "panel_id": f"feedback-panel-{instance.pk}",
            "list_url": reverse("page_feedback_api", kwargs={"page_pk": instance.pk}),
            "chart_url": reverse("page_feedback_api_chart", kwargs={"page_pk": instance.pk}),
        }
