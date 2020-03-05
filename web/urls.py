from django.conf.urls import url

from web import views

app_name = 'web'

urlpatterns = [
    url(r'',
        views.index,
        name='web-index')
]
