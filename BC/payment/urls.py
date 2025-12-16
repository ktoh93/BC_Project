from django.urls import path
from . import views

urlpatterns = [
    path("order/<int:reservation_id>/", views.create_payment_order_view, name="create_payment_order"),
    path("try/<str:order_no>/", views.create_payment_view, name="create_payment"),
    path("approve/<int:payment_id>/", views.approve_payment_view, name="approve_payment"),
    path("<str:order_no>/", views.payment_page_view, name="payment_page"),
    path("payments/", views.manager_payment_list, name="manager_payment_list"),
    path("confirm/", views.payment_confirm_view),
    # payment/urls.py
    path("redirect/complete/", views.payment_redirect_complete, name="payment_redirect_complete")

]