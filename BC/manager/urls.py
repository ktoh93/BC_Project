from django.urls import path
from . import views

urlpatterns = [
    path('', views.manager, name='manager_login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('facility_add/', views.facility, name='facility_add'),
    
    path('sport_type/', views.sport_type, name='sport_type'),
    
    # 종목 관리
    path("add_sport/", views.add_sport, name="add_sport"),
    path("save_selected_sports/", views.save_selected_sports, name="save_selected_sports"),
    path('sport_delete/', views.sport_delete, name='sport_delete'),

    path('facility_list/', views.facility_list, name='facility_list'),
    path('recruitment_manager/', views.recruitment_manager, name='recruitment_manager'),
    path('event_manager/', views.event_manager, name='event_manager'),
    path('board_manager/', views.board_manager, name='board_manager'),
    path('post_manager/', views.post_manager, name='post_manager'),
    path('banner/', views.banner_manager, name='banner_manager'),
    path('event_form/', views.event_form, name='event_form'),
    path('board_form/', views.board_form, name='board_form'),
    # 관리자 전용 상세 페이지
    path('post/<int:article_id>/', views.manager_post_detail, name='manager_post_detail'),
    path('notice/<int:article_id>/', views.manager_notice_detail, name='manager_notice_detail'),
    path('event/<int:article_id>/', views.manager_event_detail, name='manager_event_detail'),
    # 삭제 API
    path('api/articles/delete/', views.delete_articles, name='delete_articles'),
    path('api/communities/delete/', views.delete_communities, name='delete_communities'),
]