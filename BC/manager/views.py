import requests
from django.shortcuts import render
from django.core.paginator import Paginator
import os
import json
import xmltodict


def manager(request):
    if request.method == "POST":
        admin_id = request.POST.get('admin_id')
        admin_pw = request.POST.get('admin_pw')
        # TODO: DB에서 관리자 검증
        """
        admin = db(username=admin_id, password=admin_pw)

        if admin is not None:
            login(request, admin)
            return redirect(/manager/dashboard/')
        else:
           return render(request, "manager/", {
                "error": "관리자의 아이디 혹은 비밀번호가 아닙니다."
            })
        """
    return render(request, 'login_manager.html')

def facility(request):
    DATA_API_KEY = os.getenv("DATA_API_KEY")

    cp_nm = request.GET.get("cpNm", "") or "서울특별시"
    cpb_nm = request.GET.get("cpbNm", "")
    keyword = request.GET.get("keyword", "")

    per_page = int(request.GET.get("per_page", 15))
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

    merged = []

    try:
        res = requests.get(API_URL, params=params, timeout=3)
        text = res.text.strip()

        try:
            data = json.loads(text)
            items = data["response"]["body"]["items"].get("item", [])
        except:
            xml = xmltodict.parse(text)
            items = xml["response"]["body"]["items"].get("item", [])

        if isinstance(items, dict):
            items = [items]

        for item in items:
            merged.append({
                "id": item.get("faci_cd"),
                "name": item.get("faci_nm"),
                "address": item.get("faci_road_addr"),
                "sido": item.get("cp_nm"),
                "sigungu": item.get("cpb_nm"),
                "lat": item.get("faci_lat"),
                "lng": item.get("faci_lot"),
                "phone": item.get("faci_tel_no", ""),
            })

    except:
        pass

    paginator = Paginator(merged, per_page)
    page_obj = paginator.get_page(page)

    block_size = 5
    current_block = (page - 1) // block_size
    block_start = current_block * block_size + 1
    block_end = min(block_start + block_size - 1, paginator.num_pages)

    start_index = (page_obj.number - 1) * per_page
    facility_page = []

    for idx, item in enumerate(page_obj.object_list):
        obj = dict(item)
        obj["row_no"] = start_index + idx + 1
        facility_page.append(obj)

    context = {
        "page_obj": page_obj,
        "paginator": paginator,
        "per_page": per_page,
        "page": page,
        "block_range": range(block_start, block_end + 1),
        "block_start": block_start,
        "block_end": block_end,
        "cpNm": cp_nm,
        "cpbNm": cpb_nm,
        "keyword": keyword,
        "facility_json": json.dumps(facility_page, ensure_ascii=False),
    }

    return render(request, "facility_add_manager.html", context)

def sport_type(request):
    return render(request, 'sport_type_manager.html')