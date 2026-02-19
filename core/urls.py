from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('video_feed/<str:section>/', views.video_feed, name='video_feed'),
    path('upload_video/<str:section>/', views.upload_video, name='upload_video'),
    path('switch_live/<str:section>/', views.switch_live, name='switch_live'),
    path('stop_feed/<str:section>/', views.stop_feed, name='stop_feed'),
]

from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

