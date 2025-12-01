from django.shortcuts import render, redirect
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

# TODO: DB 연결 이후 쿼리로 교체하고 삭제 필요
# from common.utils import get_recruitment_dummy_list

    # articles = Article.objects.filter(delete_date__isnull=True).order_by('-article_id')
    # return render(request, 'board/list.html', {'articles': articles})

def recruitment_list(request):
    # 1) 기본 QuerySet
    qs = Community.objects.filter(delete_date__isnull=True).order_by('-community_id')

    # 2) 정렬값
    sort = request.GET.get("sort", "recent")

    if sort == "title":
        qs = qs.order_by("title")
    elif sort == "views":
        qs = qs.order_by("-view_cnt")
    else:  # recent (등록일 최신순)
        qs = qs.order_by("-reg_date")

    # 3) 페이지당 표시 개수
    per_page = int(request.GET.get("per_page", 15))

    # 4) 현재 페이지
    page = int(request.GET.get("page", 1))

    # 5) Paginator
    paginator = Paginator(qs, per_page)
    page_obj = paginator.get_page(page)

    # 6) 블록 페이징
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

        return redirect("recruitment_detail", pk=recruit.pk)

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
        return redirect("recruitment_list")

    # 3) 작성자 본인인지 체크
    if community.member_id != member:
        messages.error(request, "본인이 작성한 글만 수정할 수 있습니다.")
        return redirect("recruitment_detail", pk=pk)

    # 4) POST: 실제 수정 처리
    if request.method == "POST":
        title = request.POST.get("title")
        region = request.POST.get("sido")
        region2 = request.POST.get("sigungu")
        sport_type = request.POST.get("sport")
        num_member = request.POST.get("personnel")
        contents = request.POST.get("content")
        chat_url = request.POST.get("openchat_url") or None

        raw_facility = request.POST.get("facility", "").strip()
        if raw_facility:
            facility = raw_facility
        else:
            facility = "미정"

        community.title = title
        community.region = region
        community.region2 = region2
        community.sport_type = sport_type
        community.num_member = num_member
        community.contents = contents
        community.chat_url = chat_url
        community.facility = facility
        community.update_date = timezone.now()
        community.save()

        return redirect("recruitment_detail", pk=community.pk)

    # 5) GET: 수정 폼 화면
    context = {
        "community": community,
        "recruit": community,
    }
    return render(request, "recruitment_update.html", context)





def detail(request, pk):
    # 0) 로그인 체크
    user_id = request.session.get("user_id")
    if not user_id:
        messages.error(request, "로그인이 필요합니다.")
        return redirect("/login/")
    user_id = request.session.get("user_id")
    login_member = None

    if user_id:
        try:
            login_member = Member.objects.get(user_id=user_id)
        except Member.DoesNotExist:
            login_member = None

    # 모집글
    try:
        recruit = Community.objects.get(pk=pk, delete_date__isnull=True)
    except Community.DoesNotExist:
        raise Http404("존재하지 않는 모집글입니다.")

    # 글 작성자인지 여부
    is_owner = (login_member is not None and recruit.member_id == login_member)

    # ✅ 참여자 목록
    join_list = []
    if is_owner:
        join_list = (
            JoinStat.objects
            .filter(community_id=recruit)
            .select_related("member_id")
            .order_by("join_status", "member_id__user_id")
        )

    # ✅ 댓글 목록 (여기는 원래 쓰시던 코드로)
    comments = Comment.objects.filter(
        community_id=recruit
    ).order_by("reg_date")

    context = {
        "recruit": recruit,
        "is_owner": is_owner,
        "join_list": join_list,
        "comments": comments,
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
    return redirect("recruitment_list")







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
        return redirect("recruitment_detail", pk=pk)

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
    return redirect("recruitment_detail", pk=pk)




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
        return redirect("recruitment_list")

    # 3) 작성자 본인만 변경 가능
    if community.member_id != member:
        messages.error(request, "작성자만 참여 상태를 변경할 수 있습니다.")
        return redirect("recruitment_detail", pk=pk)

    # 4) JoinStat 한 줄 가져오기
    try:
        join_obj = JoinStat.objects.get(id=join_id, community_id=community)
    except JoinStat.DoesNotExist:
        messages.error(request, "해당 참여 신청을 찾을 수 없습니다.")
        return redirect("recruitment_detail", pk=pk)

    # 5) 변경할 상태값 (0=대기, 1=승인, 2=거절 등)
    try:
        new_status = int(request.POST.get("status"))
    except (TypeError, ValueError):
        messages.error(request, "잘못된 상태 값입니다.")
        return redirect("recruitment_detail", pk=pk)

    join_obj.join_status = new_status
    join_obj.save()

    messages.success(request, "참여 상태를 변경했습니다.")
    return redirect("recruitment_detail", pk=pk)