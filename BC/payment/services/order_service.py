from django.utils import timezone
from datetime import timedelta
from payment.models import PaymentOrder

def create_payment_order(reservation):
    order = PaymentOrder.objects.create(
        reservation=reservation,
        member=reservation.member,
        amount=reservation.payment,
        expired_at=timezone.now() + timedelta(minutes=15)
    )
    return order
