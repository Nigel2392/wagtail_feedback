from django.templatetags.static import static
from django.utils.html import format_html

from wagtail import hooks

# from .templatetags.feedback import FEEDBACK_CSS
from .urls import admin_urlpatterns

@hooks.register("register_admin_urls")
def register_admin_urls():
    return admin_urlpatterns

# @hooks.register("insert_global_admin_css")
# def global_admin_css():
#     return format_html(
#         '<link rel="stylesheet" href="{}">',
#         static(FEEDBACK_CSS)
#     )
