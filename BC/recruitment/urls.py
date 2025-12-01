from django.urls import path
from . import views

urlpatterns = [
    path('', views.recruitment_list, name='recruitment_list'),
    path('write/', views.write, name = 'recruitment_write'),
    path('detail/<int:pk>/', views.detail, name = 'recruitment_detail'),
    path('update/<int:pk>/', views.update, name = 'recruitment_update'),
    path('delete/<int:pk>/', views.delete, name = 'recruitment_delete'),
    path('join/<int:pk>/', views.join, name = 'recruitment_join'),
    
    path(
        "recruitment/<int:pk>/join/<int:join_id>/status/",
        views.update_join_status,
        name="recruitment_update_join_status",
    ),
]