from django.conf.urls import url
from . import views
urlpatterns = [
    url(r'^$', views.index),
    url(r'^q/(?P<key>\w+)/', views.query, name='query'),
]
