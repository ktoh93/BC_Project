from django.urls import path
from . import views

urlpatterns = [
    path('', views.manager, name='manager_login'),
    path('facility_add/', views.facility, name='facility_add'),
    path('sport_type/', views.sport_type, name ='sport_type')
]