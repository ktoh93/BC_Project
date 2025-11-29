from django.urls import path
from . import views


urlpatterns = [
    path('',views.index, name='index'),
    path('login/', views.login, name='login'),
    path('signup/', views.signup, name='signup'),
    path('findID/', views.find_id, name='findID'),
    path('findPW/', views.find_pw, name='findPW'),

    path('check/userid/', views.check_userid, name='check_userid'),
    path('check/nickname/', views.check_nickname, name='check_nickname'),
    path('check/phone/', views.check_phone, name='check_phone'),
]