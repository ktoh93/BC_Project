from django.shortcuts import render
import random
import string
from django.shortcuts import render, redirect
from django.contrib import messages
from member.models import Member
from django.contrib.auth.hashers import make_password, check_password
from django.http import JsonResponse
import re

def index(request):
    # DB에서 랜덤 시설 3개 가져오기
    try:
        from facility.models import FacilityInfo
        import random
        
        # 모든 시설 가져오기
        all_facilities = FacilityInfo.objects.all()
        
        # 랜덤으로 3개 선택 (최대 3개)
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
    
    context = {
        'random_facilities': facilities,
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

        # 생년월일 검증
        if len(birthday) != 8 or not birthday.isdigit():
            return render(request, "findPW.html", {
                "error": "생년월일은 8자리 숫자로 입력해주세요. (예: 20020528)"
            })

        # 전화번호 검증
        if (len(phone1) != 3 or not phone1.isdigit() or
            len(phone2) != 4 or not phone2.isdigit() or
            len(phone3) != 4 or not phone3.isdigit()):
            return render(request, "findPW.html", {
                "error": "전화번호는 3-4-4 숫자로 입력해주세요."
            })

        phone_num = phone1 + phone2 + phone3
        
        # TODO : DB user_id = user_id 확인 하는 if 문 작성 필요 

        # 12자리 랜덤 비밀번호 생성
        new_password = generate_random_pw(12)


        return render(request, "findPW.html", {
            "result_pw": new_password
        })

    return render(request, "findPW.html")