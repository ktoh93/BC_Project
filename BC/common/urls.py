from django.urls import path
from . import views


urlpatterns = [
    path('login/', views.login, name='login'),
    path('signup/', views.signup, name='signup'),
    path('findID/', views.find_id, name='findID'),
    path('findPW/', views.find_pw, name='findPW'),
]