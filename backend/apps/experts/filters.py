import django_filters

from .choices import VerificationStatus
from .models import ExpertProfile


class ExpertFilter(django_filters.FilterSet):
    skill = django_filters.NumberFilter(field_name="expert_skills__skill_id", distinct=True)
    skill_name = django_filters.CharFilter(
        field_name="expert_skills__skill__name", lookup_expr="iexact", distinct=True
    )
    min_level = django_filters.NumberFilter(field_name="level", lookup_expr="gte")
    timezone = django_filters.CharFilter(field_name="timezone")
    verified = django_filters.BooleanFilter(method="filter_verified")

    class Meta:
        model = ExpertProfile
        fields = ["level", "verification_status"]

    def filter_verified(self, queryset, name, value):
        if value:
            return queryset.filter(verification_status=VerificationStatus.VERIFIED)
        return queryset.exclude(verification_status=VerificationStatus.VERIFIED)
