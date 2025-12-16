# manager/views/payment_views.py
from django.shortcuts import render, get_object_or_404, redirect
from payment.models import PaymentOrder, Payment, PaymentLog


def manager_payment_list(request):
    orders = (
        PaymentOrder.objects
        .select_related("member")
        .order_by("-reg_date")
    )

    return render(request, "manager/payment_list.html", {
        "orders": orders
    })


def manager_payment_detail(request, order_no):
    order = get_object_or_404(PaymentOrder, order_no=order_no)
    payments = order.payments.all().order_by("-requested_at")

    logs = PaymentLog.objects.filter(
        payment__order=order
    ).select_related("payment").order_by("-reg_date")

    # 상태 수동 변경
    if request.method == "POST":
        new_status = request.POST.get("status")
        if new_status is not None:
            order.status = int(new_status)
            order.save(update_fields=["status"])
            return redirect("manager_payment_detail", order_no=order.order_no)

    return render(request, "manager/payment_detail.html", {
        "order": order,
        "payments": payments,
        "logs": logs,
        "status_choices": PaymentOrder.Status.choices
    })
