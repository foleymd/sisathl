from django.conf.urls import url
# from django.views.generic import TemplateView

from sisathl.sas.sp.views import *


urlpatterns = [
    url(r'^student_details/(?P<major_id>\d+)/$', 'sisathl.sas.sp.views.student_details', name='student_details'),
    url(r'^percentage/(?P<major_id>\d+)/$', 'sisathl.sas.sp.views.percentage_of_degree', name='percentage_of_degree'),
    url(r'^create_forms/$', 'sisathl.sas.sp.views.create_forms', name='create_forms'),
    url(r'^create_forms/(?P<ccyys>\w{5})/$', 'sisathl.sas.sp.views.create_forms', name='create_forms_a'),
    url(r'^inbox/$', 'sisathl.sas.sp.views.inbox', name='inbox'),
    url(r'^index/$', 'sisathl.sas.sp.views.index', name='index'),
    url(r'^user_admin/$','sisathl.sas.sp.views.user_admin', name='user_admin'),
    url(r'^spd_instructions/$', TemplateView.as_view(template_name="spd_instructions.html"), name='spd_instructions'),
    url(r'^comments/$', 'sisathl.sas.sp.views.comments', name='comments'),
    url(r'^comment_required/(?P<form_type_name>\w+)/(?P<form_id>\d+)/(?P<action>\w{2})/$', 'sisathl.sas.sp.views.comment_required', name='comment_required'),
    url(r'^log/$', 'sisathl.sas.sp.views.log', name='log'),
    url(r'^log_record/$', 'sisathl.sas.sp.views.log_record', name='log_record'),
    url(r'^sp_error/$', ErrorView.as_view(), name='sp_error'),
    url(r'^contact/$', ContactView.as_view(), name="contact"),
    url(r'^custom_forms/$', 'sisathl.sas.sp.views.custom_form', name="custom_form"),
    url(r'^date_admin/$', 'sisathl.sas.sp.views.ccyys_admin', name="ccyys_admin"),
    url(r'^date_admin/(?P<ccyys_to_edit>\d{5})/$', 'sisathl.sas.sp.views.ccyys_admin', name="ccyys_admin_by_ccyys"),
    url(r'^activate/(?P<form_type_name>\w+)/(?P<form_id>\d+)/(?P<action>\w{1})/$', 'sisathl.sas.sp.views.activate', name="activate"),
    url(r'$', 'sisathl.sas.sp.views.index', name='index'),
]
