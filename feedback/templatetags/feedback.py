from typing import Union, Literal
from django.template import library, loader
from django.utils.safestring import mark_safe
from django.templatetags.static import static
from django.template.defaultfilters import date as date_filter
from django.utils import timezone
import datetime
from wagtail.models import PAGE_TEMPLATE_VAR

register = library.Library()

FEEDBACK_TEMPLATE = "feedback/happy-sad.html"
FEEDBACK_CSS = "feedback/css/feedback.css"
FEEDBACK_JS = "feedback/js/feedback.js"

@register.simple_tag(takes_context=True, name="feedback")
def feedback(context, page = None):
    request = context["request"]

    if page is None and PAGE_TEMPLATE_VAR not in context:
        raise RuntimeError("No page found in context")
    
    if page is None:
        page = context[PAGE_TEMPLATE_VAR]

    context = {
        "page": page,
        "request": request,
    }

    return mark_safe(loader.render_to_string(
        FEEDBACK_TEMPLATE,
        context,
        request=request,
    ))

@register.simple_tag(name="feedback_css")
def feedback_css():
    return mark_safe(f"<link rel='stylesheet' href='{static(FEEDBACK_CSS)}'>")

@register.simple_tag(name="feedback_js")
def feedback_js():
    return mark_safe(f"<script src='{static(FEEDBACK_JS)}'></script>")

@register.simple_tag
def get_proper_elided_page_range(p, number, on_each_side=3, on_ends=2):
    return p.get_elided_page_range(number=number, on_each_side=on_each_side, on_ends=on_ends)

class _impossible:
    def __bool__(self):
        return False
    
@register.simple_tag(name="page_params", takes_context=True)
def do_page_params(context, page_param: str, page_index: int):
    request = context["request"]
    query = request.GET.copy()
    query[page_param] = page_index
    return query.urlencode()

@register.simple_tag(name="get_date")
def do_date(obj, default=_impossible, **formats):

    for field, format in formats.items():
        if isinstance(obj, dict):
            value = obj.get(field, default)
        else:
            value = getattr(obj, field, default)

        if value is not _impossible:
            break

    if value is _impossible and default is _impossible:
        raise RuntimeError("No date found")
    
    if value is _impossible:
        return default
    
    if not isinstance(value, (datetime.date, datetime.datetime, str)):
        return value

    return date_filter(value, format)

@register.simple_tag(name="format_date")
def do_format_date(year = None, month = None, day = None, hour = None, minute = None, second = None, absolute = None, period: Union[Literal['hour'], Literal['date'], Literal['month'], Literal['year']] = "hour"):
    if year is None and month is None and day is None and absolute is None:
        raise RuntimeError("No date found")
    
    if not absolute:
        absolute = timezone.now() 
    
    if year is None:
        year = absolute.year

    if month is None:
        month = absolute.month

    if day is None:
        day = absolute.day

    if hour is None:
        hour = getattr(absolute, "hour", 0)

    if minute is None:
        minute = getattr(absolute, "minute", 0)

    if second is None:
        second = getattr(absolute, "second", 0)

    match period:
        case "hour":
            value = datetime.datetime(year, month, day, hour, minute, second)
            return date_filter(value, "j F Y H:i")
        case "date":
            value = datetime.date(year, month, day)
            return date_filter(value, "j F Y")
        case "month":
            value = datetime.date(year, month, day)
            return date_filter(value, "F Y")
        case "year":
            value = datetime.date(year, month, day)
            return date_filter(value, "Y")
        case _:
            return absolute




