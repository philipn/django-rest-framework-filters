
from django.conf.urls import include, url
from rest_framework import routers

from . import views

router = routers.DefaultRouter()
router.register(r'df-notes', views.DFNoteViewSet, base_name='df-notes')
router.register(r'drf-notes', views.DRFFNoteViewSet, base_name='drf-notes')


urlpatterns = [
    url(r'^', include(router.urls)),
]
