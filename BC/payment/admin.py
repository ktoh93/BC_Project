from django.contrib import admin
from .models import PaymentOrder, Payment, PaymentLog

@admin.register(PaymentOrder)
class PaymentOrderAdmin(admin.ModelAdmin):
    list_display = ("order_no", "member", "amount", "status", "reg_date")
    list_filter = ("status",)
    search_fields = ("order_no",)

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("payment_key", "order", "status", "requested_at")
    list_filter = ("status",)

@admin.register(PaymentLog)
class PaymentLogAdmin(admin.ModelAdmin):
    list_display = ("payment", "event_type", "reg_date")
