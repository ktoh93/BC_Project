import os
import time
import json
import requests
import urllib.request
import urllib.parse
from django.core.cache import cache
from django.shortcuts import render
from django.core.paginator import Paginator

# 시설 api 가져오기
FACILITY_CACHE_TIMEOUT = 60 * 10  # 10분
GEO_CACHE_TTL = 60 * 30  # 30분
_geo_cache = {}


def facility(data, rows=200):

    DATA_API_KEY = os.getenv("DATA_API_KEY")  
    cp_nm = (data.get('cp_nm') or "").strip()
    cpb_nm = (data.get('cpb_nm') or "").strip()
    keyword = (data.get('keyword') or "").strip()

    cache_key = f"facility:{cp_nm}:{cpb_nm}:{keyword}:{rows}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    API_URL = "https://apis.data.go.kr/B551014/SRVC_API_FACI_SCHK_RESULT/TODZ_API_FACI_SAFETY"
    params = {
        "serviceKey": DATA_API_KEY,
        "numOfRows": rows,
        "pageNo": 1,
        "faci_gb_nm": "공공",
        "cp_nm": cp_nm or None,
        "cpb_nm": cpb_nm or None,
        "resultType": "json"
    }
    if keyword:
        params["faci_nm"] = keyword

    # None 값은 API 호출 시 제외
    params = {k: v for k, v in params.items() if v not in (None, "")}

    facilities = []

    try:
        res = requests.get(API_URL, params=params, timeout=5)
        res.raise_for_status()
        data = res.json()
        items = data["response"]["body"]["items"].get("item", [])

        if isinstance(items, dict):
            items = [items]

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

        cache.set(cache_key, facilities, FACILITY_CACHE_TIMEOUT)

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
def _get_cached_geo(address):
    entry = _geo_cache.get(address)
    if not entry:
        return None
    if time.time() - entry["ts"] > GEO_CACHE_TTL:
        _geo_cache.pop(address, None)
        return None
    return entry["coords"]


def _set_cached_geo(address, lat, lng):
    _geo_cache[address] = {
        "coords": (lat, lng),
        "ts": time.time()
    }


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

        cached_coords = _get_cached_geo(full_addr)
        if cached_coords:
            fac["lat"], fac["lng"] = cached_coords
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
                lat = float(docs[0]["y"])
                lng = float(docs[0]["x"])
                fac["lat"] = lat
                fac["lng"] = lng
                _set_cached_geo(full_addr, lat, lng)

        except Exception as e:
            print("카카오 지오코딩 오류:", e)

    return list(page_obj)




# 상세페이지
def facility_detail(request, fk):
    KAKAO_SCRIPT_KEY = os.getenv("KAKAO_SCRIPT_KEY")

    try:
        # FacilityInfo에서 시설 정보 가져오기
        from facility.models import FacilityInfo
        facility_info = FacilityInfo.objects.get(id=fk)
        
        # FacilityInfo 데이터를 딕셔너리로 변환
        r_data = {
            'id': facility_info.id,
            'name': facility_info.faci_nm,
            'address': facility_info.address,
            'phone': facility_info.tel if facility_info.tel else '',
            'homepage': facility_info.homepage if facility_info.homepage else '',
            'lat': None,
            'lng': None,
        }
        
        # Facility 모델이 있으면 추가 정보 가져오기
        if facility_info.facility:
            fac = facility_info.facility
            r_data.update({
                'sido': fac.cp_nm if fac.cp_nm else '',
                'sigungu': fac.cpb_nm if fac.cpb_nm else '',
                'fcob_nm': fac.fcob_nm if fac.fcob_nm else '',
                'faci_stat_nm': fac.faci_stat_nm if fac.faci_stat_nm else '',
                'schk_tot_grd_nm': fac.schk_tot_grd_nm if fac.schk_tot_grd_nm else '',
                'lat': fac.faci_lat,
                'lng': fac.faci_lot,
            })
        
        # 지도 좌표가 없으면 카카오 지오코딩으로 가져오기
        if not r_data.get('lat') or not r_data.get('lng'):
            r_data_with_map = kakao_for_map([r_data])[0]
        else:
            r_data_with_map = r_data

        # 네이버 이미지 검색
        query = f"{r_data_with_map.get('name', '')}"
        img_url = get_naver_image(query)
        
        r_data_with_map["image_url"] = img_url 
        
        # FacilityInfo의 photo가 있으면 사용
        if facility_info.photo:
            r_data_with_map["image_url"] = facility_info.photo.url

        return render(request, "facility_view.html", {
            "facility": r_data_with_map,
            "KAKAO_SCRIPT_KEY": KAKAO_SCRIPT_KEY,
        })
        
    except FacilityInfo.DoesNotExist:
        # FacilityInfo에 없으면 기존 방식(공공데이터 API)으로 시도
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

        return render(request, "facility_view.html", {
            "facility": r_data_with_map,
            "KAKAO_SCRIPT_KEY": KAKAO_SCRIPT_KEY,
        })
    except Exception as e:
        print(f"[ERROR] facility_detail 오류: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return render(request, 'facility_view.html', {"error": f"시설 정보를 불러오는 중 오류가 발생했습니다: {str(e)}"})



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

 