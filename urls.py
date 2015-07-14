from django.conf.urls import url
from . import views
urlpatterns = [
    url(r'^$', views.index),
    url(r'^hosts/', views.hosts),
    url(r'^q/(?P<query_key>\w+)/', views.query),
]
