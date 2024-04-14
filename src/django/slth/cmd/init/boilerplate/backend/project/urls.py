from django.urls import path, include
from slth import urls
from slth.views import dispatcher

urlpatterns = [
    path('api/', include(urls)),
    path('', dispatcher)
]
