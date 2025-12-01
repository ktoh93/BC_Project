from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.hashers import make_password, check_password
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import datetime
import re
import json
from member.models import Member


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
            
            # 주소 파싱
            from common.utils import parse_address
            import json
            
            address_data_str = request.POST.get('address_data', '')
            address_detail = request.POST.get('address_detail', '')
            
            if address_data_str:
                try:
                    address_data = json.loads(address_data_str)
                    addr1, addr2, addr3 = parse_address(address_data, address_detail)
                    user.addr1 = addr1
                    user.addr2 = addr2
                    user.addr3 = addr3
                except (json.JSONDecodeError, Exception) as e:
                    # 파싱 실패 시 기존 방식 사용
                    print(f"주소 파싱 오류: {e}")
                    user.addr1 = request.POST.get('addr1', user.addr1)
                    user.addr2 = request.POST.get('addr2', user.addr2)
                    user.addr3 = request.POST.get('addr3', user.addr3)
            else:
                # 기존 방식 (레거시 지원)
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
    
    try:
        # 로그인한 사용자 정보 가져오기
        user = Member.objects.get(user_id=login_id)
        
        # DB에서 본인의 예약 내역 조회 (취소되지 않은 것만, 삭제되지 않은 것만)
        from reservation.models import Reservation
        
        reservations = Reservation.objects.filter(
            member=user,
            delete_yn=0,
            delete_date__isnull=True
        ).order_by('-reg_date')
        
    except Member.DoesNotExist:
        messages.error(request, "회원 정보를 찾을 수 없습니다.")
        return redirect('/login/')
    except Exception as e:
        import traceback
        print(f"[ERROR] 내 예약 내역 조회 오류: {str(e)}")
        print(traceback.format_exc())
        reservations = Reservation.objects.none()
    
    # 정렬 기능
    sort = request.GET.get("sort", "recent")
    if sort == "title":
        # 예약에는 제목이 없으므로 시설명으로 정렬
        reservations = reservations.order_by('facility')
    elif sort == "views":
        # 예약에는 조회수가 없으므로 예약일자로 정렬
        reservations = reservations.order_by('-reservation_date')
    else:  # recent
        reservations = reservations.order_by('-reg_date')
    
    # 페이지네이션
    per_page = int(request.GET.get("per_page", 15))
    page = int(request.GET.get("page", 1))
    
    paginator = Paginator(reservations, per_page)
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
    
    try:
        # 로그인한 사용자 정보 가져오기
        user = Member.objects.get(user_id=login_id)
        
        # DB에서 본인이 작성한 모집글 조회 (삭제되지 않은 것만)
        from recruitment.models import Community
        
        communities = Community.objects.filter(
            member_id=user,
            delete_date__isnull=True
        ).order_by('-reg_date')
        
    except Member.DoesNotExist:
        messages.error(request, "회원 정보를 찾을 수 없습니다.")
        return redirect('/login/')
    except Exception as e:
        import traceback
        print(f"[ERROR] 내 모집글 조회 오류: {str(e)}")
        print(traceback.format_exc())
        communities = Community.objects.none()
    
    # 정렬 기능
    sort = request.GET.get("sort", "recent")
    if sort == "title":
        communities = communities.order_by('title')
    elif sort == "views":
        communities = communities.order_by('-view_cnt')
    else:  # recent
        communities = communities.order_by('-reg_date')
    
    # 페이지네이션
    per_page = int(request.GET.get("per_page", 15))
    page = int(request.GET.get("page", 1))
    
    paginator = Paginator(communities, per_page)
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
    # 로그인 체크
    login_id = request.session.get("user_id")
    if not login_id:
        return redirect('/login?next=/member/myjoin/')
    
    try:
        # 로그인한 사용자 정보 가져오기
        user = Member.objects.get(user_id=login_id)
        
        # DB에서 본인이 신청한 참여 내역 조회 (JoinStat)
        from recruitment.models import JoinStat, Community
        
        # 본인이 신청한 참여 내역 조회 (삭제되지 않은 모집글만)
        join_stats = JoinStat.objects.filter(
            member_id=user
        ).select_related('community_id').filter(
            community_id__delete_date__isnull=True
        ).order_by('-community_id__reg_date')
        
    except Member.DoesNotExist:
        messages.error(request, "회원 정보를 찾을 수 없습니다.")
        return redirect('/login/')
    except Exception as e:
        import traceback
        print(f"[ERROR] 내 참여 내역 조회 오류: {str(e)}")
        print(traceback.format_exc())
        join_stats = JoinStat.objects.none()
    
    # 정렬 기능
    sort = request.GET.get("sort", "recent")
    if sort == "title":
        join_stats = join_stats.order_by('community_id__title')
    elif sort == "views":
        join_stats = join_stats.order_by('-community_id__view_cnt')
    else:  # recent
        join_stats = join_stats.order_by('-community_id__reg_date')
    
    # 페이지네이션
    per_page = int(request.GET.get("per_page", 15))
    page = int(request.GET.get("page", 1))
    
    paginator = Paginator(join_stats, per_page)
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
    
    return render(request, 'myjoin.html', context)


@csrf_exempt
def delete_my_article(request):
    """마이페이지에서 본인이 작성한 게시글 삭제 API"""
    if request.method != "POST":
        return JsonResponse({"status": "error", "msg": "POST만 가능"}, status=405)
    
    # 로그인 체크
    login_id = request.session.get("user_id")
    if not login_id:
        return JsonResponse({"status": "error", "msg": "로그인이 필요합니다."}, status=403)
    
    try:
        user = Member.objects.get(user_id=login_id)
        data = json.loads(request.body)
        article_id = data.get("article_id")
        
        if not article_id:
            return JsonResponse({"status": "error", "msg": "게시글 ID가 필요합니다."})
        
        # 본인이 작성한 게시글인지 확인
        from board.models import Article
        from board.utils import get_category_by_type
        
        category = get_category_by_type('post')
        article = Article.objects.get(
            article_id=article_id,
            member_id=user,
            category_id=category
        )
        
        # 이미 삭제된 경우
        if article.delete_date:
            return JsonResponse({"status": "error", "msg": "이미 삭제된 게시글입니다."})
        
        # 삭제 처리 (soft delete)
        article.delete_date = datetime.now()  # 한국 시간으로 저장
        article.save(update_fields=['delete_date'])
        
        return JsonResponse({"status": "ok", "msg": "게시글이 삭제되었습니다."})
    
    except Member.DoesNotExist:
        return JsonResponse({"status": "error", "msg": "회원 정보를 찾을 수 없습니다."}, status=404)
    except Article.DoesNotExist:
        return JsonResponse({"status": "error", "msg": "게시글을 찾을 수 없거나 권한이 없습니다."}, status=404)
    except Exception as e:
        import traceback
        print(f"[ERROR] delete_my_article 오류: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({"status": "error", "msg": str(e)})


@csrf_exempt
def delete_my_community(request):
    """마이페이지에서 본인이 작성한 모집글 삭제 API"""
    if request.method != "POST":
        return JsonResponse({"status": "error", "msg": "POST만 가능"}, status=405)
    
    # 로그인 체크
    login_id = request.session.get("user_id")
    if not login_id:
        return JsonResponse({"status": "error", "msg": "로그인이 필요합니다."}, status=403)
    
    try:
        user = Member.objects.get(user_id=login_id)
        data = json.loads(request.body)
        community_id = data.get("community_id")
        
        if not community_id:
            return JsonResponse({"status": "error", "msg": "모집글 ID가 필요합니다."})
        
        # 본인이 작성한 모집글인지 확인
        from recruitment.models import Community
        
        community = Community.objects.get(
            community_id=community_id,
            member_id=user
        )
        
        # 이미 삭제된 경우
        if community.delete_date:
            return JsonResponse({"status": "error", "msg": "이미 삭제된 모집글입니다."})
        
        # 삭제 처리 (soft delete)
        community.delete_date = datetime.now()  # 한국 시간으로 저장
        community.save(update_fields=['delete_date'])
        
        return JsonResponse({"status": "ok", "msg": "모집글이 삭제되었습니다."})
    
    except Member.DoesNotExist:
        return JsonResponse({"status": "error", "msg": "회원 정보를 찾을 수 없습니다."}, status=404)
    except Community.DoesNotExist:
        return JsonResponse({"status": "error", "msg": "모집글을 찾을 수 없거나 권한이 없습니다."}, status=404)
    except Exception as e:
        import traceback
        print(f"[ERROR] delete_my_community 오류: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({"status": "error", "msg": str(e)})




