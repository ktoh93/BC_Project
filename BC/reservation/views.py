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
from .models import TimeSlot


# TODO: DB 연결 이후 FacilityInfo 모델에서 시설 정보 조회
# from facility.models import FacilityInfo

def reservation_list(request):
    # 종목불러오기
    sports = Sports.objects.all()
    # 시설불러오기
    facilities = FacilityInfo.objects.all()

    sido = request.GET.get('sido')
    sigungu = request.GET.get('sigungu')
    keyword = request.GET.get('keyword')
    sport = request.GET.get('sport')

    if sido:
        facilities = facilities.filter(sido=sido)
    if sigungu:
        facilities = facilities.filter(sigugun=sigungu)
    if keyword:
        facilities = facilities.filter(faci_nm__icontains=keyword)
    
    if sport:
        facilities = facilities.filter(faci_nm__icontains=sport)


    
 

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
        "sido" : sido,
        "sigungu" : sigungu,
        "page": page,
        "sort": sort,
        "block_range": block_range,
        "block_start": block_start,
        "block_end": block_end,
        "sportsList" : sports_list,
        "sport" : sport
    }

    return render(request, "reservation_list.html", context)


def reservation_detail(request, facility_id):  # facility_id=문자열 코드!
    facility = get_object_or_404(FacilityInfo, facility_id=facility_id)

    time_slots = TimeSlot.objects.filter(
        facility_id=facility      # FK 비교는 객체
    ).values("date", "start_time", "end_time")

    reserved_list = []
    for t in time_slots:
        reserved_list.append({
            "date": t["date"].strftime("%Y-%m-%d"),
            "start": t["start_time"],
            "end": t["end_time"]
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
    facility_code = data.get("facility_id")

    if not (date and start and end and facility_code):
        return JsonResponse({"result": "error", "msg": "필수 데이터 누락"})

    # facility_id(문자열 코드)로 시설 조회
    try:
        facility = FacilityInfo.objects.get(facility_id=facility_code)
    except FacilityInfo.DoesNotExist:
        return JsonResponse({"result": "error", "msg": "시설을 찾을 수 없습니다."})

    # 중복 체크
    conflict = TimeSlot.objects.filter(
        facility_id=facility,  # ← 여기 중요!
        date=date,
        start_time=start,
        end_time=end
    ).exists()

    if conflict:
        return JsonResponse({"result": "error", "msg": "이미 예약된 시간입니다."})

    # Reservation 생성
    reservation_num = str(random.randint(10000000, 99999999))
    reservation = Reservation.objects.create(
        reservation_num=reservation_num,
        member=Member.objects.get(user_id=request.session["user_id"])
    )

    # TimeSlot 생성
    time_slot = TimeSlot.objects.create(
        facility_id=facility,  # ← 반드시 facility_id 필드에 넣기
        date=date,
        start_time=start,
        end_time=end,
        reservation_id=reservation
    )

    return JsonResponse({"result": "ok"})
