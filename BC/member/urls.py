from django.urls import path
from . import views

urlpatterns = [
    path('info/', views.info),
    path('edit/', views.edit),
    path('password/', views.edit_password),
    path('myreservation/', views.myreservation),
    path('myrecruitment/', views.myrecruitment),
    path('myarticle/', views.myarticle),
    path('myjoin/', views.myjoin),
    
]