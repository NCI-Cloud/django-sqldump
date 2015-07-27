from django.conf.urls import url
from . import views
urlpatterns = [
    url(r'^$', views.index),
    url(r'^q/(?P<key>\w+)/(?P<uuid>[-_a-zA-Z0-9]*)/', views.query),
    url(r'^q/(?P<key>\w+)/', views.query, name='query'),
]
