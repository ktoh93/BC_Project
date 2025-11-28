from django.urls import path
from . import views

urlpatterns = [
    path('', views.facility_list, name='list'),
    path('detail/<fk>', views.facility_detail, name='detail')
]