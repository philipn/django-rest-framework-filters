
from django.apps import AppConfig
from django.db.models import CharField, TextField

from .lookups import Unaccent


class TestappConfig(AppConfig):
    name = 'tests.testapp'

    def ready(self):
        CharField.register_lookup(Unaccent)
        TextField.register_lookup(Unaccent)
