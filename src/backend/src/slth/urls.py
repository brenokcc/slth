from django.conf import settings
from django.urls import path
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('<str:name>/', views.dispatcher),
] + static('/api/media/', document_root=settings.MEDIA_ROOT)
