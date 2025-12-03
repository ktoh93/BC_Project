from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .models import Reservation, TimeSlot
import json, random
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import make_aware
from datetime import datetime
from facility.models import FacilityInfo
from reservation.models import Sports, Reservation
from member.models import Member

# TODO: DB 연결 이후 FacilityInfo 모델에서 시설 정보 조회
# from facility.models import FacilityInfo

def reservation_list(request):
    # 종목불러오기
    sports = Sports.objects.all()
    # 시설불러오기
    facilities = FacilityInfo.objects.all()

    cp_nm = request.GET.get('sido')
    cpb_nm = request.GET.get('sigungu')
    keyword = request.GET.get('keyword')
    sport = request.GET.get('sport')

    if cp_nm:
        facilities = facilities.filter(cp_nm=cp_nm)
    if cpb_nm:
        facilities = facilities.filter(cpb_nm=cpb_nm)
    if keyword:
        facilities = facilities.filter(faci_nm__icontains=keyword)

    if sport:
        sports = sports.fillter(s_name=sport)

    sports_list = []
    for s in sports:
        sports_list.append({
            "sName" : s.s_name
        })

    # 정렬 값 (기본값: 제목순)
    sort = request.GET.get("sort", "title")

    # 정렬 적용 (DB 연결 후 쿼리로 교체)
    if sort == "title":
        facilities = facilities.order_by('faci_nm')
    elif sort == "views":
        facilities = facilities.order_by('-view_cnt')
    elif sort == "distance":
        facilities = facilities.order_by('distance')
    elif sort == "rating":
        facilities = facilities.order_by('-rating')

    facility_list = []  # 빈 리스트 (DB 연결 후 교체)
    
    


    for f in facilities:
        facility_list.append({
            "id": f.facility_id,
            "name": f.faci_nm or "",
            "address": f.address,
            "sido": f.sido or "",
            "sigungu": f.sigugun or "",
            "phone": f.tel or "",
            "homepage": f.homepage or "",
            "viewCnt": f.view_cnt
        })

    # 페이지당 개수
    per_page = int(request.GET.get("per_page", 15))

    # 현재 페이지
    page = int(request.GET.get("page", 1))

    # 페이징 처리
    paginator = Paginator(facility_list, per_page)
    page_obj = paginator.get_page(page)

    # 블록 페이징 처리
    block_size = 5
    current_block = (page - 1) // block_size
    block_start = current_block * block_size + 1
    block_end = block_start + block_size - 1

    if block_end > paginator.num_pages:
        block_end = paginator.num_pages

    block_range = range(block_start, block_end + 1)

    context = {
        "page_obj": page_obj,
        "paginator": paginator,
        "per_page": per_page,
        "sido" : cp_nm,
        "sigungu" : cpb_nm,
        "page": page,
        "sort": sort,
        "block_range": block_range,
        "block_start": block_start,
        "block_end": block_end,
        "sportsList" : sports_list
    }

    return render(request, "reservation_list.html", context)


def reservation_detail(request, facility_id):
    facility = get_object_or_404(FacilityInfo, facility_id=facility_id)

    # facility_id는 UUID 문자열이므로 Reservation.facility와 문자열 비교
    reservations = Reservation.objects.filter(
        facility=facility_id,
        delete_yn=0
    ).values("reservation_date", "hour")

    reserved_list = []
    for r in reservations:
        date_str = r["reservation_date"].strftime("%Y-%m-%d")

        hour_data = r["hour"]
        if isinstance(hour_data, str):
            hour_data = json.loads(hour_data)

        reserved_list.append({
            "date": date_str,
            "start": hour_data["start"],
            "end": hour_data["end"]
        })

    return render(request, "reservation_detail.html", {
        "facility": facility,
        "reservation_time_json": json.dumps(facility.reservation_time),
        "reserved_json": json.dumps(reserved_list)
    })

@csrf_exempt
def reservation_save(request):
    if request.method != "POST":
        return JsonResponse({"result": "error", "msg": "잘못된 요청"})

    data = json.loads(request.body)

    date = data.get("date")
    start = data.get("start")
    end = data.get("end")
    facility_id = data.get("facility_id")

    if not (date and start and end and facility_id):
        return JsonResponse({"result": "error", "msg": "필수 데이터 누락"})

    reservation_num = str(random.randint(10000000, 99999999))

    # ★★★★★ make_aware 삭제 — MySQL + USE_TZ=False 환경은 naive datetime만 허용 ★★★★★
    reservation_datetime = datetime.strptime(f"{date} {start}", "%Y-%m-%d %H:%M")

    # 중복 예약 체크
    exists = Reservation.objects.filter(
        reservation_date=reservation_datetime,
        delete_yn=0,
        facility=facility_id
    ).exists()

    if exists:
        return JsonResponse({"result": "error", "msg": "이미 예약된 시간입니다."})

    r = Reservation.objects.create(
        reservation_num=reservation_num,
        reservation_date=reservation_datetime,
        hour={"start": start, "end": end},
        facility=facility_id,
        member = Member.objects.get(user_id=request.session["user_id"])
    )

    return JsonResponse({
        "result": "ok",
        "reservation_id": r.reservation_id
    })