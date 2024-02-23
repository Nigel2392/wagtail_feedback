from django.shortcuts import render, redirect
from django.contrib import messages as django_messages


def redirect_or_respond(request, url, template, context=None, message_type = "success", message = None, *args, **kwargs):
    if context is None:
        context = {}

    if is_htmx_request(request):

        return render(
            request,
            template,
            context=context,
            *args,
            **kwargs,
        )

    if message:
        fn = getattr(django_messages, message_type)
        fn(request, message)

    return redirect(url)


def error(request, message, status=200, key = "error", to: str = None, *args, **kwargs):

    if not is_htmx_request(request):
        django_messages.error(request, message)
        if not to:
            to = request.META.get("HTTP_REFERER", "/")
        return redirect(to, *args)

    return render(request, "feedback/panels/partials/error.html", {
        key: message,
        **kwargs,
    }, status=status)


def is_htmx_request(request):
    if hasattr(request, "is_htmx"):
        return bool(request.is_htmx)
    
    if hasattr(request, "htmx"):
        return bool(request.htmx)
    
    return request.headers.get("HX-Request", "false").lower() == "true"

def is_json_request(request):
    if hasattr(request, "is_json"):
        return request.is_json
    
    return request.content_type == "application/json" and request.accepts("application/json")
