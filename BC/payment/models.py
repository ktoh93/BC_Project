# payment/models.py
from django.db import models
from django.utils import timezone
import uuid

from reservation.models import Reservation
from member.models import Member


class PaymentOrder(models.Model):
    """
    Reservation 1건에 대해 생성되는 결제 '요청' 단위
    - 결제 흐름의 기준 엔티티
    """

    class Status(models.IntegerChoices):
        CREATED = 0, "CREATED"     # 결제 생성
        PAID = 1, "PAID"           # 결제 완료
        CANCELED = 2, "CANCELED"   # 결제 취소
        FAILED = 3, "FAILED"       # 결제 실패
        EXPIRED = 4, "EXPIRED"     # 결제 유효시간 만료

    order_id = models.BigAutoField(primary_key=True)

    order_no = models.CharField(
        max_length=50,
        unique=True,
        default=uuid.uuid4,
        editable=False
    )

    reservation = models.OneToOneField(
        Reservation,
        on_delete=models.CASCADE,
        related_name="payment_order"
    )

    member = models.ForeignKey(
        Member,
        on_delete=models.DO_NOTHING,
        related_name="payment_orders"
    )

    # 예약 시점의 결제 금액 스냅샷
    amount = models.IntegerField(default=0)
    currency = models.CharField(max_length=10, default="KRW")

    status = models.IntegerField(
        choices=Status.choices,
        default=Status.CREATED
    )

    expired_at = models.DateTimeField(null=True, blank=True)
    reg_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "payment_order"
        indexes = [
            models.Index(fields=["order_no"]),
            models.Index(fields=["status", "reg_date"]),
        ]

    def __str__(self):
        return f"{self.order_no} ({self.get_status_display()})"


class Payment(models.Model):
    """
    결제 시도 단위
    - 하나의 PaymentOrder에 대해 여러 번 생성 가능
    """

    class Status(models.IntegerChoices):
        READY = 0, "READY"
        DONE = 1, "DONE"
        FAILED = 2, "FAILED"
        CANCELED = 3, "CANCELED"

    class Provider(models.TextChoices):
        MOCK = "MOCK", "Mock"
        TOSS = "TOSS", "Toss"
        KAKAO = "KAKAO", "Kakao"

    class Method(models.TextChoices):
        MOCK = "MOCK", "Mock"
        CARD = "CARD", "Card"
        TRANSFER = "TRANSFER", "Transfer"

    payment_id = models.BigAutoField(primary_key=True)

    order = models.ForeignKey(
        PaymentOrder,
        on_delete=models.CASCADE,
        related_name="payments"
    )

    payment_key = models.CharField(
        max_length=100,
        unique=True,
        default=uuid.uuid4,
        editable=False
    )

    provider = models.CharField(
        max_length=20,
        choices=Provider.choices,
        default=Provider.MOCK
    )

    method = models.CharField(
        max_length=20,
        choices=Method.choices,
        default=Method.MOCK
    )

    status = models.IntegerField(
        choices=Status.choices,
        default=Status.READY
    )

    requested_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    fail_reason = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = "payment"
        indexes = [
            models.Index(fields=["payment_key"]),
            models.Index(fields=["status", "requested_at"]),
        ]

    def approve(self):
        self.status = self.Status.DONE
        self.approved_at = timezone.now()
        self.save(update_fields=["status", "approved_at"])

    def fail(self, reason=None):
        self.status = self.Status.FAILED
        self.fail_reason = reason
        self.save(update_fields=["status", "fail_reason"])

    def cancel(self, reason=None):
        self.status = self.Status.CANCELED
        self.fail_reason = reason
        self.save(update_fields=["status", "fail_reason"])

    def __str__(self):
        return f"{self.payment_key} ({self.get_status_display()})"
    

class PaymentMethod(models.Model):

    method_id = models.BigAutoField(primary_key=True)

    payment = models.OneToOneField(
        Payment,
        on_delete=models.CASCADE,
        related_name="payment_method"
    )

    method_type = models.CharField(max_length=30, default="MOCK_CARD")
    display_name = models.CharField(max_length=50, default="모의 카드")
    masked_value = models.CharField(max_length=30, default="****-****-****-1234")

    class Meta:
        db_table = "payment_method"

    def __str__(self):
        return self.display_name

class PaymentLog(models.Model):

    log_id = models.BigAutoField(primary_key=True)

    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name="logs"
    )

    event_type = models.CharField(max_length=20)
    message = models.TextField(null=True, blank=True)
    reg_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "payment_log"
        indexes = [
            models.Index(fields=["event_type", "reg_date"]),
        ]

    def __str__(self):
        return f"{self.event_type} - {self.payment.payment_key}"

