from django.shortcuts import render
import random
import string


def index(request):
    return render(request, 'index.html')

def login(request):
    return render(request, 'login.html')

def signup(request):
    return render(request, 'signup.html')

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