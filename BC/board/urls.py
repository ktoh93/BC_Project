from django.urls import path
from . import views

urlpatterns = [
    path('', views.notice, name='board'),  # 기본 경로는 공지사항으로
    path('notice/', views.notice, name='notice'),
    path('notice/<int:article_id>/', views.notice_detail, name='notice_detail'),
    path('notice/<int:article_id>/comment/', views.notice_comment, name='notice_comment'),
    path('event/', views.event, name='event'),
    path('event/<int:article_id>/', views.event_detail, name='event_detail'),
    path('event/<int:article_id>/comment/', views.event_comment, name='event_comment'),
    path('post/', views.post, name='post'),
    path('post/<int:article_id>/', views.post_detail, name='post_detail'),
    path('post/<int:article_id>/comment/', views.post_comment, name='post_comment'),
    path('post/write/', views.post_write, name='post_write'),
    path('faq/', views.faq, name='faq'),
]