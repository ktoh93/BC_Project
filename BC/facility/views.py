import os
import time
import json
import requests
import urllib.request
import urllib.parse
import re, time
from django.core.cache import cache
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.conf import settings
from django.contrib import messages



from facility.models import Facility
from facility.models import FacilityInfo
from member.models import Member
from common.models import AddInfo,Comment

# 시설 api 가져오기
FACILITY_CACHE_TIMEOUT = 60 * 10  # 10분
GEO_CACHE_TTL = 60 * 30  # 30분
_geo_cache = {}


# 공공 api 안쓸거여
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



def facility_list(request):

    KAKAO_SCRIPT_KEY = os.getenv("KAKAO_SCRIPT_KEY")

    cp_nm = request.GET.get('cpNm')
    cpb_nm = request.GET.get('cpbNm')
    keyword = request.GET.get('keyword')
    keyword = keyword or ''

    

    # ----------------------------
    # 로그인 기본 주소
    # ----------------------------
    user = request.session.get("user_id")

    if not keyword:
        if not cp_nm or not cpb_nm:
            if user:
                SIDO_MAP = {
                    "서울": "서울특별시",
                    "경기": "경기도",
                    "부산": "부산광역시",
                    "대구": "대구광역시",
                    "인천": "인천광역시",
                    "광주": "광주광역시",
                    "대전": "대전광역시",
                    "울산": "울산광역시",
                    "세종": "세종특별자치시",
                    "강원": "강원도",
                    "충북": "충청북도",
                    "충남": "충청남도",
                    "전북": "전라북도",
                    "전남": "전라남도",
                    "경북": "경상북도",
                    "경남": "경상남도",
                    "제주": "제주특별자치도",
                }
                
                try:
                    member = Member.objects.get(user_id=user)
                    addr1_raw = (member.addr1 or "").strip()
                    # addr1 = 서울특별시 / addr2 = 강남구 이런 구조라고 가정
                    if not cp_nm:
                        cp_nm = SIDO_MAP.get(addr1_raw, addr1_raw)
                    if not cpb_nm:
                        cpb_nm = member.addr2.strip()
                except Member.DoesNotExist:
                    pass

    # ----------------------------
    # 비로그인 기본값
    # ----------------------------
    if not keyword:
        if not cp_nm:
            cp_nm = "서울특별시"
        if not cpb_nm:
            cpb_nm = "강남구"

    # ----------------------------
    # DB 조회
    # ----------------------------
    qs = Facility.objects.all()

    if cp_nm:
        qs = qs.filter(cp_nm=cp_nm)
    if cpb_nm:
        # '성남시 분당구'가 faci_road_addr에 포함되어 있다면 
        
        if not qs.filter(cpb_nm=cpb_nm).exists():
            qs = qs.filter(faci_road_addr__icontains=cpb_nm)
        else :
            qs.filter(cpb_nm=cpb_nm)
        
    if keyword:
        qs = qs.filter(faci_nm__icontains=keyword)

    #qs = qs.filter(faci_stat_nm__icontains='정상운영')

    # ----------------------------
    # 데이터 가공
    # ----------------------------
    facilities = []
    for f in qs:
        facilities.append({
            "id": f.faci_cd,
            "name": f.faci_nm or "",
            "address": f.faci_road_addr or f.faci_addr or "",
            "sido": f.cp_nm or "",
            "sigungu": f.cpb_nm or "",
            "phone": f.faci_tel_no or "",
            "lat": f.faci_lat,
            "lng": f.faci_lot,
        })
    no_result = (len(facilities) == 0)

    per_page = int(request.GET.get("per_page", 10))
    page = int(request.GET.get("page", 1))

    paginator = Paginator(facilities, per_page)
    page_obj = paginator.get_page(page)

    # 지도용 데이터 (lat/lng 정상값만)
    page_facilities = kakao_for_map(page_obj)

    # ----------------------------
    # 페이징 블록 계산
    # ----------------------------
    block_size = 10
    current_block = (page - 1) // block_size
    block_start = current_block * block_size + 1
    block_end = min(block_start + block_size - 1, paginator.num_pages)
    block_range = range(block_start, block_end + 1)

    context = {
        "page_obj": page_obj,
        "page_facilities": page_facilities,
        "paginator": paginator,
        "per_page": per_page,
        "cpNm": cp_nm,
        "cpbNm": cpb_nm,
        "keyword": keyword,
        "page": page,
        "merged_count": len(facilities),
        "block_range": block_range,
        "block_start": block_start,
        "block_end": block_end,
        "no_result": no_result,
        "KAKAO_SCRIPT_KEY": KAKAO_SCRIPT_KEY,
    }
    
    
    return render(request, "facility_list.html", context)


_geo_cache = {}
GEO_CACHE_TTL = 60 * 60 * 24  # 24시간


# -----------------------------
# 1) 주소 정규화 함수
# -----------------------------
def clean_address(addr):
    if not addr:
        return ""

    addr = re.sub(r'\(.*?\)', '', addr)           # (목동) 제거
    addr = re.sub(r'지하?\d*층?', '', addr)        # 지하2층, 지층 제거
    addr = re.sub(r'B\d+호?', '', addr)            # B02호 제거
    addr = re.sub(r'\d+블럭', '', addr)            # 6블럭 제거
    addr = addr.replace(",", " ")

    return addr.strip()


# -----------------------------
# 2) 캐시 조회/저장
# -----------------------------
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
        "ts": time.time(),
    }


# -----------------------------
# 3) 시군구 중심좌표 fallback
# -----------------------------
def get_sigungu_center(sido, sigungu):
    """시군구 중심 좌표 가져오는 fallback"""
    query = f"{sido} {sigungu}"

    key = os.getenv("KAKAO_REST_API_KEY")
    headers = {"Authorization": f"KakaoAK {key}"}

    try:
        resp = requests.get(
            "https://dapi.kakao.com/v2/local/search/address.json",
            params={"query": query},
            headers=headers,
            timeout=3
        )
        docs = resp.json().get("documents")
        if docs:
            return float(docs[0]["y"]), float(docs[0]["x"])

    except:
        pass

    # 최종 fallback → 서울
    return 37.5665, 126.9780


# -----------------------------
# 4) kakao_for_map — 여기만 바꾸면 OK
# -----------------------------
def kakao_for_map(page_obj):
    KAKAO_REST_KEY = os.getenv("KAKAO_REST_API_KEY")
    headers = {"Authorization": f"KakaoAK {KAKAO_REST_KEY}"} if KAKAO_REST_KEY else None

    result = []

    for fac in page_obj:
        raw_addr = fac.get("address") or ""
        clean_addr_text = clean_address(raw_addr)

        fac["full_address"] = raw_addr
        lat = None
        lng = None

        # ----------------------------------
        # 1) 원래 DB 좌표가 있으면 최우선 사용
        # ----------------------------------
        # if fac.get("lat") and fac.get("lng"):
        #     lat = fac["lat"]
        #     lng = fac["lng"]
        
        # else:
            # -------------------------------
            # 2) 캐시 조회
            # -------------------------------
        if clean_addr_text:
            cached = _get_cached_geo(clean_addr_text)
            if cached:
                lat, lng = cached

            # -------------------------------
            # 3) 카카오 지오코딩 호출
            # -------------------------------
        if headers and clean_addr_text and (lat is None or lng is None):
            try:
                resp = requests.get(
                    "https://dapi.kakao.com/v2/local/search/address.json",
                    params={"query": clean_addr_text},
                    headers=headers,
                    timeout=3,
                )
                docs = resp.json().get("documents")

                if docs:
                    lat = float(docs[0]["y"])
                    lng = float(docs[0]["x"])
                    _set_cached_geo(clean_addr_text, lat, lng)

            except Exception as e:
                print("[지오코딩 오류]", e)

            # -------------------------------
            # 4) 여전히 좌표가 없으면 시군구 fallback
            # -------------------------------
        if lat is None or lng is None:
            lat, lng = get_sigungu_center(fac["sido"], fac["sigungu"])

        # 최종 좌표 부여
        fac["lat"] = lat
        fac["lng"] = lng

        # 지도에 반드시 추가 → 누락되는 시설 없음!
        result.append(fac)

    return result

def facility_detail(request, fk):

    KAKAO_SCRIPT_KEY = os.getenv("KAKAO_SCRIPT_KEY")

    try:
        # ------------------------------------------------------
        # 항상 files 초기화 (facility_info 없어도 사용 가능하도록)
        # ------------------------------------------------------
        files = []

        # ======================================================
        # 1) FacilityInfo / Facility 조회
        # ======================================================
        facility_info = FacilityInfo.objects.filter(facility_id=fk).first()
        facility = Facility.objects.filter(faci_cd=fk).first()

        if not facility_info and not facility:
            return render(request, "facility_view.html", {
                "error": "시설 정보를 찾을 수 없습니다."
            })

        # ======================================================
        # 2) 기본 구조
        # ======================================================
        r_data = {
            "id": fk,
            "name": "",
            "address": "",
            "sido": "",
            "sigungu": "",
            "phone": "",
            "homepage": "",
            "fcob_nm": "",
            "faci_stat_nm": "",
            "schk_tot_grd_nm": "",
            "lat": None,
            "lng": None,
            "image_url": "/media/default.png",
        }

        # 버튼 표시 여부
        can_reserve = False
        can_recruit = False
        reserve_message = "해당 시설에 문의해주세요"

        # ======================================================
        # 3) FacilityInfo 있는 경우 (관리자 데이터 우선)
        # ======================================================
        if facility_info:

            r_data["name"] = facility_info.faci_nm or (facility.faci_nm if facility else "")
            r_data["address"] = facility_info.address or (facility.faci_road_addr or facility.faci_addr if facility else "")
            r_data["sido"] = facility_info.sido or (facility.cp_nm if facility else "")
            r_data["sigungu"] = facility_info.sigugun or (facility.cpb_nm if facility else "")
            r_data["phone"] = facility_info.tel or (facility.faci_tel_no if facility else "")
            r_data["homepage"] = facility_info.homepage or (facility.faci_homepage if facility else "")

            # 이미지
            if facility_info.photo:
                r_data["image_url"] = facility_info.photo.url

            # 예약 가능
            if facility_info.reservation_time:
                can_reserve = True
                reserve_message = "가능"

            # 모집 가능
            can_recruit = True

            # Facility 원본에서 부족한 값 보완
            if facility:
                r_data["fcob_nm"] = facility.fcob_nm or ""
                r_data["faci_stat_nm"] = facility.faci_stat_nm or ""
                r_data["schk_tot_grd_nm"] = facility.schk_tot_grd_nm or ""
                r_data["lat"] = facility.faci_lat
                r_data["lng"] = facility.faci_lot

            # 첨부파일 조회
            add_info_objs = AddInfo.objects.filter(facility_id=facility_info.id)

            for add_info in add_info_objs:
                file_ext = os.path.splitext(add_info.file_name)[1].lower()
                is_image = file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']

                file_data = {
                    'id': add_info.add_info_id,
                    'name': add_info.file_name,
                    'url': f"{settings.MEDIA_URL}{add_info.path}",
                    'is_image': is_image,
                }

                # 이미지 제외 → files에만 넣기
                if not is_image:
                    files.append(file_data)

        # ======================================================
        # 4) FacilityInfo 없는 경우 (Facility 원본 + 네이버 이미지)
        # ======================================================
        else:
            r_data.update({
                "id": facility.faci_cd,
                "name": facility.faci_nm or "",
                "address": facility.faci_road_addr or facility.faci_addr or "",
                "sido": facility.cp_nm or "",
                "sigungu": facility.cpb_nm or "",
                "phone": facility.faci_tel_no or "",
                "homepage": facility.faci_homepage or "",
                "fcob_nm": facility.fcob_nm or "",
                "faci_stat_nm": facility.faci_stat_nm or "",
                "schk_tot_grd_nm": facility.schk_tot_grd_nm or "",
                "lat": facility.faci_lat,
                "lng": facility.faci_lot,
            })

            # 네이버 이미지 자동 검색
            img_url = get_naver_image(r_data["name"])
            if img_url:
                r_data["image_url"] = img_url

            # recruitment / reservation 버튼 숨김
            can_reserve = False
            can_recruit = False

        # ======================================================
        # 5) 좌표 보완 (카카오 지오코딩)
        # ======================================================
        #if not r_data["lat"] or not r_data["lng"]:
        try:
            geo_fixed = kakao_for_map([r_data])[0]
            r_data["lat"] = geo_fixed["lat"]
            r_data["lng"] = geo_fixed["lng"]
        except:
            print("카카오 지오코딩 실패 → 좌표 없음")

        # ======================================================
        # 6) 댓글 조회
        # ======================================================
        comment_objs = Comment.objects.select_related("member_id").filter(
            facility=fk
        ).order_by("reg_date")

        comments = []
        for c in comment_objs:
            comments.append({
                "comment_id": c.comment_id,
                "comment": c.comment,
                "author": c.member_id.nickname if hasattr(c.member_id, 'nickname') else "알 수 없음",
                "is_admin": (c.member_id.member_id == 1 if c.member_id else False),
                "reg_date": c.reg_date,
                "is_deleted": c.delete_date is not None,
            })

        # ======================================================
        # 7) 페이지 렌더링
        # ======================================================
        return render(request, "facility_view.html", {
            "facility": r_data,
            "files": files,   # ← 여기 항상 files 있음
            "KAKAO_SCRIPT_KEY": KAKAO_SCRIPT_KEY,
            "can_reserve": can_reserve,
            "can_recruit": can_recruit,
            "reserve_message": reserve_message,
            "comments": comments,
        })
 
    except Exception as e:
        print("[facility_detail ERROR]", e)
        import traceback
        print(traceback.format_exc())
        return render(request, "facility_view.html", {
            "error": f"상세 정보를 불러오는 중 오류가 발생했습니다: {str(e)}"
        })
    
# 댓글 추가 기능
def add_comment(request, fk):
    # GET 으로 들어오면 그냥 상세로 돌려보냄
    if request.method != "POST":
        return redirect("detail", fk=fk)

    # 0) 세션 로그인 확인
    user_id = request.session.get("user_id")
    if not user_id:
        messages.error(request, "로그인이 필요합니다.")
        return redirect("/login/")

    # 1) 로그인 회원
    try:
        member = Member.objects.get(user_id=user_id)
    except Member.DoesNotExist:
        request.session.flush()
        messages.error(request, "다시 로그인 해주세요.")
        return redirect("/login/")


    # 3) 폼에서 넘어온 댓글 내용
    content = request.POST.get("content", "").strip()
    if not content:
        messages.error(request, "댓글 내용을 입력해 주세요.")
        return redirect("detail", fk=fk)

    # 4) 댓글 생성
    Comment.objects.create(
        facility=Facility.objects.get(faci_cd=fk),
        member_id=member,
        comment=content,
    )

    messages.success(request, "댓글이 등록되었습니다.")
    return redirect("detail", fk=fk)




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

 