from django.urls import path
from . import views

urlpatterns = [
    path('', views.manager, name='manager_login'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # 공공시설추가페이지
    path('facility_add/', views.facility, name='facility_add'),
    
    path('sport_type/', views.sport_type, name='sport_type'),
    
    # 종목 관리
    path("add_sport/", views.add_sport, name="add_sport"),
    path("save_selected_sports/", views.save_selected_sports, name="save_selected_sports"),
    path('sport_delete/', views.sport_delete, name='sport_delete'),

    # 시설등록
    path("facility_register/", views.facility_register, name="facility_register"),
    
    # 시설관리
    path('facility_list/', views.facility_list, name='facility_list'),
    path('facility/<id>/', views.facility_detail, name='facility_detail'),
    path('facility/<id>/modify/', views.facility_modify, name='facility_modify'),
    path('delete/', views.facility_delete, name='facility_delete'),
    path('reservations/', views.reservation_list_manager, name='reservation_list_manager'),
    path('facility_inspection_stats/', views.facility_inspection_stats, name='facility_inspection_stats'),
    path('facility_inspection_stats/yearly/', views.facility_inspection_yearly_detail, name='facility_inspection_yearly_detail'),
    path('facility_inspection_stats/grade/', views.facility_inspection_grade_detail, name='facility_inspection_grade_detail'),


    path('post_manager/', views.post_manager, name='post_manager'),

    # 모집글관리
    path('recruitment_manager/', views.recruitment_manager, name='recruitment_manager'),
    path('recruitment_manager/detail/<int:id>/', views.recruitment_detail, name='recruitment_detail'),
    
    # 게시판 관리
    path('event_manager/', views.event_manager, name='event_manager'),
    path('board_manager/', views.board_manager, name='board_manager'),
    path('event_form/', views.event_form, name='event_form'),
    path('board_form/', views.board_form, name='board_form'),
    path('event_edit/<int:article_id>/', views.event_edit, name='event_edit'),
    path('board_edit/<int:article_id>/', views.board_edit, name='board_edit'),
    path('detail/<int:article_id>/', views.manager_detail, name='manager_detail'),


    # 배너 페이지
    path('banner/', views.banner_manager, name='banner_manager'),
    path('banner_form/', views.banner_form, name='banner_form'),
    path("banner_edit/<int:img_id>/", views.banner_edit, name="banner_edit"),
    path("banner_delete/", views.banner_delete, name="banner_delete"),
    path("banner_detail/<int:img_id>/", views.banner_detail, name="banner_detail"),
    path("banner_download/<int:img_id>/", views.banner_download, name="banner_download"),


    # 관리자 전용 상세 페이지
    path('post/<int:article_id>/', views.manager_post_detail, name='manager_post_detail'),
    path('notice/<int:article_id>/', views.manager_notice_detail, name='manager_notice_detail'),
    path('event/<int:article_id>/', views.manager_event_detail, name='manager_event_detail'),

    # 삭제 API
    path('api/articles/delete/', views.delete_articles, name='delete_articles'),
    path('api/communities/delete/', views.delete_communities, name='delete_communities'),
    
    # 예약 취소 API
    path('api/reservations/cancel-timeslot/<str:reservation_num>/', views.manager_cancel_timeslot, name='manager_cancel_timeslot'),
]