
from django.conf.urls import include, url
from django.contrib import admin
from rest_framework import routers

from . import views


router = routers.DefaultRouter()
router.register(r'df-users', views.DFUserViewSet, base_name='df-users')
router.register(r'users', views.UserViewSet,)
router.register(r'notes', views.NoteViewSet,)


urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^', include(router.urls)),
]
