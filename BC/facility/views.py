import requests
from django.shortcuts import render
from django.core.paginator import Paginator
import os
#from .models import Facility 

def facility(request):
    DATA_API_KEY = os.getenv("DATA_API_KEY")
    # 시(서울특별시, 경기도)
    cp_nm = request.GET.get('cpNm',"경기도")
    # 구
    cpb_nm = request.GET.get('cpbNm','과천시')
    # 시설이름
    keyword = request.GET.get('keyword','')
    per_page = 10
    page = int(request.GET.get("page", 1))

    # -------------------------
    # ① DB에서 데이터 먼저 가져오기 (우선순위 1)
    # -------------------------
    # qs = Facility.objects.all()

    # if sido:
    #     qs = qs.filter(addr1=sido)
    # if sigungu:
    #     qs = qs.filter(addr2=sigungu)
    # if keyword:
    #     qs = qs.filter(name__icontains=keyword)

    # db_list = list(qs.values(
    #     "id","name", "addr1", "addr2", "addr3"
    # ))
  
    API_URL = "https://apis.data.go.kr/B551014/SRVC_API_FACI_SCHK_RESULT/TODZ_API_FACI_SAFETY"
    params = {
        "serviceKey": DATA_API_KEY,
        "numOfRows": 500,
        "pageNo": 1,
        "faci_gb_nm" : '공공',
        "cp_nm" : cp_nm,
        "cpb_nm" : cpb_nm,
        "resultType": "json"
    }
    if keyword:
        params["facility_nm"] = keyword

    api_list = []
    try:
        res = requests.get(API_URL, params=params)
        data = res.json()

        items = data["response"]["body"]["items"]["item"]

        for item in items:
            api_list.append({
                "id" : item.get('faci_cd'),
                "name": item.get("faci_nm"),
                "address": item.get("faci_addr"),
                "sido": item.get("cp_nm"),
                "sigungu": item.get("cpb_nm"),
                "lat": item.get("faci_lat"),
                "lng": item.get("faci_lot"),
                "phone": item.get("faci_tel_no", ""),
            })

    except Exception as e:
        print('오류')

    #db_ids = {item["id"] for item in db_list}
    # merged = db_list[:] 
    # for api_item in api_list:
    #     if api_item["id"] not in db_ids:  
    #         merged.append(api_item)

    merged = api_list
    # 페이징 처리
    paginator = Paginator(merged, per_page)
    page_obj = paginator.get_page(page)

    # 블록 페이징 처리
    block_size = 10
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
        "merged_count": len(merged),
        "block_range": block_range,
        "block_start": block_start,
        "block_end": block_end,
    }
    print(page_obj)
    return context

def facility_list(request) :
    context = facility(request)
    return render(request, "facility_list.html", context)
