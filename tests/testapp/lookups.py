from django.db.models import Transform


# This is a copy of the `Unaccent` transform from `django.contrib.postgres`.
# This is necessary as the postgres app requires psycopg2 to be installed.
class Unaccent(Transform):
    bilateral = True
    lookup_name = 'unaccent'
    function = 'UNACCENT'
