import random
from django.db import transaction
from django.utils import timezone
from payment.models import PaymentLog

def approve_mock_payment(payment):

    with transaction.atomic():
        order = payment.order
        reservation = order.reservation

        success = random.choice([True, True, False])

        if success:
            payment.approve()
            order.status = order.Status.PAID
            order.save(update_fields=["status"])

            reservation.expire_yn = 0
            reservation.save(update_fields=["expire_yn"])

            PaymentLog.objects.create(
                payment=payment,
                event_type="APPROVE",
                message="Mock 결제 성공"
            )
        else:
            payment.fail("Mock 결제 실패")
            order.status = order.Status.FAILED
            order.save(update_fields=["status"])

            PaymentLog.objects.create(
                payment=payment,
                event_type="FAIL",
                message="Mock 결제 실패"
            )

        return success