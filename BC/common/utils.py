"""공통 유틸리티 함수"""
# TODO: DB 연결 이후 쿼리로 교체하고 삭제 필요 - 더미 데이터 생성 함수들
from datetime import datetime, timedelta
import random
import re

# 모듈 레벨 변수로 캐싱 (한 번 생성 후 재사용)
# TODO: DB 연결 이후 쿼리로 교체하고 삭제 필요
_notice_pinned_posts_cache = None
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
def reset_notice_pinned_posts_cache():
    """공지사항 고정 게시글 캐시 초기화"""
    global _notice_pinned_posts_cache
    _notice_pinned_posts_cache = None


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
    reset_event_pinned_posts_cache()
    reset_post_dummy_list_cache()


# 로그인 체크 함수
# -----------------------------------------------------
from django.shortcuts import redirect

def is_manager(request):
    """현재 로그인한 사용자가 관리자인지 확인 (manager_yn == 1)
    
    Args:
        request: Django request 객체
    
    Returns:
        bool: 관리자이면 True, 아니면 False
    """
    manager_id = request.session.get('manager_id')
    if not manager_id:
        return False
    try:
        from member.models import Member
        member = Member.objects.get(member_id=manager_id)
        return member.manager_yn == 1
    except Member.DoesNotExist:
        return False

def is_admin(member):
    """Member 객체가 관리자인지 확인 (manager_yn == 1)
    
    Args:
        member: Member 모델 인스턴스 또는 None
    
    Returns:
        bool: 관리자이면 True, 아니면 False
    """
    if not member:
        return False
    return member.manager_yn == 1

def check_login(request):
    """로그인 체크 및 리다이렉트
    관리자(manager_yn == 1)는 모든 로그인 검증에서 통과
    카카오 회원가입 미완료 상태에서 다른 페이지로 이동 시 세션 삭제
    """
    # 관리자 체크: 관리자는 로그인 검증 통과
    if is_manager(request):
        return None
    
    # 카카오 회원가입 미완료 상태 체크
    # 회원가입 관련 페이지는 예외 처리
    allowed_paths = ['/signup/', '/terms/', '/login/', '/logout/', '/login/kakao/', '/login/kakao/callback/']
    current_path = request.path
    
    # 카카오 회원가입 모드이고, 허용된 경로가 아니면
    if request.session.get('kakao_signup_mode'):
        if current_path not in allowed_paths:
            # 허용되지 않은 경로로 이동 시 세션 삭제
            request.session.pop('kakao_signup_mode', None)
            request.session.pop('kakao_signup_user_id', None)
            request.session.pop('kakao_signup_name', None)
            request.session.pop('kakao_signup_nickname', None)
            request.session.pop('kakao_id', None)
            from django.contrib import messages
            messages.info(request, "회원가입이 취소되었습니다.")
            return redirect('/')
        # 허용된 경로면 그대로 진행
    
    # 일반 사용자 로그인 체크
    if 'user_id' not in request.session:
        from django.contrib import messages
        messages.error(request, "로그인이 필요합니다.")
        next_url = request.path
        if request.GET:
            next_url += '?' + request.GET.urlencode()
        return redirect(f'/login?next={next_url}')
    return None


# 주소 파싱 함수
# -----------------------------------------------------
def parse_address(address_data, address_detail=""):
    """
    다음 주소 API 데이터를 파싱하여 addr1, addr2, addr3로 분리
    
    Args:
        address_data: 다음 주소 API에서 반환하는 데이터 객체 또는 딕셔너리
        address_detail: 상세주소 (직접 입력)
    
    Returns:
        tuple: (addr1, addr2, addr3)
        - addr1: 시도 (시/도, 군이 있으면 시도+군)
        - addr2: 구 (시군구에서 구 부분만)
        - addr3: 나머지 (도로명주소 + 상세주소)
    
    예시:
        입력: sido="서울특별시", sigungu="강남구", roadAddress="테헤란로 123"
        출력: ("서울특별시", "강남구", "테헤란로 123")
        
        입력: sido="경기도", sigungu="수원시 영통구", roadAddress="광교로 123"
        출력: ("경기도 수원시", "영통구", "광교로 123")
    """
    # 딕셔너리인 경우와 객체인 경우 모두 처리
    if hasattr(address_data, 'sido'):
        sido = address_data.sido
        sigungu = getattr(address_data, 'sigungu', '')
        road_address = getattr(address_data, 'roadAddress', '')
        jibun_address = getattr(address_data, 'jibunAddress', '')
    elif isinstance(address_data, dict):
        sido = address_data.get('sido', '')
        sigungu = address_data.get('sigungu', '')
        road_address = address_data.get('roadAddress', '')
        jibun_address = address_data.get('jibunAddress', '')
    else:
        # 문자열인 경우 파싱 시도
        return _parse_address_string(address_data, address_detail)
    
    # 시도 / 시군구 정리
    sido = sido.strip() if sido else ''
    sigungu = sigungu.strip() if sigungu else ''

    # addr1: 시/도 (광역단위)
    # addr2: 시·군·구 전체 (기초지자체) - 예: "성남시 분당구", "광주시", "강남구"
    addr1 = sido
    addr2 = sigungu
    
    # addr3 구성 (도로명주소 + 상세주소)
    addr3_parts = []
    
    # 도로명주소 사용 (우선)
    if road_address:
        # 도로명주소에서 시도, 시군구 부분 제거
        road_addr = road_address
        # "서울특별시 강남구 테헤란로 123" -> "테헤란로 123"
        if sido and road_addr.startswith(sido):
            road_addr = road_addr[len(sido):].strip()
        if sigungu and road_addr.startswith(sigungu):
            road_addr = road_addr[len(sigungu):].strip()
        
        addr3_parts.append(road_addr)
    
    # 상세주소 추가
    if address_detail:
        addr3_parts.append(address_detail)
    
    addr3 = ' '.join(addr3_parts).strip()
    
    return (addr1, addr2, addr3)


def _parse_address_string(address_str, address_detail=""):
    """
    문자열 주소를 파싱 (레거시 지원)
    """
    if not address_str:
        return ("", "", address_detail)
    
    # 기본 파싱 시도
    parts = address_str.split()
    if len(parts) >= 2:
        addr1 = parts[0]  # 시도
        addr2 = parts[1] if len(parts) > 1 else ""  # 구
        addr3 = ' '.join(parts[2:]) if len(parts) > 2 else ""  # 나머지
        
        if address_detail:
            if addr3:
                addr3 += " " + address_detail
            else:
                addr3 = address_detail
        
        return (addr1, addr2, addr3)
    
    return (address_str, "", address_detail)


# 파일 업로드 처리 함수
# -----------------------------------------------------
import os
import uuid
from django.conf import settings
from django.contrib import messages
from common.models import AddInfo


def handle_file_uploads(request, article):
    """게시글에 첨부된 파일들을 처리하고 AddInfo에 저장
    보안: 이미지(jpg, jpeg, png, gif, bmp, webp) 및 PDF만 허용, 최대 2MB 제한
    
    Args:
        request: Django request 객체
        article: Article 모델 인스턴스
    
    Returns:
        list: 업로드된 파일 정보 리스트
    """
    uploaded_files = []
    
    # 허용된 파일 확장자
    ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.pdf', '.txt', '.hwp', '.docx']
    MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB
    
    print(f"[DEBUG] handle_file_uploads 호출: article_id={article.article_id}")
    
    if 'file' in request.FILES:
        files = request.FILES.getlist('file')
        print(f"[DEBUG] 첨부된 파일 개수: {len(files)}")
        
        # media 디렉토리 생성
        media_dir = settings.MEDIA_ROOT
        upload_dir = os.path.join(media_dir, 'uploads', 'articles')
        print(f"[DEBUG] 업로드 디렉토리: {upload_dir}")
        os.makedirs(upload_dir, exist_ok=True)
        
        for file in files:
            try:
                print(f"[DEBUG] 파일 처리 시작: {file.name}, 크기: {file.size} bytes")
                
                # 파일 확장자 검증
                file_ext = os.path.splitext(file.name)[1].lower()
                if file_ext not in ALLOWED_EXTENSIONS:
                    messages.error(request, f"허용되지 않은 파일 형식입니다: {file.name} (허용: 이미지, PDF)")
                    print(f"[ERROR] 허용되지 않은 파일 형식: {file.name} (확장자: {file_ext})")
                    continue
                
                # 파일 크기 검증 (2MB 제한)
                if file.size > MAX_FILE_SIZE:
                    messages.error(request, f"파일 크기가 너무 큽니다: {file.name} (최대 2MB)")
                    print(f"[ERROR] 파일 크기 초과: {file.name} ({file.size} bytes > {MAX_FILE_SIZE} bytes)")
                    continue
                
                # 파일명 생성 (UUID로 고유성 보장)
                encoded_name = f"{uuid.uuid4()}{file_ext}"
                file_path = os.path.join(upload_dir, encoded_name)
                
                print(f"[DEBUG] 저장 경로: {file_path}")
                
                # 파일 저장
                with open(file_path, 'wb+') as destination:
                    for chunk in file.chunks():
                        destination.write(chunk)
                
                print(f"[DEBUG] 파일 저장 완료: {file_path}")
                
                # 상대 경로 저장 (media/uploads/articles/...)
                relative_path = f"uploads/articles/{encoded_name}"
                print(f"[DEBUG] 상대 경로: {relative_path}, 길이: {len(relative_path)}")
                
                # AddInfo에 저장
                add_info = AddInfo.objects.create(
                    path=relative_path,
                    file_name=file.name,
                    encoded_name=encoded_name,
                    article_id=article,
                )
                
                print(f"[DEBUG] AddInfo 저장 성공: add_info_id={add_info.add_info_id}")
                
                uploaded_files.append({
                    'id': add_info.add_info_id,
                    'name': file.name,
                    'path': relative_path,
                    'url': f"{settings.MEDIA_URL}{relative_path}",
                    'is_image': file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
                })
                
                print(f"[DEBUG] 파일 업로드 성공: {file.name} -> {relative_path}")
                
            except Exception as e:
                import traceback
                print(f"[ERROR] 파일 업로드 실패 ({file.name}): {str(e)}")
                print(traceback.format_exc())
                messages.error(request, f"파일 업로드 실패: {file.name}")
                continue
    else:
        print(f"[DEBUG] request.FILES에 'file' 키가 없음. 사용 가능한 키: {list(request.FILES.keys())}")
    
    print(f"[DEBUG] handle_file_uploads 완료: {len(uploaded_files)}개 파일 업로드됨")
    return uploaded_files



# -----------------------------------------------------
# Facility 대표 이미지 업로드 (UUID 인코딩 저장)
# -----------------------------------------------------
def save_encoded_image(request, instance, field_name="photo", sub_dir="uploads/facility/photo", delete_old=True):
    """
    단일 이미지 업로드 + 인코딩 저장 + AddInfo 저장
    """
    if field_name not in request.FILES:
        return

    upload = request.FILES[field_name]

    allowed_ext = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
    ext = os.path.splitext(upload.name)[1].lower()
    MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB

    # -------------------------
    # 확장자 체크
    # -------------------------
    if ext not in allowed_ext:
        messages.error(request, f"이미지 파일만 업로드 가능합니다: {upload.name}")
        return

    # -------------------------
    # 용량 체크
    # -------------------------
    if upload.size > MAX_FILE_SIZE:
        messages.error(request, f"대표 이미지 용량이 너무 큽니다 (최대 2MB): {upload.name}")
        return

    # -------------------------
    # 기존 파일 삭제
    # -------------------------
    if delete_old:
        old_path = None

        old_file = getattr(instance, field_name, None)
        if old_file:
            old_path = old_file.path

        # AddInfo에 저장된 기존 대표 이미지 삭제
        old_addinfo = AddInfo.objects.filter(facility_id=instance, file_name="대표이미지").first()

        if old_addinfo:
            ai_path = os.path.join(settings.MEDIA_ROOT, old_addinfo.path)
            if os.path.exists(ai_path):
                os.remove(ai_path)
            old_addinfo.delete()

        if old_path and os.path.exists(old_path):
            os.remove(old_path)

    # -------------------------
    # 새 파일 저장
    # -------------------------
    new_name = f"{uuid.uuid4()}{ext}"
    save_dir = os.path.join(settings.MEDIA_ROOT, sub_dir)
    os.makedirs(save_dir, exist_ok=True)

    save_path = os.path.join(save_dir, new_name)

    with open(save_path, "wb+") as dest:
        for chunk in upload.chunks():
            dest.write(chunk)

    # 모델 필드 업데이트
    setattr(instance, field_name, f"{sub_dir}/{new_name}")
    instance.save()

    # AddInfo 기록 생성
    AddInfo.objects.create(
        file_name="대표이미지",
        encoded_name=new_name,
        path=f"{sub_dir}/{new_name}",
        facility_id=instance
    )


# -----------------------------------------------------
# Facility 첨부파일 업로드 (여러 개, AddInfo 저장)
# -----------------------------------------------------
def upload_multiple_files(request, instance, file_field="attachment_files", sub_dir="uploads/facility"):
    """
    여러 개의 첨부파일을 업로드하고 AddInfo 테이블에 저장한다.
    - instance: FacilityInfo 인스턴스 (facility_id FK로 연결)
    - file_field: <input type="file" name="attachment_files" multiple> 의 name
    - sub_dir: MEDIA_ROOT 기준 저장 경로 (예: uploads/facility)
    """
    if file_field not in request.FILES:
        return

    files = request.FILES.getlist(file_field)

    save_dir = os.path.join(settings.MEDIA_ROOT, sub_dir)
    os.makedirs(save_dir, exist_ok=True)

    allowed_exts = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.pdf', '.txt', '.hwp', '.docx']
    MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB 제한

    for f in files:
        ext = os.path.splitext(f.name)[1].lower()

        # 확장자 체크
        if ext not in allowed_exts:
            messages.error(request, f"허용되지 않은 파일 형식입니다: {f.name}")
            continue

        # 용량 체크
        if f.size > MAX_FILE_SIZE:
            messages.error(request, f"파일 크기 초과(2MB): {f.name}")
            continue

        # UUID 파일명 생성
        new_name = f"{uuid.uuid4()}{ext}"
        save_path = os.path.join(save_dir, new_name)

        # 실제 파일 저장
        with open(save_path, "wb+") as dest:
            for chunk in f.chunks():
                dest.write(chunk)

        # AddInfo DB 저장
        AddInfo.objects.create(
            file_name=f.name,
            encoded_name=new_name,
            path=f"{sub_dir}/{new_name}",
            facility_id=instance
        )

# -----------------------------------------------------
# Facility 첨부파일 삭제 (체크된 것만)
# -----------------------------------------------------
def delete_selected_files(request):
    """
    폼에서 넘어온 체크박스(name='delete_file') 목록을 기준으로
    AddInfo + 실제 파일을 삭제한다.
    """
    delete_ids = request.POST.getlist("delete_files")

    for fid in delete_ids:
        try:
            f = AddInfo.objects.get(add_info_id=fid)
        except AddInfo.DoesNotExist:
            continue

        # 물리 파일 삭제
        file_path = os.path.join(settings.MEDIA_ROOT, f.path)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass

        # DB 레코드 삭제
        f.delete()



import os
import uuid
from django.conf import settings
from django.contrib import messages
from common.models import AddInfo


def upload_files(request, instance, file_field="file", sub_dir="uploads/common"):
    """
    다중 파일 업로드 통합 함수
    
    - instance: Article 또는 FacilityInfo 인스턴스
    - file_field: <input type="file" name="file" multiple> 의 name
    - sub_dir: 저장 경로 (예: uploads/articles, uploads/facility)
    """

    if file_field not in request.FILES:
        return []

    files = request.FILES.getlist(file_field)

    save_dir = os.path.join(settings.MEDIA_ROOT, sub_dir)
    os.makedirs(save_dir, exist_ok=True)

    allowed_exts = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.pdf', '.txt', '.hwp', '.docx']
    MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB 제한

    uploaded_files = []

    # instance가 Article인지 FacilityInfo인지 자동 감지
    fk_field = None
    if hasattr(instance, "article_id"):  # Article PK 존재
        fk_field = "article_id"
    elif hasattr(instance, "community_id"):  # Community PK 존재
        fk_field = "community_id"
    elif hasattr(instance, "facility_id") or hasattr(instance, "faci_nm"):
        fk_field = "facility_id"
    else:
        raise Exception("지원되지 않는 모델 타입입니다.")

    for f in files:
        ext = os.path.splitext(f.name)[1].lower()

        # 확장자 체크
        if ext not in allowed_exts:
            messages.error(request, f"허용되지 않은 파일 형식입니다: {f.name}")
            continue

        # 용량 체크
        if f.size > MAX_FILE_SIZE:
            messages.error(request, f"파일 크기 초과(2MB): {f.name}")
            continue

        # UUID 파일명 생성
        new_name = f"{uuid.uuid4()}{ext}"
        save_path = os.path.join(save_dir, new_name)

        # 실제 파일 저장
        with open(save_path, "wb+") as dest:
            for chunk in f.chunks():
                dest.write(chunk)

        # AddInfo 저장
        add_info = AddInfo.objects.create(
            file_name=f.name,
            encoded_name=new_name,
            path=f"{sub_dir}/{new_name}",
            **{fk_field: instance}  # article_id 또는 facility_id 자동 연결
        )

        # 출력용 리스트 저장
        uploaded_files.append({
            "id": add_info.add_info_id,
            "file_name": f.name,
            "encoded_name": new_name,
            "url": f"{settings.MEDIA_URL}{sub_dir}/{new_name}",
            "is_image": ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        })

    return uploaded_files
