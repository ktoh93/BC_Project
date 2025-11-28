from django.shortcuts import render
from django.core.paginator import Paginator
# TODO: DB 연결 이후 쿼리로 교체하고 삭제 필요
from common.utils import get_notice_pinned_posts, get_notice_dummy_list, get_event_dummy_list, get_event_pinned_posts

def notice(request):
    # TODO: DB 연결 이후 쿼리로 교체하고 삭제 필요 - 더미 데이터 생성 (100개, 캐싱됨)
    dummy_list = get_notice_dummy_list()
    
    # TODO: DB 연결 이후 쿼리로 교체하고 삭제 필요 - 고정 게시글 5개 생성 (공통 함수 사용)
    pinned_posts = get_notice_pinned_posts()
    
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
        "pinned_posts": pinned_posts,
    }
    
    return render(request, 'notice.html', context)

def event(request):
    # TODO: DB 연결 이후 쿼리로 교체하고 삭제 필요 - 더미 데이터 생성 (100개, 캐싱됨)
    dummy_list = get_event_dummy_list()
    
    # TODO: DB 연결 이후 쿼리로 교체하고 삭제 필요 - 고정 게시글 5개 생성 (공통 함수 사용)
    pinned_posts = get_event_pinned_posts()
    
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
        "pinned_posts": pinned_posts,
    }
    
    return render(request, 'event.html', context)

def post(request):
    # TODO: DB 연결 이후 쿼리로 교체하고 삭제 필요 - 더미 데이터 생성
    # 임시로 notice 더미 데이터 사용 (추후 post 전용 더미 데이터로 교체)
    dummy_list = get_notice_dummy_list()
    
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
    return render(request, 'post_write.html')

def notice_detail(request, article_id):
    # TODO: DB 연결 이후 실제 데이터 조회로 교체
    # article = Article.objects.get(article_id=article_id)
    # comments = Comment.objects.filter(article_id=article_id, delete_date__isnull=True)
    
    # 임시 더미 데이터
    article = {
        'article_id': article_id,
        'title': '공지사항 제목 예시',
        'contents': '공지사항 내용입니다.\n여러 줄로 작성할 수 있습니다.',
        'author': '관리자',
        'date': '2024-01-15',
        'views': 123,
        'reg_date': '2024-01-15 10:00:00',
    }
    
    comments = []  # TODO: 댓글 데이터
    
    context = {
        'article': article,
        'comments': comments,
        'board_type': 'notice',
    }
    
    return render(request, 'board_detail.html', context)

def event_detail(request, article_id):
    # TODO: DB 연결 이후 실제 데이터 조회로 교체
    # article = Article.objects.get(article_id=article_id)
    # comments = Comment.objects.filter(article_id=article_id, delete_date__isnull=True)
    
    # 임시 더미 데이터
    article = {
        'article_id': article_id,
        'title': '이벤트 제목 예시',
        'contents': '이벤트 내용입니다.\n여러 줄로 작성할 수 있습니다.',
        'author': '관리자',
        'date': '2024-01-15',
        'views': 456,
        'reg_date': '2024-01-15 10:00:00',
    }
    
    comments = []  # TODO: 댓글 데이터
    
    context = {
        'article': article,
        'comments': comments,
        'board_type': 'event',
    }
    
    return render(request, 'board_detail.html', context)

def post_detail(request, article_id):
    # TODO: DB 연결 이후 실제 데이터 조회로 교체
    # article = Article.objects.get(article_id=article_id)
    # comments = Comment.objects.filter(article_id=article_id, delete_date__isnull=True)
    
    # 임시 더미 데이터
    article = {
        'article_id': article_id,
        'title': '자유게시판 제목 예시',
        'contents': '자유게시판 내용입니다.\n여러 줄로 작성할 수 있습니다.',
        'author': '사용자1',
        'date': '2024-01-15',
        'views': 789,
        'reg_date': '2024-01-15 10:00:00',
    }
    
    comments = []  # TODO: 댓글 데이터
    
    context = {
        'article': article,
        'comments': comments,
        'board_type': 'post',
    }
    
    return render(request, 'board_detail.html', context)

def faq(request):
    return render(request, 'faq.html')