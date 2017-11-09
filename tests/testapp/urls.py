
from django.conf.urls import include, url
from rest_framework import routers

from . import views


router = routers.DefaultRouter()
router.register(r'df-users', views.DFUserViewSet, base_name='df-users')
router.register(r'ff-users', views.FilterFieldsUserViewSet, base_name='ff-users')
router.register(r'users', views.UserViewSet,)
router.register(r'notes', views.NoteViewSet,)
router.register(r'applications', views.ApplicationViewSet,)
router.register(r'releases', views.ReleaseViewSet,)


urlpatterns = [
    url(r'^', include(router.urls)),
]
