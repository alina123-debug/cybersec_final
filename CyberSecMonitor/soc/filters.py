import django_filters
from .models import Case, Alert

class CaseFilter(django_filters.FilterSet):
    incident_type = django_filters.CharFilter(field_name="incident_type", lookup_expr="exact")
    severity = django_filters.CharFilter(field_name="severity", lookup_expr="exact")
    status = django_filters.CharFilter(field_name="status", lookup_expr="exact")
    verdict = django_filters.CharFilter(field_name="verdict", lookup_expr="exact")
    today = django_filters.BooleanFilter(method="filter_today")

    def filter_today(self, qs, name, value):
        if not value:
            return qs
        from django.utils import timezone
        start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        return qs.filter(created_at__gte=start)

    class Meta:
        model = Case
        fields = ["incident_type","severity","status","verdict","today"]

class AlertFilter(django_filters.FilterSet):
    incident_type = django_filters.CharFilter(field_name="incident_type", lookup_expr="exact")
    severity = django_filters.CharFilter(field_name="severity", lookup_expr="exact")
    today = django_filters.BooleanFilter(method="filter_today")

    def filter_today(self, qs, name, value):
        if not value:
            return qs
        from django.utils import timezone
        start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        return qs.filter(created_at__gte=start)

    class Meta:
        model = Alert
        fields = ["incident_type","severity","today"]
