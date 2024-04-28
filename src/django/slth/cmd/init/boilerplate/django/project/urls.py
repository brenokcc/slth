from django.urls import path, re_path, include
from slth import urls
from slth.views import dispatcher, index, service_worker

urlpatterns = [
    path('', index),
    path('service_worker.js', service_worker),
    re_path(r'^app/(?P<path>.*)/$', index),
    path('api/', include(urls)),
    path('', dispatcher)
]