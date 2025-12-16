from django.http import HttpResponse
from django.http import JsonResponse
from payment.models import Payment
from payment.services.mock_pg import approve_mock_payment
from django.shortcuts import render, get_object_or_404, redirect
from reservation.models import Reservation
from payment.services.order_service import create_payment_order
from payment.services.payment_service import create_payment
from payment.models import PaymentOrder
from payment.services.mock_pg import approve_mock_payment
from payment.models import Payment
from django.views.decorators.csrf import csrf_exempt
from reservation.models import TimeSlot
from common.utils import check_login
import json, random
from facility.models import FacilityInfo
from member.models import Member
from datetime import datetime

def approve_payment_view(request, payment_id):
    payment = Payment.objects.get(pk=payment_id)

    success = approve_mock_payment(payment)

    return JsonResponse({
        "result": "SUCCESS" if success else "FAIL"
    })


def create_payment_order_view(request, reservation_id):
    reservation = get_object_or_404(Reservation, pk=reservation_id)

    order = create_payment_order(reservation)

    return JsonResponse({
        "order_no": order.order_no,
        "amount": order.amount
    })


def create_payment_view(request, order_no):
    order = get_object_or_404(PaymentOrder, order_no=order_no)
    payment = create_payment(order)

    return JsonResponse({
        "payment_id": payment.payment_id
    })


def approve_payment_view(request, payment_id):
    payment = get_object_or_404(Payment, pk=payment_id)

    success = approve_mock_payment(payment)

    return JsonResponse({
        "result": "SUCCESS" if success else "FAIL"
    })

from django.utils import timezone

def payment_page_view(request, order_no):
    order = get_object_or_404(PaymentOrder, order_no=order_no)

    if order.expired_at and order.expired_at < timezone.now():
        order.status = order.Status.EXPIRED
        order.save(update_fields=["status"])

        return render(request, "payment/payment_expired.html")

    return render(request, "payment/payment_page.html", {
        "order_no": order.order_no,
        "amount": order.amount
    })


from django.shortcuts import render
from payment.models import PaymentOrder

def manager_payment_list(request):
    payments = PaymentOrder.objects.select_related("member").order_by("-reg_date")

    return render(request, "manager/payment_list.html", {
        "payments": payments
    })

@csrf_exempt
def payment_confirm_view(request):
    res = check_login(request)
    if res:
        return res

    data = json.loads(request.body)

    payload = data.get("payload")
    if not payload:
        return JsonResponse({"result": "error", "msg": "payload 없음"})

    member = Member.objects.get(user_id=request.session["user_id"])
    facility = FacilityInfo.objects.get(facility_id=payload["facility_id"])
    res_date = datetime.strptime(payload["date"], "%Y-%m-%d").date()

    price_per_slot = int(
        facility.reservation_time[
            res_date.strftime("%A").lower()
        ].get("payment", 0)
    )

    total_payment = price_per_slot * len(payload["slots"])

    # ✅ 여기서 예약 생성
    reservation = Reservation.objects.create(
        reservation_num = str(random.randint(10000000, 99999999)),
        member=member,
        payment=total_payment
    )

    for slot in payload["slots"]:
        TimeSlot.objects.create(
            facility_id=facility,
            date=res_date,
            start_time=slot["start"],
            end_time=slot["end"],
            reservation_id=reservation
        )

    return JsonResponse({
        "result": "ok",
        "reservation_id": reservation.reservation_id
    })


def payment_redirect_complete(request):
    """
    이니시스 결제 완료 후 무조건 이 URL로 돌아옴
    """

    imp_uid = request.GET.get("imp_uid")
    merchant_uid = request.GET.get("merchant_uid")

    if not imp_uid or not merchant_uid:
        return HttpResponse("결제 정보 누락", status=400)

    payload = request.session.get(f"pay:{merchant_uid}")
    if not payload:
        return HttpResponse("세션 만료", status=400)

    # TODO: (선택) imp_uid로 실제 결제 검증 API 호출 가능

    # ✅ 여기서 예약 확정
    from reservation.models import Reservation, TimeSlot
    from member.models import Member

    member = Member.objects.get(user_id=request.session["user_id"])

    reservation = Reservation.objects.create(
        reservation_num=merchant_uid,
        member=member,
        payment=payload["amount"]
    )

    for slot in payload["slots"]:
        TimeSlot.objects.create(
            facility_id_id=payload["facility_id"],
            date=payload["date"],
            start_time=slot["start"],
            end_time=slot["end"],
            reservation_id=reservation
        )

    del request.session[f"pay:{merchant_uid}"]

    return redirect(f"/reservation/complete/{reservation.reservation_id}/")