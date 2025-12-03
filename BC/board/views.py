from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import os
import uuid
from common.utils import check_login, handle_file_uploads
from board.models import Article, Board, Category
from board.utils import get_category_by_type, get_board_by_name
from common.models import Comment, AddInfo
from member.models import Member
# TODO: DB 연결 이후 쿼리로 교체하고 삭제 필요
from common.utils import get_notice_pinned_posts, get_event_pinned_posts, get_post_dummy_list

def notice(request):
    # DB에서 공지사항 조회 (category_type='notice')
    try:
        now = timezone.now()
        category = get_category_by_type('notice')
        
        articles = (
            Article.objects
            .select_related('member_id', 'category_id')
            .filter(
                category_id=category,
                delete_date__isnull=True
            )
            .filter(
                Q(always_on=0) |
                Q(
                    Q(start_date__isnull=True) | Q(start_date__lte=now),
                    Q(end_date__isnull=True) | Q(end_date__gte=now)
                )
            )
            .annotate(
                comment_count=Count(
                    "comment",
                    filter=Q(comment__delete_date__isnull=True)
                )  # 🔥 댓글 개수
            )
            .order_by('-reg_date')
        )
        
        # 상단 고정 게시글 (always_on=0) - 고정 섹션용
        pinned_articles = articles.filter(always_on=0).order_by('-reg_date')[:5]
        
        # 검색 기능
        keyword = request.GET.get("keyword", "")
        search_type = request.GET.get("search_type", "all")
        
        if keyword:
            if search_type == "title":
                articles = articles.filter(title__icontains=keyword)
            elif search_type == "author":
                articles = articles.filter(member_id__nickname__icontains=keyword)
            elif search_type == "all":
                articles = articles.filter(
                    Q(title__icontains=keyword) | Q(member_id__nickname__icontains=keyword)
                )
        
        # 정렬 기능
        sort = request.GET.get("sort", "recent")
        if sort == "title":
            articles = articles.order_by('title')
        elif sort == "views":
            articles = articles.order_by('-view_cnt')
        else:  # recent
            articles = articles.order_by('-reg_date')
        
        # 페이징 (고정 게시글 포함하여 전체 표시)
        per_page = int(request.GET.get("per_page", 15))
        page = int(request.GET.get("page", 1))
        
        paginator = Paginator(articles, per_page)
        page_obj = paginator.get_page(page)
        
        # 상단 고정 게시글 변환
        pinned_posts = []
        for article in pinned_articles:
            pinned_posts.append({
                'id': article.article_id,
                'comment_count': article.comment_count,
                'title': article.title,
                'author': article.member_id.nickname if article.member_id else '',
                'is_admin': article.member_id.member_id == 1 if article.member_id else False,
                'date': article.reg_date.strftime('%Y-%m-%d'),
                'views': article.view_cnt,
            })
        
    except Exception as e:
        # DB 오류 시 빈 리스트
        print(f"[ERROR] notice 함수 오류: {str(e)}")
        pinned_posts = []
        articles = Article.objects.none()
        paginator = Paginator(articles, 15)
        page_obj = paginator.get_page(1)
    
    # 페이지 기준 블록
    block_size = 5
    current_block = (page_obj.number - 1) // block_size
    block_start = current_block * block_size + 1
    block_end = block_start + block_size - 1
    
    if block_end > paginator.num_pages:
        block_end = paginator.num_pages
    
    block_range = range(block_start, block_end + 1)
    
    sort = request.GET.get("sort", "recent")
    
    context = {
        "page_obj": page_obj,  # Paginator의 Page 객체 그대로 전달
        "paginator": paginator,
        "per_page": per_page,
        "page": page_obj.number,
        "sort": sort,
        "block_range": block_range,
        "block_start": block_start,
        "block_end": block_end,
        "pinned_posts": pinned_posts,
    }
    
    return render(request, 'notice.html', context)

def event(request):
    # DB에서 이벤트 조회 (category_type='event')
    try:
        now = timezone.now()
        category = get_category_by_type('event')
        
        articles = (
            Article.objects
            .select_related('member_id', 'category_id')
            .filter(
                category_id=category,
                delete_date__isnull=True
            )
            .filter(
                Q(always_on=0) |
                Q(
                    Q(start_date__isnull=True) | Q(start_date__lte=now),
                    Q(end_date__isnull=True) | Q(end_date__gte=now)
                )
            )
            .annotate(
                comment_count=Count(
                    "comment",
                    filter=Q(comment__delete_date__isnull=True)
                )
            )
            .order_by('-reg_date')
        )
        
        # 상단 고정 게시글 (always_on=0) - 고정 섹션용
        pinned_articles = articles.filter(always_on=0).order_by('-reg_date')[:5]
        
        # 검색 기능
        keyword = request.GET.get("keyword", "")
        search_type = request.GET.get("search_type", "all")
        
        if keyword:
            if search_type == "title":
                articles = articles.filter(title__icontains=keyword)
            elif search_type == "author":
                articles = articles.filter(member_id__nickname__icontains=keyword)
            elif search_type == "all":
                articles = articles.filter(
                    Q(title__icontains=keyword) | Q(member_id__nickname__icontains=keyword)
                )
        
        # 정렬 기능
        sort = request.GET.get("sort", "recent")
        if sort == "title":
            articles = articles.order_by('title')
        elif sort == "views":
            articles = articles.order_by('-view_cnt')
        else:  # recent
            articles = articles.order_by('-reg_date')
        
        # 페이지네이션 (고정 게시글 포함하여 전체 표시)
        per_page = int(request.GET.get("per_page", 15))
        page = int(request.GET.get("page", 1))
        
        paginator = Paginator(articles, per_page)
        page_obj = paginator.get_page(page)
        
        # 상단 고정 게시글 변환
        pinned_posts = []
        for article in pinned_articles:
            pinned_posts.append({
                'id': article.article_id,
                'comment_count': article.comment_count,
                'title': article.title,
                'author': article.member_id.nickname if article.member_id else '',
                'is_admin': article.member_id.member_id == 1 if article.member_id else False,
                'date': article.reg_date.strftime('%Y-%m-%d'),
                'views': article.view_cnt,
            })
        
    except Exception as e:
        # DB 오류 시 빈 리스트
        print(f"[ERROR] event 함수 오류: {str(e)}")
        pinned_posts = []
        articles = Article.objects.none()
        paginator = Paginator(articles, 15)
        page_obj = paginator.get_page(1)
    
    # 페이지 블록 계산
    block_size = 5
    current_block = (page_obj.number - 1) // block_size
    block_start = current_block * block_size + 1
    block_end = block_start + block_size - 1
    
    if block_end > paginator.num_pages:
        block_end = paginator.num_pages
    
    block_range = range(block_start, block_end + 1)
    
    sort = request.GET.get("sort", "recent")
    
    context = {
        "page_obj": page_obj,  # Paginator의 Page 객체 그대로 전달
        "paginator": paginator,
        "per_page": per_page,
        "page": page_obj.number,
        "sort": sort,
        "block_range": block_range,
        "block_start": block_start,
        "block_end": block_end,
        "pinned_posts": pinned_posts,
    }
    
    return render(request, 'event.html', context)

def post(request):
    # DB에서 게시글 조회
    try:
        category = get_category_by_type('post')
        articles = (
            Article.objects
            .select_related('member_id', 'category_id')
            .filter(
                category_id=category,
                delete_date__isnull=True
            )
            .annotate(
                comment_count=Count(
                    "comment",
                    filter=Q(comment__delete_date__isnull=True)
                )
            )
            .order_by('-reg_date')
        )
    except (Category.DoesNotExist, Exception):
        # 카테고리가 없으면 더미 데이터 사용
        articles = []
        dummy_list = get_post_dummy_list()
    else:
        # 검색 기능
        keyword = request.GET.get("keyword", "")
        search_type = request.GET.get("search_type", "all")
        
        if keyword:
            if search_type == "title":
                articles = articles.filter(title__icontains=keyword)
            elif search_type == "author":
                articles = articles.filter(member_id__nickname__icontains=keyword)
            elif search_type == "all":
                articles = articles.filter(
                    Q(title__icontains=keyword) | Q(member_id__nickname__icontains=keyword)
                )
        
        # 정렬 기능
        sort = request.GET.get("sort", "recent")
        if sort == "title":
            articles = articles.order_by('title')
        elif sort == "views":
            articles = articles.order_by('-view_cnt')
        else:  # recent
            articles = articles.order_by('-reg_date')
        
        # 페이징
        per_page = int(request.GET.get("per_page", 15))
        page = int(request.GET.get("page", 1))
        
        paginator = Paginator(articles, per_page)
        page_obj = paginator.get_page(page)
        
        # 페이지 기준 블록
        block_size = 5
        current_block = (page - 1) // block_size
        block_start = current_block * block_size + 1
        block_end = block_start + block_size - 1
        
        if block_end > paginator.num_pages:
            block_end = paginator.num_pages
        
        block_range = range(block_start, block_end + 1)
        
        context = {
            "page_obj": page_obj,  # Paginator의 Page 객체 그대로 전달
            "paginator": paginator,
            "per_page": per_page,
            "page": page,
            "sort": sort,
            "block_range": block_range,
            "block_start": block_start,
            "block_end": block_end,
        }
        
        return render(request, 'post.html', context)
    
    # 더미 데이터 사용 (게시판이 없는 경우)
    dummy_list = get_post_dummy_list()
    
    # 검색 기능
    keyword = request.GET.get("keyword", "")
    search_type = request.GET.get("search_type", "all")
    
    if keyword:
        if search_type == "title":
            dummy_list = [item for item in dummy_list if keyword in item["title"]]
        elif search_type == "author":
            dummy_list = [item for item in dummy_list if keyword in item.get("author", "")]
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
    
    # 페이징
    per_page = int(request.GET.get("per_page", 15))
    page = int(request.GET.get("page", 1))
    
    paginator = Paginator(dummy_list, per_page)
    page_obj = paginator.get_page(page)
    
    # 페이지 기준 블록
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
    
    return render(request, 'post.html', context)

def post_write(request):
    # 로그인 체크
    redirect_response = check_login(request)
    if redirect_response:
        return redirect_response
    
    if request.method == "POST":
        # 게시글 작성 처리
        # 관리자 우선 체크
        manager_id = request.session.get('manager_id')
        if manager_id:
            # 관리자인 경우
            try:
                member = Member.objects.get(member_id=manager_id)
            except Member.DoesNotExist:
                messages.error(request, "관리자 정보를 찾을 수 없습니다.")
                return redirect('/manager/')
        else:
            # 일반 사용자인 경우
            login_id = request.session.get('user_id')
            if not login_id:
                messages.error(request, "로그인이 필요합니다.")
                return redirect('/login/')
            try:
                member = Member.objects.get(user_id=login_id)
            except Member.DoesNotExist:
                messages.error(request, "회원 정보를 찾을 수 없습니다.")
                return redirect('/login/')
        
        try:
            category = get_category_by_type('post')
            board = get_board_by_name('post')
            
            title = request.POST.get('title')
            content = request.POST.get('content')
            
            if not title or not content:
                messages.error(request, "제목과 내용을 입력해주세요.")
                return render(request, 'post_write.html')
            
            article = Article.objects.create(
                title=title,
                contents=content,
                member_id=member,
                board_id=board,
                category_id=category,
                always_on=1
            )
            
            # 파일 업로드 처리
            handle_file_uploads(request, article)
            
            messages.success(request, "게시글이 작성되었습니다.")
            # 관리자인 경우 관리자 페이지로, 일반 사용자는 게시판 목록으로
            if manager_id:
                return redirect('/manager/post_manager/')
            else:
                return redirect('/board/post/')
        except (Category.DoesNotExist, Board.DoesNotExist):
            messages.error(request, "게시판을 찾을 수 없습니다.")
            if manager_id:
                return redirect('/manager/post_manager/')
            else:
                return redirect('/board/post/')
        except Exception as e:
            import traceback
            print(f"[ERROR] post_write 오류: {str(e)}")
            print(traceback.format_exc())
            messages.error(request, f"게시글 작성 중 오류가 발생했습니다: {str(e)}")
            return render(request, 'post_write.html')
    
    return render(request, 'post_write.html')

def notice_detail(request, article_id):
    print(f"[DEBUG] notice_detail 호출: article_id={article_id}")
    
    # 로그인 체크
    redirect_response = check_login(request)
    if redirect_response:
        print(f"[DEBUG] notice_detail: 로그인 필요 - 리다이렉트")
        return redirect_response
    
    try:
        # category_type='notice'로 조회
        category = get_category_by_type('notice')
        print(f"[DEBUG] notice_detail: category={category.category_type} (ID: {category.category_id})")
        
        # 관리자 여부 확인
        manager_id = request.session.get('manager_id')
        is_manager = manager_id == 1 if manager_id else False
        
        # DB에서 게시글 조회 (관리자는 삭제된 게시글도 볼 수 있음)
        if is_manager:
            article_obj = Article.objects.select_related('member_id', 'category_id', 'board_id').get(
                article_id=article_id,
                category_id=category
            )
        else:
            article_obj = Article.objects.select_related('member_id', 'category_id', 'board_id').get(
                article_id=article_id,
                category_id=category,
                delete_date__isnull=True
            )
        print(f"[DEBUG] notice_detail: 게시글 조회 성공 - title={article_obj.title}")
        
        # 조회수 증가 (삭제되지 않은 게시글만)
        if not article_obj.delete_date:
            article_obj.view_cnt += 1
            article_obj.save(update_fields=['view_cnt'])
        
        # 댓글 조회 및 변환 (삭제된 댓글도 포함)
        comment_objs = Comment.objects.select_related('member_id').filter(
            article_id=article_id
        ).order_by('reg_date')
        
        comments = []
        for comment_obj in comment_objs:
            comment_author = comment_obj.member_id.nickname if comment_obj.member_id and hasattr(comment_obj.member_id, 'nickname') else '알 수 없음'
            comment_is_admin = comment_obj.member_id.member_id == 1 if comment_obj.member_id else False
            is_deleted = comment_obj.delete_date is not None
            # DB에 저장된 댓글 내용 그대로 사용 (이미 '관리자에 의해 삭제된 댓글입니다.'로 저장됨)
            comments.append({
                'comment_id': comment_obj.comment_id,
                'comment': comment_obj.comment,
                'author': comment_author,
                'is_admin': comment_is_admin,
                'reg_date': comment_obj.reg_date,
                'is_deleted': is_deleted,
            })
        
        # 작성자 정보 안전하게 가져오기
        author_name = article_obj.member_id.nickname if article_obj.member_id and hasattr(article_obj.member_id, 'nickname') else '알 수 없음'
        is_admin = article_obj.member_id.member_id == 1 if article_obj.member_id else False
        
        # 첨부파일 조회
        add_info_objs = AddInfo.objects.filter(article_id=article_id)
        files = []
        images = []
        for add_info in add_info_objs:
            file_ext = os.path.splitext(add_info.file_name)[1].lower()
            is_image = file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
            file_data = {
                'id': add_info.add_info_id,
                'name': add_info.file_name,
                'url': f"{settings.MEDIA_URL}{add_info.path}",
                'is_image': is_image,
            }
            if is_image:
                images.append(file_data)
                # 이미지 파일도 다운로드 링크로 표시하기 위해 files에 추가
                files.append(file_data)
            else:
                files.append(file_data)
        
        # 삭제 여부 확인
        is_deleted = article_obj.delete_date is not None
        
        article = {
            'article_id': article_obj.article_id,
            'title': article_obj.title,
            'contents': article_obj.contents if article_obj.contents else '',
            'author': author_name,
            'is_admin': is_admin,
            'date': article_obj.reg_date.strftime('%Y-%m-%d'),
            'views': article_obj.view_cnt,
            'reg_date': article_obj.reg_date,
            'images': images,  # 이미지 파일들
            'files': files,     # 일반 파일들 (PDF 등)
            'delete_date': article_obj.delete_date.strftime('%Y-%m-%d %H:%M') if article_obj.delete_date else None,
        }
        
        context = {
            'article': article,
            'comments': comments,
            'board_type': 'notice',
            'is_manager': is_manager,
            'is_deleted': is_deleted,
        }
        
        print(f"[DEBUG] notice_detail: article_id={article_id}, title={article_obj.title}")
        print(f"[DEBUG] contents 길이: {len(article_obj.contents) if article_obj.contents else 0}")
        
        return render(request, 'board_detail.html', context)
    except Category.DoesNotExist:
        import traceback
        print(f"[ERROR] notice_detail: Category.DoesNotExist - article_id={article_id}")
        print(traceback.format_exc())
        messages.error(request, "공지사항 카테고리를 찾을 수 없습니다.")
        return redirect('/board/notice/')
    except Article.DoesNotExist:
        import traceback
        print(f"[ERROR] notice_detail: Article.DoesNotExist - article_id={article_id}, category_id={category.category_id if 'category' in locals() else 'N/A'}")
        print(traceback.format_exc())
        messages.error(request, f"게시글을 찾을 수 없습니다. (ID: {article_id})")
        return redirect('/board/notice/')
    except Exception as e:
        import traceback
        print(f"[ERROR] notice_detail 오류: {str(e)}")
        print(f"[ERROR] article_id={article_id}")
        print(traceback.format_exc())
        messages.error(request, f"게시글을 불러오는 중 오류가 발생했습니다: {str(e)}")
        return redirect('/board/notice/')

def event_detail(request, article_id):
    print(f"[DEBUG] event_detail 호출: article_id={article_id}")
    
    # 로그인 체크
    redirect_response = check_login(request)
    if redirect_response:
        print(f"[DEBUG] event_detail: 로그인 필요 - 리다이렉트")
        return redirect_response
    
    try:
        # category_type='event'로 조회
        category = get_category_by_type('event')
        print(f"[DEBUG] event_detail: category={category.category_type} (ID: {category.category_id})")
        
        # 관리자 여부 확인
        manager_id = request.session.get('manager_id')
        is_manager = manager_id == 1 if manager_id else False
        
        # DB에서 게시글 조회 (관리자는 삭제된 게시글도 볼 수 있음)
        if is_manager:
            article_obj = Article.objects.select_related('member_id', 'category_id', 'board_id').get(
                article_id=article_id,
                category_id=category
            )
        else:
            article_obj = Article.objects.select_related('member_id', 'category_id', 'board_id').get(
                article_id=article_id,
                category_id=category,
                delete_date__isnull=True
            )
        print(f"[DEBUG] event_detail: 게시글 조회 성공 - title={article_obj.title}")
        
        # 조회수 증가 (삭제되지 않은 게시글만)
        if not article_obj.delete_date:
            article_obj.view_cnt += 1
            article_obj.save(update_fields=['view_cnt'])
        
        # 댓글 조회 및 변환 (삭제된 댓글도 포함)
        comment_objs = Comment.objects.select_related('member_id').filter(
            article_id=article_id
        ).order_by('reg_date')
        
        comments = []
        for comment_obj in comment_objs:
            comment_author = comment_obj.member_id.nickname if comment_obj.member_id and hasattr(comment_obj.member_id, 'nickname') else '알 수 없음'
            comment_is_admin = comment_obj.member_id.member_id == 1 if comment_obj.member_id else False
            is_deleted = comment_obj.delete_date is not None
            # DB에 저장된 댓글 내용 그대로 사용 (이미 '관리자에 의해 삭제된 댓글입니다.'로 저장됨)
            comments.append({
                'comment_id': comment_obj.comment_id,
                'comment': comment_obj.comment,
                'author': comment_author,
                'is_admin': comment_is_admin,
                'reg_date': comment_obj.reg_date,
                'is_deleted': is_deleted,
            })
        
        # 작성자 정보 안전하게 가져오기
        author_name = article_obj.member_id.nickname if article_obj.member_id and hasattr(article_obj.member_id, 'nickname') else '알 수 없음'
        is_admin = article_obj.member_id.member_id == 1 if article_obj.member_id else False
        
        # 첨부파일 조회
        add_info_objs = AddInfo.objects.filter(article_id=article_id)
        files = []
        images = []
        for add_info in add_info_objs:
            file_ext = os.path.splitext(add_info.file_name)[1].lower()
            is_image = file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
            file_data = {
                'id': add_info.add_info_id,
                'name': add_info.file_name,
                'url': f"{settings.MEDIA_URL}{add_info.path}",
                'is_image': is_image,
            }
            if is_image:
                images.append(file_data)
                # 이미지 파일도 다운로드 링크로 표시하기 위해 files에 추가
                files.append(file_data)
            else:
                files.append(file_data)
        
        # 삭제 여부 확인
        is_deleted = article_obj.delete_date is not None
        
        article = {
            'article_id': article_obj.article_id,
            'title': article_obj.title,
            'contents': article_obj.contents if article_obj.contents else '',
            'author': author_name,
            'is_admin': is_admin,
            'date': article_obj.reg_date.strftime('%Y-%m-%d'),
            'views': article_obj.view_cnt,
            'reg_date': article_obj.reg_date,
            'images': images,  # 이미지 파일들
            'files': files,     # 일반 파일들 (PDF 등)
            'delete_date': article_obj.delete_date.strftime('%Y-%m-%d %H:%M') if article_obj.delete_date else None,
        }
        
        context = {
            'article': article,
            'comments': comments,
            'board_type': 'event',
            'is_manager': is_manager,
            'is_deleted': is_deleted,
        }
        
        return render(request, 'board_detail.html', context)
    except Category.DoesNotExist:
        import traceback
        print(f"[ERROR] event_detail: Category.DoesNotExist - article_id={article_id}")
        print(traceback.format_exc())
        messages.error(request, "이벤트 카테고리를 찾을 수 없습니다.")
        return redirect('/board/event/')
    except Article.DoesNotExist:
        import traceback
        print(f"[ERROR] event_detail: Article.DoesNotExist - article_id={article_id}, category_id={category.category_id if 'category' in locals() else 'N/A'}")
        print(traceback.format_exc())
        messages.error(request, f"게시글을 찾을 수 없습니다. (ID: {article_id})")
        return redirect('/board/event/')
    except Exception as e:
        import traceback
        print(f"[ERROR] event_detail 오류: {str(e)}")
        print(f"[ERROR] article_id={article_id}")
        print(traceback.format_exc())
        messages.error(request, f"게시글을 불러오는 중 오류가 발생했습니다: {str(e)}")
        return redirect('/board/event/')

def post_detail(request, article_id):
    # 로그인 체크
    redirect_response = check_login(request)
    if redirect_response:
        return redirect_response
    
    try:
        # category_type='post'로 조회
        category = get_category_by_type('post')
        
        # 관리자 여부 확인
        manager_id = request.session.get('manager_id')
        is_manager = manager_id == 1 if manager_id else False
        
        # DB에서 게시글 조회 (관리자는 삭제된 게시글도 볼 수 있음)
        if is_manager:
            article_obj = Article.objects.select_related('member_id', 'category_id', 'board_id').get(
                article_id=article_id,
                category_id=category
            )
        else:
            article_obj = Article.objects.select_related('member_id', 'category_id', 'board_id').get(
                article_id=article_id,
                category_id=category,
                delete_date__isnull=True
            )
        
        # 조회수 증가 (삭제되지 않은 게시글만)
        if not article_obj.delete_date:
            article_obj.view_cnt += 1
            article_obj.save(update_fields=['view_cnt'])
        
        # 댓글 조회 및 변환 (삭제된 댓글도 포함)
        comment_objs = Comment.objects.select_related('member_id').filter(
            article_id=article_id
        ).order_by('reg_date')
        
        comments = []
        for comment_obj in comment_objs:
            comment_author = comment_obj.member_id.nickname if comment_obj.member_id and hasattr(comment_obj.member_id, 'nickname') else '알 수 없음'
            comment_is_admin = comment_obj.member_id.member_id == 1 if comment_obj.member_id else False
            is_deleted = comment_obj.delete_date is not None
            # DB에 저장된 댓글 내용 그대로 사용 (이미 '관리자에 의해 삭제된 댓글입니다.'로 저장됨)
            comments.append({
                'comment_id': comment_obj.comment_id,
                'comment': comment_obj.comment,
                'author': comment_author,
                'is_admin': comment_is_admin,
                'reg_date': comment_obj.reg_date,
                'is_deleted': is_deleted,
            })
        
        # 작성자 정보 안전하게 가져오기
        author_name = article_obj.member_id.nickname if article_obj.member_id and hasattr(article_obj.member_id, 'nickname') else '알 수 없음'
        is_admin = article_obj.member_id.member_id == 1 if article_obj.member_id else False
        
        # 첨부파일 조회
        add_info_objs = AddInfo.objects.filter(article_id=article_id)
        files = []
        images = []
        for add_info in add_info_objs:
            file_ext = os.path.splitext(add_info.file_name)[1].lower()
            is_image = file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
            file_data = {
                'id': add_info.add_info_id,
                'name': add_info.file_name,
                'url': f"{settings.MEDIA_URL}{add_info.path}",
                'is_image': is_image,
            }
            if is_image:
                images.append(file_data)
                # 이미지 파일도 다운로드 링크로 표시하기 위해 files에 추가
                files.append(file_data)
            else:
                files.append(file_data)
        
        # 삭제 여부 확인
        is_deleted = article_obj.delete_date is not None
        
        article = {
            'article_id': article_obj.article_id,
            'title': article_obj.title,
            'contents': article_obj.contents if article_obj.contents else '',
            'author': author_name,
            'is_admin': is_admin,
            'date': article_obj.reg_date.strftime('%Y-%m-%d'),
            'views': article_obj.view_cnt,
            'reg_date': article_obj.reg_date,
            'images': images,  # 이미지 파일들
            'files': files,     # 일반 파일들 (PDF 등)
            'delete_date': article_obj.delete_date.strftime('%Y-%m-%d %H:%M') if article_obj.delete_date else None,
        }
        
        context = {
            'article': article,
            'comments': comments,
            'board_type': 'post',
            'is_manager': is_manager,
            'is_deleted': is_deleted,
        }
        
        return render(request, 'board_detail.html', context)
    except Category.DoesNotExist:
        messages.error(request, "수다떨래 카테고리를 찾을 수 없습니다.")
        return redirect('/board/post/')
    except Article.DoesNotExist:
        messages.error(request, "게시글을 찾을 수 없습니다.")
        return redirect('/board/post/')
    except Exception as e:
        import traceback
        print(f"[ERROR] post_detail 오류: {str(e)}")
        print(traceback.format_exc())
        messages.error(request, f"게시글을 불러오는 중 오류가 발생했습니다: {str(e)}")
        return redirect('/board/post/')


# 댓글 작성 함수들
def notice_comment(request, article_id):
    """공지사항 댓글 작성"""
    return create_comment(request, article_id, 'notice')

def event_comment(request, article_id):
    """이벤트 댓글 작성"""
    return create_comment(request, article_id, 'event')

def post_comment(request, article_id):
    """수다떨래 댓글 작성"""
    return create_comment(request, article_id, 'post')

def create_comment(request, article_id, board_type):
    """댓글 작성 공통 함수"""
    print(f"[DEBUG] create_comment 호출: article_id={article_id}, board_type={board_type}")
    
    # 로그인 체크
    redirect_response = check_login(request)
    if redirect_response:
        print(f"[DEBUG] create_comment: 로그인 필요 - 리다이렉트")
        return redirect_response
    
    if request.method != "POST":
        messages.error(request, "잘못된 요청입니다.")
        return redirect(f'/board/{board_type}/')
    
    try:
        # 로그인한 사용자 정보 가져오기 (관리자 우선)
        manager_id = request.session.get('manager_id')
        if manager_id:
            # 관리자인 경우
            member = Member.objects.get(member_id=manager_id)
        else:
            # 일반 사용자인 경우
            login_id = request.session.get('user_id')
            if not login_id:
                messages.error(request, "로그인이 필요합니다.")
                return redirect(f'/login?next=/board/{board_type}/{article_id}/')
            member = Member.objects.get(user_id=login_id)
        print(f"[DEBUG] create_comment: member={member.user_id}")
        
        # 게시글 확인
        category = get_category_by_type(board_type)
        article = Article.objects.get(
            article_id=article_id,
            category_id=category,
            delete_date__isnull=True
        )
        print(f"[DEBUG] create_comment: article={article.title}")
        
        # 댓글 내용 가져오기
        content = request.POST.get('content', '').strip()
        if not content:
            messages.error(request, "댓글 내용을 입력해주세요.")
            return redirect(f'/board/{board_type}/{article_id}/')
        
        # 댓글 생성
        comment = Comment.objects.create(
            comment=content,
            member_id=member,
            article_id=article,
        )
        
        print(f"[DEBUG] create_comment: 댓글 생성 성공 - comment_id={comment.comment_id}")
        
        messages.success(request, "댓글이 등록되었습니다.")
        return redirect(f'/board/{board_type}/{article_id}/')
        
    except Member.DoesNotExist:
        import traceback
        print(f"[ERROR] create_comment: Member.DoesNotExist - user_id={login_id}")
        print(traceback.format_exc())
        messages.error(request, "회원 정보를 찾을 수 없습니다.")
        return redirect(f'/login/')
    except Article.DoesNotExist:
        import traceback
        print(f"[ERROR] create_comment: Article.DoesNotExist - article_id={article_id}, board_type={board_type}")
        print(traceback.format_exc())
        messages.error(request, "게시글을 찾을 수 없습니다.")
        return redirect(f'/board/{board_type}/')
    except Category.DoesNotExist:
        import traceback
        print(f"[ERROR] create_comment: Category.DoesNotExist - board_type={board_type}")
        print(traceback.format_exc())
        messages.error(request, "게시판을 찾을 수 없습니다.")
        return redirect(f'/board/{board_type}/')
    except Exception as e:
        import traceback
        print(f"[ERROR] create_comment 오류: {str(e)}")
        print(f"[ERROR] article_id={article_id}, board_type={board_type}")
        print(traceback.format_exc())
        messages.error(request, f"댓글 작성 중 오류가 발생했습니다: {str(e)}")
        return redirect(f'/board/{board_type}/{article_id}/')


# 파일 업로드 처리 함수는 common/utils.py로 이동됨

@csrf_exempt
def delete_comment(request):
    """관리자 댓글 삭제 API (soft delete)"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'msg': '잘못된 요청입니다.'}, status=400)
    
    # 관리자 권한 확인
    manager_id = request.session.get('manager_id')
    if not manager_id or manager_id != 1:
        return JsonResponse({'status': 'error', 'msg': '관리자 권한이 필요합니다.'}, status=403)
    
    try:
        import json
        data = json.loads(request.body)
        comment_id = data.get('comment_id')
        
        if not comment_id:
            return JsonResponse({'status': 'error', 'msg': '댓글 ID가 필요합니다.'}, status=400)
        
        # 댓글 조회
        comment = Comment.objects.get(comment_id=comment_id)
        
        # 이미 삭제된 댓글인지 확인
        if comment.delete_date:
            return JsonResponse({'status': 'error', 'msg': '이미 삭제된 댓글입니다.'}, status=400)
        
        # Soft delete: delete_date 설정
        from datetime import datetime
        comment.delete_date = datetime.now()
        comment.comment = '관리자에 의해 삭제된 댓글입니다.'
        comment.save()
        
        return JsonResponse({
            'status': 'ok',
            'msg': '댓글이 삭제되었습니다.',
            'comment_id': comment_id
        })
        
    except Comment.DoesNotExist:
        return JsonResponse({'status': 'error', 'msg': '댓글을 찾을 수 없습니다.'}, status=404)
    except Exception as e:
        import traceback
        print(f"[ERROR] delete_comment 오류: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({'status': 'error', 'msg': f'삭제 중 오류가 발생했습니다: {str(e)}'}, status=500)

def faq(request):
    return render(request, 'faq.html')