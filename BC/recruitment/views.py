from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404
from django.utils import timezone
from django.core.paginator import Paginator
from .models import *

from member.models import Member
from common.models import Comment

from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib import messages

from django.views.decorators.http import require_POST
from django.db import transaction, IntegrityError
from django.db.models import Q

# TODO: DB 연결 이후 쿼리로 교체하고 삭제 필요
# from common.utils import get_recruitment_dummy_list

    # articles = Article.objects.filter(delete_date__isnull=True).order_by('-article_id')
    # return render(request, 'board/list.html', {'articles': articles})



def recruitment_list(request):
    # 0) 검색 파라미터 받기
    search_type = request.GET.get("search_type", "all")   # 전체 / facility / sport
    keyword = request.GET.get("keyword", "").strip()
    sido = request.GET.get("sido", "")
    sigungu = request.GET.get("sigungu", "")

    # 1) 기본 QuerySet
    qs = Community.objects.filter(delete_date__isnull=True)

    # 2) 지역 필터
    if sido:
        qs = qs.filter(sido=sido)
    if sigungu:
        qs = qs.filter(sigungu=sigungu)

    # 3) 검색어 필터
    if keyword:
        if search_type == "facility":
            qs = qs.filter(facility_name__icontains=keyword)
        elif search_type == "sport":
            qs = qs.filter(sport__icontains=keyword)
        else:  # all
            qs = qs.filter(
                Q(title__icontains=keyword) |
                Q(facility_name__icontains=keyword) |
                Q(sport__icontains=keyword)
            )

    # 4) 정렬값
    sort = request.GET.get("sort", "recent")

    if sort == "title":
        qs = qs.order_by("title")
    elif sort == "views":
        qs = qs.order_by("-view_cnt")
    else:  # recent (등록일 최신순)
        qs = qs.order_by("-reg_date")

    # 5) 페이지당 표시 개수
    per_page = int(request.GET.get("per_page", 15))

    # 6) 현재 페이지
    page = int(request.GET.get("page", 1))

    # 7) Paginator
    paginator = Paginator(qs, per_page)
    page_obj = paginator.get_page(page)

    # 8) 블록 페이징
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

        # 검색값 다시 템플릿에 넘겨서 유지
        "search_type": search_type,
        "keyword": keyword,
        "sido": sido,
        "sigungu": sigungu,
    }

    return render(request, "recruitment_list.html", context)




def write(request):
    # 0) 세션에 로그인 정보 있는지 확인
    user_id = request.session.get("user_id")   # 로그인할 때 넣어줬던 값

    if not user_id:
        messages.error(request, "로그인이 필요합니다.")
        return redirect("/login/")  # 로그인 URL에 맞게 수정

    # 1) 세션의 user_id 로 Member 객체 가져오기
    try:
        member = Member.objects.get(user_id=user_id)
    except Member.DoesNotExist:
        # 세션에는 있는데 실제 회원은 없으면 세션 정리 후 로그인 페이지로
        request.session.flush()
        messages.error(request, "다시 로그인 해주세요.")
        return redirect("/login/")

    # 2) POST 처리
    if request.method == "POST":
        title = request.POST.get("title")
        region = request.POST.get("sido")
        region2 = request.POST.get("sigungu")
        sport_type = request.POST.get("sport")
        num_member = request.POST.get("personnel")
        contents = request.POST.get("content")
        chat_url = request.POST.get("openchat_url") or None   # 빈값이면 None

        # facility = request.POST.get("facility_name") or None   # 빈값이면 None
        
        # 🔹 시설 입력값 처리
        raw_facility = request.POST.get("facility", "").strip()
        if raw_facility:
            facility = raw_facility
        else:
            facility = "미정"   # ← NULL 절대 안 보내게 강제
        
        recruit = Community.objects.create(
            title=title,
            region=region,
            region2=region2,
            sport_type=sport_type,
            num_member=num_member,
            facility=facility,
            contents=contents,
            chat_url=chat_url,
            member_id=member,   # ✅ FK 에 실제 Member 인스턴스 넣기
        )

        return redirect("recruitment:recruitment_detail", pk=recruit.pk)

    # 3) GET 요청이면 작성 폼 보여주기
    return render(request, "recruitment_write.html")





def update(request, pk):
    # 0) 세션 로그인 확인
    user_id = request.session.get("user_id")
    if not user_id:
        messages.error(request, "로그인이 필요합니다.")
        return redirect("/login/")

    # 1) 세션의 user_id 로 Member 가져오기
    try:
        member = Member.objects.get(user_id=user_id)
    except Member.DoesNotExist:
        request.session.flush()
        messages.error(request, "다시 로그인 해주세요.")
        return redirect("/login/")

    # 2) 수정할 모집글 가져오기  🔻 여기만 수정
    try:
        community = Community.objects.get(
            pk=pk,
            delete_date__isnull=True,  # 삭제된 글은 아예 못 열게
        )
    except Community.DoesNotExist:
        messages.error(request, "삭제되었거나 존재하지 않는 모집글입니다.")
        return redirect("recruitment:recruitment_list")

    # 3) 작성자 본인인지 체크
    if community.member_id != member:
        messages.error(request, "본인이 작성한 글만 수정할 수 있습니다.")
        return redirect("recruitment:recruitment_detail", pk=pk)

    # 4) POST: 실제 수정 처리
    if request.method == "POST":
        contents = request.POST.get("content")
        community.contents = contents

        community.update_date = timezone.now()
        community.save()

        return redirect("recruitment:recruitment_detail", pk=community.pk)

    # 5) GET: 수정 폼 화면
    context = {
        "community": community,
        "recruit": community,
    }
    return render(request, "recruitment_update.html", context)






# def detail(request, pk):
#     # 0) 로그인 체크
#     user_id = request.session.get("user_id")
#     if not user_id:
#         messages.error(request, "로그인이 필요합니다.")
#         return redirect("/login/")

#     login_member = None
#     if user_id:
#         try:
#             login_member = Member.objects.get(user_id=user_id)
#         except Member.DoesNotExist:
#             login_member = None

#     # 관리자 여부 확인
#     manager_id = request.session.get('manager_id')
#     is_manager = manager_id == 1 if manager_id else False

#     # 모집글 조회 (관리자는 삭제된 게시글도 볼 수 있음)
#     try:
#         if is_manager:
#             recruit = Community.objects.get(pk=pk)
#         else:
#             recruit = Community.objects.get(pk=pk, delete_date__isnull=True)
#     except Community.DoesNotExist:
#         raise Http404("존재하지 않는 모집글입니다.")

#     # 조회수 증가
#     recruit.view_cnt += 1
#     recruit.save()

#     # 글 작성자인지 여부
#     is_owner = (login_member is not None and recruit.member_id == login_member)

#     # ✅ 참여자 공통 queryset
#     joins_qs = JoinStat.objects.filter(community_id=recruit)

#     # ✅ 인원 수 집계
#     total_join_count = joins_qs.count()
#     approved_count = joins_qs.filter(join_status=1).count()
#     waiting_rejected_count = joins_qs.filter(join_status__in=[0, 2]).count()

#     # ✅ 정원/마감 여부
#     capacity = recruit.num_member or 0
#     is_full = capacity > 0 and approved_count >= capacity
#     remaining_slots = max(capacity - approved_count, 0)

#     # ✅ 상세 목록은 소유자/관리자에게만
#     join_list = []
#     if is_owner or is_manager:
#         join_list = (
#             joins_qs
#             .select_related("member_id")
#             .order_by("join_status", "member_id__user_id")
#         )

#     # ✅ 댓글 목록
#     comments = Comment.objects.filter(
#         community_id=recruit,
#         delete_date__isnull=True
#     ).order_by("reg_date")

#     # 삭제 여부 확인
#     is_deleted = recruit.delete_date is not None

#     context = {
#         "recruit": recruit,
#         "is_owner": is_owner,
#         "is_manager": is_manager,
#         "join_list": join_list,

#         "total_join_count": total_join_count,
#         "approved_count": approved_count,
#         "waiting_rejected_count": waiting_rejected_count,

#         "capacity": capacity,
#         "is_full": is_full,
#         "remaining_slots": remaining_slots,

#         "comments": comments,
#         "is_deleted": is_deleted,
#     }

#     return render(request, "recruitment_detail.html", context)



# recruitment/views.py



def detail(request, pk):
    # 0) 로그인 체크
    user_id = request.session.get("user_id")
    if not user_id:
        messages.error(request, "로그인이 필요합니다.")
        return redirect("/login/")

    login_member = None
    if user_id:
        try:
            login_member = Member.objects.get(user_id=user_id)
        except Member.DoesNotExist:
            login_member = None

    # 관리자 여부 확인
    manager_id = request.session.get('manager_id')
    is_manager = manager_id == 1 if manager_id else False

    # 모집글 조회 (관리자는 삭제된 게시글도 볼 수 있음)
    try:
        if is_manager:
            recruit = Community.objects.get(pk=pk)
        else:
            recruit = Community.objects.get(pk=pk, delete_date__isnull=True)
    except Community.DoesNotExist:
        raise Http404("존재하지 않는 모집글입니다.")

    # 조회수 증가
    recruit.view_cnt += 1
    recruit.save()

    # 글 작성자인지 여부
    is_owner = (login_member is not None and recruit.member_id == login_member)

    # ✅ 참여자 공통 queryset
    joins_qs = JoinStat.objects.filter(community_id=recruit)

    # ✅ 인원 수 집계
    total_join_count = joins_qs.count()
    approved_count = joins_qs.filter(join_status=1).count()
    waiting_rejected_count = joins_qs.filter(join_status__in=[0, 2]).count()

    # ✅ 정원/마감 여부 (인원 기준)
    capacity = recruit.num_member or 0
    is_full = capacity > 0 and approved_count >= capacity
    remaining_slots = max(capacity - approved_count, 0)

    # ✅ EndStatus 기준 수동 마감 여부
    try:
        end_status = EndStatus.objects.get(community=recruit)
        is_closed = (end_status.end_stat == 1)
    except EndStatus.DoesNotExist:
        end_status = None
        is_closed = False

    # 둘 중 하나라도 true면 화면에서는 “모집 마감”
    is_closed_or_full = is_full or is_closed

    # ✅ 상세 목록은 소유자/관리자에게만
    join_list = []
    if is_owner or is_manager:
        join_list = (
            joins_qs
            .select_related("member_id")
            .order_by("join_status", "member_id__user_id")
        )

    # ✅ 댓글 목록
    comments = Comment.objects.filter(
        community_id=recruit,
        delete_date__isnull=True
    ).order_by("reg_date")

    # 삭제 여부 확인
    is_deleted = recruit.delete_date is not None

    context = {
        "recruit": recruit,
        "is_owner": is_owner,
        "is_manager": is_manager,
        "join_list": join_list,

        "total_join_count": total_join_count,
        "approved_count": approved_count,
        "waiting_rejected_count": waiting_rejected_count,

        "capacity": capacity,
        "is_full": is_full,
        "remaining_slots": remaining_slots,

        "is_closed": is_closed,
        "is_closed_or_full": is_closed_or_full,

        "comments": comments,
        "is_deleted": is_deleted,
    }

    return render(request, "recruitment_detail.html", context)





def delete(request, pk):
    # 0) 로그인 체크
    user_id = request.session.get("user_id")
    if not user_id:
        messages.error(request, "로그인이 필요합니다.")
        return redirect("/login/")

    # 1) 세션 user_id 로 Member 조회
    try:
        member = Member.objects.get(user_id=user_id)
    except Member.DoesNotExist:
        request.session.flush()
        messages.error(request, "다시 로그인 해주세요.")
        return redirect("/login/")

    # 2) 삭제 대상 글 조회
    try:
        community = Community.objects.get(pk=pk)
    except Community.DoesNotExist:
        raise Http404("존재하지 않는 글입니다.")

    # 3) 작성자 본인 확인 (URL로 악의적 접근 방지)
    if community.member_id != member:
        messages.error(request, "작성자만 글을 삭제할 수 있습니다.")
        return redirect("recruitment_detail", pk=pk)

    # 4) soft delete
    community.delete_date = timezone.now()
    community.save()

    messages.success(request, "글이 삭제되었습니다.")
    return redirect("recruitment:recruitment_list")







def join(request, pk):
    # 0) 로그인 체크
    user_id = request.session.get("user_id")
    if not user_id:
        messages.error(request, "로그인이 필요합니다.")
        return redirect("/member/login/")

    # 1) 세션의 user_id 로 Member 찾기
    try:
        member = Member.objects.get(user_id=user_id)
    except Member.DoesNotExist:
        request.session.flush()
        messages.error(request, "다시 로그인 해주세요.")
        return redirect("/login/")

    # 2) 모집 글 가져오기
    try:
        community = Community.objects.get(pk=pk)
    except Community.DoesNotExist:
        raise Http404("존재하지 않는 모집글입니다.")

    # 3) 본인 글 참여 방지 (URL 직접 입력하는 놈 방어)
    if community.member_id == member:
        messages.error(request, "본인이 작성한 글에는 참여 신청을 할 수 없습니다.")
        return redirect("recruitment:recruitment_detail", pk=pk)

    # 4) JoinStat 생성 (이미 있으면 그대로)
    try:
        join_obj, created = JoinStat.objects.get_or_create(
            member_id=member,
            community_id=community,
            defaults={"join_status": 0},   # 0 = 대기
        )
    except IntegrityError:
        join_obj = JoinStat.objects.get(
            member_id=member,
            community_id=community
        )
        created = False

    # 5) 메시지
    if created:
        messages.success(request, "참여 신청이 완료되었습니다. 작성자의 승인 후 확정됩니다.")
    else:
        messages.info(request, "이미 이 모집에 참여 신청을 하셨습니다.")

    # 6) 상세 페이지로 복귀
    return redirect("recruitment:recruitment_detail", pk=pk)




@require_POST           # GET말고 POST만 받음
@transaction.atomic     # DB 저장시 꼬이지 않게
def update_join_status(request, pk, join_id):
    # 0) 로그인 체크
    user_id = request.session.get("user_id")
    if not user_id:
        messages.error(request, "로그인이 필요합니다.")
        return redirect("/member/login/")

    # 1) 로그인 유저
    try:
        member = Member.objects.get(user_id=user_id)
    except Member.DoesNotExist:
        request.session.flush()
        messages.error(request, "다시 로그인 해주세요.")
        return redirect("/member/login/")

    # 2) 모집글
    try:
        community = Community.objects.get(pk=pk, delete_date__isnull=True)
    except Community.DoesNotExist:
        messages.error(request, "삭제되었거나 존재하지 않는 모집글입니다.")
        return redirect("recruitment:recruitment_list")

    # 3) 작성자 본인만 변경 가능
    if community.member_id != member:
        messages.error(request, "작성자만 참여 상태를 변경할 수 있습니다.")
        return redirect("recruitment:recruitment_detail", pk=pk)

    # 4) JoinStat 한 줄 가져오기
    try:
        join_obj = JoinStat.objects.get(id=join_id, community_id=community)
    except JoinStat.DoesNotExist:
        messages.error(request, "해당 참여 신청을 찾을 수 없습니다.")
        return redirect("recruitment:recruitment_detail", pk=pk)

    # 5) 변경할 상태값 (0=대기, 1=승인, 2=거절 등)
    try:
        new_status = int(request.POST.get("status"))
    except (TypeError, ValueError):
        messages.error(request, "잘못된 상태 값입니다.")
        return redirect("recruitment:recruitment_detail", pk=pk)

    join_obj.join_status = new_status
    join_obj.save()

    messages.success(request, "참여 상태를 변경했습니다.")
    return redirect("recruitment:recruitment_detail", pk=pk)





# 댓글 추가 기능
def add_comment(request, pk):
    # GET 으로 들어오면 그냥 상세로 돌려보냄
    if request.method != "POST":
        return redirect("recruitment:recruitment_detail", pk=pk)

    # 0) 세션 로그인 확인
    user_id = request.session.get("user_id")
    if not user_id:
        messages.error(request, "로그인이 필요합니다.")
        return redirect("/login/")

    # 1) 로그인 회원
    try:
        member = Member.objects.get(user_id=user_id)
    except Member.DoesNotExist:
        request.session.flush()
        messages.error(request, "다시 로그인 해주세요.")
        return redirect("/login/")

    # 2) 대상 모집글
    community = get_object_or_404(
        Community,
        pk=pk,
        delete_date__isnull=True,
    )

    # 3) 폼에서 넘어온 댓글 내용
    content = request.POST.get("content", "").strip()
    if not content:
        messages.error(request, "댓글 내용을 입력해 주세요.")
        return redirect("recruitment:recruitment_detail", pk=pk)

    # 4) 댓글 생성
    Comment.objects.create(
        community_id=community,
        member_id=member,
        comment=content,
    )

    messages.success(request, "댓글이 등록되었습니다.")
    return redirect("recruitment:recruitment_detail", pk=pk)





# 모집 마감 여부 체크

def close_recruitment(request, pk):
    # 로그인 체크
    user_id = request.session.get("user_id")
    if not user_id:
        messages.error(request, "로그인이 필요합니다.")
        return redirect("/login/")

    # 글 가져오기 (삭제된 글은 마감 안 하도록)
    try:
        recruit = Community.objects.get(pk=pk, delete_date__isnull=True)
    except Community.DoesNotExist:
        raise Http404("존재하지 않는 모집글입니다.")

    # 작성자 / 관리자 확인
    login_member = Member.objects.filter(user_id=user_id).first()
    manager_id = request.session.get("manager_id")
    is_manager = manager_id == 1 if manager_id else False
    is_owner = (login_member is not None and recruit.member_id == login_member)

    if not (is_owner or is_manager):
        messages.error(request, "모집을 마감할 권한이 없습니다.")
        return redirect("recruitment:recruitment_detail", pk=pk)

    if request.method == "POST":
        today = timezone.now().date()
        end_status, created = EndStatus.objects.get_or_create(
            community=recruit,
            defaults={
                "end_set_date": today,
            },
        )
        end_status.end_stat = 1
        end_status.end_date = today
        if not end_status.end_set_date:
            end_status.end_set_date = today
        end_status.save()
        messages.success(request, "모집을 마감했습니다.")

    return redirect("recruitment:recruitment_detail", pk=pk)
