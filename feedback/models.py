from typing import Literal as L, Self, Type, Union, TYPE_CHECKING
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.functional import classproperty
from django.utils.module_loading import import_string

from wagtail.models import Page
from wagtail.admin.panels import (
    FieldPanel,
    TabbedInterface,
    ObjectList,
)

from .options import (
    FEEDBACK_FORM_CLASS,
    FEEDBACK_FILTER_CLASS,
)

if TYPE_CHECKING:
    from feedback.filters import AbstractFeedbackFilter
    from feedback.forms import AbstractFeedbackForm


class FeedbackQuerySet(models.QuerySet):
    default_period: Union[L['hour'], L['date'], L["month"], L["year"]] = "hour"

    def positive(self):
        return self.filter(positive=True)
    
    def negative(self):
        return self.filter(positive=False)
    
    def for_page(self, page):
        return self.filter(page=page)
    
    def percentages(self):
        return self.annotate(
            total=models.Count('id'),
            positive_count=models.Count('id', filter=models.Q(positive=True)),
            negative_count=models.Count('id', filter=models.Q(positive=False)),
        ).annotate(
            positive_percentage=models.ExpressionWrapper(
                models.F('positive_count') * 100.0 / models.F('total'),
                output_field=models.FloatField()
            ),
            negative_percentage=models.ExpressionWrapper(
                100.0 - models.F('positive_percentage'),
                output_field=models.FloatField()
            ),
        )
    
    def aggregate_percentage(self, date_arg: Union[L['hour'], L['date'], L["month"], L["year"]] = None, extra_values_args: list[str] = None):
        if extra_values_args is None:
            extra_values_args = []

        filter_by = date_arg

        if filter_by is None:
            filter_by = self.default_period

        values_args = []
        hours = filter_by == "hour"
        if hours:
            filter_by = "date"
            values_args.append(f"created_at__{filter_by}")
            values_args.append("created_at__hour")
        else:
            values_args.append(f"created_at__{filter_by}")
        
        values_args.extend(extra_values_args)

        qs = self.values(*values_args).percentages()

        if hours:
            qs = qs.order_by(f"-created_at__{filter_by}", "-created_at__hour")
        else:
            qs = qs.order_by(f"-created_at__{filter_by}")

        setattr(qs, "period", filter_by)
        setattr(qs, "hours", hours)
        return qs


class AbstractFeedback(models.Model):
    FEEDBACK_FORM_CLASS = FEEDBACK_FORM_CLASS
    FEEDBACK_FILTER_CLASS = FEEDBACK_FILTER_CLASS

    panel_tabs: list[tuple[str, str]] = [
        ("content_panels", _("Content")),
        ("metadata_panels", _("Metadata")),
    ]

    positive = models.BooleanField(
        blank=False,
        null=False,
        verbose_name=_("Positive"),
        help_text=_("Whether the feedback is positive or negative."),
    )
    message = models.TextField(
        blank=False,
        null=True,
        verbose_name=_("Message"),
        help_text=_("The message of the feedback."),
    )
    page = models.ForeignKey(
        "wagtailcore.Page",
        on_delete=models.CASCADE,
        blank=False,
        null=False,
        related_name="+",
        verbose_name=_("Page"),
        help_text=_("The page the feedback is for."),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At"),
        help_text=_("The time the feedback was created."),
    )

    content_panels = [
        FieldPanel("positive"),
        FieldPanel("message"),
    ]

    metadata_panels = [
        FieldPanel("page"),
        FieldPanel("created_at"),
    ]

    objects: FeedbackQuerySet = FeedbackQuerySet.as_manager()

    class Meta:
        abstract = True

    @classmethod
    def serialize(cls, instance: Self):
        return {
            "id": instance.pk,
            "page": instance.page_id,
            "message": instance.message,
            "created_at": instance.created_at,
            "urls": {
                "list":      reverse("feedback_api_list"),
                "page_list": reverse("page_feedback_api", kwargs={"page_pk": instance.page_id}),
                "view":      reverse("feedback_api_detail", kwargs={"page_pk": instance.page_id, "pk": instance.pk}),
                "detail":    reverse("feedback_api_detail", kwargs={"pk": instance.pk}),
                "delete":    reverse("feedback_api_delete", kwargs={"pk": instance.pk}),
            },
        }
    
    @classmethod
    def get_filter_class(cls) -> Type["AbstractFeedbackFilter"]:
        filter_class = cls.FEEDBACK_FILTER_CLASS
        if isinstance(filter_class, str):
            filter_class = import_string(filter_class)
        return filter_class

    @classmethod
    def get_form_class(cls) -> Type["AbstractFeedbackForm"]:
        form_class = cls.FEEDBACK_FORM_CLASS
        if isinstance(form_class, str):
            form_class = import_string(form_class)
        return form_class

    def __str__(self):
        if self.message and len(self.message) > 50:
            return f"{self.message[:50]}... ({self.page.title})"
        elif self.message:
            return f"{self.message} ({self.page.title})"
        else:
            message = _("Positive") if self.positive else _("Negative")
            return f"{message} ({self.page.title})"

    @property
    def is_positive(self):
        return self.positive

    @property
    def is_negative(self):
        return not self.positive
    
    @property
    def negative(self):
        return not self.positive
    
    @is_positive.setter
    def is_positive(self, value):
        self.positive = value

    @is_negative.setter
    def is_negative(self, value):
        self.positive = not value

    @negative.setter
    def negative(self, value):
        self.positive = not value


    # @property
    # def is_neutral(self):
    #     return (
    #         # Allow for a 10% margin of error
    #         self.is_positive + 10 > self.is_negative
    #         and self.is_positive - 10 < self.is_negative
    #     )\
    #     or int(self.is_positive) == int(self.is_negative)
    
    @classmethod
    def edit_handler_kwargs(cls):
        return {}

    @classproperty
    def edit_handler(cls):
        tabs = []

        for panel_attr, heading in cls.panel_tabs:
            tabs.append(
                ObjectList(getattr(cls, panel_attr), heading=heading),
            )

        return TabbedInterface(tabs, **cls.edit_handler_kwargs())


class Feedback(AbstractFeedback):
    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        verbose_name=_("IP Address"),
        help_text=_("The IP address of the feedback."),
    )

    metadata_panels = AbstractFeedback.metadata_panels + [
        FieldPanel("ip_address"),
    ]

    objects: FeedbackQuerySet = FeedbackQuerySet.as_manager()

    class Meta:
        verbose_name = _("Feedback")
        verbose_name_plural = _("Feedback")
        ordering = ["-created_at"]

    def serialize(cls, instance: Self):
        return super().serialize(instance) | {
            "ip_address": instance.ip_address,
        }

    