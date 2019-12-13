
from django.conf.urls import include, url
from rest_framework import routers

from . import views

router = routers.DefaultRouter()
router.register(r'df-users', views.DFUserViewSet, basename='df-users')
router.register(r'ff-users', views.FilterFieldsUserViewSet, basename='ff-users')
router.register(r'ffcomplex-users', views.ComplexFilterFieldsUserViewSet, basename='ffcomplex-users')
router.register(r'ffjsoncomplex-users', views.ComplexJSONFilterFieldsUserViewSet, basename='ffcomplex-users')
router.register(r'users', views.UserViewSet,)
router.register(r'notes', views.NoteViewSet,)


urlpatterns = [
    url(r'^', include(router.urls)),
]
