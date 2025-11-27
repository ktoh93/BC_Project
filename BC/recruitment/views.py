from django.shortcuts import render
from django.core.paginator import Paginator
# TODO: DB 연결 이후 쿼리로 교체하고 삭제 필요
from common.utils import get_recruitment_dummy_list

def recruitment_list(request):
    # TODO: DB 연결 이후 쿼리로 교체하고 삭제 필요 - 공통 함수에서 더미 리스트 가져오기
    dummy_list = get_recruitment_dummy_list()

    # 정렬 값 (기본값: 최신순)
    sort = request.GET.get("sort", "recent")

    # 정렬 적용
    if sort == "title":
        dummy_list.sort(key=lambda x: x["title"])
    elif sort == "views":
        dummy_list.sort(key=lambda x: x["views"], reverse=True)
    else:  # recent
        dummy_list.sort(key=lambda x: x["date"], reverse=True)

    # 페이지당 개수
    per_page = int(request.GET.get("per_page", 15))

    # 현재 페이지
    page = int(request.GET.get("page", 1))

    # 페이징 처리
    paginator = Paginator(dummy_list, per_page)
    page_obj = paginator.get_page(page)

    # 블록 페이징 처리
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

        # sort 유지용
        "sort": sort,

        "block_range": block_range,
        "block_start": block_start,
        "block_end": block_end,
    }

    return render(request, "recruitment_list.html", context)


def write(request):
    return render(request, 'recruitment_write.html')
def update(request,pk):
    return render(request, 'recruitment_update.html')
def detail(request, pk):
    recruit={
        'pk':pk,
        'title':'제목~ 운동같이할랭?',
        'sido':'서울특별시',
        'sigungu':'양천구',
        'sport':'축구',
        'personnel':10,
        'facility_name':'체육센터',
        'content' : """sodyudaspjdofpasdjfp;oijwerpoaskdlgj
        asldifj;oawiejr내용입니다!!ㄴ아아아아아아아아앙아아아아아아""",

    }
    context ={
        'recruit':recruit,
    }
    # return render(request, 'recruitment_detail.html')
    return render(request, 'recruitment_detail.html', context)