from payment.models import Payment, PaymentLog

def create_payment(order):
    payment = Payment.objects.create(order=order)

    PaymentLog.objects.create(
        payment=payment,
        event_type="REQUEST",
        message="결제 시도 생성"
    )

    return payment
