from django.urls import path, re_path, include
from slth import urls
from slth.views import dispatcher, index
from django.conf.urls.static import static

urlpatterns = [
    path('', index),
    re_path(r'^app/(?P<path>.*)/$', index),
    path('api/', include(urls)),
    path('', dispatcher)
]