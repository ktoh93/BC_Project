"""공통 유틸리티 함수"""
# TODO: DB 연결 이후 쿼리로 교체하고 삭제 필요 - 더미 데이터 생성 함수들
from datetime import datetime, timedelta
import random

# 모듈 레벨 변수로 캐싱 (한 번 생성 후 재사용)
# TODO: DB 연결 이후 쿼리로 교체하고 삭제 필요
_notice_pinned_posts_cache = None
_recruitment_dummy_list_cache = None
_reservation_dummy_list_cache = None
_notice_dummy_list_cache = None
_event_dummy_list_cache = None
_event_pinned_posts_cache = None
_post_dummy_list_cache = None


# TODO: DB 연결 이후 쿼리로 교체하고 삭제 필요
def get_notice_pinned_posts():
    """공지사항 고정 게시글 생성 (한 번 생성 후 재사용)"""
    global _notice_pinned_posts_cache
    
    # 캐시가 없으면 생성
    if _notice_pinned_posts_cache is None:
        pinned_posts = []
        for i in range(1, 6):
            days_ago = random.randint(0, 30)  # 최근 30일 내
            random_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
            pinned_posts.append({
                "id": 1000 + i,  # 고정 게시글은 1000번대 ID
                "title": f"🔒 [중요] 고정 공지사항 {i} - 반드시 확인해주세요",
                "date": random_date,
                "views": random.randint(100, 10000),
                "author": "관리자"
            })
        _notice_pinned_posts_cache = pinned_posts
    
    # 캐시된 데이터의 복사본 반환 (원본 수정 방지)
    return [post.copy() for post in _notice_pinned_posts_cache]


# TODO: DB 연결 이후 쿼리로 교체하고 삭제 필요
def get_recruitment_dummy_list():
    """모집 게시글 더미 리스트 생성 (한 번 생성 후 재사용)"""
    global _recruitment_dummy_list_cache
    
    # 캐시가 없으면 생성
    if _recruitment_dummy_list_cache is None:
        _recruitment_dummy_list_cache = [
            {
                "title": f"테스트 모집글 {i}",
                "date": "2025-11-26",
                "views": i * 3
            }
            for i in range(1, 201)
        ]
    
    # 캐시된 데이터의 복사본 반환 (원본 수정 방지)
    return [item.copy() for item in _recruitment_dummy_list_cache]

# TODO: DB 연결 이후 쿼리로 교체하고 삭제 필요
def get_reservation_dummy_list():
    """모집 게시글 더미 리스트 생성 (한 번 생성 후 재사용)"""
    global _reservation_dummy_list_cache
    
    # 캐시가 없으면 생성
    if _reservation_dummy_list_cache is None:
        _reservation_dummy_list_cache = [
            {
                "facility_num": f"시설 숫자~ {i}",
                "facility_name": "시설명임다~",
                "facility_addr1": "서울특별시",
                "facility_addr2": "양천구",
                "views": i * 3
            }
            for i in range(1, 201)
        ]
    
    # 캐시된 데이터의 복사본 반환 (원본 수정 방지)
    return [item.copy() for item in _reservation_dummy_list_cache]
    



# TODO: DB 연결 이후 쿼리로 교체하고 삭제 필요
def reset_reservation_cache():
    """공지사항 고정 게시글 캐시 초기화"""
    global _reservation_dummy_list_cache
    _reservation_dummy_list_cache = None




# TODO: DB 연결 이후 쿼리로 교체하고 삭제 필요
def reset_notice_pinned_posts_cache():
    """공지사항 고정 게시글 캐시 초기화"""
    global _notice_pinned_posts_cache
    _notice_pinned_posts_cache = None


# TODO: DB 연결 이후 쿼리로 교체하고 삭제 필요
def reset_recruitment_dummy_list_cache():
    """모집 게시글 더미 리스트 캐시 초기화"""
    global _recruitment_dummy_list_cache
    _recruitment_dummy_list_cache = None


# TODO: DB 연결 이후 쿼리로 교체하고 삭제 필요
def get_notice_dummy_list():
    """공지사항 더미 리스트 생성 (한 번 생성 후 재사용)"""
    global _notice_dummy_list_cache
    
    # 캐시가 없으면 생성
    if _notice_dummy_list_cache is None:
        dummy_list = []
        titles = [
            "공지사항", "안내", "업데이트", "변경사항", "중요 공지",
            "시스템 점검", "이벤트 안내", "서비스 이용", "회원 안내", "정책 변경"
        ]
        authors = ["관리자", "운영팀", "시스템", "고객센터", "할래말래팀"]
        
        for i in range(1, 101):
            random_title = random.choice(titles)
            random_author = random.choice(authors)
            # 랜덤 날짜 생성 (최근 1년 내)
            days_ago = random.randint(0, 365)
            random_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
            
            dummy_list.append({
                "id": i,
                "title": f"{random_title} {i}번째 공지사항입니다",
                "date": random_date,
                "views": random.randint(10, 5000),
                "author": random_author
            })
        _notice_dummy_list_cache = dummy_list
    
    # 캐시된 데이터의 복사본 반환 (원본 수정 방지)
    return [item.copy() for item in _notice_dummy_list_cache]





# TODO: DB 연결 이후 쿼리로 교체하고 삭제 필요
def get_event_dummy_list():
    """이벤트 더미 리스트 생성 (한 번 생성 후 재사용)"""
    global _event_dummy_list_cache
    
    # 캐시가 없으면 생성
    if _event_dummy_list_cache is None:
        dummy_list = []
        titles = [
            "이벤트", "특별 할인", "프로모션", "경품 이벤트", "참여 이벤트",
            "시작 이벤트", "종료 임박", "신규 이벤트", "연말 이벤트", "신년 이벤트"
        ]
        authors = ["이벤트팀", "마케팅팀", "운영팀", "관리자", "할래말래팀"]
        
        for i in range(1, 101):
            random_title = random.choice(titles)
            random_author = random.choice(authors)
            # 랜덤 날짜 생성 (최근 1년 내)
            days_ago = random.randint(0, 365)
            random_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
            
            dummy_list.append({
                "id": i,
                "title": f"{random_title} {i}번째 이벤트가 진행 중입니다!",
                "date": random_date,
                "views": random.randint(10, 5000),
                "author": random_author
            })
        _event_dummy_list_cache = dummy_list
    
    # 캐시된 데이터의 복사본 반환 (원본 수정 방지)
    return [item.copy() for item in _event_dummy_list_cache]


# TODO: DB 연결 이후 쿼리로 교체하고 삭제 필요
def get_event_pinned_posts():
    """이벤트 고정 게시글 생성 (한 번 생성 후 재사용)"""
    global _event_pinned_posts_cache
    
    # 캐시가 없으면 생성
    if _event_pinned_posts_cache is None:
        pinned_posts = []
        for i in range(1, 6):
            days_ago = random.randint(0, 30)  # 최근 30일 내
            random_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
            pinned_posts.append({
                "id": 2000 + i,  # 고정 이벤트는 2000번대 ID
                "title": f"🎉 [진행중] 고정 이벤트 {i} - 지금 바로 참여하세요!",
                "date": random_date,
                "views": random.randint(100, 10000),
                "author": "이벤트팀"
            })
        _event_pinned_posts_cache = pinned_posts
    
    # 캐시된 데이터의 복사본 반환 (원본 수정 방지)
    return [post.copy() for post in _event_pinned_posts_cache]


# TODO: DB 연결 이후 쿼리로 교체하고 삭제 필요
def reset_notice_dummy_list_cache():
    """공지사항 더미 리스트 캐시 초기화"""
    global _notice_dummy_list_cache
    _notice_dummy_list_cache = None


# TODO: DB 연결 이후 쿼리로 교체하고 삭제 필요
def reset_event_dummy_list_cache():
    """이벤트 더미 리스트 캐시 초기화"""
    global _event_dummy_list_cache
    _event_dummy_list_cache = None


# TODO: DB 연결 이후 쿼리로 교체하고 삭제 필요
def reset_event_pinned_posts_cache():
    """이벤트 고정 게시글 캐시 초기화"""
    global _event_pinned_posts_cache
    _event_pinned_posts_cache = None


# TODO: DB 연결 이후 쿼리로 교체하고 삭제 필요
def get_post_dummy_list():
    """자유게시판 더미 리스트 생성 (한 번 생성 후 재사용)"""
    global _post_dummy_list_cache
    
    # 캐시가 없으면 생성
    if _post_dummy_list_cache is None:
        dummy_list = []
        titles = [
            "오늘 운동 어떠셨어요?", "운동 추천 부탁드려요", "함께 운동하실 분 구해요",
            "시설 이용 후기", "운동 팁 공유", "다이어트 성공담", "헬스장 추천",
            "운동 초보 질문", "식단 관리 꿀팁", "운동 동기부여 받고 싶어요",
            "오늘의 운동 인증", "운동 루틴 공유", "부상 예방 방법", "운동화 추천",
            "홈트레이닝 추천", "요가 수업 후기", "필라테스 어때요?", "크로스핏 도전기",
            "마라톤 완주 후기", "수영 배우고 싶어요", "테니스 치실 분", "배드민턴 모임",
            "야구 동호회 모집", "축구 같이 하실 분", "농구 팀원 구해요", "볼링장 추천"
        ]
        authors = [
            "운동러버", "헬스초보", "다이어터", "피트니스매니아", "요가러버",
            "마라토너", "수영러버", "테니스러버", "축구러버", "농구러버",
            "배드민턴러버", "볼링러버", "홈트러버", "필라테스러버", "크로스핏러버",
            "사용자1", "사용자2", "사용자3", "사용자4", "사용자5",
            "운동좋아", "건강관리", "다이어트중", "운동시작", "피트니스"
        ]
        
        for i in range(1, 101):
            random_title = random.choice(titles)
            random_author = random.choice(authors)
            # 랜덤 날짜 생성 (최근 1년 내)
            days_ago = random.randint(0, 365)
            random_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
            
            dummy_list.append({
                "id": i,
                "title": f"{random_title} {i}",
                "date": random_date,
                "views": random.randint(5, 3000),
                "author": random_author
            })
        _post_dummy_list_cache = dummy_list
    
    # 캐시된 데이터의 복사본 반환 (원본 수정 방지)
    return [item.copy() for item in _post_dummy_list_cache]


# TODO: DB 연결 이후 쿼리로 교체하고 삭제 필요
def reset_post_dummy_list_cache():
    """자유게시판 더미 리스트 캐시 초기화"""
    global _post_dummy_list_cache
    _post_dummy_list_cache = None


# TODO: DB 연결 이후 쿼리로 교체하고 삭제 필요
def reset_all_caches():
    """모든 캐시 초기화"""
    reset_notice_pinned_posts_cache()
    reset_recruitment_dummy_list_cache()
    reset_notice_dummy_list_cache()
    reset_event_dummy_list_cache()
    reset_event_pinned_posts_cache()
    reset_post_dummy_list_cache()


# 로그인 체크 함수
# -----------------------------------------------------
from django.shortcuts import redirect

def check_login(request):
    """로그인 체크 및 리다이렉트"""
    if 'user_id' not in request.session:
        next_url = request.path
        if request.GET:
            next_url += '?' + request.GET.urlencode()
        return redirect(f'/login?next={next_url}')
    return None

