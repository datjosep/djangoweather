from django.conf.urls import url
from django.contrib import admin
from mysite.asgard import views

urlpatterns = [
    url('admin/', admin.site.urls),
    url(r'^$', views.DataHandling, name='home'),
    url(r'^DataHandling/$', views.DataHandling, name='nexrad'),
    url(r'^signup/$', views.signup, name='signup'),
]
