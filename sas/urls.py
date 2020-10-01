from django.conf.urls import include, url

urlpatterns = [
    url(r'^apps/sisathl/sas/$', 'sisathl.sas.portal.views.portal', name='portal'),
    url(r'^apps/sisathl/sas/sp/', include('sisathl.sas.sp.urls')),
    url(r'^apps/sisathl/sas/compliance/', include('sisathl.sas.compliance.urls')),
]
