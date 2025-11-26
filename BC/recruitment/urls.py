from django.urls import path
from . import views

urlpatterns = [
    path('', views.list, name='list'),
    path('write/', views.write, name = 'write')
]