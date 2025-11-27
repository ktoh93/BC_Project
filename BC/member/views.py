from django.shortcuts import render


def info(request):
    member = {
        'name':'최재영',
        'user_id':'young010514',
        'nickname':'ㅇㅇㅇ',
        'birthday' : '2001-01-01',
        'email':'test@email.com',
        'phone_num':'010-1111-2222',
        'addr1' :'서울특별시',
        'addr2' :'양천구',
        'addr3' :'신정동',
    }


    return render(request, 'info.html', member)
def edit(request):
    member = {
        'name':'최재영',
        'user_id':'young010514',
        'nickname':'ㅇㅇㅇ',
        'birthday' : '2001-01-01',
        'email':'test@email.com',
        'phone_num':'010-1111-2222',
        'addr1' :'서울특별시',
        'addr2' :'양천구',
        'addr3' :'신정동',
    }

    return render('', 'info_edit.html', member)

def edit_password(request):


    return render('', 'info_edit_password.html')


def myreservation(request):

    list =[
        {
            'reservation_id':'예약번호 예시',
            'facility':'예약시설 예시',
            'reservation_date' : '예약한 날짜 예시',
            'reg_date' : '결제한 날짜 예시',
        },
        {
            'reservation_id':'예약번호 예시',
            'facility':'예약시설 예시',
            'reservation_date' : '예약한 날짜 예시',
            'reg_date' : '결제한 날짜 예시',
        },
    ]
    return render('', 'myreservation.html', {'list' : list})


def myrecruitment(request):
    list =[
        {
            'community_id':'게시글번호 예시',
            'title':'게시글 제목임다',
            'reg_date' : '게시 날짜임다',
            'reg_date' : '게시 날짜임다',
            'view_cnt' : '조회수임다',
        },
    ]
    return render('', 'myrecruitment.html',{'list':list})


def myarticle(request):
    list =[
        {
            'article_id':'게시글번호 예시',
            'title':'게시글 제목임다',
            'reg_date' : '게시 날짜임다',
            'view_cnt' : '조회수임다',
        },
    ]
    return render('', 'myarticle.html',{'list':list})


def myjoin(request):
    list=[
        {
            'community_id':'모집글 번호 예시',
            'title' : '모집글 제목 예시',
            'num_member' : '몇명참여?',
            'join_stat' : '참여했냐?',
        },
    ]
    return render('', 'myjoin.html', {'list':list})