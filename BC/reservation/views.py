from django.shortcuts import render
from django.core.paginator import Paginator

# TODO: DB 연결 이후 FacilityInfo 모델에서 시설 정보 조회
# from facility.models import FacilityInfo

def reservation_list(request):
    # TODO: DB 연결 이후 FacilityInfo 모델에서 시설 정보 조회
    # facilities = FacilityInfo.objects.all().order_by('-reg_date')
    # 필드 매핑: facility_addr1 -> sido, facility_addr2 -> sigugun, 
    #           facility_name -> faci_nm, facility_num -> faci_cd 등
    facility_list = []  # 빈 리스트 (DB 연결 후 교체)

    # 정렬 값 (기본값: 제목순)
    sort = request.GET.get("sort", "title")

    # 정렬 적용 (DB 연결 후 쿼리로 교체)
    # if sort == "title":
    #     facilities = facilities.order_by('faci_nm')
    # elif sort == "views":
    #     facilities = facilities.order_by('-view_cnt')
    # elif sort == "distance":
    #     facilities = facilities.order_by('distance')
    # elif sort == "rating":
    #     facilities = facilities.order_by('-rating')

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
        "page": page,
        "sort": sort,
        "block_range": block_range,
        "block_start": block_start,
        "block_end": block_end,
    }

    return render(request, "reservation_list.html", context)
