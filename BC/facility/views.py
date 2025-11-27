import os
import requests
from django.shortcuts import render
from django.core.paginator import Paginator


def facility_list(request):
    DATA_API_KEY = os.getenv("DATA_API_KEY")       
    KAKAO_REST_KEY = os.getenv("KAKAO_REST_API_KEY") 
    KAKAO_SCRIPT_KEY = os.getenv("KAKAO_SCRIPT_KEY")  


    cp_nm = request.GET.get('cpNm', "서울특별시")
    cpb_nm = request.GET.get('cpbNm', "강남구")
    keyword = request.GET.get('keyword', '')


    per_page = int(request.GET.get("per_page", 10))
    page = int(request.GET.get("page", 1))

    API_URL = "https://apis.data.go.kr/B551014/SRVC_API_FACI_SCHK_RESULT/TODZ_API_FACI_SAFETY"
    params = {
        "serviceKey": DATA_API_KEY,
        "numOfRows": 500,
        "pageNo": 1,
        "faci_gb_nm": "공공",
        "cp_nm": cp_nm,
        "cpb_nm": cpb_nm,
        "resultType": "json"
    }
    if keyword:
        params["facility_nm"] = keyword

    facilities = []

    try:
        res = requests.get(API_URL, params=params, timeout=5)
        data = res.json()
        items = data["response"]["body"]["items"]["item"]

        for item in items:
            facilities.append({
                "id": item.get("faci_cd", ""),
                "name": item.get("faci_nm", ""),
                "address": item.get("faci_road_addr", ""), 
                "sido": item.get("cp_nm", ""),
                "sigungu": item.get("cpb_nm", ""),
                "phone": item.get("faci_tel_no", ""),
                "lat": None,
                "lng": None,
            })

    except Exception as e:
        print("공공데이터 API 오류:", e)

 
    paginator = Paginator(facilities, per_page)
    page_obj = paginator.get_page(page)


    headers = None
    if KAKAO_REST_KEY:
        headers = {"Authorization": f"KakaoAK {KAKAO_REST_KEY}"}

    for fac in page_obj:
       
        addr_parts = [fac.get("sido") or "", fac.get("sigungu") or "", fac.get("address") or ""]
        full_addr = " ".join(p for p in addr_parts if p).strip()
        fac["full_address"] = full_addr

        fac["lat"] = None
        fac["lng"] = None

        if not (headers and full_addr):
            continue

        try:
            resp = requests.get(
                "https://dapi.kakao.com/v2/local/search/address.json",
                params={"query": full_addr},
                headers=headers,
                timeout=3,
            )
            data = resp.json()
            docs = data.get("documents")
            if docs:
                fac["lat"] = float(docs[0]["y"])
                fac["lng"] = float(docs[0]["x"])
        except Exception as e:
            print("카카오 지오코딩 오류:", e)


    page_facilities = list(page_obj)


    block_size = 10
    current_block = (page - 1) // block_size
    block_start = current_block * block_size + 1
    block_end = block_start + block_size - 1
    if block_end > paginator.num_pages:
        block_end = paginator.num_pages

    block_range = range(block_start, block_end + 1)

    context = {
        "page_obj": page_obj,
        "page_facilities": page_facilities,
        "paginator": paginator,
        "per_page": per_page,
        "page": page,
        "merged_count": len(facilities),
        "block_range": block_range,
        "block_start": block_start,
        "block_end": block_end,
        "KAKAO_SCRIPT_KEY": KAKAO_SCRIPT_KEY,
    }

    return render(request, "facility_list.html", context)
