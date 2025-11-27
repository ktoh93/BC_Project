from django.urls import path
from . import views

urlpatterns = [
    path('', views.manager, name='manager_login'),
    path('facility/', views.facility, name='facility')
]