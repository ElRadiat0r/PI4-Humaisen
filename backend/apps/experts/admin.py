from django.contrib import admin

from .models import ExpertProfile, ExpertSkill, Skill


class ExpertSkillInline(admin.TabularInline):
    model = ExpertSkill
    extra = 0


@admin.register(ExpertProfile)
class ExpertProfileAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "former_profession", "level", "verification_status", "is_active"]
    list_filter = ["verification_status", "level", "is_active"]
    search_fields = ["user__email", "user__first_name", "user__last_name", "former_profession"]
    inlines = [ExpertSkillInline]
    actions = ["mark_verified"]

    @admin.action(description="Marquer comme vérifiés")
    def mark_verified(self, request, queryset):
        for profile in queryset:
            profile.verify(request.user)


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ["name", "category"]
    search_fields = ["name", "category"]
