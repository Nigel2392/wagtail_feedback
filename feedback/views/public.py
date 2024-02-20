from typing import Callable, Type
from django.forms import ValidationError
from django.shortcuts import (
    get_object_or_404,
)
from django.utils.translation import gettext_lazy as _
from django.http import (
    HttpRequest,
    HttpResponseNotAllowed,
)
from wagtail.models import (
    Page,
)
from ..backends import (
    get_feedback_backend,
)
from .. import (
    get_feedback_model,
)
from .utils import (
    redirect_or_respond,
    error,
)

from wagtail import hooks


Feedback = get_feedback_model()
FeedbackForm = Feedback.get_form_class()


_BeforeFunc = Type[Callable[[HttpRequest, Type[FeedbackForm]], None]]
_AfterFunc = Type[Callable[[HttpRequest, Type[Feedback]], None]]


before_feedback_form_valid         = "before_feedback_form_valid"
after_feedback_form_valid          = "after_feedback_form_valid"
before_feedback_message_form_valid = "before_feedback_message_form_valid"
after_feedback_message_form_valid  = "after_feedback_message_form_valid"


# Create your views here.
def feedback(request, *args, **kwargs):        
    if not request.method == "POST":
        return HttpResponseNotAllowed(["POST"])
    
    template = "feedback/form.html"

    page_qs = Page.objects.live().public().specific()
    page: Page = get_object_or_404(page_qs, pk=kwargs.get("page_pk", None))
    form = Feedback.get_form_class()(
        request.POST,
        request=request,
        requires_message=False,
    )

    backend = get_feedback_backend()
    if backend.is_duplicate(request, page, form, exists=False):
        return error(
            request, 
            _("You have already submitted feedback for this page."), 
            WRAPPER="feedback/wrapper.html", 
            to=page.get_url(request),
        )

    try:
        hks: list[_BeforeFunc] = hooks.get_hooks(before_feedback_form_valid)
        for fn in hks:
            fn(request, form)
    except ValidationError as e:
        form.add_error(None, e)

    valid = form.is_valid()

    if valid:
        form.instance.page = page
        form.instance = form.save()

        hks: list[_AfterFunc] = hooks.get_hooks(after_feedback_form_valid)
        for fn in hks:
            fn(request, form.instance)

        backend.end_check(request, page, form, form.instance, exists=False)

        # If the feedback is positive and it is allowed, or if it is negative
        # then show the message form.
        if hasattr(page, "allow_feedback_message_on_positive")\
            and not page.allow_feedback_message_on_positive()\
            and form.instance.positive\
            or not form.instance.positive:

            form = FeedbackForm(
                request=request,
                page=page,
                requires_message=True,
                instance=form.instance,
            )
        else:
            template = "feedback/thanks.html"
    else:
        template = "feedback/happy-sad.html"

    context = page.get_context(request, *args, **kwargs)
    context["form"] = form
    context["feedback"] = form.instance

    if form.errors:
        context["errors"] = form.errors

    return redirect_or_respond(
        request,
        page.get_url(request),
        template,
        context=context,
        message=_("Thank you for your feedback."),
    )


def feedback_with_message(request, *args, **kwargs):
    if not request.method == "POST":
        return HttpResponseNotAllowed(["POST"])
    
    template = "feedback/form.html"

    page_qs = Page.objects.live().public().specific()
    page: Page = get_object_or_404(page_qs, pk=kwargs.get("page_pk", None))
    feedback = get_object_or_404(Feedback, pk=kwargs.get("pk", None))

    if hasattr(page, "allow_feedback_message_on_positive") \
        and not page.allow_feedback_message_on_positive() \
        and feedback.positive:
        return error(
            request, 
            _("Feedback messages are not allowed on positive feedback."), 
            WRAPPER="feedback/wrapper.html", 
            to=page.get_url(request),
        )

    form = FeedbackForm(
        request.POST,
        request=request,
        page=page,
        requires_message=True,
        instance=feedback,
    )

    backend = get_feedback_backend()
    if backend.is_duplicate(request, page, form, exists=True):
        return error(
            request, 
            _("You have already submitted feedback for this page."), 
            WRAPPER="feedback/wrapper.html", 
            to=page.get_url(request),
        )

    try:
        hks: list[_BeforeFunc] = hooks.get_hooks(before_feedback_message_form_valid)
        for fn in hks:
            fn(request, form)
    except ValidationError as e:
        form.add_error(None, e)

    if form.is_valid():
        form.instance.page = page
        form.instance = form.save()
        template = "feedback/thanks.html"

        backend.end_check(request, page, form, form.instance, exists=True)

        hks: list[_AfterFunc] = hooks.get_hooks(after_feedback_message_form_valid)
        for fn in hks:
            fn(request, form.instance)

    context = page.get_context(request, *args, **kwargs)
    context["form"] = form
    context["feedback"] = form.instance

    return redirect_or_respond(
        request,
        page.get_url(request),
        template,
        context=context,
    )

