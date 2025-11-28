import os
import requests
from django.shortcuts import render
from django.core.paginator import Paginator
import urllib.request
import urllib.parse
import json

# 시설 api 가져오기
def facility(data):
    DATA_API_KEY = os.getenv("DATA_API_KEY")  
    cp_nm = data.get('cp_nm')
    cpb_nm = data.get('cpb_nm')
    keyword = data.get('keyword')

    API_URL = "https://apis.data.go.kr/B551014/SRVC_API_FACI_SCHK_RESULT/TODZ_API_FACI_SAFETY"
    params = {
        "serviceKey": DATA_API_KEY,
        "numOfRows": 300,
        "pageNo": 1,
        "faci_gb_nm": "공공",
        "cp_nm": cp_nm,
        "cpb_nm": cpb_nm,
        "resultType": "json"
    }
    if keyword:
        params["faci_nm"] = keyword

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
                "phone": item.get("faci_tel_no", ""),# 전화번호
                "fcob_nm" : item.get("fcob_nm",""), # 종목
                "homepage" : item.get("faci_homepage",""), # 홈페이지
                "faci_stat_nm" : item.get("faci_stat_nm",""), # 정상운영인지 아닌지
                "schk_tot_grd_nm" : item.get("schk_tot_grd_nm",""), # 주의인지 정상인지
                "schk_open_ymd": item.get("schk_open_ymd",""), # 안전점검공개일자
                "faci_gfa" : item.get("faci_gfa",""),
                "lat": None,
                "lng": None,
            })

    except Exception as e:
        print("공공데이터 API 오류:", e)

    return facilities



# 시설목록
def facility_list(request):
         
    KAKAO_SCRIPT_KEY = os.getenv("KAKAO_SCRIPT_KEY")  
    cp_nm = request.GET.get('cpNm', "서울특별시")
    cpb_nm = request.GET.get('cpbNm', "강남구")
    keyword = request.GET.get('keyword', '')    
    data = {'cp_nm' : cp_nm, 'cpb_nm' : cpb_nm, 'keyword' : keyword}
    facilities = facility(data)

    per_page = int(request.GET.get("per_page", 10))
    page = int(request.GET.get("page", 1))
 
    paginator = Paginator(facilities, per_page)
    page_obj = paginator.get_page(page)

    page_facilities = kakao_for_map(page_obj)

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
        "cpNm" : cp_nm,
        "cpbNm" : cpb_nm,
        "keyword" : keyword,
        "page": page,
        "merged_count": len(facilities),
        "block_range": block_range,
        "block_start": block_start,
        "block_end": block_end,
        "KAKAO_SCRIPT_KEY": KAKAO_SCRIPT_KEY,
    }
    print(page_facilities)
    return render(request, "facility_list.html", context)



# 주소를 기반으로 지도에 표시하기 위한 작업
def kakao_for_map(page_obj):
    KAKAO_REST_KEY = os.getenv("KAKAO_REST_API_KEY")
    headers = {"Authorization": f"KakaoAK {KAKAO_REST_KEY}"} if KAKAO_REST_KEY else None

    for fac in page_obj:

        # 공공데이터 주소는 이미 완전한 도로명주소다!
        full_addr = fac.get("address") or ""
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

    return list(page_obj)




# 상세페이지
def facility_detail(request, fk):
    KAKAO_SCRIPT_KEY = os.getenv("KAKAO_SCRIPT_KEY")

    faci_cd = fk
    faci_nm = request.GET.get('fName')

    # 목록 검색
    data = {'keyword': faci_nm}
    facility_data = facility(data)

    # 해당 시설 찾기
    r_data = None
    for f_data in facility_data:
        if f_data.get('id') == faci_cd:
            r_data = f_data
            break

    if r_data is None:
        return render(request, 'facility_view.html', {"error": "시설 정보를 찾을 수 없습니다."})

     # 지도 좌표 1개만 처리
    r_data_with_map = kakao_for_map([r_data])[0]

    # 네이버 이미지 검색
    query = f"{r_data_with_map.get('name', '')}"
    img_url = get_naver_image(query)
    
    r_data_with_map["image_url"] = img_url 

    print("나오냐 ",r_data_with_map)

    return render(request, "facility_view.html", {
        "facility": r_data_with_map,
        "KAKAO_SCRIPT_KEY": KAKAO_SCRIPT_KEY,
    })



# 네이버 이미지로 한번 해보자

def get_naver_image(query):
    """
    네이버 이미지 검색 API - 시설명 기반 사진 1장 반환
    """
    NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
    NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

    if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
        print("❌ 네이버 API 키 없음")
        return None

    # 검색어 인코딩
    enc_query = urllib.parse.quote(query)

    url = f"https://openapi.naver.com/v1/search/image?query={enc_query}&display=1&sort=sim"

    # 요청 객체 생성
    req = urllib.request.Request(url)
    req.add_header("X-Naver-Client-Id", NAVER_CLIENT_ID)
    req.add_header("X-Naver-Client-Secret", NAVER_CLIENT_SECRET)

    try:
        response = urllib.request.urlopen(req, timeout=3)
        rescode = response.getcode()

        if rescode == 200:
            response_body = response.read().decode('utf-8')
            data = json.loads(response_body)

            items = data.get("items")
            if not items:
                print("❌ 네이버 이미지 없음:", query)
                return None

            # 가장 첫 번째 이미지 링크 반환
            return items[0].get("link")
        else:
            print("네이버 API 오류코드:", rescode)
            return None

    except Exception as e:
        print("네이버 이미지 검색 오류:", e)
        return None

 