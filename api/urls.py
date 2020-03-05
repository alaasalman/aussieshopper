from django.conf.urls import url, include

from rest_framework import routers

from api import views

app_name = 'api'

router = routers.SimpleRouter()
router.register(r'stats', views.StatsViewSet)

urlpatterns = [
    url(r'bot/handle/',
        views.HandleChatMessage.as_view(),
        name='api-handle-message'),
    url(r'^', include(router.urls))
]
