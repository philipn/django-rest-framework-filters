
from django.conf.urls import include, url
from rest_framework import routers

from . import views

router = routers.DefaultRouter()
router.register(r'df-notes', views.DFNoteViewSet, basename='df-notes')
router.register(r'drf-notes', views.DRFFNoteViewSet, basename='drf-notes')


urlpatterns = [
    url(r'^', include(router.urls)),
]
