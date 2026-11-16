from rest_framework.routers import SimpleRouter

from .views import ExpertViewSet, SkillViewSet

router = SimpleRouter()
router.register("experts", ExpertViewSet, basename="expert")
router.register("skills", SkillViewSet, basename="skill")

urlpatterns = router.urls
