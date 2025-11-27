from django.urls import path
from . import views

urlpatterns = [
    path('', views.recruitment_list, name='recruitment_list'),
    path('write/', views.write, name = 'write')
]