
from django.conf.urls import include, url
from rest_framework import routers

from . import views

router = routers.DefaultRouter()
router.register(r'df-users', views.DFUserViewSet, base_name='df-users')
router.register(r'ff-users', views.FilterFieldsUserViewSet, base_name='ff-users')
router.register(r'ffcomplex-users', views.ComplexFilterFieldsUserViewSet, base_name='ffcomplex-users')
router.register(r'users', views.UserViewSet,)
router.register(r'notes', views.NoteViewSet,)


urlpatterns = [
    url(r'^', include(router.urls)),
]
