import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg, Sum, Case, When, Value, IntegerField
from django.db import connection
from django.utils import timezone
from datetime import datetime, timedelta
import traceback
import os
import json
import xmltodict
import pandas as pd
from django_pandas.io import read_frame
from django.contrib import messages
from board.utils import get_board_by_name
from django.conf import settings
import uuid
from django.utils.dateparse import parse_datetime
from common.utils import save_encoded_image, delete_selected_files, is_manager, upload_files
from django.http import FileResponse, Http404

# models import 
from member.models import Member
from recruitment.models import Community, EndStatus, Rating, JoinStat
from reservation.models import Reservation, TimeSlot
from board.models import Article, Board, Category
from common.models import Comment, AddInfo
from manager.models import HeroImg
from facility.models import FacilityInfo


from django.http import JsonResponse


# 제거예정
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime

# 시설
from facility.models import Facility, FacilityInfo
from reservation.models import Sports



def manager(request):
    """
    관리자 로그인 페이지
    member_id == 1인 계정만 관리자로 인정
    """
    admin = request.session.get("manager_id")
    if not admin : 
        if request.method == "POST":
            admin_id = request.POST.get("admin_id", "").strip()
            admin_pw = request.POST.get("admin_pw", "").strip()
        
            # 입력값 검증
            if not admin_id or not admin_pw:
                return render(request, 'manager/login_manager.html', {
                    'error': '아이디와 비밀번호를 입력해주세요.'
                })
        
            try:
                from django.contrib.auth.hashers import check_password
                from member.models import Member
            
                # user_id로 계정 조회
                try:
                    admin_user = Member.objects.get(user_id=admin_id)
                except Member.DoesNotExist:
                    return render(request, 'manager/login_manager.html', {
                        'error': '존재하지 않는 아이디입니다.'
                    })
            
                # 관리자 권한 확인 (member_id == 1만 관리자)
                if admin_user.manager_yn != 1:
                    return render(request, 'manager/login_manager.html', {
                        'error': '관리자 권한이 없습니다.'
                    })
            
                # 비밀번호 검증
                if not check_password(admin_pw, admin_user.password):
                    return render(request, 'manager/login_manager.html', {
                        'error': '비밀번호가 올바르지 않습니다.'
                    })
            
                # 세션 완전히 삭제
                request.session.flush()
                
                # 세션 쿠키도 삭제하기 위해 만료 시간 설정
                request.session.set_expiry(0)
    
                # 로그인 성공 → 세션에 저장
                request.session["user_id"] = admin_user.user_id
                request.session["user_name"] = admin_user.name
                request.session["nickname"] = admin_user.nickname
                request.session['manager_id'] = admin_user.member_id
                #request.session['manager_name'] = admin_user.name

                return redirect('manager:dashboard')
            
            except Exception as e:
                print(f"[ERROR] 관리자 로그인 오류: {str(e)}")
                print(traceback.format_exc())
                return render(request, 'manager/login_manager.html', {
                    'error': '로그인 중 오류가 발생했습니다.'
            })
            
        return render(request, 'manager/login_manager.html')
    else:
        return redirect('manager:dashboard')



# 시설 추가
def facility(request):
    # 관리자 권한 확인
    if not is_manager(request):
        messages.error(request, "관리자 권한이 필요합니다.")
        return redirect('manager:manager_login')
    #DATA_API_KEY = os.getenv("DATA_API_KEY")

    cp_nm = request.GET.get("sido", "") 
    cpb_nm = request.GET.get("sigungu", "")
    keyword = request.GET.get("keyword", "")
    
    per_page = int(request.GET.get("per_page", 15))
    page = int(request.GET.get("page", 1))
    apply_sports = request.GET.get("apply_sports", "")

    queryset = Facility.objects.all()
    

    # 세션에서 선택된 종목 로드
    selected_ids = request.session.get("selected_sports", [])
    selected_ids = list(map(int, selected_ids)) if selected_ids else []

    # 종목 필터 적용
    if apply_sports and selected_ids:
        selected_sports = Sports.objects.filter(sports_id__in=selected_ids)
        if selected_sports.exists():
            q = Q()
            for s in selected_sports:
                word = s.s_name.strip()
                if word:
                    q |= (
                        Q(faci_nm__icontains=word) |
                        Q(ftype_nm__icontains=word) |
                        Q(cp_nm__icontains=word) |
                        Q(cpb_nm__icontains=word)
                    )
            queryset = queryset.filter(q)

    # 지역
    if cp_nm:
        queryset = queryset.filter(faci_addr__icontains=cp_nm)
    if cpb_nm:
        queryset = queryset.filter(faci_addr__icontains=cpb_nm)

    # 검색어
    if keyword:
        queryset = queryset.filter(faci_nm__icontains=keyword)

    # 이미 등록된 시설 제외
    registered_ids = FacilityInfo.objects.values_list("facility_id", flat=True)
    queryset = queryset.exclude(faci_cd__in=registered_ids)

    paginator = Paginator(queryset, per_page)
    page_obj = paginator.get_page(page)

    block_size = 10
    current_block = (page - 1) // block_size
    block_start = current_block * block_size + 1
    block_end = block_start + block_size - 1
    if block_end > paginator.num_pages:
        block_end = paginator.num_pages

    block_range = range(block_start, block_end + 1)


    # 번호 계산
    start_index = (page_obj.number - 1) * per_page

    facility_page = [
        {
            "id": item.id,
            "name": item.faci_nm,
            "address": item.faci_road_addr,
            "row_no": start_index + idx + 1,
            "faci_stat_nm" : item.faci_stat_nm
        }
        for idx, item in enumerate(page_obj.object_list)
    ]

    # 종목 JSON (selected 여부 포함)
    all_sports = Sports.objects.all()
    sports_json = json.dumps(
        [
            {
                "id": s.sports_id,
                "s_name": s.s_name,
                "selected": s.sports_id in selected_ids
            }
            for s in all_sports
        ],
        ensure_ascii=False
    )

    context = {
        "page_obj": page_obj,
        "per_page": per_page,
        "sido": cp_nm,
        "sigungu": cpb_nm,
        "keyword": keyword,
        "facility_json": json.dumps(facility_page, ensure_ascii=False),
        "sports_json": sports_json,
        "block_range": block_range,
        "block_start": block_start,
        "block_end": block_end,
        "paginator": paginator,
        "apply_sports" : apply_sports,
    }
    return render(request, "manager/facility_add_manager.html", context)


# 종목 추가
def add_sport(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()

        if not name:
            return JsonResponse({"status": "error", "message": "종목명을 입력하세요."})

        # 중복 체크
        if Sports.objects.filter(s_name=name).exists():
            return JsonResponse({"status": "error", "message": "이미 존재하는 종목입니다."})

        sport = Sports.objects.create(s_name=name)

        return JsonResponse({
            "status": "success",
            "id": sport.sports_id,
            "name": sport.s_name
        })

    return JsonResponse({"status": "error", "message": "Invalid request"})


# 선택된 종목 저장 (세션에 저장)
def save_selected_sports(request):
    if request.method == "POST":
        ids = request.POST.getlist("ids[]", [])
        ids = list(map(int, ids))
        request.session["selected_sports"] = ids
        return JsonResponse({"status": "success"})
    return JsonResponse({"status": "error"})


# 종목 삭제 (DB 삭제)
def sport_delete(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "msg": "POST만 가능"}, status=405)

    try:
        data = json.loads(request.body)
        ids = data.get("ids", [])

        if not ids:
            return JsonResponse({"status": "error", "msg": "삭제할 항목 없음"})

        Sports.objects.filter(sports_id__in=ids).delete()

        return JsonResponse({"status": "ok", "deleted": ids})

    except Exception as e:
        return JsonResponse({"status": "error", "msg": str(e)})


# 시설등록(insert)
def facility_register(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "POST만 가능"}, status=405)

    try:
        ids = request.POST.getlist("ids[]", [])

        if not ids:
            return JsonResponse({"status": "error", "message": "선택된 시설이 없습니다."})

        facilities = Facility.objects.filter(id__in=ids)

        count = 0
        for fac in facilities:
            FacilityInfo.objects.create(
                facility_id = fac.faci_cd or "",
                faci_nm=fac.faci_nm or "",
                address=fac.faci_road_addr or "",
                sido = fac.cp_nm or "",
                sigugun = fac.cpb_nm or "",
                tel=fac.faci_tel_no or "",
                homepage=fac.faci_homepage or "",
                photo=None,
                reservation_time=None,
            )
            count += 1

        return JsonResponse({"status": "success", "count": count})

    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"status": "error", "message": str(e)})


# 시설관리
def facility_list(request):
    # 관리자 권한 확인
    if not is_manager(request):
        messages.error(request, "관리자 권한이 필요합니다.")
        return redirect('manager:manager_login')
    # 필터 파라미터
    sido = request.GET.get("sido", "")
    sigungu = request.GET.get("sigungu", "")
    keyword = request.GET.get("keyword", "")
    per_page = int(request.GET.get("per_page", 15))
    page = int(request.GET.get("page", 1))

    
    # 시설 api 정보
    queryset = FacilityInfo.objects.all()
    
    if sido:
        queryset = queryset.filter(sido__icontains=sido)

    if sigungu:
        queryset = queryset.filter(sigugun__icontains=sigungu)

    if keyword:
        queryset = queryset.filter(faci_nm__icontains=keyword)

    paginator = Paginator(queryset, per_page)
    page_obj = paginator.get_page(page)

    block_size = 10
    current_block = (page - 1) // block_size
    block_start = current_block * block_size + 1
    block_end = block_start + block_size - 1
    if block_end > paginator.num_pages:
        block_end = paginator.num_pages

    block_range = range(block_start, block_end + 1)

    start_index = (page_obj.number - 1) * per_page
    facility_page = []
    
    # 오늘 날짜
    today = timezone.now().date()

    for idx, item in enumerate(page_obj.object_list):
        # 금일 활성 예약: 오늘 날짜 기준으로 예약이 발생한 건 수 (Reservation의 reg_date가 오늘)
        # TimeSlot을 통해 해당 시설의 예약을 찾고, Reservation의 reg_date가 오늘인 것
        today_reservations = Reservation.objects.filter(
            timeslot__facility_id=item,
            reg_date__date=today,
            delete_yn=0
        ).distinct().count()
        
        # 누적 예약: 오늘까지 누적된 예약 건 수, 취소된 건 제외 (delete_yn=0)
        total_reservations = Reservation.objects.filter(
            timeslot__facility_id=item,
            reg_date__date__lte=today,
            delete_yn=0
        ).distinct().count()
        
        facility_page.append({
            "id": item.id,
            "name": item.faci_nm,
            "address": item.address,
            "row_no": start_index + idx + 1,
            "facilityCd": item.facility_id,
            "today_count": today_reservations,
            "total_count": total_reservations,
            "rsPosible" : item.rs_posible
        })

    context = {
        "page_obj": page_obj,
        "per_page": per_page,
        "sido": sido,
        "sigungu": sigungu,
        "keyword": keyword,
        "facility_json": json.dumps(facility_page, ensure_ascii=False),
        "block_range": block_range,
    }

    return render(request, "manager/facility_list_manager.html", context)


# 시설상세보기 
def facility_detail(request, id):
    # 관리자 권한 확인
    if not is_manager(request):
        messages.error(request, "관리자 권한이 필요합니다.")
        return redirect('manager:manager_login')
    facilityInfo = get_object_or_404(FacilityInfo, facility_id=id)
    facility = get_object_or_404(Facility,faci_cd=id )

    # 요일 한국어 매핑 + 순서 정의
    DAY_ORDER = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

    KOREAN_DAYS = {
        "monday": "월요일",
        "tuesday": "화요일",
        "wednesday": "수요일",
        "thursday": "목요일",
        "friday": "금요일",
        "saturday": "토요일",
        "sunday": "일요일",
    }

    # reservation_time 정렬
    reservation_list = []
    rt = facilityInfo.reservation_time or {}

    for day in DAY_ORDER:  # 👉 월요일부터 반복
        info = rt.get(day, {})
        reservation_list.append({
            "day_kr": KOREAN_DAYS[day],
            "active": info.get("active", False),
            "open": info.get("open"),
            "close": info.get("close"),
            "interval": info.get("interval"),
        })


    comment_objs = Comment.objects.select_related("member_id").filter(
        facility=id
    ).order_by("reg_date")

    comments = []
    for comment_obj in comment_objs:
        comment_author = comment_obj.member_id.nickname if comment_obj.member_id and hasattr(comment_obj.member_id, 'nickname') else '알 수 없음'
        comment_is_admin = comment_obj.member_id.manager_yn == 1 if comment_obj.member_id else False
        is_deleted = comment_obj.delete_date is not None
        comment = "관리자에 의해 삭제된 댓글입니다." if comment_obj.delete_date else comment_obj.comment
        
        comments.append({
            'comment_id': comment_obj.comment_id,
            'comment': comment,
            'author': comment_author,
            'is_admin': comment_is_admin,
            'reg_date': comment_obj.reg_date,
            'is_deleted': is_deleted,
            
        })

    # 첨부파일
    files = AddInfo.objects.filter(facility_id=facilityInfo.id)

    downloadable_files = [
        f for f in files 
        if not f.encoded_name.lower().endswith(('.jpg','.jpeg','.png','.gif','.bmp','.webp'))
    ]


    context = {
        "facilityInfo": facilityInfo,
        "facility" : facility,
        "comments" : comments,
        "reservation_list": reservation_list,
        "files":files,
        "downloadable_files": downloadable_files,
    }
    return render(request, "manager/facility_detail.html", context)


# 시설수정
def facility_modify(request, id):

    info = get_object_or_404(FacilityInfo, id=id)

    # -----------------------------
    # GET — 수정 페이지
    # -----------------------------
    if request.method == "GET":

        time_json = json.dumps(info.reservation_time, ensure_ascii=False) if info.reservation_time else "{}"

        # ✔ AddInfo는 FK → facility_id = info.id
        files = AddInfo.objects.filter(facility_id=info.id)

        return render(request, "manager/facility_write.html", {
            "info": info,
            "files": files,
            "time_json": time_json
        })

    # -----------------------------
    # POST — 실제 저장
    # -----------------------------
    info.tel = request.POST.get("tel", "")
    info.homepage = request.POST.get("homepage", "")
    rs_posible = 1 if request.POST.get("rs_posible") else 0
    info.rs_posible = rs_posible
    # 예약 JSON 파싱
    raw_time = request.POST.get("reservation_time", "{}")
    try:
        info.reservation_time = json.loads(raw_time)
    except:
        info.reservation_time = {}

    info.save()

    # 1) 대표 이미지 저장
    save_encoded_image(
        request=request,
        instance=info,
        field_name="photo",
        sub_dir="uploads/facility/photo",
        delete_old=True
    )

    # 2) 첨부파일 삭제
    delete_selected_files(request)

    # 3) 첨부파일 업로드 (FK 자동 저장됨)
    upload_files(
        request=request,
        instance=info,
        file_field="attachment_files",
        sub_dir="uploads/facility/files"
    )

    messages.success(request, "시설 정보가 수정되었습니다.")
    return redirect("manager:facility_detail", id=info.facility_id)

@csrf_exempt
def facility_delete(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "msg": "POST만 가능"}, status=405)

    try:
        data = json.loads(request.body)
        ids = data.get("ids", [])

        if not ids:
            return JsonResponse({"status": "error", "msg": "삭제할 항목이 없습니다."})

        # 1) 삭제 대상 FacilityInfo
        infos = FacilityInfo.objects.filter(id__in=ids)

        # 2) 관련 AddInfo 가져오기 (PK 기반)
        files = AddInfo.objects.filter(facility_id__in=ids)

        # 2-1) 파일 삭제
        for f in files:
            if f.path:
                file_path = os.path.join(settings.MEDIA_ROOT, f.path)
                if os.path.exists(file_path):
                    os.remove(file_path)

        # 2-2) DB 레코드 삭제
        files.delete()

        # 3) FacilityInfo 대표이미지 삭제
        for info in infos:
            if info.photo and info.photo.name:
                photo_path = os.path.join(settings.MEDIA_ROOT, info.photo.name)
                if os.path.exists(photo_path):
                    os.remove(photo_path)

        # 4) FacilityInfo 삭제 (FK CASCADE로 AddInfo 자동삭제 가능)
        infos.delete()

        return JsonResponse({"status": "success", "deleted": ids})

    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"status": "error", "msg": str(e)})

def dashboard(request):
    # 관리자 권한 확인
    if not is_manager(request):
        messages.error(request, "관리자 권한이 필요합니다.")
        return redirect('manager:manager_login')
    """
    관리자 대시보드
    DB가 없어도 동작하도록 모든 DB 쿼리에 예외 처리 포함
    """
    # 필터 파라미터
    region_filter = request.GET.get('region', '')
    sport_filter = request.GET.get('sport', '')
    date_range = request.GET.get('date_range', '7')  # 기본 7일
    
    try:
        days = int(date_range)
    except (ValueError, TypeError):
        days = 7
    
    start_date = timezone.now() - timedelta(days=days)
    
    # ============================================
    # 1. 실시간 현황 KPI 카드
    # ============================================
    today = timezone.now().date()
    
    kpi_data = {
        'today_reservations': 0,
        'today_communities': 0,
        'today_members': 0,
        'active_communities': 0,
    }
    
    try:
        # DB 연결 확인
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        # DB가 있으면 쿼리 실행
        try:
            kpi_data = {
                'today_reservations': Reservation.objects.filter(
                    reg_date__date=today,
                    delete_yn=0
                ).count(),
                'today_communities': Community.objects.filter(
                    reg_date__date=today,
                    delete_date__isnull=True
                ).count(),
                'today_members': Member.objects.filter(
                    reg_date__date=today,
                    delete_yn=0
                ).count(),
                'active_communities': Community.objects.filter(
                    delete_date__isnull=True
                ).count(),
            }
        except Exception as e:
            # 테이블이 없거나 쿼리 실패 시 기본값 유지
            pass
    except Exception:
        # DB 연결 자체가 안되면 기본값 유지
        pass
    
    # ============================================
    # 2. 예약/모집글 통계 (일별 추이)
    # ============================================
    daily_recruitment = {}
    daily_reservations = {}
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        try:
            communities = Community.objects.filter(
                reg_date__gte=start_date,
                delete_date__isnull=True
            )
            
            if region_filter:
                communities = communities.filter(region=region_filter)
            if sport_filter:
                communities = communities.filter(sport_type=sport_filter)
            
            # pandas로 일별 집계
            if communities.exists():
                df_communities = read_frame(communities.values('reg_date', 'region', 'sport_type'))
                if not df_communities.empty:
                    df_communities['date'] = pd.to_datetime(df_communities['reg_date']).dt.date
                    daily_recruitment = df_communities.groupby('date').size().to_dict()
                    # 날짜를 문자열로 변환 (JSON 직렬화)
                    daily_recruitment = {str(k): int(v) for k, v in daily_recruitment.items()}
            
            # 예약 추이
            reservations = Reservation.objects.filter(
                reg_date__gte=start_date,
                delete_yn=0
            )
            
            if reservations.exists():
                df_reservations = read_frame(reservations.values('reg_date'))
                if not df_reservations.empty:
                    df_reservations['date'] = pd.to_datetime(df_reservations['reg_date']).dt.date
                    daily_reservations = df_reservations.groupby('date').size().to_dict()
                    daily_reservations = {str(k): int(v) for k, v in daily_reservations.items()}
        except Exception:
            # 테이블이 없거나 쿼리 실패 시 빈 딕셔너리 유지
            pass
    except Exception:
        # DB 연결 실패 시 빈 딕셔너리 유지
        pass
    
    # ============================================
    # 3. 모집 완료 추이
    # ============================================
    completion_trend = {}
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        try:
            end_statuses = EndStatus.objects.select_related('community').filter(
                community__reg_date__gte=start_date
            )
            
            if region_filter:
                end_statuses = end_statuses.filter(community__region=region_filter)
            if sport_filter:
                end_statuses = end_statuses.filter(community__sport_type=sport_filter)
            
            if end_statuses.exists():
                df_end = read_frame(end_statuses.values('community__reg_date', 'end_stat'))
                if not df_end.empty:
                    df_end['date'] = pd.to_datetime(df_end['community__reg_date']).dt.date
                    total_by_date = df_end.groupby('date').size()
                    completed_by_date = df_end[df_end['end_stat'] == 1].groupby('date').size()
                    
                    for date in total_by_date.index:
                        total = int(total_by_date.get(date, 0))
                        completed = int(completed_by_date.get(date, 0))
                        completion_trend[str(date)] = {
                            'total': total,
                            'completed': completed,
                            'rate': round((completed / total * 100) if total > 0 else 0, 1)
                        }
        except Exception:
            pass
    except Exception:
        pass
    
    # ============================================
    # 4. 게시판 통계
    # ============================================
    board_stats = []
    comment_count = 0
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        try:
            articles = Article.objects.filter(
                reg_date__gte=start_date,
                delete_date__isnull=True
            )
            
            board_stats = list(articles.values('board_id__board_name').annotate(
                count=Count('article_id'),
                total_views=Sum('view_cnt')
            ))
            
            # 댓글 통계
            comment_count = Comment.objects.filter(
                reg_date__gte=start_date,
                delete_date__isnull=True
            ).count()
        except Exception:
            pass
    except Exception:
        pass
    
    # ============================================
    # 5. 회원 가입 추이
    # ============================================
    daily_members = {}
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        try:
            members = Member.objects.filter(
                reg_date__gte=start_date,
                delete_yn=0
            )
            
            if members.exists():
                df_members = read_frame(members.values('reg_date'))
                if not df_members.empty:
                    df_members['date'] = pd.to_datetime(df_members['reg_date']).dt.date
                    daily_members = df_members.groupby('date').size().to_dict()
                    daily_members = {str(k): int(v) for k, v in daily_members.items()}
        except Exception:
            pass
    except Exception:
        pass
    
    # ============================================
    # 6. 성별 분포
    # ============================================
    gender_data = {}
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        try:
            gender_dist = Member.objects.filter(delete_yn=0).values('gender').annotate(
                count=Count('member_id')
            )
            gender_data = {str(item['gender']): item['count'] for item in gender_dist}
        except Exception:
            pass
    except Exception:
        pass
    
    # ============================================
    # 7. 예약 취소율 (개선: 기간별 추이 포함)
    # ============================================
    cancellation_rate = 0
    daily_cancellation_rate = {}
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        try:
            # 전체 취소율
            total_reservations = Reservation.objects.filter(reg_date__gte=start_date).count()
            cancelled_reservations = Reservation.objects.filter(
                reg_date__gte=start_date,
                delete_yn=1
            ).count()
            
            cancellation_rate = round((cancelled_reservations / total_reservations * 100) if total_reservations > 0 else 0, 2)
            
            # 일별 취소율 추이
            all_reservations = Reservation.objects.filter(reg_date__gte=start_date)
            if all_reservations.exists():
                df_all = read_frame(all_reservations.values('reg_date', 'delete_yn'))
                if not df_all.empty:
                    df_all['date'] = pd.to_datetime(df_all['reg_date']).dt.date
                    df_all['is_cancelled'] = df_all['delete_yn'] == 1
                    
                    # 일별 총 예약 수
                    daily_total = df_all.groupby('date').size()
                    # 일별 취소 수
                    daily_cancelled = df_all[df_all['is_cancelled']].groupby('date').size()
                    
                    for date in daily_total.index:
                        total = int(daily_total.get(date, 0))
                        cancelled = int(daily_cancelled.get(date, 0))
                        rate = round((cancelled / total * 100) if total > 0 else 0, 2)
                        daily_cancellation_rate[str(date)] = {
                            'total': total,
                            'cancelled': cancelled,
                            'rate': rate
                        }
        except Exception:
            pass
    except Exception:
        pass
    
    # ============================================
    # 8. 참여율 통계 (개선: 기간별 추이 포함)
    # ============================================
    participation_rate = 0
    daily_participation_rate = {}
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        try:
            join_stats = JoinStat.objects.select_related('community_id').filter(
                community_id__reg_date__gte=start_date
            )
            
            if region_filter:
                join_stats = join_stats.filter(community_id__region=region_filter)
            if sport_filter:
                join_stats = join_stats.filter(community_id__sport_type=sport_filter)
            
            if join_stats.exists():
                df_join = read_frame(join_stats.values('community_id__reg_date', 'join_status'))
                if not df_join.empty:
                    # 전체 참여율
                    total_joins = len(df_join)
                    completed_joins = len(df_join[df_join['join_status'] == 1])
                    participation_rate = round((completed_joins / total_joins * 100) if total_joins > 0 else 0, 2)
                    
                    # 일별 참여율 추이
                    df_join['date'] = pd.to_datetime(df_join['community_id__reg_date']).dt.date
                    df_join['is_completed'] = df_join['join_status'] == 1
                    
                    daily_total_joins = df_join.groupby('date').size()
                    daily_completed_joins = df_join[df_join['is_completed']].groupby('date').size()
                    
                    for date in daily_total_joins.index:
                        total = int(daily_total_joins.get(date, 0))
                        completed = int(daily_completed_joins.get(date, 0))
                        rate = round((completed / total * 100) if total > 0 else 0, 2)
                        daily_participation_rate[str(date)] = {
                            'total': total,
                            'completed': completed,
                            'rate': rate
                        }
        except Exception:
            pass
    except Exception:
        pass
    
    # ============================================
    # 9. 성별 분포 (개선: 예약자/참여자 기준 추가)
    # ============================================
    gender_data = {}  # 전체 회원
    reservation_gender_data = {}  # 예약자 성별
    participation_gender_data = {}  # 참여자 성별
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        try:
            # 전체 회원 성별 분포
            gender_dist = Member.objects.filter(delete_yn=0).values('gender').annotate(
                count=Count('member_id')
            )
            gender_data = {str(item['gender']): item['count'] for item in gender_dist}
            
            # 예약자 성별 분포
            reservations_with_member = Reservation.objects.filter(
                reg_date__gte=start_date,
                delete_yn=0
            ).select_related('member')
            
            if reservations_with_member.exists():
                reservation_gender_dist = reservations_with_member.values('member__gender').annotate(
                    count=Count('reservation_id')
                )
                reservation_gender_data = {str(item['member__gender']): item['count'] for item in reservation_gender_dist}
            
            # 참여자 성별 분포 (join_status=1인 경우만)
            join_stats_with_member = JoinStat.objects.select_related('member_id', 'community_id').filter(
                community_id__reg_date__gte=start_date,
                join_status=1
            )
            
            if region_filter:
                join_stats_with_member = join_stats_with_member.filter(community_id__region=region_filter)
            if sport_filter:
                join_stats_with_member = join_stats_with_member.filter(community_id__sport_type=sport_filter)
            
            if join_stats_with_member.exists():
                participation_gender_dist = join_stats_with_member.values('member_id__gender').annotate(
                    count=Count('member_id')
                )
                participation_gender_data = {str(item['member_id__gender']): item['count'] for item in participation_gender_dist}
        except Exception:
            pass
    except Exception:
        pass
    
    # 지역별, 종목별 옵션
    regions = []
    sports = []
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        try:
            regions = list(Community.objects.values_list('region', flat=True).distinct())
            sports = list(Community.objects.values_list('sport_type', flat=True).distinct())
        except Exception:
            pass
    except Exception:
        pass
    
    context = {
        'kpi_data': kpi_data,
        'daily_recruitment': json.dumps(daily_recruitment),
        'daily_reservations': json.dumps(daily_reservations),
        'completion_trend': json.dumps(completion_trend),
        'board_stats': board_stats,
        'comment_count': comment_count,
        'daily_members': json.dumps(daily_members),
        'gender_data': json.dumps(gender_data),
        'reservation_gender_data': json.dumps(reservation_gender_data),
        'participation_gender_data': json.dumps(participation_gender_data),
        'cancellation_rate': cancellation_rate,
        'daily_cancellation_rate': json.dumps(daily_cancellation_rate),
        'participation_rate': participation_rate,
        'daily_participation_rate': json.dumps(daily_participation_rate),
        'regions': regions,
        'sports': sports,
        'selected_region': region_filter,
        'selected_sport': sport_filter,
        'date_range': date_range,
    }
    
    return render(request, 'manager/dashboard.html', context)


def facility_inspection_stats(request):
    # 관리자 권한 확인
    if not is_manager(request):
        messages.error(request, "관리자 권한이 필요합니다.")
        return redirect('manager:manager_login')
    """
    시설 안전점검 통계 페이지
    """
    # 필터 파라미터
    region_filter = request.GET.get('region', '')
    sport_filter = request.GET.get('sport', '')
    
    # 연도별 점검 추세
    yearly_inspection_trend = {}
    # 등급별 분포
    grade_distribution = {}
    # 지역별 안전점검 통계
    region_inspection_stats = {}
    # 종목별 안전점검 통계
    sport_inspection_stats = {}
    
    # 지역/종목 옵션
    regions = []
    sports = []
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        try:
            facilities = Facility.objects.exclude(schk_visit_ymd__isnull=True).exclude(schk_visit_ymd='')
            
            # 필터 적용
            if region_filter:
                facilities = facilities.filter(cp_nm=region_filter)
            if sport_filter:
                facilities = facilities.filter(fcob_nm=sport_filter)
            
            if facilities.exists():
                df_facilities = read_frame(facilities.values(
                    'schk_visit_ymd', 'schk_tot_grd_nm', 'cp_nm', 'fcob_nm'
                ))
                
                if not df_facilities.empty:
                    # 연도별 점검 추세 (2000~2025년만)
                    df_facilities['year'] = df_facilities['schk_visit_ymd'].str[:4]
                    df_facilities['year_int'] = pd.to_numeric(df_facilities['year'], errors='coerce')
                    valid_df = df_facilities[(df_facilities['year_int'] >= 2000) & (df_facilities['year_int'] <= 2025)]
                    yearly_trend = valid_df.groupby('year').size()
                    
                    # 최초 년도와 최종 년도 확인
                    min_year = int(valid_df['year'].min()) if not valid_df['year'].empty else 2020
                    max_year = 2025  # 올해
                    
                    # 모든 년도에 대해 데이터 채우기 (없으면 0)
                    yearly_inspection_trend = {}
                    for year in range(min_year, max_year + 1):
                        year_str = str(year)
                        yearly_inspection_trend[year_str] = int(yearly_trend.get(year_str, 0))
                    
                    # 등급별 분포
                    grade_dist = df_facilities['schk_tot_grd_nm'].value_counts()
                    grade_distribution = {str(k): int(v) for k, v in grade_dist.items() if pd.notna(k)}
                    
                    # 지역별 안전점검 통계
                    if 'cp_nm' in df_facilities.columns:
                        for region in df_facilities['cp_nm'].dropna().unique():
                            region_df = df_facilities[df_facilities['cp_nm'] == region]
                            grade_counts = region_df['schk_tot_grd_nm'].value_counts()
                            region_inspection_stats[str(region)] = {
                                str(k): int(v) for k, v in grade_counts.items() if pd.notna(k)
                            }
                    
                    # 종목별 안전점검 통계
                    if 'fcob_nm' in df_facilities.columns:
                        for sport in df_facilities['fcob_nm'].dropna().unique():
                            sport_df = df_facilities[df_facilities['fcob_nm'] == sport]
                            grade_counts = sport_df['schk_tot_grd_nm'].value_counts()
                            sport_inspection_stats[str(sport)] = {
                                str(k): int(v) for k, v in grade_counts.items() if pd.notna(k)
                            }
            
            # 필터 옵션 가져오기
            all_facilities = Facility.objects.exclude(cp_nm__isnull=True).exclude(cp_nm='')
            regions = list(all_facilities.values_list('cp_nm', flat=True).distinct())
            
            all_facilities_sport = Facility.objects.exclude(fcob_nm__isnull=True).exclude(fcob_nm='')
            sports = list(all_facilities_sport.values_list('fcob_nm', flat=True).distinct())
            
        except Exception as e:
            print(f"[시설 안전점검 통계] 오류: {e}")
            pass
    except Exception:
        pass
    
    context = {
        'yearly_inspection_trend': json.dumps(yearly_inspection_trend),
        'grade_distribution': json.dumps(grade_distribution),
        'region_inspection_stats': json.dumps(region_inspection_stats),
        'sport_inspection_stats': json.dumps(sport_inspection_stats),
        'regions': regions,
        'sports': sports,
        'selected_region': region_filter,
        'selected_sport': sport_filter,
    }
    
    return render(request, 'manager/facility_inspection_stats.html', context)


def facility_inspection_yearly_detail(request):
    # 관리자 권한 확인
    if not is_manager(request):
        messages.error(request, "관리자 권한이 필요합니다.")
        return redirect('manager:manager_login')
    """
    연도별 안전점검 추세 상세 페이지
    연도, 지역, 종목을 교차 선택하여 통계 확인 가능
    """
    # 필터 파라미터 (모두 동시 선택 가능)
    year_filter = request.GET.get('year', '')  # 단일 선택
    region_filter = request.GET.get('region', '')
    sport_filter = request.GET.get('sport', '')
    
    # 통계 데이터
    stats_data = {}
    grade_by_year = {}  # 연도별 등급별 분포
    summary_stats = {
        'total_inspections': 0,
        'avg_per_year': 0,
        'max_year': '',
        'min_year': ''
    }
    
    # 옵션 리스트
    years = []
    regions = []
    sports = []
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        try:
            facilities = Facility.objects.exclude(schk_visit_ymd__isnull=True).exclude(schk_visit_ymd='')
            
            # 필터 적용 (모두 동시 적용)
            if year_filter:
                facilities = facilities.filter(schk_visit_ymd__startswith=year_filter)
            if region_filter:
                facilities = facilities.filter(cp_nm=region_filter)
            if sport_filter:
                facilities = facilities.filter(fcob_nm=sport_filter)
            
            if facilities.exists():
                df_facilities = read_frame(facilities.values(
                    'schk_visit_ymd', 'schk_tot_grd_nm', 'cp_nm', 'fcob_nm'
                ))
                
                if not df_facilities.empty:
                    df_facilities['year'] = df_facilities['schk_visit_ymd'].str[:4]
                    
                    # 연도별 통계 (2000~2025년만)
                    df_facilities['year_int'] = pd.to_numeric(df_facilities['year'], errors='coerce')
                    valid_df = df_facilities[(df_facilities['year_int'] >= 2000) & (df_facilities['year_int'] <= 2025)]
                    
                    # 전체 연도 표시 (선택된 연도 필터는 이미 적용됨)
                    yearly_trend = valid_df.groupby('year').size()
                    min_year = int(valid_df['year'].min()) if not valid_df['year'].empty else 2020
                    max_year = 2025
                    
                    # 연도별 점검 건수
                    for year in range(min_year, max_year + 1):
                        year_str = str(year)
                        stats_data[year_str] = int(yearly_trend.get(year_str, 0))
                    
                    # 연도별 등급별 분포 (상세 정보용)
                    grade_by_year = {}
                    if 'schk_tot_grd_nm' in valid_df.columns:
                        for year in range(min_year, max_year + 1):
                            year_str = str(year)
                            year_df = valid_df[valid_df['year'] == year_str]
                            if not year_df.empty:
                                grade_counts = year_df['schk_tot_grd_nm'].value_counts()
                                grade_by_year[year_str] = {
                                    str(k): int(v) for k, v in grade_counts.items() if pd.notna(k)
                                }
                            else:
                                grade_by_year[year_str] = {}
                    
                    # 요약 통계
                    summary_stats['total_inspections'] = len(df_facilities)
                    if stats_data:
                        non_zero_years = {k: v for k, v in stats_data.items() if v > 0}
                        if non_zero_years:
                            summary_stats['avg_per_year'] = round(sum(non_zero_years.values()) / len(non_zero_years), 1)
                            summary_stats['max_year'] = max(non_zero_years, key=non_zero_years.get)
                            summary_stats['min_year'] = min(non_zero_years, key=non_zero_years.get)
            
            # 옵션 리스트 생성 (2000~2025년만)
            all_facilities = Facility.objects.exclude(schk_visit_ymd__isnull=True).exclude(schk_visit_ymd='')
            if all_facilities.exists():
                df_all = read_frame(all_facilities.values('schk_visit_ymd'))
                if not df_all.empty:
                    df_all['year'] = df_all['schk_visit_ymd'].str[:4]
                    # 연도 유효성 검사 (2000~2025년만)
                    df_all['year_int'] = pd.to_numeric(df_all['year'], errors='coerce')
                    valid_years = df_all[(df_all['year_int'] >= 2000) & (df_all['year_int'] <= 2025)]['year'].unique()
                    years = sorted(valid_years.tolist(), reverse=True)
            
            all_regions = Facility.objects.exclude(cp_nm__isnull=True).exclude(cp_nm='')
            regions = list(all_regions.values_list('cp_nm', flat=True).distinct())
            
            all_sports = Facility.objects.exclude(fcob_nm__isnull=True).exclude(fcob_nm='')
            sports = list(all_sports.values_list('fcob_nm', flat=True).distinct())
            
        except Exception as e:
            print(f"[연도별 상세] 오류: {e}")
            pass
    except Exception:
        pass
    
    context = {
        'stats_data': json.dumps(stats_data),
        'grade_by_year': json.dumps(grade_by_year),
        'summary_stats': summary_stats,
        'years': years,
        'regions': regions,
        'sports': sports,
        'selected_year': year_filter,
        'selected_region': region_filter,
        'selected_sport': sport_filter,
    }
    
    return render(request, 'manager/facility_inspection_yearly_detail.html', context)


def facility_inspection_grade_detail(request):
    # 관리자 권한 확인
    if not is_manager(request):
        messages.error(request, "관리자 권한이 필요합니다.")
        return redirect('manager:manager_login')
    """
    등급별 분포 상세 페이지 (시설 목록 표시)
    """
    # 필터 파라미터
    year_filter = request.GET.get('year', '')
    region_filter = request.GET.get('region', '')
    sport_filter = request.GET.get('sport', '')
    grade_filter = request.GET.get('grade', '')  # 양호, 주의, 경고, 사용중지
    
    # 페이징 파라미터
    per_page = int(request.GET.get("per_page", 15))
    page = int(request.GET.get("page", 1))
    
    # 옵션 리스트
    years = []
    regions = []
    sports = []
    grades = ['양호', '주의', '경고']
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        try:
            facilities = Facility.objects.exclude(schk_visit_ymd__isnull=True).exclude(schk_visit_ymd='')
            
            # 연도 필터링 (2000~2025년만)
            facilities = facilities.extra(
                where=["SUBSTRING(schk_visit_ymd, 1, 4) >= '2000' AND SUBSTRING(schk_visit_ymd, 1, 4) <= '2025'"]
            )
            
            # 필터 적용
            if year_filter:
                facilities = facilities.filter(schk_visit_ymd__startswith=year_filter)
            if region_filter:
                facilities = facilities.filter(cp_nm=region_filter)
            if sport_filter:
                facilities = facilities.filter(fcob_nm=sport_filter)
            if grade_filter:
                facilities = facilities.filter(schk_tot_grd_nm=grade_filter)
            
            # 페이징 적용
            paginator = Paginator(facilities, per_page)
            page_obj = paginator.get_page(page)
            
            # 페이지 블록 계산
            block_size = 10
            current_block = (page - 1) // block_size
            block_start = current_block * block_size + 1
            block_end = min(block_start + block_size - 1, paginator.num_pages)
            block_range = range(block_start, block_end + 1)
            
            # 시설 목록 생성 (values()로 성능 개선)
            start_index = (page_obj.number - 1) * per_page
            facilities_list = []
            
            for idx, fac in enumerate(page_obj.object_list):
                # 점검일자 포맷팅
                visit_date = fac.schk_visit_ymd
                if visit_date and len(visit_date) == 8:
                    visit_date_formatted = f"{visit_date[:4]}-{visit_date[4:6]}-{visit_date[6:8]}"
                else:
                    visit_date_formatted = visit_date or '-'
                
                facilities_list.append({
                    'faci_cd': fac.faci_cd,
                    'faci_nm': fac.faci_nm or '-',
                    'cp_nm': fac.cp_nm or '-',
                    'fcob_nm': fac.fcob_nm or '-',
                    'faci_road_addr': fac.faci_road_addr or fac.faci_addr or '-',
                    'schk_visit_ymd': visit_date_formatted,
                    'schk_tot_grd_nm': fac.schk_tot_grd_nm or '-',
                    'faci_stat_nm': fac.faci_stat_nm or '-',  # 시설 상태 (사유로 활용)
                    'faci_tel_no': fac.faci_tel_no or '-',
                    'row_no': start_index + idx + 1,
                })
            
            # 옵션 리스트 생성 (2000~2025년만)
            all_facilities = Facility.objects.exclude(schk_visit_ymd__isnull=True).exclude(schk_visit_ymd='')
            if all_facilities.exists():
                df_all = read_frame(all_facilities.values('schk_visit_ymd'))
                if not df_all.empty:
                    df_all['year'] = df_all['schk_visit_ymd'].str[:4]
                    # 연도 유효성 검사 (2000~2025년만)
                    df_all['year_int'] = pd.to_numeric(df_all['year'], errors='coerce')
                    valid_years = df_all[(df_all['year_int'] >= 2000) & (df_all['year_int'] <= 2025)]['year'].unique()
                    years = sorted(valid_years.tolist(), reverse=True)
            
            all_regions = Facility.objects.exclude(cp_nm__isnull=True).exclude(cp_nm='')
            regions = list(all_regions.values_list('cp_nm', flat=True).distinct())
            
            all_sports = Facility.objects.exclude(fcob_nm__isnull=True).exclude(fcob_nm='')
            sports = list(all_sports.values_list('fcob_nm', flat=True).distinct())
            
        except Exception as e:
            print(f"[등급별 상세] 오류: {e}")
            pass
    except Exception:
        pass
    
    context = {
        'facilities_list': facilities_list,
        'page_obj': page_obj,
        'paginator': paginator,
        'per_page': per_page,
        'block_range': block_range,
        'years': years,
        'regions': regions,
        'sports': sports,
        'grades': grades,
        'selected_year': year_filter,
        'selected_region': region_filter,
        'selected_sport': sport_filter,
        'selected_grade': grade_filter,
    }
    
    return render(request, 'manager/facility_inspection_grade_detail.html', context)

def reservation_list_manager(request):
    """
    관리자용 예약 목록 페이지
    - facility_id: 시설 ID (선택)
    - type: 'today' (금일 활성 예약) 또는 'all' (누적 예약)
    """
    # 관리자 권한 확인
    if not is_manager(request):
        messages.error(request, "관리자 권한이 필요합니다.")
        return redirect('manager:manager_login')
    
    # 필터 파라미터
    facility_id = request.GET.get("facility_id", "")
    reservation_type = request.GET.get("type", "all")  # 'today' or 'all'
    status = request.GET.get("status", "active")  # 'active' (예약완료) or 'cancelled' (예약취소)
    sort_by = request.GET.get("sort", "reg_date")  # 'reg_date' or 'timeslot'
    search_type = request.GET.get("search_type", "reservation_num")  # 'reservation_num', 'member_id', 'member_name'
    search_keyword = request.GET.get("search_keyword", "")
    per_page = int(request.GET.get("per_page", 15))
    page = int(request.GET.get("page", 1))
    
    # 오늘 날짜
    today = timezone.now().date()
    
    # 예약 조회 (TimeSlot을 통해 시설과 연결)
    queryset = Reservation.objects.filter(
        timeslot__isnull=False
    ).select_related('member').distinct()
    
    # 상태 필터 (누적 예약일 때만 적용, 금일 활성 예약은 항상 예약완료만)
    if reservation_type == 'all':
        if status == 'cancelled':
            queryset = queryset.filter(delete_yn=1)  # 취소된 예약만
        else:
            queryset = queryset.filter(delete_yn=0)  # 예약완료만 (기본값)
    else:
        # 금일 활성 예약은 항상 예약완료만
        queryset = queryset.filter(delete_yn=0)
    
    # 시설 필터
    if facility_id:
        try:
            facility = FacilityInfo.objects.get(facility_id=facility_id)
            queryset = queryset.filter(timeslot__facility_id=facility)
        except FacilityInfo.DoesNotExist:
            messages.error(request, "시설을 찾을 수 없습니다.")
            return redirect('manager:facility_list')
    
    # 타입 필터 (금일 활성 예약)
    if reservation_type == 'today':
        queryset = queryset.filter(reg_date__date=today)
    
    # 누적 예약 (type='all')은 reg_date__date__lte=today 조건 추가
    else:
        queryset = queryset.filter(reg_date__date__lte=today)
    
    # 검색 필터
    if search_keyword:
        if search_type == 'reservation_num':
            queryset = queryset.filter(reservation_num__icontains=search_keyword)
        elif search_type == 'member_id':
            queryset = queryset.filter(member__user_id__icontains=search_keyword)
        elif search_type == 'member_name':
            queryset = queryset.filter(member__nickname__icontains=search_keyword)
    
    # 정렬
    if sort_by == 'timeslot':
        # 시설 예약 시간 순 (TimeSlot의 date, start_time 기준)
        queryset = queryset.order_by('timeslot__date', 'timeslot__start_time')
    else:
        # 예약 발생 시간 순 (reg_date 기준, default)
        queryset = queryset.order_by('-reg_date')
    
    # 페이징
    paginator = Paginator(queryset, per_page)
    page_obj = paginator.get_page(page)
    
    # 페이지 블록
    block_size = 10
    current_block = (page - 1) // block_size
    block_start = current_block * block_size + 1
    block_end = block_start + block_size - 1
    if block_end > paginator.num_pages:
        block_end = paginator.num_pages
    block_range = range(block_start, block_end + 1)
    
    # 데이터 변환
    start_index = (page_obj.number - 1) * per_page
    reservation_page = []
    
    for idx, reservation in enumerate(page_obj.object_list):
        # 시설 정보 가져오기 (TimeSlot을 통해) - 취소된 예약도 포함
        timeslots = TimeSlot.objects.filter(
            reservation_id=reservation
        ).select_related('facility_id').first()
        
        facility_name = timeslots.facility_id.faci_nm if timeslots and timeslots.facility_id else "미정"
        facility_id_val = timeslots.facility_id.facility_id if timeslots and timeslots.facility_id else ""
        
        # 종목 정보 가져오기 (Facility 모델에서)
        sport_type = "미정"
        if timeslots and timeslots.facility_id and timeslots.facility_id.facility_id:
            try:
                facility = Facility.objects.filter(faci_cd=timeslots.facility_id.facility_id).first()
                if facility and facility.ftype_nm:
                    sport_type = facility.ftype_nm
            except:
                pass
        
        # 이용 시간 정보 (모든 TimeSlot의 시간을 합쳐서 표시) - 취소된 예약도 포함
        time_slots = TimeSlot.objects.filter(
            reservation_id=reservation
        ).order_by('date', 'start_time')
        
        time_info_list = []
        slot_list_for_json = []  # 팝업에서 사용할 상세 시간 정보
        earliest_date = None
        
        for ts in time_slots:
            date_str = ts.date.strftime('%Y-%m-%d') if ts.date else ""
            time_str = f"{ts.start_time}~{ts.end_time}" if ts.start_time and ts.end_time else ""
            if date_str and time_str:
                time_info_list.append(f"{date_str} {time_str}")
            
            # 가장 빠른 예약 날짜 확인 (체크박스 활성화 여부 판단용)
            if not earliest_date and ts.date:
                earliest_date = ts.date
            
            # 팝업용 상세 정보
            slot_list_for_json.append({
                "date": date_str,
                "start": ts.start_time,
                "end": ts.end_time,
                "is_cancelled": (ts.delete_yn == 1),
                "t_id": ts.t_id
            })
        
        time_info = ", ".join(time_info_list) if time_info_list else "미정"
        
        # 오늘 날짜와 비교 (체크박스 활성화 여부)
        is_past = False
        if earliest_date and earliest_date < today:
            is_past = True
        
        # 회원 정보
        member_name = reservation.member.nickname if reservation.member else "알 수 없음"
        member_id = reservation.member.user_id if reservation.member else ""
        
        reservation_page.append({
            "id": reservation.reservation_id,
            "reservation_num": reservation.reservation_num,
            "member_name": member_name,
            "member_id": member_id,
            "facility_name": facility_name,
            "facility_id": facility_id_val,
            "facility_address": timeslots.facility_id.address if timeslots and timeslots.facility_id else "",
            "facility_tel": timeslots.facility_id.tel if timeslots and timeslots.facility_id else "",
            "sport_type": sport_type,
            "time_info": time_info,
            "slot_list": slot_list_for_json,  # 팝업에서 사용할 상세 시간 정보
            "reg_date": reservation.reg_date.strftime('%Y-%m-%d %H:%M') if reservation.reg_date else "",
            "delete_date": reservation.delete_date.strftime('%Y-%m-%d %H:%M') if reservation.delete_date else "",
            "delete_yn": reservation.delete_yn,  # 예약 상태 (0: 예약완료, 1: 취소)
            "is_past": is_past,  # 예약 날짜가 지났는지 여부
            "row_no": start_index + idx + 1,
        })
    
    # 시설 정보 (필터용)
    facility_info = None
    if facility_id:
        try:
            facility_info = FacilityInfo.objects.get(facility_id=facility_id)
        except FacilityInfo.DoesNotExist:
            pass
    
    context = {
        "page_obj": page_obj,
        "per_page": per_page,
        "facility_id": facility_id,
        "reservation_type": reservation_type,
        "status": status,
        "sort_by": sort_by,
        "search_type": search_type,
        "search_keyword": search_keyword,
        "facility_info": facility_info,
        "reservation_json": json.dumps(reservation_page, ensure_ascii=False),
        "block_range": block_range,
    }
    
    return render(request, "manager/reservation_list_manager.html", context)

# 모집글관리
def recruitment_manager(request):
    # 관리자 권한 확인
    if not is_manager(request):
        messages.error(request, "관리자 권한이 필요합니다.")
        return redirect('manager:manager_login')
    # DB에서 모집글 조회 (삭제된 것도 포함)
    try:
        queryset = Community.objects.select_related('member_id') \
        .order_by(
            Case(
                When(delete_date__isnull=True, then=Value(0)),  # 삭제 안된 글 → 우선
                default=Value(1),                               # 삭제된 글 → 뒤로
                output_field=IntegerField()
            ),
            '-reg_date'  # 그 안에서 최신순
        )
    except Exception:
        queryset = []
    
    per_page = int(request.GET.get("per_page", 15))

    try:
        page = int(request.GET.get("page", 1))
        if page < 1:
            page = 1
    except:
        page = 1

    paginator = Paginator(queryset, per_page)
    page_obj = paginator.get_page(page)

    # 페이지 블록
    block_size = 5
    current_block = (page - 1) // block_size
    block_start = current_block * block_size + 1
    block_end = min(block_start + block_size - 1, paginator.num_pages)

    # facility_json 형식으로 데이터 변환
    start_index = (page_obj.number - 1) * per_page
    facility_page = []
    
    for idx, community in enumerate(page_obj.object_list):
        delete_date_str = None
        if community.delete_date:
            # 이미 한국 시간으로 저장되어 있음
            delete_date_str = community.delete_date.strftime('%Y-%m-%d %H:%M')
        
        facility_page.append({
            "id": community.community_id,
            "title": community.title,
            "author": community.member_id.user_id if community.member_id else "",
            "row_no": start_index + idx + 1,
            "delete_date": delete_date_str,
        })

    context = {
        "page_obj": page_obj,
        "per_page": per_page,
        "facility_json": json.dumps(facility_page, ensure_ascii=False),
        "block_range": range(block_start, block_end + 1),
    }
    return render(request, 'manager/recruitment_manager.html', context)

# 모집글 상세페이지
def recruitment_detail(request, id):
    # 관리자 권한 확인
    if not is_manager(request):
        messages.error(request, "관리자 권한이 필요합니다.")
        return redirect('manager:manager_login')

    # 모집글 조회
    try:
        recruit = Community.objects.get(
            pk=id
        )
    except Community.DoesNotExist:
        raise Http404("관리자에 의해 삭제된 모집글입니다.")

    # 참여자 목록
    joins_qs = JoinStat.objects.filter(community_id=recruit)
    waiting_count= joins_qs.count()
    # 승인된 인원만 count
    approved_count = joins_qs.filter(join_status=1).count()
    capacity = recruit.num_member or 0

    # -------------------------
    # 🔥 자동 마감 처리 로직 (핵심)
    # -------------------------
    end_status, created = EndStatus.objects.get_or_create(
        community=recruit,
        defaults={
            "end_set_date": timezone.now().date(),
            "end_stat": 0,
        }
    )

    # 승인된 인원이 정원 이상이면 자동 마감
    if approved_count >= capacity and capacity > 0:
        if end_status.end_stat != 1:  
            end_status.end_stat = 1
            end_status.end_date = timezone.now().date()
            end_status.save()

    # -------------------------
    # 최종 마감 여부
    # -------------------------
    is_closed = (end_status.end_stat == 1)



    # 상세 참여 리스트 (owner/관리자만)
    join_list = []
    join_list = (
        joins_qs
        .select_related("member_id")
        .order_by("join_status", "member_id__user_id")
    )

    comment_objs = Comment.objects.select_related('member_id').filter(
            community_id=recruit
        ).order_by('reg_date')
        
    comments = []
    for comment_obj in comment_objs:
        comment_author = comment_obj.member_id.nickname if comment_obj.member_id and hasattr(comment_obj.member_id, 'nickname') else '알 수 없음'
        comment_is_admin = comment_obj.member_id.manager_yn == 1 if comment_obj.member_id else False
        is_deleted = comment_obj.delete_date is not None
        comment = "관리자에 의해 삭제된 댓글입니다." if comment_obj.delete_date else comment_obj.comment
        
        comments.append({
            'comment_id': comment_obj.comment_id,
            'comment': comment,
            'author': comment_author,
            'is_admin': comment_is_admin,
            'reg_date': comment_obj.reg_date,
            'is_deleted': is_deleted,
            
        })

    context = {
        "recruit": recruit,
        "is_manager": is_manager,
        "join_list": join_list,
        "approved_count": approved_count,
        "capacity": capacity,
        "is_closed": is_closed,
        "comments": comments,
        "waiting_rejected_count":waiting_count,
    }

    return render(request, "manager/recruitment_manager_detail.html", context)


@csrf_exempt
def delete_articles(request):
    """게시글 일괄 삭제 API (Article)"""
    if request.method != "POST":
        return JsonResponse({"status": "error", "msg": "POST만 가능"}, status=405)
    
    # 관리자 체크
    if not request.session.get('manager_id'):
        return JsonResponse({"status": "error", "msg": "관리자 권한이 필요합니다."}, status=403)
    
    try:
        data = json.loads(request.body)
        article_ids = data.get("ids", [])
        #board_type = data.get("board_type", "")  # 'notice', 'event', 'post'
        
        if not article_ids:
            return JsonResponse({"status": "error", "msg": "삭제할 항목 없음"})
        
        # 게시판 확인
        # try:
        #     board = get_board_by_name(board_type)
        # except Exception:
        #     return JsonResponse({"status": "error", "msg": f"잘못된 게시판 타입: {board_type}"})
        
        # 게시글 조회 및 삭제 처리
        articles = Article.objects.filter(
            article_id__in=article_ids
            #,board_id=board
        )
        
        deleted_count = 0
        now = datetime.now()  # 한국 시간으로 저장
        
        for article in articles:
            if article.delete_date is None:  # 아직 삭제되지 않은 경우만
                article.delete_date = now
                article.save(update_fields=['delete_date'])
                deleted_count += 1
        
        return JsonResponse({
            "status": "ok",
            "deleted": deleted_count,
            "total": len(article_ids)
        })
    
    except Exception as e:
        import traceback
        print(f"[ERROR] delete_articles 오류: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({"status": "error", "msg": str(e)})

@csrf_exempt
def hard_delete_articles(request):
    """게시글 일괄 영구 삭제 (Article)"""
    if request.method != "POST":
        return JsonResponse({"status": "error", "msg": "POST만 가능"}, status=405)
    
    # 관리자 체크
    if not request.session.get('manager_id'):
        return JsonResponse({"status": "error", "msg": "관리자 권한이 필요합니다."}, status=403)
    
    try:
        data = json.loads(request.body)
        article_ids = data.get("ids", [])
        #board_type = data.get("board_type", "")  # 'notice', 'event', 'post'
        
        if not article_ids:
            return JsonResponse({"status": "error", "msg": "영구 삭제할 항목 없음"})
        
        # 게시판 확인
        # try:
        #     board = get_board_by_name(board_type)
        # except Exception:
        #     return JsonResponse({"status": "error", "msg": f"잘못된 게시판 타입: {board_type}"})
        
        # 게시글 조회 및 삭제 처리
        articles = Article.objects.filter(
            article_id__in=article_ids
            #,board_id=board
        )
        
        deleted_count, _ = articles.delete()

        return JsonResponse({
            "status": "ok",
            "deleted": deleted_count,
            "total": len(article_ids)
        })
    
    except Exception as e:
        import traceback
        print(f"[ERROR] hard_delete_articles 오류: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({"status": "error", "msg": str(e)})

@csrf_exempt
def restore_articles(request):
    """게시글 일괄 복구 (Article)"""
    if request.method != "POST":
        return JsonResponse({"status": "error", "msg": "POST만 가능"}, status=405)
    
    # 관리자 체크
    if not request.session.get('manager_id'):
        return JsonResponse({"status": "error", "msg": "관리자 권한이 필요합니다."}, status=403)
    
    try:
        data = json.loads(request.body)
        article_ids = data.get("ids", [])
        #board_type = data.get("board_type", "")  # 'notice', 'event', 'post'
        
        if not article_ids:
            return JsonResponse({"status": "error", "msg": "복구할 항목 없음"})
        
        # 게시판 확인
        # try:
        #     board = get_board_by_name(board_type)
        # except Exception:
        #     return JsonResponse({"status": "error", "msg": f"잘못된 게시판 타입: {board_type}"})
        
        # 게시글 조회 및 복구 처리
        articles = Article.objects.filter(
            article_id__in=article_ids
            #,board_id=board
        )
        
        restore_count = 0
        # now = datetime.now()  # 한국 시간으로 저장
        
        for article in articles:
            if article.delete_date:  # 이미 삭제된 경우만
                article.delete_date = None
                article.save(update_fields=['delete_date'])
                restore_count += 1
        
        return JsonResponse({
            "status": "ok",
            "restore": restore_count,
            "total": len(article_ids)
        })
    
    except Exception as e:
        import traceback
        print(f"[ERROR] delete_articles 오류: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({"status": "error", "msg": str(e)})



@csrf_exempt
def delete_communities(request):
    """모집글 일괄 삭제 API (Community)"""
    if request.method != "POST":
        return JsonResponse({"status": "error", "msg": "POST만 가능"}, status=405)
    
    # 관리자 체크
    if not request.session.get('manager_id'):
        return JsonResponse({"status": "error", "msg": "관리자 권한이 필요합니다."}, status=403)
    
    try:
        data = json.loads(request.body)
        community_ids = data.get("ids", [])
        
        if not community_ids:
            return JsonResponse({"status": "error", "msg": "삭제할 항목 없음"})
        
        # 모집글 조회 및 삭제 처리
        communities = Community.objects.filter(community_id__in=community_ids)
        
        deleted_count = 0
        now = datetime.now()  # 한국 시간으로 저장
        
        for community in communities:
            if community.delete_date is None:  # 아직 삭제되지 않은 경우만
                community.delete_date = now
                community.save(update_fields=['delete_date'])
                deleted_count += 1
        
        return JsonResponse({
            "status": "ok",
            "deleted": deleted_count,
            "total": len(community_ids)
        })
    
    except Exception as e:
        print(f"[ERROR] delete_communities 오류: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({"status": "error", "msg": str(e)})

@csrf_exempt
def hard_delete_communities(request):
    """모집글 일괄 삭제 API (Community)"""
    if request.method != "POST":
        return JsonResponse({"status": "error", "msg": "POST만 가능"}, status=405)
    
    # 관리자 체크
    if not request.session.get('manager_id'):
        return JsonResponse({"status": "error", "msg": "관리자 권한이 필요합니다."}, status=403)
    
    try:
        data = json.loads(request.body)
        community_ids = data.get("ids", [])
        
        if not community_ids:
            return JsonResponse({"status": "error", "msg": "삭제할 항목 없음"})
        
        # 모집글 조회 및 삭제 처리
        communities = Community.objects.filter(community_id__in=community_ids)
        
        deleted_count = 0
        
        for community in communities:
            community.delete()
            deleted_count += 1
        
        return JsonResponse({
            "status": "ok",
            "deleted": deleted_count,
            "total": len(community_ids)
        })
    
    except Exception as e:
        print(f"[ERROR] delete_communities 오류: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({"status": "error", "msg": str(e)})


@csrf_exempt
def restore_communities(request):
    """모집글 일괄 복구 (Community)"""
    if request.method != "POST":
        return JsonResponse({"status": "error", "msg": "POST만 가능"}, status=405)
    
    # 관리자 체크
    if not request.session.get('manager_id'):
        return JsonResponse({"status": "error", "msg": "관리자 권한이 필요합니다."}, status=403)
    
    try:
        data = json.loads(request.body)
        community_ids = data.get("ids", [])
        
        if not community_ids:
            return JsonResponse({"status": "error", "msg": "복구할 항목 없음"})
        
        # 삭제된 모집글 조회 및 복구 처리
        communities = Community.objects.filter(community_id__in=community_ids)
        
        restore_count = 0
        # now = datetime.now()  # 한국 시간으로 저장
        
        for community in communities:
            if community.delete_date:  # 이미 삭제된 경우만
                community.delete_date = None
                community.save(update_fields=['delete_date'])
                restore_count += 1
        
        return JsonResponse({
            "status": "ok",
            "restore": restore_count,
            "total": len(community_ids)
        })
    
    except Exception as e:
        print(f"[ERROR] restore_communities 오류: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({"status": "error", "msg": str(e)})


# 배너 관리----------------------------------
def banner_manager(request):
    # 관리자 권한 확인
    if not is_manager(request):
        messages.error(request, "관리자 권한이 필요합니다.")
        return redirect('manager:manager_login')
    
    per_page = int(request.GET.get("per_page", 15))
    page = int(request.GET.get("page", 1))

    # 모델 그대로 가져오기 ( dict로 재조립 절대 안함 )
    queryset = HeroImg.objects.filter(delete_date__isnull=True).order_by('-img_id')

    paginator = Paginator(queryset, per_page)
    page_obj = paginator.get_page(page)

    # row_no 계산 (import 없음)
    start_index = (page_obj.number - 1) * per_page

    # 모델 객체 그대로 사용하면서 row_no만 붙여줌
    for idx, obj in enumerate(page_obj.object_list):
        obj.row_no = start_index + idx + 1

    # 블록 페이징
    block_size = 5
    current_block = (page - 1) // block_size
    block_start = current_block * block_size + 1
    block_end = min(block_start + block_size - 1, paginator.num_pages)

    context = {
        "page_obj": page_obj,
        "banner_list": page_obj.object_list,   # 모델 객체 그대로 전달!
        "per_page": per_page,
        "block_range": range(block_start, block_end + 1),
    }

    return render(request, "manager/banner_manager.html", context)

def banner_detail(request, img_id):
    # 관리자 권한 확인
    if not is_manager(request):
        messages.error(request, "관리자 권한이 필요합니다.")
        return redirect('manager:manager_login')
    banner = get_object_or_404(HeroImg, img_id=img_id, delete_date__isnull=True)
    return render(request, "manager/banner_detail.html", {"banner": banner})


def banner_form(request):
    # 관리자 권한 확인
    if not is_manager(request):
        messages.error(request, "관리자 권한이 필요합니다.")
        return redirect('manager:manager_login')
    
    if request.method == "POST":
        upload_file = request.FILES.get("file")
        title = request.POST.get("title", "").strip()
        context = request.POST.get("context", "").strip()
        img_status = request.POST.get("img_status", "").strip()
        start_date = request.POST.get("start_date") or None
        end_date = request.POST.get("end_date") or None

        # ====== 필수값 검증 ======
        if not upload_file:
            return render(request, "manager/banner_form.html", {
                "alert": "배너 이미지를 첨부해주세요.",
                "title": title,
                "context": context,
                "selected_status": img_status,
                "start_date": start_date,
                "end_date": end_date,
            })

        if img_status == "":
            return render(request, "manager/banner_form.html", {
                "alert": "배너 상태를 선택해주세요.",
                "title": title,
                "context": context,
                "start_date": start_date,
                "end_date": end_date,
            })
        
        if title == "":
            return render(request, "manager/banner_form.html", {
                "alert" : "제목을 입력해주세요.",
                "title": title,
                "context": context,
                "selected_status": img_status,
                "start_date": start_date,
                "end_date": end_date,
            })
        img_status = int(img_status)

        # 기간 지정 아닐 때는 기간 날리기
        if img_status != 1:
            start_date = None
            end_date = None

        # ====== 파일 저장 ======
        save_dir = os.path.join(settings.MEDIA_ROOT, "banners")
        os.makedirs(save_dir, exist_ok=True)

        filename = f"{uuid.uuid4().hex}_{upload_file.name}"
        filepath = os.path.join(save_dir, filename)

        with open(filepath, "wb+") as f:
            for chunk in upload_file.chunks():
                f.write(chunk)

        file_url = f"banners/{filename}"

        HeroImg.objects.create(
            url=file_url,
            title=title,
            context=context,
            img_status=img_status,
            start_date=start_date,
            end_date=end_date,
        )

        return redirect("manager:banner_manager")

    # GET
    return render(request, "manager/banner_form.html")

def banner_edit(request, img_id):
    banner = get_object_or_404(HeroImg, img_id=img_id, delete_date__isnull=True)

    if request.method == "POST":
        upload_file = request.FILES.get("file")
        title = request.POST.get("title")
        context = request.POST.get("context")

        img_status = int(request.POST.get("img_status", 0))
        start_date = request.POST.get("start_date") or None
        end_date = request.POST.get("end_date") or None

        if img_status != 1:
            start_date = None
            end_date = None

        # 삭제 플래그 (X 버튼 또는 새 파일 선택 시 "1")
        delete_flag = request.POST.get("delete_file", "0")

        banner.title = title
        banner.context = context
        banner.img_status = img_status
        banner.start_date = start_date
        banner.end_date = end_date

        # 파일 저장 디렉터리
        save_dir = os.path.join(settings.MEDIA_ROOT, "banners")
        os.makedirs(save_dir, exist_ok=True)

        # 새 파일 업로드 우선 처리
        if upload_file:
            # 기존 파일 삭제
            if banner.url:
                old_path = os.path.join(settings.MEDIA_ROOT, banner.url)
                if os.path.exists(old_path):
                    os.remove(old_path)

            filename = f"{uuid.uuid4().hex}_{upload_file.name}"
            filepath = os.path.join(save_dir, filename)

            with open(filepath, "wb+") as f:
                for chunk in upload_file.chunks():
                    f.write(chunk)

            banner.url = f"banners/{filename}"

        # 새 파일은 없고, delete_flag == "1" 인 경우 → 기존 파일만 삭제
        elif delete_flag == "1":
            # 이미지 삭제 후 새 이미지가 없으면 에러
            messages.error(request, "이미지를 삭제하셨습니다. 새 이미지를 첨부해주세요.")
            return render(request, "manager/banner_edit.html", {"banner": banner})
        # 새 파일도 없고 삭제 플래그도 없는 경우는 그대로 유지

        banner.save()
        return redirect("manager:banner_manager")

    return render(request, "manager/banner_edit.html", {"banner": banner})

def banner_delete(request):
    data = json.loads(request.body)
    ids = data.get("ids", [])

    HeroImg.objects.filter(img_id__in=ids).update(delete_date=timezone.now())

    return JsonResponse({"status": "ok"})


def banner_download(request, img_id):
    banner = get_object_or_404(HeroImg, img_id=img_id, delete_date__isnull=True)

    if not banner.url:
        raise Http404("파일이 없습니다.")

    file_path = os.path.join(settings.MEDIA_ROOT, banner.url)

    if not os.path.exists(file_path):
        raise Http404("파일을 찾을 수 없습니다.")

    return FileResponse(
        open(file_path, "rb"),
        as_attachment=True,
        filename=os.path.basename(file_path),
    )



# 게시판 list
def board_list(request, id):
    # 관리자 권한 확인
    if not is_manager(request):
        messages.error(request, "관리자 권한이 필요합니다.")
        return redirect('manager:manager_login')
    try:
        boardName = Board.objects.filter(board_id=id).values_list('board_name', flat=True).first()
        queryset = Article.objects.select_related('member_id', 'board_id') \
        .filter(board_id=id) \
        .order_by(
            Case(
                When(delete_date__isnull=True, then=Value(0)),  # 삭제 안된 글 → 우선
                default=Value(1),                               # 삭제된 글 → 뒤로
                output_field=IntegerField()
            ),
            '-reg_date'  # 그 안에서 최신순
        )
    except Exception:
        queryset = []
    
    per_page = int(request.GET.get("per_page", 15))

    try:
        page = int(request.GET.get("page", 1))
        if page < 1:
            page = 1
    except:
        page = 1

    paginator = Paginator(queryset, per_page)
    page_obj = paginator.get_page(page)

    # 페이지 블록
    block_size = 5
    current_block = (page - 1) // block_size
    block_start = current_block * block_size + 1
    block_end = min(block_start + block_size - 1, paginator.num_pages)

    # json 형식으로 데이터 변환
    start_index = (page_obj.number - 1) * per_page
    article_list = []
    
    for idx, article in enumerate(page_obj.object_list):
        delete_date_str = None
        if article.delete_date:
            # 이미 한국 시간으로 저장되어 있음
            delete_date_str = article.delete_date.strftime('%Y-%m-%d %H:%M')
        
        article_list.append({
            "id": article.article_id,
            "title": article.title,
            "author": article.member_id.user_id if article.member_id else "",
            "row_no": start_index + idx + 1,
            "delete_date": delete_date_str,
            "boardId" : id
        })

    context = {
        "page_obj": page_obj,
        "per_page": per_page,
        "boardName":boardName,
        "article_list": json.dumps(article_list, ensure_ascii=False),
        "block_range": range(block_start, block_end + 1),
        "boardId":id
    }

    return render(request, 'manager/board_list.html', context)

# 게시글 등록 & 수정
def board_write(request, id, pk=None):
    # 관리자 권한 확인
    if not is_manager(request):
        messages.error(request, "관리자 권한이 필요합니다.")
        return redirect('manager:manager_login')
    if pk:
        article = get_object_or_404(Article, board_id=id, article_id=pk)
        start_date_str = ""
        end_date_str = ""

        if article.start_date:
            start_date_str = article.start_date.strftime("%Y-%m-%dT%H:%M")

        if article.end_date:
            end_date_str = article.end_date.strftime("%Y-%m-%dT%H:%M")
        # GET = 수정 페이지 열기
        if request.method == "GET":
            context = {
                "article": article,
                "existing_files": get_existing_files(pk),
                "start_date": start_date_str,
                "end_date" : end_date_str,
                "is_edit": True,
                "boardId": id,
                "boardName": article.board_id.board_name,
            }
            return render(request, "manager/board_write.html", context)

        # POST = 실제 수정 처리
        elif request.method == "POST":
            return update_article(request, article, id, pk)

    else:
        # GET = 빈 글쓰기 폼
        if request.method == "GET":
            boardName = get_object_or_404(Board, board_id=id)
            context = {
                "boardId": id,
                "boardName": boardName,
                "is_edit": False
            }
            return render(request, "manager/board_write.html", context)

        # POST = 새 글 등록 처리
        elif request.method == "POST":
            return create_article(request, id)

# 파일 있는지 확인
def get_existing_files(article_id):
    add_info_objs = AddInfo.objects.filter(article_id=article_id)
    files = []

    for add_info in add_info_objs:
        ext = os.path.splitext(add_info.file_name)[1].lower()
        files.append({
            'id': add_info.add_info_id,
            'name': add_info.file_name,
            'url': f"{settings.MEDIA_URL}{add_info.path}",
            'is_image': ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        })
    return files


# 게시글 등록
def create_article(request, board_id):
    title = request.POST.get('title')
    contents = request.POST.get('context')

    board = get_object_or_404(Board, board_id=board_id)

    article = Article(
        title=title,
        contents=contents,
        board_id=board,
        member_id=Member.objects.get(member_id=request.session.get("manager_id"))
    )

    # 공지사항(board_id=2)일 때만 적용
    if board_id == 2:
        notice_type = request.POST.get('notice_type')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        pin_top = request.POST.get('pin_top', '0')

        always_on = 0 if notice_type == 'always' else 1
        if pin_top == '1':
            always_on = 0

        article.always_on = always_on
        article.start_date = parse_datetime(start_date) if start_date else None
        article.end_date = parse_datetime(end_date) if end_date else None

    article.save()

    # 파일 업로드
    upload_files(request, article, file_field="file", sub_dir="uploads/articles")

    messages.success(request, "등록되었습니다.")
    return redirect('manager:board_detail', pk=article.article_id)

# 게시글 수정
def update_article(request, article, board_id, pk):
    title = request.POST.get('title')
    contents = request.POST.get('context')

    article.title = title
    article.contents = contents

    if board_id == 2:
        notice_type = request.POST.get('notice_type')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        pin_top = request.POST.get('pin_top', '0')

        always_on = 0 if notice_type == 'always' else 1
        print("notice_type : ", notice_type)
        print("always_on : ", always_on)

        article.always_on = always_on
        article.start_date = parse_datetime(start_date) if start_date else None
        article.end_date = parse_datetime(end_date) if end_date else None

    article.save()

    # 기존 파일 삭제
    delete_ids = request.POST.getlist("delete_files")
    if delete_ids:
        files_to_delete = AddInfo.objects.filter(add_info_id__in=delete_ids)
        for f in files_to_delete:
            if f.path:
                file_path = os.path.join(settings.MEDIA_ROOT, f.path)
                if os.path.exists(file_path):
                    os.remove(file_path)
        files_to_delete.delete()

    # 새 파일 업로드
    upload_files(request, article, file_field="file", sub_dir="uploads/articles")

    messages.success(request, "수정되었습니다.")
    return redirect('manager:board_detail',pk=pk)



# 게시글 상세페이지
def board_detail(request, pk):
    # 관리자 권한 확인
    if not is_manager(request):
        messages.error(request, "관리자 권한이 필요합니다.")
        return redirect('manager:manager_login')
    article = get_object_or_404(Article, article_id=pk)
    memberNm = get_object_or_404(Member, member_id = article.member_id_id ).nickname

    board_type = article.board_id.board_name  # notice / event / post

    # 파일 로딩
    add_info = AddInfo.objects.filter(article_id=pk)
    files = []
    images = []
    for f in add_info:
        ext = os.path.splitext(f.file_name)[1].lower()
        info = {
            "url": f"{settings.MEDIA_URL}{f.path}",
            "name": f.file_name,
            "is_image": ext in ['.jpg', '.jpeg', '.png', '.gif'],
            "add_info_id" : f.add_info_id,
            "file_name" : f.file_name
        }
        if info["is_image"]:
            images.append(info)
        else:
            files.append(info)
    comment_objs = Comment.objects.select_related('member_id').filter(
        article_id = pk
    ).order_by('reg_date')
        
    comments = []
    for comment_obj in comment_objs:
        comment_author = comment_obj.member_id.nickname if comment_obj.member_id and hasattr(comment_obj.member_id, 'nickname') else '알 수 없음'
        comment_is_admin = comment_obj.member_id.manager_yn == 1 if comment_obj.member_id else False
        is_deleted = comment_obj.delete_date is not None
        comment = "관리자에 의해 삭제된 댓글입니다." if comment_obj.delete_date else comment_obj.comment
        
        comments.append({
            'comment_id': comment_obj.comment_id,
            'comment': comment,
            'author': comment_author,
            'is_admin': comment_is_admin,
            'reg_date': comment_obj.reg_date,
            'is_deleted': is_deleted,
            
        })
    return render(request, "manager/board_manager_detail.html", {
        "article": article,
        "author" : memberNm,
        "board_type": board_type,
        "files": files,
        "images": images,
        "comments" : comments
    })

def facility_file_download(request, file_id):
    """
    Facility 첨부파일 다운로드 (원본 파일명으로 저장되도록)
    """
    file_obj = get_object_or_404(AddInfo, add_info_id=file_id)

    # 실제 파일 경로 (AddInfo.path 안에 이미 encoded_name까지 들어있음)
    file_path = os.path.join(settings.MEDIA_ROOT, file_obj.path)

    if not os.path.exists(file_path):
        raise Http404("파일을 찾을 수 없습니다.")

    original_name = file_obj.file_name or os.path.basename(file_path)

    # ❗ Django 5.x 에서 제일 깔끔한 방법
    return FileResponse(
        open(file_path, "rb"),
        as_attachment=True,          # 무조건 다운로드
        filename=original_name,      # 여기 이름이 저장창에 뜸 (한글도 OK)
    )

def logout(request):
    """
    로그아웃 처리
    - 카카오 로그인 사용자: 세션 삭제 후 카카오 로그아웃 페이지로 이동
    - 일반 로그인 사용자: 세션 삭제 후 메인 페이지로 이동
    """
    # 로그인하지 않은 경우
    if not request.session.get('user_id'):
        return redirect('/')
    
    # 카카오 로그인 사용자 여부 확인
    is_kakao_user = request.session.get('is_kakao_user', False)
    if not is_kakao_user:
        user_id = request.session.get('user_id', '')
        is_kakao_user = user_id.startswith('kakao_') if user_id else False
    
    # 카카오 로그인 사용자인 경우: 세션 먼저 삭제 후 카카오 로그아웃 페이지로 이동
    if is_kakao_user:
        # 세션의 모든 키를 명시적으로 삭제
        session_keys = list(request.session.keys())
        for key in session_keys:
            del request.session[key]
        
        # 세션 완전히 삭제
        request.session.flush()
        request.session.set_expiry(0)
        
        KAKAO_REST_API_KEY = os.getenv('KAKAO_REST_API_KEY')
        if KAKAO_REST_API_KEY:
            # 카카오 로그아웃 후 메인 페이지로 돌아옴 (세션은 이미 삭제됨)
            kakao_logout_url = (
                "https://kauth.kakao.com/oauth/logout"
                f"?client_id={KAKAO_REST_API_KEY}"
                f"&logout_redirect_uri={request.build_absolute_uri('/')}"
            )
            return redirect(kakao_logout_url)
    
    # 일반 로그인 사용자: 세션 삭제 후 메인 페이지로
    # 세션의 모든 키를 명시적으로 삭제
    session_keys = list(request.session.keys())
    for key in session_keys:
        del request.session[key]
    
    # 세션 완전히 삭제
    request.session.flush()
    
    # 세션 쿠키도 삭제하기 위해 만료 시간 설정
    request.session.set_expiry(0)
    
    messages.success(request, "로그아웃되었습니다.")
    return redirect('manager:manager_login')


def member_list(request):
    # 관리자 권한 확인
    if not is_manager(request):
        messages.error(request, "관리자 권한이 필요합니다.")
        return redirect('manager:manager_login')
    
    members = Member.objects.all().order_by('delete_yn', 'member_id')
    search = request.GET.get("search", "name")
    q = request.GET.get("q", "")
    member_type = request.GET.get("member_type", "")
    per_page = int(request.GET.get("per_page", 15))


    # 검색 기능
    if q:
        if search == "name":
            members = members.filter(name__icontains=q)
        elif search == "user_id":
            members = members.filter(user_id__icontains=q)
        elif search == "nickname":
            members = members.filter(nickname__icontains=q)


    # 회원 유형 필터링
    if member_type == "kakao":
        members = members.filter(user_id__startswith="kakao")
    elif member_type == "normal":
        members = members.exclude(user_id__startswith="kakao")
    elif member_type == 'withdraw':
        members = members.filter(delete_yn__in =  [1,2])


    for m in members:
        a1 = m.addr1 or ""
        a2 = m.addr2 or ""
        a3 = m.addr3 or ""

        a1 = a1.strip()
        a2 = a2.strip()
        a3 = a3.strip()

        # join할 때 None, 공백 제거
        m.full_address = " ".join([p for p in [a1, a2, a3] if p])

    paginator = Paginator(members, per_page)
    page = request.GET.get("page", 1)
    page_obj = paginator.get_page(page)

    page_range = paginator.get_elided_page_range(page_obj.number, on_each_side=2, on_ends=1)
    context = {
        "member_list": page_obj,     
        "page_obj": page_obj,
        "page_range": page_range,
        "per_page": per_page,
        "search": search,
        "q": q,
        "member_type": member_type,
    }

    return render(request, 'manager/member_list.html', context)


def member_delete(request):
    if request.method == "POST":
        ids = request.POST.getlist("ids")  # 선택된 member_id 목록

        if ids:
            # delete_yn = 2 로 변경
            Member.objects.filter(member_id__in=ids).update(delete_yn=2)
            Member.objects.filter(member_id__in=ids).update(delete_date=timezone.now().date())


    messages.success(request, "탈퇴 처리가 완료되었습니다.")
    return redirect("manager:member_list")


def member_restore(request):
    if request.method == "POST":
        ids = request.POST.getlist("ids")

        if ids:
            Member.objects.filter(member_id__in=ids).update(delete_yn=0)
            Member.objects.filter(member_id__in=ids).update(delete_date=None)
            

    messages.success(request, "회원 복구가 완료되었습니다.")
    return redirect("manager:member_list")

        
