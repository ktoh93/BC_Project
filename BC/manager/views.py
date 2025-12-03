import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg, Sum
from django.db import connection
from django.utils import timezone
from datetime import datetime, timedelta
import os
import json
import xmltodict
import pandas as pd
from django_pandas.io import read_frame
from django.contrib import messages
from board.utils import get_category_by_type, get_board_by_name
from django.conf import settings
import uuid
from django.utils.dateparse import parse_datetime
from common.utils import handle_file_uploads, save_encoded_image, upload_multiple_files, delete_selected_files
from django.http import FileResponse, Http404

# models import 
from member.models import Member
from recruitment.models import Community, EndStatus, Rating, JoinStat
from reservation.models import Reservation
from board.models import Article, Board, Category
from common.models import Comment, AddInfo
from manager.models import HeroImg
from facility.models import FacilityInfo


from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404

# 제거예정
from django.views.decorators.csrf import csrf_exempt

# 시설
from facility.models import Facility, FacilityInfo
from reservation.models import Sports



def manager(request):
    """
    관리자 로그인 페이지
    member_id == 1인 계정만 관리자로 인정
    """
    if request.method == "POST":
        admin_id = request.POST.get("admin_id", "").strip()
        admin_pw = request.POST.get("admin_pw", "").strip()
        
        # 입력값 검증
        if not admin_id or not admin_pw:
            return render(request, 'login_manager.html', {
                'error': '아이디와 비밀번호를 입력해주세요.'
            })
        
        try:
            from django.contrib.auth.hashers import check_password
            from member.models import Member
            
            # user_id로 계정 조회
            try:
                admin_user = Member.objects.get(user_id=admin_id)
            except Member.DoesNotExist:
                return render(request, 'login_manager.html', {
                    'error': '존재하지 않는 아이디입니다.'
                })
            
            # 관리자 권한 확인 (member_id == 1만 관리자)
            if admin_user.member_id != 1:
                return render(request, 'login_manager.html', {
                    'error': '관리자 권한이 없습니다.'
                })
            
            # 비밀번호 검증
            if not check_password(admin_pw, admin_user.password):
                return render(request, 'login_manager.html', {
                    'error': '비밀번호가 올바르지 않습니다.'
                })
            
            # 로그인 성공 → 세션에 저장
            request.session['manager_id'] = admin_user.member_id
            request.session['manager_name'] = admin_user.name
            
            return redirect('/manager/dashboard/')
            
        except Exception as e:
            import traceback
            print(f"[ERROR] 관리자 로그인 오류: {str(e)}")
            print(traceback.format_exc())
            return render(request, 'login_manager.html', {
                'error': '로그인 중 오류가 발생했습니다.'
            })
    
    return render(request, 'login_manager.html')


# 시설 추가
def facility(request):
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
    return render(request, "facility_add_manager.html", context)


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
        import traceback
        traceback.print_exc()
        return JsonResponse({"status": "error", "message": str(e)})


# 시설관리
def facility_list(request):

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

    for idx, item in enumerate(page_obj.object_list):
        facility_page.append({
            "id": item.id,
            "name": item.faci_nm,
            "address": item.address,
            "row_no": start_index + idx + 1,
            "facilityCd" : item.facility_id
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

    return render(request, "facility_list_manager.html", context)


# 시설상세보기 
def facility_detail(request, id):
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
    for c in comment_objs:
        comments.append({
            "comment_id": c.comment_id,
            "comment": c.comment,
            "author": c.member_id.nickname if hasattr(c.member_id, 'nickname') else "알 수 없음",
            "is_admin": (c.member_id.member_id == 1 if c.member_id else False),
            "reg_date": c.reg_date,
            "is_deleted": c.delete_date is not None,
        })

    context = {
        "facilityInfo": facilityInfo,
        "facility" : facility,
        "comments" : comments,
        "reservation_list": reservation_list,
    }
    return render(request, "facility_detail.html", context)


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

        return render(request, "facility_write.html", {
            "info": info,
            "files": files,
            "time_json": time_json
        })

    # -----------------------------
    # POST — 실제 저장
    # -----------------------------
    info.tel = request.POST.get("tel", "")
    info.homepage = request.POST.get("homepage", "")

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
    upload_multiple_files(
        request=request,
        instance=info,
        file_field="attachment_files",
        sub_dir="uploads/facility/files"
    )

    messages.success(request, "시설 정보가 수정되었습니다.")
    return redirect("facility_detail", id=info.facility_id)


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
        import traceback; traceback.print_exc()
        return JsonResponse({"status": "error", "msg": str(e)})


def sport_type(request):
    return render(request, 'sport_type_manager.html')



def dashboard(request):
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
    # 7. 평점 통계 (시설명 매칭)
    # ============================================
    region_ratings_dict = {}
    rating_stats = {'avg': 0, 'max': 0, 'min': 0, 'count': 0}
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        try:
            ratings = Rating.objects.all()
            facilities = FacilityInfo.objects.all()
            
            if ratings.exists() and facilities.exists():
                df_ratings = read_frame(ratings.values('facility', 'rated'))
                df_facilities = read_frame(facilities.values('facility_name', 'addr1', 'addr2'))
                
                if not df_ratings.empty and not df_facilities.empty:
                    # 시설명으로 매칭
                    df_merged = df_ratings.merge(
                        df_facilities,
                        left_on='facility',
                        right_on='facility_name',
                        how='left'
                    )
                    
                    # 지역별 평균 평점
                    if 'addr1' in df_merged.columns and 'rated' in df_merged.columns:
                        region_stats = df_merged.groupby('addr1')['rated'].agg(['mean', 'max', 'min'])
                        for region, row in region_stats.iterrows():
                            if pd.notna(region):
                                region_ratings_dict[region] = {
                                    'mean': round(float(row['mean']), 2),
                                    'max': int(row['max']),
                                    'min': int(row['min'])
                                }
                    
                    # 전체 평점 통계
                    rating_stats = {
                        'avg': round(float(df_ratings['rated'].mean()), 2) if not df_ratings.empty else 0,
                        'max': int(df_ratings['rated'].max()) if not df_ratings.empty else 0,
                        'min': int(df_ratings['rated'].min()) if not df_ratings.empty else 0,
                        'count': len(df_ratings)
                    }
        except Exception:
            pass
    except Exception:
        pass
    
    # ============================================
    # 8. 예약 취소율
    # ============================================
    cancellation_rate = 0
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        try:
            total_reservations = Reservation.objects.filter(reg_date__gte=start_date).count()
            cancelled_reservations = Reservation.objects.filter(
                reg_date__gte=start_date,
                delete_yn=1
            ).count()
            
            cancellation_rate = round((cancelled_reservations / total_reservations * 100) if total_reservations > 0 else 0, 2)
        except Exception:
            pass
    except Exception:
        pass
    
    # ============================================
    # 9. 참여율 통계
    # ============================================
    participation_rate = 0
    
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
                df_join = read_frame(join_stats.values('community_id', 'join_status'))
                if not df_join.empty:
                    total_joins = len(df_join)
                    completed_joins = len(df_join[df_join['join_status'] == 1])
                    participation_rate = round((completed_joins / total_joins * 100) if total_joins > 0 else 0, 2)
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
        'region_ratings': json.dumps(region_ratings_dict),
        'rating_stats': rating_stats,
        'cancellation_rate': cancellation_rate,
        'participation_rate': participation_rate,
        'regions': regions,
        'sports': sports,
        'selected_region': region_filter,
        'selected_sport': sport_filter,
        'date_range': date_range,
    }
    
    return render(request, 'dashboard.html', context)


# 종목관리
def sport_add(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "msg": "POST만 가능"}, status=405)

    try:
        data = json.loads(request.body)
        name = data.get("name", "").strip()

        if not name:
            return JsonResponse({"status": "error", "msg": "종목명이 비어있음"})

        # 중복 체크
        if Sports.objects.filter(s_name=name).exists():
            return JsonResponse({"status": "error", "msg": "이미 존재하는 종목"})

        sp = Sports(s_name=name)
        sp.save()

        return JsonResponse({"status": "ok", "id": sp.sports_id, "name": sp.s_name})

    except Exception as e:
        return JsonResponse({"status": "error", "msg": str(e)})
    



# 예약관리
def recruitment_manager(request):
    # DB에서 모집글 조회 (삭제된 것도 포함)
    try:
        queryset = Community.objects.select_related('member_id').all().order_by('-reg_date')
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
    return render(request, 'recruitment_manager.html', context)

def event_manager(request):
    # DB에서 이벤트 조회 (category_type='event', 삭제된 것도 포함)
    try:
        from board.utils import get_category_by_type
        category = get_category_by_type('event')
        queryset = Article.objects.select_related('member_id', 'category_id').filter(
            category_id=category
        ).order_by('-reg_date')
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
    
    for idx, article in enumerate(page_obj.object_list):
        delete_date_str = None
        if article.delete_date:
            # 이미 한국 시간으로 저장되어 있음
            delete_date_str = article.delete_date.strftime('%Y-%m-%d %H:%M')
        
        facility_page.append({
            "id": article.article_id,
            "title": article.title,
            "author": article.member_id.user_id if article.member_id else "",
            "row_no": start_index + idx + 1,
            "delete_date": delete_date_str,
        })

    context = {
        "page_obj": page_obj,
        "per_page": per_page,
        "facility_json": json.dumps(facility_page, ensure_ascii=False),
        "block_range": range(block_start, block_end + 1),
    }

    return render(request, 'event_manager.html', context)


def board_manager(request):
    # DB에서 공지사항 조회 (category_type='notice', 삭제된 것도 포함)
    try:
        from board.utils import get_category_by_type
        category = get_category_by_type('notice')
        queryset = Article.objects.select_related('member_id', 'category_id').filter(
            category_id=category
        ).order_by('-reg_date')
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
    
    for idx, article in enumerate(page_obj.object_list):
        delete_date_str = None
        if article.delete_date:
            # 이미 한국 시간으로 저장되어 있음
            delete_date_str = article.delete_date.strftime('%Y-%m-%d %H:%M')
        
        facility_page.append({
            "id": article.article_id,
            "title": article.title,
            "author": article.member_id.user_id if article.member_id else "",
            "row_no": start_index + idx + 1,
            "delete_date": delete_date_str,
        })

    context = {
        "page_obj": page_obj,
        "per_page": per_page,
        "facility_json": json.dumps(facility_page, ensure_ascii=False),
        "block_range": range(block_start, block_end + 1),
    }

    return render(request, "board_manager.html", context)


# handle_file_uploads_manager 함수는 common/utils.py의 handle_file_uploads로 통합됨

def event_form(request):
    if request.method == "POST":
        title = request.POST.get('title')
        context = request.POST.get('context')
        notice_type = request.POST.get('notice_type')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        pin_top = request.POST.get('pin_top', '0')  # 상단 고정 체크박스
        
        try:
            # category_type='event'로 조회
            category = get_category_by_type('event')
            
            # board_name='event'로 조회
            board = get_board_by_name('event')
            
            # 관리자 계정
            member_id = request.session.get('manager_id', 1)
            try:
                member = Member.objects.get(member_id=member_id)
            except Member.DoesNotExist:
                member = Member.objects.first()
                if not member:
                    messages.error(request, "회원 정보를 찾을 수 없습니다.")
                    return render(request, 'event_form.html')
            
            # always_on 설정
            always_on = 0 if notice_type == 'always' else 1
            if pin_top == '1':
                always_on = 0
            
            from django.utils.dateparse import parse_datetime
            start_datetime = parse_datetime(start_date) if start_date else None
            end_datetime = parse_datetime(end_date) if end_date else None
            
            # DB에 저장
            article = Article.objects.create(
                title=title,
                contents=context,
                member_id=member,
                board_id=board,
                category_id=category,
                always_on=always_on,
                start_date=start_datetime,
                end_date=end_datetime,
            )
            
            # 파일 업로드 처리
            handle_file_uploads(request, article)
            
            print(f"[DEBUG] 이벤트 저장 완료:")
            print(f"  - article_id: {article.article_id}")
            print(f"  - category_id: {category.category_id} (type: {category.category_type})")
            print(f"  - board_id: {board.board_id} (name: {board.board_name})")
            
            messages.success(request, "이벤트가 등록되었습니다.")
            return redirect('/manager/event_manager/')
        except Category.DoesNotExist:
            messages.error(request, "이벤트 카테고리(category_type='event')를 찾을 수 없습니다. 초기 데이터를 생성해주세요.")
        except Board.DoesNotExist:
            messages.error(request, "이벤트 게시판(board_name='event')을 찾을 수 없습니다. 초기 데이터를 생성해주세요.")
        except Exception as e:
            import traceback
            print(f"[ERROR] 이벤트 등록 오류: {str(e)}")
            print(traceback.format_exc())
            messages.error(request, f"이벤트 등록 중 오류가 발생했습니다: {str(e)}")
    
    return render(request, 'event_form.html')

def event_edit(request, article_id):
    """이벤트 게시글 수정"""

    # 관리자 체크
    if not request.session.get('manager_id'):
        messages.error(request, "관리자 권한이 필요합니다.")
        return redirect('/manager/')

    # 기존 이벤트 게시글 로드
    try:
        category = get_category_by_type('event')
        article_obj = Article.objects.get(
            article_id=article_id,
            category_id=category
        )
    except Article.DoesNotExist:
        messages.error(request, "게시글을 찾을 수 없습니다.")
        return redirect('/manager/event_manager/')

    # POST: 수정 처리
    if request.method == "POST":
        title = request.POST.get('title')
        context = request.POST.get('context')
        notice_type = request.POST.get('notice_type')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        pin_top = request.POST.get('pin_top', '0')

        try:
            # always_on 처리
            always_on = 0 if notice_type == 'always' else 1
            if pin_top == '1':
                always_on = 0

            from django.utils.dateparse import parse_datetime
            start_datetime = parse_datetime(start_date) if start_date else None
            end_datetime = parse_datetime(end_date) if end_date else None

            # 필드 업데이트
            article_obj.title = title
            article_obj.contents = context
            article_obj.always_on = always_on
            article_obj.start_date = start_datetime
            article_obj.end_date = end_datetime
            article_obj.save()

            # 새 파일 업로드
            handle_file_uploads(request, article_obj)

            messages.success(request, "이벤트가 수정되었습니다.")

            # 수정 후 관리자 상세 페이지로 이동
            return redirect(f'/manager/detail/{article_id}/')

        except Exception as e:
            import traceback
            print(f"[ERROR] 이벤트 수정 오류: {str(e)}")
            print(traceback.format_exc())
            messages.error(request, f"이벤트 수정 중 오류가 발생했습니다: {str(e)}")

    # GET: 기존 파일 조회
    add_info_objs = AddInfo.objects.filter(article_id=article_id)
    existing_files = []

    for add_info in add_info_objs:
        file_ext = os.path.splitext(add_info.file_name)[1].lower()
        existing_files.append({
            'id': add_info.add_info_id,
            'name': add_info.file_name,
            'url': f"{settings.MEDIA_URL}{add_info.path}",
            'is_image': file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        })

    # 날짜 포맷
    start_date_str = article_obj.start_date.strftime('%Y-%m-%dT%H:%M') if article_obj.start_date else ''
    end_date_str = article_obj.end_date.strftime('%Y-%m-%dT%H:%M') if article_obj.end_date else ''

    context = {
        'article': article_obj,
        'existing_files': existing_files,
        'start_date': start_date_str,
        'end_date': end_date_str,
        'is_edit': True,
    }

    return render(request, 'event_form.html', context)


def post_manager(request):
    # DB에서 자유게시판(post) 조회 (삭제된 것도 포함)
    try:
        from board.utils import get_category_by_type
        category = get_category_by_type('post')
        queryset = Article.objects.select_related('member_id', 'category_id').filter(
            category_id=category
        ).order_by('-reg_date')
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
    
    for idx, article in enumerate(page_obj.object_list):
        delete_date_str = None
        if article.delete_date:
            # 이미 한국 시간으로 저장되어 있음
            delete_date_str = article.delete_date.strftime('%Y-%m-%d %H:%M')
        
        facility_page.append({
            "id": article.article_id,
            "title": article.title,
            "author": article.member_id.user_id if article.member_id else "",
            "row_no": start_index + idx + 1,
            "delete_date": delete_date_str,
        })

    context = {
        "page_obj": page_obj,
        "per_page": per_page,
        "facility_json": json.dumps(facility_page, ensure_ascii=False),
        "block_range": range(block_start, block_end + 1),
    }

    return render(request, 'post_manager.html', context)

def manager_post_detail(request, article_id):
    """관리자 전용 자유게시판 상세 페이지"""
    # 관리자 체크
    if not request.session.get('manager_id'):
        messages.error(request, "관리자 권한이 필요합니다.")
        return redirect('/manager/')
    
    try:
        from board.utils import get_category_by_type
        category = get_category_by_type('post')
        article_obj = Article.objects.select_related('member_id', 'category_id', 'board_id').get(
            article_id=article_id,
            category_id=category
        )
        
        # 댓글 조회
        comment_objs = Comment.objects.select_related('member_id').filter(
            article_id=article_id,
            delete_date__isnull=True
        ).order_by('reg_date')
        
        comments = []
        for comment_obj in comment_objs:
            comment_author = comment_obj.member_id.nickname if comment_obj.member_id and hasattr(comment_obj.member_id, 'nickname') else '알 수 없음'
            comment_is_admin = comment_obj.member_id.member_id == 1 if comment_obj.member_id else False
            comments.append({
                'comment_id': comment_obj.comment_id,
                'comment': comment_obj.comment,
                'author': comment_author,
                'is_admin': comment_is_admin,
                'reg_date': comment_obj.reg_date,
            })
        
        # 작성자 정보
        author_name = article_obj.member_id.nickname if article_obj.member_id and hasattr(article_obj.member_id, 'nickname') else '알 수 없음'
        is_admin = article_obj.member_id.member_id == 1 if article_obj.member_id else False
        
        # 첨부파일 조회
        add_info_objs = AddInfo.objects.filter(article_id=article_id)
        files = []
        images = []
        for add_info in add_info_objs:
            file_ext = os.path.splitext(add_info.file_name)[1].lower()
            is_image = file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
            file_data = {
                'id': add_info.add_info_id,
                'name': add_info.file_name,
                'url': f"{settings.MEDIA_URL}{add_info.path}",
                'is_image': is_image,
            }
            if is_image:
                images.append(file_data)
            else:
                files.append(file_data)
        
        article = {
            'article_id': article_obj.article_id,
            'title': article_obj.title,
            'contents': article_obj.contents if article_obj.contents else '',
            'author': author_name,
            'is_admin': is_admin,
            'date': article_obj.reg_date.strftime('%Y-%m-%d'),
            'views': article_obj.view_cnt,
            'reg_date': article_obj.reg_date,
            'images': images,
            'files': files,
        }
        
        context = {
            'article': article,
            'comments': comments,
            'board_type': 'post',
            'is_manager': True,  # 관리자 페이지임을 표시
        }
        
        return render(request, 'board_detail.html', context)
    except Exception as e:
        import traceback
        print(f"[ERROR] manager_post_detail 오류: {str(e)}")
        print(traceback.format_exc())
        messages.error(request, f"게시글을 불러오는 중 오류가 발생했습니다: {str(e)}")
        return redirect('/manager/post_manager/')

def manager_notice_detail(request, article_id):
    """관리자 전용 공지사항 상세 페이지"""
    # 관리자 체크
    if not request.session.get('manager_id'):
        messages.error(request, "관리자 권한이 필요합니다.")
        return redirect('/manager/')
    
    try:
        from board.utils import get_category_by_type
        category = get_category_by_type('notice')
        article_obj = Article.objects.select_related('member_id', 'category_id', 'board_id').get(
            article_id=article_id,
            category_id=category
        )
        
        # 댓글 조회
        comment_objs = Comment.objects.select_related('member_id').filter(
            article_id=article_id,
            delete_date__isnull=True
        ).order_by('reg_date')
        
        comments = []
        for comment_obj in comment_objs:
            comment_author = comment_obj.member_id.nickname if comment_obj.member_id and hasattr(comment_obj.member_id, 'nickname') else '알 수 없음'
            comment_is_admin = comment_obj.member_id.member_id == 1 if comment_obj.member_id else False
            comments.append({
                'comment_id': comment_obj.comment_id,
                'comment': comment_obj.comment,
                'author': comment_author,
                'is_admin': comment_is_admin,
                'reg_date': comment_obj.reg_date,
            })
        
        # 작성자 정보
        author_name = article_obj.member_id.nickname if article_obj.member_id and hasattr(article_obj.member_id, 'nickname') else '알 수 없음'
        is_admin = article_obj.member_id.member_id == 1 if article_obj.member_id else False
        
        # 첨부파일 조회
        add_info_objs = AddInfo.objects.filter(article_id=article_id)
        files = []
        images = []
        for add_info in add_info_objs:
            file_ext = os.path.splitext(add_info.file_name)[1].lower()
            is_image = file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
            file_data = {
                'id': add_info.add_info_id,
                'name': add_info.file_name,
                'url': f"{settings.MEDIA_URL}{add_info.path}",
                'is_image': is_image,
            }
            if is_image:
                images.append(file_data)
            else:
                files.append(file_data)
        
        article = {
            'article_id': article_obj.article_id,
            'title': article_obj.title,
            'contents': article_obj.contents if article_obj.contents else '',
            'author': author_name,
            'is_admin': is_admin,
            'date': article_obj.reg_date.strftime('%Y-%m-%d'),
            'views': article_obj.view_cnt,
            'reg_date': article_obj.reg_date,
            'images': images,
            'files': files,
        }
        
        context = {
            'article': article,
            'comments': comments,
            'board_type': 'notice',
            'is_manager': True,  # 관리자 페이지임을 표시
        }
        
        return render(request, 'board_detail.html', context)
    except Exception as e:
        import traceback
        print(f"[ERROR] manager_notice_detail 오류: {str(e)}")
        print(traceback.format_exc())
        messages.error(request, f"게시글을 불러오는 중 오류가 발생했습니다: {str(e)}")
        return redirect('/manager/board_manager/')

def manager_event_detail(request, article_id):
    """관리자 전용 이벤트 상세 페이지"""
    # 관리자 체크
    if not request.session.get('manager_id'):
        messages.error(request, "관리자 권한이 필요합니다.")
        return redirect('/manager/')
    
    try:
        from board.utils import get_category_by_type
        category = get_category_by_type('event')
        article_obj = Article.objects.select_related('member_id', 'category_id', 'board_id').get(
            article_id=article_id,
            category_id=category
        )
        
        # 댓글 조회
        comment_objs = Comment.objects.select_related('member_id').filter(
            article_id=article_id,
            delete_date__isnull=True
        ).order_by('reg_date')
        
        comments = []
        for comment_obj in comment_objs:
            comment_author = comment_obj.member_id.nickname if comment_obj.member_id and hasattr(comment_obj.member_id, 'nickname') else '알 수 없음'
            comment_is_admin = comment_obj.member_id.member_id == 1 if comment_obj.member_id else False
            comments.append({
                'comment_id': comment_obj.comment_id,
                'comment': comment_obj.comment,
                'author': comment_author,
                'is_admin': comment_is_admin,
                'reg_date': comment_obj.reg_date,
            })
        
        # 작성자 정보
        author_name = article_obj.member_id.nickname if article_obj.member_id and hasattr(article_obj.member_id, 'nickname') else '알 수 없음'
        is_admin = article_obj.member_id.member_id == 1 if article_obj.member_id else False
        
        # 첨부파일 조회
        add_info_objs = AddInfo.objects.filter(article_id=article_id)
        files = []
        images = []
        for add_info in add_info_objs:
            file_ext = os.path.splitext(add_info.file_name)[1].lower()
            is_image = file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
            file_data = {
                'id': add_info.add_info_id,
                'name': add_info.file_name,
                'url': f"{settings.MEDIA_URL}{add_info.path}",
                'is_image': is_image,
            }
            if is_image:
                images.append(file_data)
            else:
                files.append(file_data)
        
        article = {
            'article_id': article_obj.article_id,
            'title': article_obj.title,
            'contents': article_obj.contents if article_obj.contents else '',
            'author': author_name,
            'is_admin': is_admin,
            'date': article_obj.reg_date.strftime('%Y-%m-%d'),
            'views': article_obj.view_cnt,
            'reg_date': article_obj.reg_date,
            'images': images,
            'files': files,
        }
        
        context = {
            'article': article,
            'comments': comments,
            'board_type': 'event',
            'is_manager': True,  # 관리자 페이지임을 표시
        }
        
        return render(request, 'board_detail.html', context)
    except Exception as e:
        import traceback
        print(f"[ERROR] manager_event_detail 오류: {str(e)}")
        print(traceback.format_exc())
        messages.error(request, f"게시글을 불러오는 중 오류가 발생했습니다: {str(e)}")
        return redirect('/manager/event_manager/')

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
        board_type = data.get("board_type", "")  # 'notice', 'event', 'post'
        
        if not article_ids:
            return JsonResponse({"status": "error", "msg": "삭제할 항목 없음"})
        
        # 카테고리 확인
        from board.utils import get_category_by_type
        try:
            category = get_category_by_type(board_type)
        except Exception:
            return JsonResponse({"status": "error", "msg": f"잘못된 게시판 타입: {board_type}"})
        
        # 게시글 조회 및 삭제 처리
        articles = Article.objects.filter(
            article_id__in=article_ids,
            category_id=category
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
        import traceback
        print(f"[ERROR] delete_communities 오류: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({"status": "error", "msg": str(e)})

def board_form(request):
    if request.method == "POST":
        title = request.POST.get('title')
        context = request.POST.get('context')
        notice_type = request.POST.get('notice_type')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        pin_top = request.POST.get('pin_top', '0')

        try:
            category = get_category_by_type('notice')
            board = get_board_by_name('notice')

            member_id = request.session.get('manager_id', 1)
            member = Member.objects.get(member_id=member_id)

            always_on = 0 if notice_type == 'always' else 1
            if pin_top == '1':
                always_on = 0

            from django.utils.dateparse import parse_datetime
            start_datetime = parse_datetime(start_date) if start_date else None
            end_datetime = parse_datetime(end_date) if end_date else None

            article = Article.objects.create(
                title=title,
                contents=context,
                member_id=member,
                board_id=board,
                category_id=category,
                always_on=always_on,
                start_date=start_datetime,
                end_date=end_datetime,
            )

            handle_file_uploads(request, article)
            messages.success(request, "공지사항이 등록되었습니다.")
            return redirect('/manager/board_manager/')

        except Exception as e:
            messages.error(request, f"공지사항 등록 중 오류 발생: {e}")

    return render(request, 'board_form.html', {
        'is_edit': False
    })


def board_edit(request, article_id):
    """공지사항 게시글 수정"""

    # 관리자 체크
    if not request.session.get('manager_id'):
        messages.error(request, "관리자 권한이 필요합니다.")
        return redirect('/manager/')
    
    try:
        category = get_category_by_type('notice')
        article_obj = Article.objects.get(
            article_id=article_id,
            category_id=category
        )
    except Article.DoesNotExist:
        messages.error(request, "게시글을 찾을 수 없습니다.")
        return redirect('/manager/board_manager/')
    
    # POST: 수정 처리
    if request.method == "POST":
        title = request.POST.get('title')
        context = request.POST.get('context')
        notice_type = request.POST.get('notice_type')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        pin_top = request.POST.get('pin_top', '0')

        try:
            # always_on 계산
            always_on = 0 if notice_type == 'always' else 1
            if pin_top == '1':
                always_on = 0

            from django.utils.dateparse import parse_datetime
            start_datetime = parse_datetime(start_date) if start_date else None
            end_datetime = parse_datetime(end_date) if end_date else None

            # 게시글 수정
            article_obj.title = title
            article_obj.contents = context
            article_obj.always_on = always_on
            article_obj.start_date = start_datetime
            article_obj.end_date = end_datetime
            article_obj.save()

            # 파일 업로드 처리
            handle_file_uploads(request, article_obj)

            messages.success(request, "공지사항이 수정되었습니다.")
            
            # 수정 후 관리자 상세페이지로 이동
            return redirect(f'/manager/detail/{article_obj.article_id}/')

        except Exception as e:
            import traceback
            print(f"[ERROR] 공지사항 수정 오류: {str(e)}")
            print(traceback.format_exc())
            messages.error(request, f"공지사항 수정 중 오류가 발생했습니다: {str(e)}")

    # GET: 기존 정보 불러오기
    add_info_objs = AddInfo.objects.filter(article_id=article_id)
    
    existing_files = []
    for add_info in add_info_objs:
        file_ext = os.path.splitext(add_info.file_name)[1].lower()
        existing_files.append({
            'id': add_info.add_info_id,
            'name': add_info.file_name,
            'url': f"{settings.MEDIA_URL}{add_info.path}",
            'is_image': file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        })
    
    # 날짜 포맷
    start_date_str = article_obj.start_date.strftime('%Y-%m-%dT%H:%M') if article_obj.start_date else ''
    end_date_str = article_obj.end_date.strftime('%Y-%m-%dT%H:%M') if article_obj.end_date else ''

    context = {
        'article': article_obj,
        'existing_files': existing_files,
        'start_date': start_date_str,
        'end_date': end_date_str,
        'is_edit': True,
    }

    return render(request, 'board_form.html', context)


# 배너 관리----------------------------------
def banner_manager(request):
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

    return render(request, "banner_manager.html", context)

def banner_detail(request, img_id):
    banner = get_object_or_404(HeroImg, img_id=img_id, delete_date__isnull=True)
    return render(request, "banner_detail.html", {"banner": banner})


def banner_form(request):
    if request.method == "POST":
        upload_file = request.FILES.get("file")
        title = request.POST.get("title", "").strip()
        context = request.POST.get("context", "").strip()
        img_status = request.POST.get("img_status", "").strip()
        start_date = request.POST.get("start_date") or None
        end_date = request.POST.get("end_date") or None

        # ====== 필수값 검증 ======
        if not upload_file:
            return render(request, "banner_form.html", {
                "alert": "배너 이미지를 첨부해주세요.",
                "title": title,
                "context": context,
                "selected_status": img_status,
                "start_date": start_date,
                "end_date": end_date,
            })

        if img_status == "":
            return render(request, "banner_form.html", {
                "alert": "배너 상태를 선택해주세요.",
                "title": title,
                "context": context,
                "start_date": start_date,
                "end_date": end_date,
            })
        
        if title == "":
            return render(request, "banner_form.html", {
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

        return redirect("banner_manager")

    # GET
    return render(request, "banner_form.html")

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
            return render(request, "banner_edit.html", {"banner": banner})
        # 새 파일도 없고 삭제 플래그도 없는 경우는 그대로 유지

        banner.save()
        return redirect("banner_manager")

    return render(request, "banner_edit.html", {"banner": banner})

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



# manager deatil ----
def manager_detail(request, article_id):

    article = Article.objects.get(article_id=article_id)
    board_type = article.board_id.board_name  # notice / event / post

    # 파일 로딩
    add_info = AddInfo.objects.filter(article_id=article_id)
    files = []
    images = []
    for f in add_info:
        ext = os.path.splitext(f.file_name)[1].lower()
        info = {
            "url": f"{settings.MEDIA_URL}{f.path}",
            "name": f.file_name,
            "is_image": ext in ['.jpg', '.jpeg', '.png', '.gif']
        }
        if info["is_image"]:
            images.append(info)
        else:
            files.append(info)

    return render(request, "manager_detail.html/", {
        "article": article,
        "board_type": board_type,
        "files": files,
        "images": images,
    })
