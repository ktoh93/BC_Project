from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.hashers import make_password, check_password
import re
from member.models import Member


from common.utils import get_recruitment_dummy_list


def info(request):
    login_id = request.session.get("user_id")
    
    if not login_id:
        return redirect('/login?next=/member/info/')

    try:
        # DB에서 최신 회원 정보 가져오기 (캐시 무시)
        user = Member.objects.get(user_id=login_id)
        
        # 디버깅: 현재 DB 값 확인
        print("=" * 50)
        print("info 페이지 - 현재 DB 값")
        print(f"닉네임: {user.nickname}")
        print(f"전화번호: {user.phone_num}")
        print(f"주소1: {user.addr1}")
        print("=" * 50)

        # 템플릿으로 전달될 데이터
        context = {
            "name": user.name,
            "user_id": user.user_id,
            "nickname": user.nickname,
            "birthday": user.birthday,
            "email": user.email if hasattr(user, "email") else "",
            "phone_num": user.phone_num,
            "addr1": user.addr1,
            "addr2": user.addr2,
            "addr3": user.addr3 if hasattr(user, "addr3") else "",
        }

        return render(request, "info.html", context)
    except Member.DoesNotExist:
        messages.error(request, "회원 정보를 찾을 수 없습니다.")
        return redirect('/login/')

def edit(request):
    # 로그인 체크
    login_id = request.session.get("user_id")
    if not login_id:
        return redirect('/login?next=/member/edit/')
    
    if request.method == "POST":
        # AJAX 요청인지 확인
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        print("=" * 50)
        print("POST 요청 받음")
        print("AJAX 여부:", is_ajax)
        print("받은 데이터:", dict(request.POST))
        print("=" * 50)
        
        # 수정된 정보 저장
        try:
            user = Member.objects.get(user_id=login_id)
            
            # 기존 값
            old_nickname = user.nickname
            old_phone = user.phone_num
            old_addr1 = user.addr1
            
            # 새 값
            new_nickname = request.POST.get('nickname', user.nickname)
            new_phone = request.POST.get('phone', user.phone_num)
            new_addr1 = request.POST.get('addr1', user.addr1)
            
            print(f"닉네임 변경: {old_nickname} -> {new_nickname}")
            print(f"전화번호 변경: {old_phone} -> {new_phone}")
            print(f"주소1 변경: {old_addr1} -> {new_addr1}")
            
            user.nickname = new_nickname
            user.phone_num = new_phone
            user.addr1 = request.POST.get('addr1', user.addr1)
            user.addr2 = request.POST.get('addr2', user.addr2)
            user.addr3 = request.POST.get('addr3', user.addr3)
            if hasattr(user, 'email'):
                user.email = request.POST.get('email', user.email)
            
            # DB에 저장
            user.save()
            print("DB 저장 완료")
            
            # 저장 확인을 위해 DB에서 다시 조회
            user.refresh_from_db()
            print(f"저장 후 DB 닉네임: {user.nickname}")
            print(f"저장 후 DB 전화번호: {user.phone_num}")
            print(f"저장 후 DB 주소1: {user.addr1}")
            
            # 세션 정보도 업데이트
            request.session['nickname'] = user.nickname
            request.session.modified = True  # 세션 강제 저장
            
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': '정보가 수정되었습니다.',
                    'data': {
                        'nickname': user.nickname,
                        'phone_num': user.phone_num,
                        'addr1': user.addr1,
                        'addr2': user.addr2,
                        'addr3': user.addr3,
                    }
                })
            else:
                messages.success(request, "정보가 수정되었습니다.")
                return redirect('/member/info/')
        except Member.DoesNotExist:
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'message': '회원 정보를 찾을 수 없습니다.'
                }, status=400)
            else:
                messages.error(request, "회원 정보를 찾을 수 없습니다.")
                return redirect('/member/info/')
        except Exception as e:
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'message': '수정 중 오류가 발생했습니다.'
                }, status=500)
            else:
                messages.error(request, "수정 중 오류가 발생했습니다.")
                return redirect('/member/info/')
    
    # GET 요청 - 정보 조회
    try:
        user = Member.objects.get(user_id=login_id)
    except Member.DoesNotExist:
        messages.error(request, "회원 정보를 찾을 수 없습니다.")
        return redirect('/member/info/')
    
    # 템플릿으로 전달될 데이터
    context = {
        "name": user.name,
        "user_id": user.user_id,
        "nickname": user.nickname,
        "birthday": user.birthday,
        "email": user.email if hasattr(user, "email") else "",
        "phone_num": user.phone_num,
        "addr1": user.addr1,
        "addr2": user.addr2,
        "addr3": user.addr3 if hasattr(user, "addr3") else "",
    }
    
    return render(request, 'info_edit.html', context)

def edit_password(request):
    # 로그인 체크
    login_id = request.session.get("user_id")
    if not login_id:
        return redirect('/login?next=/member/password/')
    
    # AJAX 요청인지 확인
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if request.method == "POST":
        current_pw = request.POST.get('current_pw', '')
        new_pw = request.POST.get('new_pw', '')
        new_pw2 = request.POST.get('new_pw2', '')
        
        try:
            user = Member.objects.get(user_id=login_id)
            
            # 현재 비밀번호 확인
            if not check_password(current_pw, user.password):
                if is_ajax:
                    return JsonResponse({
                        'success': False,
                        'message': '현재 비밀번호가 일치하지 않습니다.'
                    }, status=400)
                else:
                    messages.error(request, "현재 비밀번호가 일치하지 않습니다.")
                    return render(request, 'info_edit_password.html')
            
            # 새 비밀번호와 확인 비밀번호 일치 확인
            if new_pw != new_pw2:
                if is_ajax:
                    return JsonResponse({
                        'success': False,
                        'message': '새 비밀번호와 확인 비밀번호가 일치하지 않습니다.'
                    }, status=400)
                else:
                    messages.error(request, "새 비밀번호와 확인 비밀번호가 일치하지 않습니다.")
                    return render(request, 'info_edit_password.html')
            
            # 비밀번호 형식 검증 (signup과 동일한 패턴)
            PASSWORD_PATTERN = re.compile(
                r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=])[A-Za-z\d!@#$%^&*()_+\-=]{8,}$'
            )
            
            if not PASSWORD_PATTERN.match(new_pw):
                if is_ajax:
                    return JsonResponse({
                        'success': False,
                        'message': '비밀번호는 8자 이상, 영문 대소문자, 숫자, 특수문자를 포함해야 합니다.'
                    }, status=400)
                else:
                    messages.error(request, "비밀번호 형식이 올바르지 않습니다.")
                    return render(request, 'info_edit_password.html')
            
            # 현재 비밀번호와 새 비밀번호가 같은지 확인
            if check_password(new_pw, user.password):
                if is_ajax:
                    return JsonResponse({
                        'success': False,
                        'message': '새 비밀번호는 현재 비밀번호와 다르게 설정해주세요.'
                    }, status=400)
                else:
                    messages.error(request, "새 비밀번호는 현재 비밀번호와 다르게 설정해주세요.")
                    return render(request, 'info_edit_password.html')
            
            # 비밀번호 변경
            old_password_hash = user.password
            user.password = make_password(new_pw)
            user.save()
            
            print("=" * 50)
            print("비밀번호 변경")
            print("기존 해시:", old_password_hash[:50] + "..." if len(old_password_hash) > 50 else old_password_hash)
            print("새 해시:", user.password[:50] + "..." if len(user.password) > 50 else user.password)
            print("=" * 50)
            
            # 저장 확인
            user.refresh_from_db()
            
            # 새 비밀번호로 로그인 가능한지 테스트
            test_result = check_password(new_pw, user.password)
            print(f"새 비밀번호 검증 결과: {test_result}")
            
            if not test_result:
                print("경고: 비밀번호 저장 후 검증 실패!")
            
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': '비밀번호가 변경되었습니다.'
                })
            else:
                messages.success(request, "비밀번호가 변경되었습니다.")
                return redirect('/member/info/')
                
        except Member.DoesNotExist:
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'message': '회원 정보를 찾을 수 없습니다.'
                }, status=400)
            else:
                messages.error(request, "회원 정보를 찾을 수 없습니다.")
                return redirect('/member/info/')
        except Exception as e:
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'message': '비밀번호 변경 중 오류가 발생했습니다.'
                }, status=500)
            else:
                messages.error(request, "비밀번호 변경 중 오류가 발생했습니다.")
                return render(request, 'info_edit_password.html')
    
    # GET 요청
    return render(request, 'info_edit_password.html')















def myreservation(request):
    # 로그인 체크
    login_id = request.session.get("user_id")
    if not login_id:
        return redirect('/login?next=/member/myreservation/')
    
    # TODO: DB 연결 이후 Reservation 모델에서 본인의 예약 내역 조회
    # 예: Reservation.objects.filter(member_id=user, delete_yn=0).order_by('-reg_date')
    dummy_list = []  # DB 연결 전까지 빈 리스트
    
    # 정렬 기능
    sort = request.GET.get("sort", "recent")
    
    # 페이지네이션
    per_page = int(request.GET.get("per_page", 15))
    page = int(request.GET.get("page", 1))
    
    paginator = Paginator(dummy_list, per_page)
    page_obj = paginator.get_page(page)
    
    # 페이지 블록 계산
    block_size = 5
    current_block = (page - 1) // block_size
    block_start = current_block * block_size + 1
    block_end = block_start + block_size - 1
    
    if block_end > paginator.num_pages:
        block_end = paginator.num_pages
    
    block_range = range(block_start, block_end + 1)
    
    context = {
        "page_obj": page_obj,
        "paginator": paginator,
        "per_page": per_page,
        "page": page,
        "sort": sort,
        "block_range": block_range,
        "block_start": block_start,
        "block_end": block_end,
    }
    
    return render(request, 'myreservation.html', context)








def myrecruitment(request):
    # 로그인 체크
    login_id = request.session.get("user_id")
    if not login_id:
        return redirect('/login?next=/member/myrecruitment/')
    
    # TODO: DB 연결 이후 Community 모델에서 본인의 모집글 조회
    # 예: Community.objects.filter(member_id=user, delete_date__isnull=True).order_by('-reg_date')
    dummy_list = []  # DB 연결 전까지 빈 리스트
    
    # 정렬 기능
    sort = request.GET.get("sort", "recent")
    
    # 페이지네이션
    per_page = int(request.GET.get("per_page", 15))
    page = int(request.GET.get("page", 1))
    
    paginator = Paginator(dummy_list, per_page)
    page_obj = paginator.get_page(page)
    
    # 페이지 블록 계산
    block_size = 5
    current_block = (page - 1) // block_size
    block_start = current_block * block_size + 1
    block_end = block_start + block_size - 1
    
    if block_end > paginator.num_pages:
        block_end = paginator.num_pages
    
    block_range = range(block_start, block_end + 1)
    
    context = {
        "page_obj": page_obj,
        "paginator": paginator,
        "per_page": per_page,
        "page": page,
        "sort": sort,
        "block_range": block_range,
        "block_start": block_start,
        "block_end": block_end,
    }
    
    return render(request, 'myrecruitment.html', context)




def myarticle(request):
    # 로그인 체크
    login_id = request.session.get("user_id")
    if not login_id:
        return redirect('/login?next=/member/myarticle/')
    
    try:
        # 로그인한 사용자 정보 가져오기
        user = Member.objects.get(user_id=login_id)
        
        # DB에서 본인이 작성한 자유게시판(post) 게시글 조회
        from board.models import Article, Category
        from board.utils import get_category_by_type
        
        category = get_category_by_type('post')
        articles = Article.objects.select_related('member_id', 'category_id').filter(
            member_id=user,
            category_id=category,
            delete_date__isnull=True
        ).order_by('-reg_date')
        
    except Member.DoesNotExist:
        messages.error(request, "회원 정보를 찾을 수 없습니다.")
        return redirect('/login/')
    except Exception as e:
        import traceback
        print(f"[ERROR] 내 게시글 조회 오류: {str(e)}")
        print(traceback.format_exc())
        articles = Article.objects.none()
    
    # 정렬 기능
    sort = request.GET.get("sort", "recent")
    if sort == "title":
        articles = articles.order_by('title')
    elif sort == "views":
        articles = articles.order_by('-view_cnt')
    else:  # recent
        articles = articles.order_by('-reg_date')
    
    # 페이지네이션
    per_page = int(request.GET.get("per_page", 15))
    page = int(request.GET.get("page", 1))
    
    paginator = Paginator(articles, per_page)
    page_obj = paginator.get_page(page)
    
    # 페이지 블록 계산
    block_size = 5
    current_block = (page - 1) // block_size
    block_start = current_block * block_size + 1
    block_end = block_start + block_size - 1
    
    if block_end > paginator.num_pages:
        block_end = paginator.num_pages
    
    block_range = range(block_start, block_end + 1)
    
    context = {
        "page_obj": page_obj,
        "paginator": paginator,
        "per_page": per_page,
        "page": page,
        "sort": sort,
        "block_range": block_range,
        "block_start": block_start,
        "block_end": block_end,
    }
    
    return render(request, 'myarticle.html', context)








def myjoin(request):
    # TODO: DB 연결 이후 쿼리로 교체하고 삭제 필요 - 더미 데이터 생성 (100개, 캐싱됨)
    dummy_list = get_recruitment_dummy_list()

    
    # 검색 기능
    keyword = request.GET.get("keyword", "")
    search_type = request.GET.get("search_type", "all")
    
    if keyword:
        if search_type == "title":
            dummy_list = [item for item in dummy_list if keyword in item["title"]]
        elif search_type == "author":
            dummy_list = [item for item in dummy_list if keyword in item["author"]]
        elif search_type == "all":
            dummy_list = [item for item in dummy_list if keyword in item["title"] or keyword in item.get("author", "")]
    
    # 정렬 기능
    sort = request.GET.get("sort", "recent")
    if sort == "title":
        dummy_list.sort(key=lambda x: x["title"])
    elif sort == "views":
        dummy_list.sort(key=lambda x: x["views"], reverse=True)
    else:  # recent
        dummy_list.sort(key=lambda x: x["date"], reverse=True)
    
    # 페이지네이션
    per_page = int(request.GET.get("per_page", 15))
    page = int(request.GET.get("page", 1))
    
    paginator = Paginator(dummy_list, per_page)
    page_obj = paginator.get_page(page)
    
    # 페이지 블록 계산
    block_size = 5
    current_block = (page - 1) // block_size
    block_start = current_block * block_size + 1
    block_end = block_start + block_size - 1
    
    if block_end > paginator.num_pages:
        block_end = paginator.num_pages
    
    block_range = range(block_start, block_end + 1)
    
    context = {
        "page_obj": page_obj,
        "paginator": paginator,
        "per_page": per_page,
        "page": page,
        "sort": sort,
        "block_range": block_range,
        "block_start": block_start,
        "block_end": block_end,
        # "pinned_posts": pinned_posts,
    }
    
    return render('', 'myjoin.html', context)




