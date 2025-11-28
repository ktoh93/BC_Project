from django.urls import path
from . import views

urlpatterns = [
    path('', views.manager, name='manager_login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('facility_add/', views.facility, name='facility_add'),
    path('sport_type/', views.sport_type, name='sport_type'),
    path('facility_list/', views.facility_list, name='facility_list'),
    path('recruitment_manager/', views.recruitment_manager, name='recruitment_manager'),
    path('evenet_manager/', views.evenet_manager, name='evenet_manager'),
    path('board_manager/', views.board_manager, name='board_manager'),
]