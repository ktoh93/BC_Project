import requests
from django.shortcuts import render, redirect
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
from member.models import Member
from recruitment.models import Community, EndStatus, Rating, JoinStat
from reservation.models import Reservation
from board.models import Article, Board
from common.models import Comment
from facility.models import FacilityInfo


def manager(request):
    """
    관리자 로그인 페이지
    TODO: DB 생성 후 실제 검증 로직으로 교체 필요
    """
    if request.method == "POST":
        # 임시 로그인 로직: 버튼만 눌러도 대시보드로 이동
        return redirect('/manager/dashboard/')
    
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
        from django.db import connection
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
        from django.db import connection
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
        from django.db import connection
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
        from django.db import connection
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
        from django.db import connection
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
        from django.db import connection
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
        from django.db import connection
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
        from django.db import connection
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
        from django.db import connection
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