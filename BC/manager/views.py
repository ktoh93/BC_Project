from django.shortcuts import render

def manager(request):
    if request.method == "POST":
        admin_id = request.POST.get('admin_id')
        admin_pw = request.POST.get('admin_pw')

        # TODO : db 연결해서 비교 필요 
        """
        admin = db(username=admin_id, password=admin_pw)

        if admin is not None:
            login(request, admin)
            return redirect(/manager/dashboard/')
        else:
           return render(request, "manager/", {
                "error": "관리자의 아이디 혹은 비밀번호가 아닙니다."
            })
        """
    return render(request, 'login_manager.html')

def facility(request):
    return render(request, 'facility_manager.html')
