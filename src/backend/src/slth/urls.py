from django.conf import settings
from django.urls import path, re_path
from django.conf.urls.static import static
from . import views

urlpatterns = [
    re_path(r'^(?P<path>.*)/$', views.dispatcher),
] + static('/api/media/', document_root=settings.MEDIA_ROOT)
