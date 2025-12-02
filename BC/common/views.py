import os
import random
import re
import string

import requests
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from manager.models import HeroImg
from member.models import Member

def index(request):
    # DB에서 랜덤 시설 3개 가져오기
    try:
        from facility.models import FacilityInfo

        all_facilities = FacilityInfo.objects.all()

        if all_facilities.exists():
            facilities_list = list(all_facilities)
            random_facilities = random.sample(facilities_list, min(3, len(facilities_list)))

            facilities = []
            for fac in random_facilities:
                facilities.append({
                    'id': fac.id,
                    'name': fac.faci_nm,
                    'address': fac.address,
                    'description': fac.tel if fac.tel else '시설 정보',
                })
        else:
            facilities = []
    except Exception as e:
        print(f"[ERROR] index 함수 시설 데이터 로드 오류: {str(e)}")
        facilities = []

    now = timezone.now()

    banners = HeroImg.objects.filter(
        delete_date__isnull=True
    ).filter(
        Q(img_status=0) |
        Q(img_status=1, start_date__lte=now, end_date__gte=now)
    ).order_by('-img_id')

    context = {
        'random_facilities': facilities,
        'banners': banners,   # ← 이거 추가!
    }

    return render(request, 'index.html', context)

def login(request):
    if request.method == "POST":
        user_id = request.POST.get("username")
        password = request.POST.get("password")
        remember = request.POST.get("remember")  # 체크박스 여부
        next_url = request.POST.get("next") or request.GET.get("next", "")  # 이전 페이지 URL

        try:
            user = Member.objects.get(user_id=user_id)

        except Member.DoesNotExist:
            messages.error(request, "존재하지 않는 아이디입니다.")
            context = {"next": next_url} if next_url else {}
            return render(request, "login.html", context)

        # 비밀번호 체크
        if not check_password(password, user.password):
            messages.error(request, "비밀번호가 올바르지 않습니다.")
            context = {"next": next_url} if next_url else {}
            return render(request, "login.html", context)

        # 로그인 성공 → 세션에 저장
        request.session["user_id"] = user.user_id
        request.session["user_name"] = user.name
        request.session["nickname"] = user.nickname

        # 관리자 체크 (member_id == 1인 경우)
        if user.member_id == 1:
            request.session["manager_id"] = user.member_id
            request.session["manager_name"] = user.name
            # 로그인 유지 선택 시 세션 만료 시간 변경
            if remember:
                request.session.set_expiry(60 * 60 * 24 * 7)  # 7일 유지
            else:
                request.session.set_expiry(0)  # 브라우저 닫으면 만료
            
            # 이전 페이지가 있으면 그곳으로, 없으면 관리자 대시보드로
            if next_url:
                return redirect(next_url)
            return redirect("/manager/dashboard/")  # 관리자는 관리자 페이지로

        # 일반 사용자
        # 로그인 유지 선택 시 세션 만료 시간 변경
        if remember:
            request.session.set_expiry(60 * 60 * 24 * 7)  # 7일 유지
        else:
            request.session.set_expiry(0)  # 브라우저 닫으면 만료

        # 이전 페이지가 있으면 그곳으로, 없으면 홈으로
        if next_url:
            return redirect(next_url)
        return redirect("/")   # 로그인 후 이동 경로

    # GET 요청: next 파라미터를 템플릿에 전달
    next_url = request.GET.get("next", "")
    context = {"next": next_url} if next_url else {}
    return render(request, "login.html", context)

def logout(request):
    request.session.flush()
    return redirect("/")

def kakao_login(request):
    """카카오 로그인 시작"""
    KAKAO_REST_API_KEY = os.getenv('KAKAO_REST_API_KEY')
    if not KAKAO_REST_API_KEY:
        messages.error(request, "카카오 로그인 설정이 완료되지 않았습니다.")
        return redirect('/login/')
    
    # next 파라미터 처리
    next_url = request.GET.get('next', '')
    if next_url:
        request.session['kakao_next'] = next_url
    
    REDIRECT_URI = request.build_absolute_uri('/login/kakao/callback/')
    kakao_auth_url = f"https://kauth.kakao.com/oauth/authorize?client_id={KAKAO_REST_API_KEY}&redirect_uri={REDIRECT_URI}&response_type=code"
    return redirect(kakao_auth_url)

def kakao_callback(request):
    """카카오 로그인 콜백 처리"""
    code = request.GET.get('code')
    if not code:
        messages.error(request, "카카오 로그인에 실패했습니다.")
        return redirect('/login/')
    
    KAKAO_REST_API_KEY = os.getenv('KAKAO_REST_API_KEY')
    if not KAKAO_REST_API_KEY:
        messages.error(request, "카카오 로그인 설정이 완료되지 않았습니다.")
        return redirect('/login/')
    
    REDIRECT_URI = request.build_absolute_uri('/login/kakao/callback/')
    
    try:
        # 1. 토큰 받기
        token_url = "https://kauth.kakao.com/oauth/token"
        token_data = {
            'grant_type': 'authorization_code',
            'client_id': KAKAO_REST_API_KEY,
            'redirect_uri': REDIRECT_URI,
            'code': code
        }
        
        token_response = requests.post(token_url, data=token_data)
        token_json = token_response.json()
        
        if 'error' in token_json:
            messages.error(request, f"카카오 로그인에 실패했습니다: {token_json.get('error_description', '알 수 없는 오류')}")
            return redirect('/login/')
        
        access_token = token_json.get('access_token')
        
        # 2. 사용자 정보 가져오기
        user_info_url = "https://kapi.kakao.com/v2/user/me"
        headers = {'Authorization': f'Bearer {access_token}'}
        user_response = requests.get(user_info_url, headers=headers)
        user_info = user_response.json()
        
        if 'error' in user_info:
            messages.error(request, "사용자 정보를 가져오는데 실패했습니다.")
            return redirect('/login/')
        
        # 3. 카카오 ID로 회원 찾기 또는 생성
        kakao_id = str(user_info['id'])
        kakao_account = user_info.get('kakao_account', {})
        profile = kakao_account.get('profile', {})
        nickname = profile.get('nickname', f'카카오사용자_{kakao_id[:6]}')
        email = kakao_account.get('email', '')
        
        # 카카오 ID를 user_id로 사용 (kakao_ 접두사 추가)
        kakao_user_id = f'kakao_{kakao_id}'
        
        try:
            # 기존 회원 찾기
            user = Member.objects.get(user_id=kakao_user_id)
        except Member.DoesNotExist:
            # 신규 회원 생성
            # 닉네임 중복 체크
            original_nickname = nickname
            counter = 1
            while Member.objects.filter(nickname=nickname).exists():
                nickname = f"{original_nickname}_{counter}"
                counter += 1
            
            # 필수 필드 기본값 설정
            user = Member.objects.create(
                user_id=kakao_user_id,
                name=nickname,
                nickname=nickname,
                password=make_password('kakao_login_no_password'),  # 카카오 로그인은 비밀번호 불필요
                birthday='19000101',  # 기본값
                gender=0,  # 기본값
                addr1='',  # 기본값
                phone_num=f'010-0000-{kakao_id[-4:]}' if len(kakao_id) >= 4 else '010-0000-0000',  # 카카오 ID로 임시 전화번호 생성
            )
            messages.success(request, "카카오 로그인으로 회원가입이 완료되었습니다.")
        
        # 4. 세션에 로그인 정보 저장
        request.session['user_id'] = user.user_id
        request.session['user_name'] = user.name
        request.session['nickname'] = user.nickname
        
        # 관리자 체크
        if user.member_id == 1:
            request.session['manager_id'] = user.member_id
            request.session['manager_name'] = user.name
            next_url = request.session.pop('kakao_next', None) or '/manager/dashboard/'
            return redirect(next_url)
        
        # 이전 페이지로 리다이렉트
        next_url = request.session.pop('kakao_next', None) or '/'
        return redirect(next_url)
        
    except requests.RequestException as e:
        messages.error(request, f"카카오 로그인 중 오류가 발생했습니다: {str(e)}")
        return redirect('/login/')
# 회원 가입 부분 ----------------------------------------
USERNAME_PATTERN = re.compile(r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{6,}$')
PASSWORD_PATTERN = re.compile(
    r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=])[A-Za-z\d!@#$%^&*()_+\-=]{8,}$'
)
PHONE_PATTERN = re.compile(r'^\d{3}-\d{4}-\d{4}$')

def signup(request):
    if request.method == "POST":
        data = request.POST
        ctx = {"input": data}

        name = data.get('name')
        user_id = data.get('username')
        password = data.get('password')
        password2 = data.get('password2')
        nickname = data.get('nickname')
        birthday = data.get('birthday')
        gender = data.get('gender')
        address = data.get('address')
        address_detail = data.get('address_detail', '')
        address_data_str = data.get('address_data', '')
        phone = data.get('phone')

        if not PASSWORD_PATTERN.match(password or ""):
            messages.error(request, "비밀번호 형식이 올바르지 않습니다.")
            return render(request, "signup.html", ctx)

        if password != password2:
            messages.error(request, "비밀번호가 일치하지 않습니다.")
            return render(request, "signup.html", ctx)

        if not USERNAME_PATTERN.match(user_id or ""):
            messages.error(request, "아이디는 6자 이상, 영문+숫자 조합이어야 합니다.")
            return render(request, "signup.html", ctx)

        if Member.objects.filter(user_id=user_id).exists():
            messages.error(request, "이미 존재하는 아이디입니다.")
            return render(request, "signup.html", ctx)

        if Member.objects.filter(nickname=nickname).exists():
            messages.error(request, "이미 존재하는 닉네임입니다.")
            return render(request, "signup.html", ctx)

        if not PHONE_PATTERN.match(phone or ""):
            messages.error(request, "전화번호는 010-0000-0000 형식으로 입력해주세요.")
            return render(request, "signup.html", ctx)

        if Member.objects.filter(phone_num=phone).exists():
            messages.error(request, "이미 등록된 전화번호입니다.")
            return render(request, "signup.html", ctx)

        gender_value = 0 if gender == "male" else 1

        # 주소 파싱
        from common.utils import parse_address
        import json
        
        addr1 = address.split()[0]
        addr2 = address.split()[1]
        addr3 = ' '.join(address.split()[2:]) + address_detail
        
        if address_data_str:
            try:
                address_data = json.loads(address_data_str)
                addr1, addr2, addr3 = parse_address(address_data, address_detail)
            except (json.JSONDecodeError, Exception) as e:
                # 파싱 실패 시 기존 방식 사용
                print(f"주소 파싱 오류: {e}")
                addr1 = address
                addr2 = address_detail
                addr3 = ""

        Member.objects.create(
            name=name,
            user_id=user_id,
            password=make_password(password),
            nickname=nickname,
            birthday=birthday,
            gender=gender_value,
            addr1=addr1,
            addr2=addr2,
            addr3=addr3,
            phone_num=phone,
        )

        return render(request, 'signup_success.html')

    return render(request, "signup.html")

def check_userid(request):
    user_id = request.GET.get('username')
    exists = Member.objects.filter(user_id=user_id).exists()
    return JsonResponse({'exists': exists})

def check_nickname(request):
    nickname = request.GET.get('nickname')
    exists = Member.objects.filter(nickname=nickname).exists()
    return JsonResponse({'exists': exists})

def check_phone(request):
    phone = request.GET.get('phone')
    exists = Member.objects.filter(phone_num=phone).exists()
    return JsonResponse({'exists': exists})
#--------------------------------------------------------------




def find_id(request):
    if request.method == "POST":
        name = request.POST.get('name')
        birthday = request.POST.get('birthday')
        phone1 = request.POST.get('phone1')
        phone2 = request.POST.get('phone2')
        phone3 = request.POST.get('phone3')

        # 생일 검증
        if len(birthday) != 8 or not birthday.isdigit():
            return render(request, "findID.html", {
                "error": "생년월일은 8자리 숫자로 입력해주세요. (예: 20020528)"
            })

        # 전화번호 검증
        if (len(phone1) != 3 or not phone1.isdigit() or
            len(phone2) != 4 or not phone2.isdigit() or
            len(phone3) != 4 or not phone3.isdigit()):
            return render(request, "findID.html", {
                "error": "전화번호는 숫자만 입력해야 하며 3-4-4 자리여야 합니다."
            })

        phone_num = phone1 + phone2 + phone3

        # TODO: DB에서 이름, 생년월일, phone_num 이 일치하는 정보 찾기

        return render(request, 'findID.html', {
            "result_id": "ID"
        })

    return render(request, 'findID.html')

def generate_random_pw(length=12):
    letters = string.ascii_letters        # ABCabc
    digits = string.digits               # 012345
    symbols = "!@#$%^&*()"
    char_set = letters + digits + symbols

    return ''.join(random.choice(char_set) for _ in range(length))


def find_pw(request):
    if request.method == "POST":
        user_id = request.POST.get("user_id")
        name = request.POST.get("name")
        birthday = request.POST.get("birthday")
        phone1 = request.POST.get("phone1")
        phone2 = request.POST.get("phone2")
        phone3 = request.POST.get("phone3")

        # 생년월일 검증 및 DB 포맷(YYYY-MM-DD)으로 변환
        birthday = (birthday or "").strip()
        birthday_db = None

        # 20020528 형식
        if len(birthday) == 8 and birthday.isdigit():
            birthday_db = f"{birthday[0:4]}-{birthday[4:6]}-{birthday[6:8]}"
        # 2002-05-28 형식
        elif len(birthday) == 10 and birthday.count("-") == 2:
            birthday_db = birthday
        else:
            return render(request, "findPW.html", {
                "error": "생년월일은 20020528 또는 2002-05-28 형식으로 입력해주세요."
            })

        # 전화번호 검증
        if (len(phone1) != 3 or not phone1.isdigit() or
            len(phone2) != 4 or not phone2.isdigit() or
            len(phone3) != 4 or not phone3.isdigit()):
            return render(request, "findPW.html", {
                "error": "전화번호는 3-4-4 숫자로 입력해주세요."
            })

        # DB에 저장된 형식(010-0000-0000)에 맞게 전화번호 구성
        phone_num = f"{phone1}-{phone2}-{phone3}"

        # 실제 회원 정보 확인
        try:
            user = Member.objects.get(
                user_id=user_id,
                name=name,
                birthday=birthday_db,
                phone_num=phone_num,
            )
        except Member.DoesNotExist:
            return render(request, "findPW.html", {
                "error": "입력하신 정보와 일치하는 회원을 찾을 수 없습니다."
            })

        # 12자리 랜덤 비밀번호 생성 및 DB 비밀번호 갱신
        new_password = generate_random_pw(12)
        user.password = make_password(new_password)
        user.save(update_fields=["password"])

        return render(request, "findPW.html", {
            "result_pw": new_password
        })

    return render(request, "findPW.html")