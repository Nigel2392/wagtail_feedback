from django.urls import path

from . import views

app_name = "feedback"

urlpatterns = [
    path("feedback/<int:page_pk>/", views.feedback, name="feedback"),
    path("feedback/<int:page_pk>/<int:pk>/", views.feedback_with_message, name="feedback_with_message"),
]

admin_urlpatterns = [
    path("feedback/api/list/", views.FeedbackListViewAPI.as_view(), name="feedback_api"),
    path("feedback/api/chart/", views.FeedbackAggregateViewAPI.as_view(), name="feedback_api_chart"),
    path("feedback/api/<int:pk>/view/", views.FeedbackDetailViewAPI.as_view(), name="feedback_api_detail"),
    path("feedback/api/<int:pk>/delete/", views.FeedbackDeleteViewAPI.as_view(), name="feedback_api_delete"),
    path("feedback/api/<int:page_pk>/list/", views.FeedbackListViewAPI.as_view(), name="page_feedback_api"),
    path("feedback/api/<int:page_pk>/chart/", views.FeedbackAggregateViewAPI.as_view(), name="page_feedback_api_chart"),
]

