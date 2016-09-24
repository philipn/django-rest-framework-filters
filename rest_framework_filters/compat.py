
import django


def set_many(instance, field, value):
    if django.VERSION < (1, 10):
        setattr(instance, field, value)
    else:
        field = getattr(instance, field)
        field.set(value)
