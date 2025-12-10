from django.urls import path
from . import views

app_name = 'manager'

urlpatterns = [
    path('', views.manager, name='manager_login'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # 공공시설추가페이지
    path('facility_add/', views.facility, name='facility_add'),
    
    
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


    # 모집글관리
    path('recruitment_manager/', views.recruitment_manager, name='recruitment_manager'),
    path('recruitment_manager/detail/<int:id>/', views.recruitment_detail, name='recruitment_detail'),
    

    # 게시판 관리
    path('board_list/<int:id>/',views.board_list, name='board_list'), # 목록
    path('board_write/<int:id>/',views.board_write, name='board_write'), # 작성
    path('board_write/<int:id>/<int:pk>/',views.board_write, name='board_edit'), # 수정
    path('board_detail/<int:pk>/',views.board_detail, name='board_detail'), # 상세페이지


    # 배너 페이지
    path('banner/', views.banner_manager, name='banner_manager'),
    path('banner_form/', views.banner_form, name='banner_form'),
    path("banner_edit/<int:img_id>/", views.banner_edit, name="banner_edit"),
    path("banner_delete/", views.banner_delete, name="banner_delete"),
    path("banner_detail/<int:img_id>/", views.banner_detail, name="banner_detail"),
    path("banner_download/<int:img_id>/", views.banner_download, name="banner_download"),

    # 삭제 API
    path('articles/delete/', views.delete_articles, name='delete_articles'),
    path('communities/delete/', views.delete_communities, name='delete_communities'),
    # 영구 삭제
    path('articles/harddelete/', views.hard_delete_articles, name='harddelete_articles'),
    path('communities/harddelete/', views.hard_delete_communities, name='harddelete_communities'),
    # 복구
    path('articles/restore/', views.restore_articles, name='restore_articles'),
    path('communities/restore/', views.restore_communities, name='restore_communities'),

    # 첨부파일 다운로드
    path('download/file/<int:file_id>/', views.facility_file_download, name='download'),
    
    path("logout/", views.logout, name="logout"),
    # 예약 취소 API
    # path('api/reservations/cancel-timeslot/<str:reservation_num>/', views.manager_cancel_timeslot, name='manager_cancel_timeslot'),

    # 회원관리
    path('member_list/', views.member_list, name='member_list'),
    path("member/delete/", views.member_delete, name="member_delete"),
    path("member/restore/", views.member_restore, name="member_restore"),
]