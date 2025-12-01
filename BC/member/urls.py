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
    # 삭제 API
    path('api/article/delete/', views.delete_my_article, name='delete_my_article'),
    path('api/community/delete/', views.delete_my_community, name='delete_my_community'),
]