from django.urls import path
from . import views

urlpatterns = [
    path('', views.manager, name='manager_login'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # 시설추가페이지
    path('facility_add/', views.facility, name='facility_add'),
    
    path('sport_type/', views.sport_type, name='sport_type'),
    
    # 종목 관리
    path("add_sport/", views.add_sport, name="add_sport"),
    path("save_selected_sports/", views.save_selected_sports, name="save_selected_sports"),
    path('sport_delete/', views.sport_delete, name='sport_delete'),

    # 시설등록
    path("facility_register/", views.facility_register, name="facility_register"),
    
    path('facility_list/', views.facility_list, name='facility_list'),
    path('post_manager/', views.post_manager, name='post_manager'),

    # 게시판 관리
    path('recruitment_manager/', views.recruitment_manager, name='recruitment_manager'),
    path('event_manager/', views.event_manager, name='event_manager'),
    path('board_manager/', views.board_manager, name='board_manager'),
    path('event_form/', views.event_form, name='event_form'),
    path('board_form/', views.board_form, name='board_form'),

<<<<<<< HEAD
    # 배너 페이지
    path('banner/', views.banner_manager, name='banner_manager'),
    path('banner_form/', views.banner_form, name='banner_form'),
    path("banner_edit/<int:img_id>/", views.banner_edit, name="banner_edit"),
    path("banner_delete/", views.banner_delete, name="banner_delete"),

=======
>>>>>>> b9c593c5240bd65b5c10ca993bb12d622d157be3
    # 관리자 전용 상세 페이지
    path('post/<int:article_id>/', views.manager_post_detail, name='manager_post_detail'),
    path('notice/<int:article_id>/', views.manager_notice_detail, name='manager_notice_detail'),
    path('event/<int:article_id>/', views.manager_event_detail, name='manager_event_detail'),

    # 삭제 API
    path('api/articles/delete/', views.delete_articles, name='delete_articles'),
    path('api/communities/delete/', views.delete_communities, name='delete_communities'),
]