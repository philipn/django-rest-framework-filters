import django_filters


class RelatedFilter(django_filters.ModelChoiceFilter):
    def __init__(self, filterset, *args, **kwargs):
        # The related filterset
        self.filterset = filterset
        kwargs['queryset'] = self.filterset._meta.model.objects.all()
        super(RelatedFilter, self).__init__(*args, **kwargs)


class AllLookupsFilter(django_filters.Filter):
    pass
