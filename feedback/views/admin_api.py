from typing import Any, Callable, TYPE_CHECKING, Tuple
from django.http.response import HttpResponse as HttpResponse
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.core.paginator import (
    Paginator,
)
from django.utils.translation import gettext_lazy as _
from django.http import (
    HttpRequest,
    HttpResponse,
    JsonResponse,
)
from django.views.generic import (
    TemplateView,
)
import django_filters as filters
from wagtail.models import (
    Page,
)
from .. import (
    get_feedback_model,
)
from ..filters import (
    FeedbackAggregationFilter,
    FeedbackAggregationTypeFilter,
)
from ..panels import (
    FeedbackPanel,
)
from .utils import (
    redirect_or_respond,
    is_json_request,
    is_htmx_request,
    error,
)

if TYPE_CHECKING:
    from feedback.models import FeedbackQuerySet

Feedback = get_feedback_model()


PAGE_PARAM = "page"


class FeedbackDateRangeFilterSet(filters.FilterSet):
    created_at = filters.DateFromToRangeFilter(
        field_name="created_at",
        label=_("Creation Range"),
        help_text=_("The range of creation dates."),
    )

    class Meta:
        model = get_feedback_model()
        fields = [
            "created_at",
        ]

def filter_created_at(request: HttpRequest, queryset):
    date_filter = FeedbackDateRangeFilterSet(request.GET, queryset=queryset)
    return date_filter, date_filter.qs

def filter_aggregation_type(request: HttpRequest, queryset):
    type_filter = FeedbackAggregationTypeFilter(request.GET, queryset=queryset)

    if "periods" not in request.GET:
        return type_filter, queryset.aggregate_percentage()
    else:
        return type_filter, type_filter.qs

def filter_aggregation_data(request: HttpRequest, queryset):
    aggr_data_filter = FeedbackAggregationFilter(request.GET, queryset=queryset)
    return aggr_data_filter, aggr_data_filter.qs

def filter_list(request: HttpRequest, queryset):
    filter_class = Feedback.get_filter_class()
    filters = filter_class(request.GET, queryset=queryset)
    return filters, filters.qs


class BaseFeedbackPermissionViewMixin:
    has_no_permissions = _("You do not have permission to view feedback instances.")

    def setup(self, request: HttpRequest, *args, **kwargs) -> None:
        r = super().setup(request, *args, **kwargs)

        if not request.user.has_perm("feedback.view_feedback"):
            return error(request, self.has_no_permissions, to="wagtailadmin_home")

        page = self.get_page()
        if page and not page.permissions_for_user(request.user).can_edit():
            return error(request, self.has_no_permissions, to="wagtailadmin_home")

        return r


class FeedbackTemplateResponseMixin:

    def get_json_data(self, context, **kwargs):
        return {}
    
    def render_to_response(self, context, **response_kwargs):

        if is_json_request(self.request):

            data = self.get_json_data(context)

            return JsonResponse(data, json_dumps_params={"indent": 2})
        
        return super().render_to_response(context, **response_kwargs)



class BaseFeedbackListingView(FeedbackTemplateResponseMixin, BaseFeedbackPermissionViewMixin, TemplateView):
    page_size = 10
    queryset_filters: list[Callable[[HttpRequest, "FeedbackQuerySet"], Tuple[filters.FilterSet, "FeedbackQuerySet"]]] = [
        filter_created_at,
    ]

    def get_page(self):
        if "page_pk" in self.kwargs:
            page_qs = Page.objects.live().public().specific()
            self.page: Page = get_object_or_404(page_qs, pk=self.kwargs.get("page_pk", None))

            # Page is passed - check if user has permission to edit (must have to view feedback instances belonging to this page)
            if not self.page.permissions_for_user(self.request.user).can_edit():
                return error(self.request, _("You do not have permission to view feedback instances."), to="wagtailadmin_home")
        else:
            self.page = None
    
    def get_queryset(self):
        self.object_list = Feedback.objects.select_related("page")
        if self.page:
            self.object_list = self.object_list.filter(page=self.page)
        return self.object_list.order_by("-created_at")
    
    def filter_queryset(self, queryset):
        self.filters = []
        for filter_func in self.queryset_filters:
            filter, queryset = filter_func(self.request, queryset)
            self.filters.append(filter)
        return queryset
    
    def paginate_queryset(self, queryset, page_size):
        paginator = Paginator(queryset, page_size)
        page_number = self.request.GET.get(PAGE_PARAM, 1)
        page_obj = paginator.get_page(page_number)

        self.next = None
        if page_obj.has_next():
            query = self.request.GET.copy()
            query[PAGE_PARAM] = page_obj.next_page_number()
            self.next = f"{self.request.path}?{query.urlencode()}"

        self.previous = None
        if page_obj.has_previous():
            query = self.request.GET.copy()
            query[PAGE_PARAM] = page_obj.previous_page_number()
            self.previous = f"{self.request.path}?{query.urlencode()}"

        return paginator, page_obj

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        self.base_queryset = self.get_queryset()
        self.base_queryset = self.filter_queryset(
            self.base_queryset,
        )
        self.paginator, self.object_list = self.paginate_queryset(
            self.base_queryset, self.page_size,
        )

        context["page"] = self.page
        context["filters"] = self.filters
        context["next"] = self.next
        context["previous"] = self.previous
        context["paginator"] = self.paginator
        context["page_obj"] = self.object_list
        context["page_param"] = PAGE_PARAM
        
        if self.page:
            context.update(
                FeedbackPanel.get_panel_context(self.page),
            )
        return context
    
    def get_json_data(self, context, **kwargs):

        extra = {}
        if self.next:
            extra["next"] = self.next

        if self.previous:
            extra["previous"] = self.previous

        return {
            "page": self.object_list.number,
            "pages": self.paginator.num_pages,
            "count": self.paginator.count,
            **extra,
            **kwargs,
        }


class FeedbackAggregateViewAPI(BaseFeedbackListingView):
    page_size = 5
    template_name = "feedback/panels/partials/aggregate.html"

    queryset_filters: list[Callable[[HttpRequest, "FeedbackQuerySet"], Tuple[filters.FilterSet, "FeedbackQuerySet"]]] = [
        *BaseFeedbackListingView.queryset_filters,
        filter_aggregation_type,
        filter_aggregation_data,
    ]    

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["period"] = self.request.GET.get(
            "periods", self.base_queryset.default_period
        )
        return context

    def get_json_data(self, context, **kwargs):
        return super().get_json_data(
            context, 
            **kwargs, 
            period=self.base_queryset.period,
            results=list(self.object_list),
        )

class FeedbackListViewAPI(BaseFeedbackListingView):
    template_name = "feedback/panels/partials/list.html"

    queryset_filters: list[Callable[[HttpRequest, "FeedbackQuerySet"], Tuple[filters.FilterSet, "FeedbackQuerySet"]]] = [
        *BaseFeedbackListingView.queryset_filters,
        filter_list,
    ]

    def get_json_data(self, context, **kwargs):
        return super().get_json_data(
            context,
            **kwargs,
            results=list(map(Feedback.serialize, self.object_list)),
        )


class FeedbackDetailViewAPI(BaseFeedbackPermissionViewMixin, FeedbackTemplateResponseMixin, TemplateView):
    template_name = "feedback/panels/partials/feedback-list-item.html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.object = None

    def get_object(self):
        if not self.object:
            pk = self.kwargs.get("pk", None)
            self.object = get_object_or_404(Feedback, pk=pk)
        return self.object

    def get_page(self):
        self.object = self.get_object()
        return self.object.page

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["feedback"] = self.get_object()
        context.update(
            FeedbackPanel.get_panel_context(self.object.page),
        )
        return context

    def get_json_data(self, context, **kwargs):
        return {
            "feedback": Feedback.serialize(
                self.get_object(),
            ),
        }


class FeedbackDeleteViewAPI(FeedbackDetailViewAPI):
    template_name = "feedback/panels/partials/delete.html"

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        page = self.get_page()

        obj.delete()

        if is_htmx_request(request):
            return HttpResponse(content="", status=200)

        elif is_json_request(request):
            return JsonResponse({
                "success": True,
            }, json_dumps_params={"indent": 2})

        return redirect(page.get_url(request))

    def delete(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        obj = self.get_object()

        if is_json_request(request):
            return JsonResponse({
                "success": True,
                "result": Feedback.serialize(obj),
            }, json_dumps_params={"indent": 2})

        resp = render(request, self.template_name, {
            "feedback": obj,
            **FeedbackPanel.get_panel_context(obj.page),
        })

        return resp
