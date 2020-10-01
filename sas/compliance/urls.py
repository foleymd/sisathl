from django.conf.urls import url
from django.views.generic import TemplateView

from sisathl.sas.compliance.views import *

urlpatterns = [
    url(r'^student/$', 'sisathl.sas.compliance.views.student', name='student'),
    url(r'^admin/$', 'sisathl.sas.compliance.views.admin', name='admin'),
    url(r'^create_panel/$', 'sisathl.sas.compliance.views.create_panel', name='create_panel'),
    url(r'^error/$', TemplateView.as_view(template_name="compliance_error.html"), name='compliance_error'),
]
