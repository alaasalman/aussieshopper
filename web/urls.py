from django.conf.urls import url

from web import views

app_name = 'web'

urlpatterns = [
    url(r'statistics/$',
        views.statistics,
        name='web-statistics'),

    url(r'',
        views.IndexView.as_view(),
        name='web-index')
]
