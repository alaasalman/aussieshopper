from django.conf.urls import url, include
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^api/',
        include('api.urls', namespace='api')),
    url(r'^',
        include('web.urls', namespace='web'))
]

urlpatterns += staticfiles_urlpatterns()
