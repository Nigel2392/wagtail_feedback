wagtail_feedback
================

A simple wagtail application for letting users give feedback on your wagtail pages - provides easily readable and accessible aggregates in the page admin via `FeedbackPanel`

Note:

* Your `page.get_context` method must implement *args and **kwargs.

Quick start
-----------

1. Add `wagtail_feedback` and `django_filters` to your INSTALLED_APPS setting like this:

   ```python
   INSTALLED_APPS = [
   	# ...,
   	'feedback',
   	'django_filters',
   ]
   ```
2. include  `feedback.urls` in your URLconf.

   ```python
   urlpatterns = [
       ...
       include('feedback.urls')
   ]
   ```
3. In your template, load the feedback template tag to use the feedback form.

   ```html
   {% load feedback %}

   {# Loads the appropriate CSS styles. `{% static 'feedback/css/feedback.css'%}` #}
   {% feedback_css %} 

   {# Loads HTMX, if you have HTMX loaded in your template this is not nescessary. `{% static 'feedback/js/feedback.js'%}` #}
   {% feedback_js %}  

   {% feedback page=self %}
   ```
4. **(Optional)** Include the feedback panel in your page definition:

   ```python
   from wagtail.models import Page
   from feedback.panels import FeedbackPanel

   class MyPage(Page):
   	content_panels = Page.content_panels + [
   		FeedbackPanel()
   	]

   ```

## Easily configurable settings:

### **A class for creating custom implementations of a feedback model**

`FEEDBACK_MODEL_NAME` *default: `feedback.Feedback`*

### **A form class for saving custom fields on your own custom feedback model:**

`FEEDBACK_FORM_CLASS` *default: `feedback.forms.FeedbackForm`*

### **Filters for the admin in-panel list-view.**

`FEEDBACK_FILTER_CLASS` *default: `feedback.filters.AbstractFeedbackFilter`*

### **Backends for validating feedback before and after submit**

`FEEDBACK_BACKEND` *default:*

```python
FEEDBACK_BACKEND = getattr(settings, "FEEDBACK_BACKEND", {
    "CLASS": "feedback.backends.SessionBasedFeedbackend",
    "OPTIONS": {
    	# ... Options passed to class
    }

})
```

Other backends include:

* `feedback.backends.SessionBasedFeedbackend`
* `feedback.backends.PageBasedFeedbackend`
* `feedback.backends.Feedbackend` *(base implementation)*

## **Custom page methods for specifying messages/functionality**

Specifies if the user is allowed to leave a message on positive feedback for this page.

`def allow_feedback_message_on_positive(self) -> bool:`

Specifies the title shown above the feedback form.

`def get_feedback_title(self) -> str:`

How you would like to thank your user after submitting the feedback.

`def get_feedback_thanks(self) -> str:`

A simple short description explaining why you are asking for feedback.

`def get_feedback_explainer(self) -> str:`

Text shown when the user hovers over the positive icon.  

`def get_feedback_positive_text(self) -> str:`

Text shown when the user hovers over the negative icon.  

`def get_feedback_negative_text(self) -> str:`

## **Django proxy settings to get IP-adress**

`USE_X_FORWARDED_HOST` *default: `False`*

Used for setting the appropriate IP-adress on the

feedback model / when using the backend.

# Contributors

* [jellelangen](https://github.com/jellelangen)