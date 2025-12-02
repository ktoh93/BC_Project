from django.urls import path
from . import views

app_name = 'member'

urlpatterns = [
    path('info/', views.info, name='info'),
    path('edit/', views.edit, name='edit'),
    path('password/', views.edit_password, name='password'),
    path('myreservation/', views.myreservation, name='myreservation'),
    path('myrecruitment/', views.myrecruitment, name='myrecruitment'),
    path('myarticle/', views.myarticle, name='myarticle'),
    path('myjoin/', views.myjoin, name='myjoin'),
    # 삭제 API
    path('api/article/delete/', views.delete_my_article, name='delete_my_article'),
    path('api/community/delete/', views.delete_my_community, name='delete_my_community'),
]