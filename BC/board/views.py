from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
import os
import uuid
from common.utils import check_login
from board.models import Article, Board, Category
from board.utils import get_category_by_type, get_board_by_name
from common.models import Comment, AddInfo
from member.models import Member
# TODO: DB 연결 이후 쿼리로 교체하고 삭제 필요
from common.utils import get_notice_pinned_posts, get_notice_dummy_list, get_event_dummy_list, get_event_pinned_posts, get_post_dummy_list

def notice(request):
    # DB에서 공지사항 조회 (category_type='notice')
    try:
        category = get_category_by_type('notice')
        articles = Article.objects.select_related('member_id', 'category_id').filter(
            category_id=category,
            delete_date__isnull=True
        ).order_by('-reg_date')
        
        # 상단 고정 게시글 (always_on=0)
        pinned_articles = articles.filter(always_on=0).order_by('-reg_date')[:5]
        # 일반 게시글 (always_on=1)
        normal_articles = articles.filter(always_on=1)
        
        # 검색 기능
        keyword = request.GET.get("keyword", "")
        search_type = request.GET.get("search_type", "all")
        
        if keyword:
            if search_type == "title":
                normal_articles = normal_articles.filter(title__icontains=keyword)
            elif search_type == "author":
                normal_articles = normal_articles.filter(member_id__nickname__icontains=keyword)
            elif search_type == "all":
                normal_articles = normal_articles.filter(
                    Q(title__icontains=keyword) | Q(member_id__nickname__icontains=keyword)
                )
        
        # 정렬 기능
        sort = request.GET.get("sort", "recent")
        if sort == "title":
            normal_articles = normal_articles.order_by('title')
        elif sort == "views":
            normal_articles = normal_articles.order_by('-view_cnt')
        else:  # recent
            normal_articles = normal_articles.order_by('-reg_date')
        
        # 페이징
        per_page = int(request.GET.get("per_page", 15))
        page = int(request.GET.get("page", 1))
        
        paginator = Paginator(normal_articles, per_page)
        page_obj = paginator.get_page(page)
        
        # 상단 고정 게시글 변환
        pinned_posts = []
        for article in pinned_articles:
            pinned_posts.append({
                'id': article.article_id,
                'title': article.title,
                'author': article.member_id.nickname if article.member_id else '',
                'date': article.reg_date.strftime('%Y-%m-%d'),
                'views': article.view_cnt,
            })
        
    except Exception as e:
        # DB 오류 시 빈 리스트
        print(f"[ERROR] notice 함수 오류: {str(e)}")
        pinned_posts = []
        normal_articles = Article.objects.none()
        paginator = Paginator(normal_articles, 15)
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
        category = get_category_by_type('event')
        articles = Article.objects.select_related('member_id', 'category_id').filter(
            category_id=category,
            delete_date__isnull=True
        ).order_by('-reg_date')
        
        # 상단 고정 게시글 (always_on=0)
        pinned_articles = articles.filter(always_on=0).order_by('-reg_date')[:5]
        # 일반 게시글 (always_on=1)
        normal_articles = articles.filter(always_on=1)
        
        # 검색 기능
        keyword = request.GET.get("keyword", "")
        search_type = request.GET.get("search_type", "all")
        
        if keyword:
            if search_type == "title":
                normal_articles = normal_articles.filter(title__icontains=keyword)
            elif search_type == "author":
                normal_articles = normal_articles.filter(member_id__nickname__icontains=keyword)
            elif search_type == "all":
                normal_articles = normal_articles.filter(
                    Q(title__icontains=keyword) | Q(member_id__nickname__icontains=keyword)
                )
        
        # 정렬 기능
        sort = request.GET.get("sort", "recent")
        if sort == "title":
            normal_articles = normal_articles.order_by('title')
        elif sort == "views":
            normal_articles = normal_articles.order_by('-view_cnt')
        else:  # recent
            normal_articles = normal_articles.order_by('-reg_date')
        
        # 페이지네이션
        per_page = int(request.GET.get("per_page", 15))
        page = int(request.GET.get("page", 1))
        
        paginator = Paginator(normal_articles, per_page)
        page_obj = paginator.get_page(page)
        
        # 상단 고정 게시글 변환
        pinned_posts = []
        for article in pinned_articles:
            pinned_posts.append({
                'id': article.article_id,
                'title': article.title,
                'author': article.member_id.nickname if article.member_id else '',
                'date': article.reg_date.strftime('%Y-%m-%d'),
                'views': article.view_cnt,
            })
        
    except Exception as e:
        # DB 오류 시 빈 리스트
        print(f"[ERROR] event 함수 오류: {str(e)}")
        pinned_posts = []
        normal_articles = Article.objects.none()
        paginator = Paginator(normal_articles, 15)
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
        articles = Article.objects.select_related('member_id', 'category_id').filter(
            category_id=category,
            delete_date__isnull=True
        ).order_by('-reg_date')
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
        login_id = request.session.get('user_id')
        try:
            member = Member.objects.get(user_id=login_id)
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
            return redirect('/board/post/')
        except Member.DoesNotExist:
            messages.error(request, "회원 정보를 찾을 수 없습니다.")
            return redirect('/login/')
        except (Category.DoesNotExist, Board.DoesNotExist):
            messages.error(request, "게시판을 찾을 수 없습니다.")
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
        
        # DB에서 게시글 조회
        article_obj = Article.objects.select_related('member_id', 'category_id', 'board_id').get(
            article_id=article_id,
            category_id=category,
            delete_date__isnull=True
        )
        print(f"[DEBUG] notice_detail: 게시글 조회 성공 - title={article_obj.title}")
        
        # 조회수 증가
        article_obj.view_cnt += 1
        article_obj.save(update_fields=['view_cnt'])
        
        # 댓글 조회 및 변환
        comment_objs = Comment.objects.select_related('member_id').filter(
            article_id=article_id,
            delete_date__isnull=True
        ).order_by('reg_date')
        
        comments = []
        for comment_obj in comment_objs:
            comment_author = comment_obj.member_id.nickname if comment_obj.member_id and hasattr(comment_obj.member_id, 'nickname') else '알 수 없음'
            comments.append({
                'comment_id': comment_obj.comment_id,
                'comment': comment_obj.comment,
                'author': comment_author,
                'reg_date': comment_obj.reg_date,
            })
        
        # 작성자 정보 안전하게 가져오기
        author_name = article_obj.member_id.nickname if article_obj.member_id and hasattr(article_obj.member_id, 'nickname') else '알 수 없음'
        
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
            else:
                files.append(file_data)
        
        article = {
            'article_id': article_obj.article_id,
            'title': article_obj.title,
            'contents': article_obj.contents if article_obj.contents else '',
            'author': author_name,
            'date': article_obj.reg_date.strftime('%Y-%m-%d'),
            'views': article_obj.view_cnt,
            'reg_date': article_obj.reg_date,
            'images': images,  # 이미지 파일들
            'files': files,     # 일반 파일들 (PDF 등)
        }
        
        context = {
            'article': article,
            'comments': comments,
            'board_type': 'notice',
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
        
        # DB에서 게시글 조회
        article_obj = Article.objects.select_related('member_id', 'category_id', 'board_id').get(
            article_id=article_id,
            category_id=category,
            delete_date__isnull=True
        )
        print(f"[DEBUG] event_detail: 게시글 조회 성공 - title={article_obj.title}")
        
        # 조회수 증가
        article_obj.view_cnt += 1
        article_obj.save(update_fields=['view_cnt'])
        
        # 댓글 조회 및 변환
        comment_objs = Comment.objects.select_related('member_id').filter(
            article_id=article_id,
            delete_date__isnull=True
        ).order_by('reg_date')
        
        comments = []
        for comment_obj in comment_objs:
            comment_author = comment_obj.member_id.nickname if comment_obj.member_id and hasattr(comment_obj.member_id, 'nickname') else '알 수 없음'
            comments.append({
                'comment_id': comment_obj.comment_id,
                'comment': comment_obj.comment,
                'author': comment_author,
                'reg_date': comment_obj.reg_date,
            })
        
        # 작성자 정보 안전하게 가져오기
        author_name = article_obj.member_id.nickname if article_obj.member_id and hasattr(article_obj.member_id, 'nickname') else '알 수 없음'
        
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
            else:
                files.append(file_data)
        
        article = {
            'article_id': article_obj.article_id,
            'title': article_obj.title,
            'contents': article_obj.contents if article_obj.contents else '',
            'author': author_name,
            'date': article_obj.reg_date.strftime('%Y-%m-%d'),
            'views': article_obj.view_cnt,
            'reg_date': article_obj.reg_date,
            'images': images,  # 이미지 파일들
            'files': files,     # 일반 파일들 (PDF 등)
        }
        
        context = {
            'article': article,
            'comments': comments,
            'board_type': 'event',
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
        
        # DB에서 게시글 조회
        article_obj = Article.objects.select_related('member_id', 'category_id', 'board_id').get(
            article_id=article_id,
            category_id=category,
            delete_date__isnull=True
        )
        
        # 조회수 증가
        article_obj.view_cnt += 1
        article_obj.save(update_fields=['view_cnt'])
        
        # 댓글 조회 및 변환
        comment_objs = Comment.objects.select_related('member_id').filter(
            article_id=article_id,
            delete_date__isnull=True
        ).order_by('reg_date')
        
        comments = []
        for comment_obj in comment_objs:
            comment_author = comment_obj.member_id.nickname if comment_obj.member_id and hasattr(comment_obj.member_id, 'nickname') else '알 수 없음'
            comments.append({
                'comment_id': comment_obj.comment_id,
                'comment': comment_obj.comment,
                'author': comment_author,
                'reg_date': comment_obj.reg_date,
            })
        
        # 작성자 정보 안전하게 가져오기
        author_name = article_obj.member_id.nickname if article_obj.member_id and hasattr(article_obj.member_id, 'nickname') else '알 수 없음'
        
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
            else:
                files.append(file_data)
        
        article = {
            'article_id': article_obj.article_id,
            'title': article_obj.title,
            'contents': article_obj.contents if article_obj.contents else '',
            'author': author_name,
            'date': article_obj.reg_date.strftime('%Y-%m-%d'),
            'views': article_obj.view_cnt,
            'reg_date': article_obj.reg_date,
            'images': images,  # 이미지 파일들
            'files': files,     # 일반 파일들 (PDF 등)
        }
        
        context = {
            'article': article,
            'comments': comments,
            'board_type': 'post',
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
        # 로그인한 사용자 정보 가져오기
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


# 파일 업로드 처리 함수
def handle_file_uploads(request, article):
    """게시글에 첨부된 파일들을 처리하고 AddInfo에 저장"""
    uploaded_files = []
    
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
                
                # 파일명 생성 (UUID로 고유성 보장)
                file_ext = os.path.splitext(file.name)[1]
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
                    'is_image': file_ext.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
                })
                
                print(f"[DEBUG] 파일 업로드 성공: {file.name} -> {relative_path}")
                
            except Exception as e:
                import traceback
                print(f"[ERROR] 파일 업로드 실패 ({file.name}): {str(e)}")
                print(traceback.format_exc())
                continue
    else:
        print(f"[DEBUG] request.FILES에 'file' 키가 없음. 사용 가능한 키: {list(request.FILES.keys())}")
    
    print(f"[DEBUG] handle_file_uploads 완료: {len(uploaded_files)}개 파일 업로드됨")
    return uploaded_files

def faq(request):
    return render(request, 'faq.html')