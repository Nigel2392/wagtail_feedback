from django.views.generic.list import (
    BaseListView,
)
from wagtail.admin.views.generic.base import (
    WagtailAdminTemplateMixin,
)

from .. import (
    get_feedback_model,
)


Feedback = get_feedback_model()


class FeedbackOverview(BaseListView):
    template_name = "feedback/feedback_overview.html"
    context_object_name = "feedback_list"
    paginate_by = 10

    def get_queryset(self):
        return Feedback.objects.all().order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['feedback_list'] = self.get_queryset()
        return context

