from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404
from django.utils import timezone
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt


from .models import *
from reservation.models import *
from member.models import Member
from common.models import *
from facility.models import FacilityInfo
from common.utils import is_manager

from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib import messages

from django.views.decorators.http import require_POST
from django.db import transaction, IntegrityError
from django.db.models import Q, F, Count

from collections import OrderedDict

import os
import uuid
from django.conf import settings

from django.db.models import Q
from django.core.paginator import Paginator

from common.utils import check_login


def recruitment_list(request):
    
    search_type = request.GET.get("search_type", "all")
    keyword = request.GET.get("keyword", "").strip()
    sido = request.GET.get("sido", "")
    sigungu = request.GET.get("sigungu", "")
    status = request.GET.get("status", "all")

    # 모집글 + end_status + 참가자수 join
    qs = (
        Community.objects
        .filter(delete_date__isnull=True)
        .select_related("endstatus")
        .annotate(
            current_member=Count("joinstat"),
            comment_count = Count('comment', distinct=True),
        )
    )

    # 지역 필터
    if sido:
        qs = qs.filter(region=sido)
    if sigungu:
        qs = qs.filter(region2=sigungu)

    # 검색 필터
    if keyword:
        if search_type == "facility":
            qs = qs.filter(facility__icontains=keyword)
        elif search_type == "sport":
            qs = qs.filter(sport_type__icontains=keyword)
        else:
            qs = qs.filter(
                Q(title__icontains=keyword) |
                Q(facility__icontains=keyword) |
                Q(sport_type__icontains=keyword)
            )

    # 모집 상태 필터
    if status == "closed":
        qs = qs.filter(endstatus__end_stat=1)
    elif status == "open":
        qs = qs.exclude(endstatus__end_stat=1)

    # 정렬
    sort = request.GET.get("sort", "recent")
    if sort == "title":
        qs = qs.order_by("title")
    elif sort == "views":
        qs = qs.order_by("-view_cnt")
    else:
        qs = qs.order_by("-reg_date")

    # 페이지네이션
    per_page = int(request.GET.get("per_page", 15))
    page = int(request.GET.get("page", 1))
    paginator = Paginator(qs, per_page)
    page_obj = paginator.get_page(page)

    # 블록 페이징
    block_size = 5
    current_block = (page - 1) // block_size
    block_start = current_block * block_size + 1
    block_end = min(block_start + block_size - 1, paginator.num_pages)
    block_range = range(block_start, block_end + 1)

    # 템플릿용 마감 상태
    for obj in page_obj:
        es = getattr(obj, "endstatus", None)
        obj.is_closed = (es and es.end_stat == 1)





    context = {
        "page_obj": page_obj,
        "paginator": paginator,
        "page": page,
        "per_page": per_page,
        "sort": sort,
        "search_type": search_type,
        "keyword": keyword,
        "sido": sido,
        "sigungu": sigungu,
        "status": status,
        "block_range": block_range,
        "block_start": block_start,
        "block_end": block_end,
    }

    return render(request, "recruitment/recruitment_list.html", context)


# recruitment/views.py

def write(request):
    
    res = check_login(request)
    if res:
        return res
      
    user_id = request.session.get("user_id")


    # 1) 세션의 user_id 로 Member 객체 가져오기
    try:
        member = Member.objects.get(user_id=user_id)
    except Member.DoesNotExist:
        request.session.flush()
        messages.error(request, "다시 로그인 해주세요.")
        return redirect("common:login")

    # ✅ 이 회원이 이미 모집글에 사용한 reservation_id 목록
    used_reservation_ids = (
        Community.objects
        .filter(
            member_id=member,
            delete_date__isnull=True,
        )
        .exclude(reservation_id__isnull=True)
        .values_list("reservation_id", flat=True)
    )

    # 🔹 이 회원의 "아직 모집글에 쓰지 않은" 예약 목록
    my_reservations = (
        Reservation.objects
        .filter(
            member=member,
            delete_date__isnull=True,
        )
        .exclude(pk__in=used_reservation_ids)
        .order_by("-reg_date")
    )

    # 🔹 그 예약들에 속한 타임슬롯 (delete_yn = 0) + 이미 사용한 reservation 제외
    my_slots = (
        TimeSlot.objects
        .filter(
            reservation_id__member=member,
            reservation_id__delete_date__isnull=True,
            delete_yn=0,
        )
        .exclude(reservation_id_id__in=used_reservation_ids)  # 🔥 이미 쓴 예약 제외
        .select_related("reservation_id", "facility_id")
        .order_by("reservation_id", "date", "start_time")
    )

    # 예약 단위로 그룹핑
    grouped_slots = OrderedDict()
    for slot in my_slots:
        rid = slot.reservation_id_id  # 또는 slot.reservation_id.pk

        if rid not in grouped_slots:
            grouped_slots[rid] = {
                "reservation": slot.reservation_id,
                "facility": slot.facility_id,
                "times": []
            }

        grouped_slots[rid]["times"].append({
            "t_id": slot.t_id,
            "date": slot.date,
            "start_time": slot.start_time,
            "end_time": slot.end_time,
        })

    my_reservation_slots = list(grouped_slots.values())

    # 2) POST 처리
    if request.method == "POST":
        print("POST data:", request.POST)
        title = request.POST.get("title")
        region = request.POST.get("sido")
        region2 = request.POST.get("sigungu")
        sport_type = request.POST.get("sport")
        num_member = request.POST.get("personnel")
        contents = request.POST.get("content")
        chat_url = request.POST.get("openchat_url") or None

        reservation_id = (request.POST.get("reservation_choice") or "").strip()

        facility_name = "미정"
        reservation_obj = None

        if reservation_id:
            # 선택된 예약 객체
            reservation_obj = (
                Reservation.objects
                .filter(
                    pk=reservation_id,
                    member=member,
                    delete_date__isnull=True,
                )
                .first()
            )

            # 선택된 예약 기준으로 시설/지역 세팅
            slot = (
                TimeSlot.objects
                .select_related("facility_id", "reservation_id")
                .filter(
                    reservation_id_id=reservation_id,
                    reservation_id__member=member,
                    reservation_id__delete_date__isnull=True,
                    delete_yn=0,
                )
                .first()
            )
            if slot:
                facility = slot.facility_id
                facility_name = facility.faci_nm
                region = facility.sido
                region2 = facility.sigugun

        recruit = Community.objects.create(
            title=title,
            region=region,
            region2=region2,
            sport_type=sport_type,
            num_member=num_member,
            facility=facility_name,
            contents=contents,
            chat_url=chat_url,
            member_id=member,
            # 🔥 여기: Community 모델의 FK 이름이 "reservation_id"
            reservation_id=reservation_obj,
        )

        files = request.FILES.getlist("files")

        for f in files:
            original_name = f.name                      # 원본 파일명
            ext = os.path.splitext(original_name)[1]    # 확장자 (.jpg, .pdf 등)
            encoded_name = f"{uuid.uuid4().hex}{ext}"   # 서버에 저장할 랜덤 이름

            # 실제 저장 경로(원하는 폴더로 바꿔도 됨)
            save_dir = "upload/recruit"                 # MEDIA_ROOT 기준 하위 폴더
            save_path = os.path.join(save_dir, encoded_name)
            full_path = os.path.join(settings.MEDIA_ROOT, save_path)

            # 디렉터리 없으면 생성
            os.makedirs(os.path.dirname(full_path), exist_ok=True)

            # 파일 실제 저장
            with open(full_path, "wb+") as dest:
                for chunk in f.chunks():
                    dest.write(chunk)

            # add_info 테이블에 메타데이터 저장
            AddInfo.objects.create(
                community_id = recruit,     # FK 는 인스턴스로 넘기는 게 정석
                path         = save_path,   # 나중에 MEDIA_URL + path 로 접근
                file_name    = original_name,
                encoded_name = encoded_name,
                # reg_date 는 model 에 auto_now_add=True 면 안 넣어도 됨
            )
        return redirect("recruitment:recruitment_detail", pk=recruit.pk)

    # 3) GET 요청이면 작성 폼 + 내 예약 목록 넘기기
    context = {
        "my_reservations": my_reservations,
        "my_reservation_slots": my_reservation_slots,
    }
    return render(request, "recruitment/recruitment_write.html", context)







def update(request, pk):
    """
    모집글 수정
    - 작성자 본인만 수정 가능
    - 예약 선택: 내 예약 중, 같은 지역 + delete_yn=0 + 다른 모집글에서 이미 쓴 예약은 제외
    - 첨부파일:
      * 기존 파일 목록 표시
      * 체크한 파일만 실제 삭제(DB + 파일)
      * 새로 업로드한 파일은 AddInfo 로 추가
    """

    # 0) 로그인 체크
    res = check_login(request)
    if res:
        return res

    user_id = request.session.get("user_id")

    # 1) 세션의 user_id 로 Member 가져오기
    try:
        member = Member.objects.get(user_id=user_id)
    except Member.DoesNotExist:
        request.session.flush()
        messages.error(request, "다시 로그인 해주세요.")
        return redirect("common:login")

    # 2) 수정할 모집글 가져오기 (soft delete 된 글 제외)
    try:
        community = Community.objects.get(
            pk=pk,
            delete_date__isnull=True,
        )
    except Community.DoesNotExist:
        messages.error(request, "삭제되었거나 존재하지 않는 모집글입니다.")
        return redirect("recruitment:recruitment_list")

    # 3) 작성자 본인인지 체크
    if community.member_id != member:
        messages.error(request, "본인이 작성한 글만 수정할 수 있습니다.")
        return redirect("recruitment:recruitment_detail", pk=pk)

    # 🔹 이 글에 지금 연결돼 있는 예약 PK (없으면 None)
    current_reservation_id = community.reservation_id_id  # FK: reservation_id 기준

    # ----------------------------------------
    # 🔹 이미 다른 모집글에서 사용 중인 예약 PK 목록
    #    - 내 글들 중 (soft delete X)
    #    - reservation_id 가 있는 글들만
    #    - 지금 수정 중인 글은 제외
    # ----------------------------------------
    used_reservation_ids = (
        Community.objects
        .filter(
            member_id=member,
            delete_date__isnull=True,
        )
        .exclude(reservation_id__isnull=True)
        .exclude(reservation_id_id=current_reservation_id)
        .values_list("reservation_id_id", flat=True)
    )

    # ----------------------------------------
    # 🔹 현재 지역에 맞는 나의 타임슬롯 중
    #    - delete_yn = 0
    #    - 예약(Reservation) soft delete X
    #    - 이미 다른 모집글에서 사용된 reservation_id 는 제외
    # ----------------------------------------
    my_slots = (
        TimeSlot.objects
        .filter(
            reservation_id__member=member,
            reservation_id__delete_date__isnull=True,
            delete_yn=0,
            facility_id__sido=community.region,
            facility_id__sigugun=community.region2,
        )
        .exclude(reservation_id_id__in=used_reservation_ids)
        .select_related("reservation_id", "facility_id")
        .order_by("reservation_id", "date", "start_time")
    )

    # 🔹 이 타임슬롯들에 해당하는 예약 목록
    reservation_ids = {slot.reservation_id_id for slot in my_slots}

    my_reservations = (
        Reservation.objects
        .filter(
            member=member,
            delete_date__isnull=True,
            pk__in=reservation_ids,
        )
        .order_by("-reg_date")
    )

    # ----------------------------------------
    # 🔹 write()와 동일한 grouped 구조 만들기
    # ----------------------------------------
    grouped_slots = OrderedDict()
    for slot in my_slots:
        rid = slot.reservation_id_id

        if rid not in grouped_slots:
            grouped_slots[rid] = {
                "reservation": slot.reservation_id,
                "facility": slot.facility_id,
                "times": [],
            }

        grouped_slots[rid]["times"].append({
            "t_id": slot.t_id,
            "date": slot.date,
            "start_time": slot.start_time,
            "end_time": slot.end_time,
        })

    my_reservation_slots = list(grouped_slots.values())

    # ----------------------------------------
    # 🔹 이 모집글의 기존 첨부파일 목록 (모두)
    #    - delete_date 없으니까 그냥 community 기준으로만 필터
    # ----------------------------------------
    existing_files = AddInfo.objects.filter(
        community_id=community,
    )

    # 4) POST: 실제 수정 처리
    if request.method == "POST":
        # ✅ 내용 수정
        contents = request.POST.get("content", "").strip()
        community.contents = contents
        community.update_date = timezone.now()

        # ✅ 1) 삭제할 첨부파일 체크 처리 (실제 삭제)
        delete_ids = request.POST.getlist("delete_files")  # 체크박스 name="delete_files"

        if delete_ids:
            to_delete_qs = AddInfo.objects.filter(
                community_id=community,
                pk__in=delete_ids,
            )

            # 파일까지 같이 삭제
            for info in to_delete_qs:
                if info.path:  # path 에 상대 경로 저장되어 있다고 가정
                    file_path = os.path.join(settings.MEDIA_ROOT, info.path)
                    if os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                        except OSError:
                            # 파일 없거나 권한 문제면 그냥 무시
                            pass

            # DB row 삭제
            to_delete_qs.delete()

        # ✅ 2) 예약 선택값 처리
        reservation_id = (request.POST.get("reservation_choice") or "").strip()

        # 기본은 기존 값 유지
        facility_name = community.facility

        if reservation_id:
            slot = (
                TimeSlot.objects
                .select_related("facility_id", "reservation_id")
                .filter(
                    reservation_id_id=reservation_id,
                    reservation_id__member=member,
                    reservation_id__delete_date__isnull=True,
                    delete_yn=0,
                )
                .first()
            )
            if slot:
                facility = slot.facility_id
                facility_name = facility.faci_nm

                # 예약 기준으로 지역 동기화
                community.region = facility.sido
                community.region2 = facility.sigugun

                # 예약 FK 변경
                community.reservation_id = slot.reservation_id

        # ✅ 3) 새 첨부파일 업로드 처리
        files = request.FILES.getlist("files")  # <input type="file" name="files" multiple>

        for f in files:
            if not f:
                continue

            original_name = f.name
            ext = os.path.splitext(original_name)[1]
            encoded_name = f"{uuid.uuid4().hex}{ext}"

            # 저장 경로 (MEDIA_ROOT 기준)
            save_dir = "upload/recruit"
            save_path = os.path.join(save_dir, encoded_name)
            full_path = os.path.join(settings.MEDIA_ROOT, save_path)

            os.makedirs(os.path.dirname(full_path), exist_ok=True)

            with open(full_path, "wb+") as dest:
                for chunk in f.chunks():
                    dest.write(chunk)

            AddInfo.objects.create(
                community_id=community,   # FK 인스턴스
                path=save_path,
                file_name=original_name,
                encoded_name=encoded_name,
            )

        # ✅ 시설 이름 최종 반영 + 저장
        community.facility = facility_name
        community.save()

        return redirect("recruitment:recruitment_detail", pk=community.pk)

    # 5) GET: 수정 폼 화면
    context = {
        "community": community,
        "recruit": community,                 # 템플릿에서 recruit 로 쓰고 있으면 유지
        "my_reservations": my_reservations,
        "my_reservation_slots": my_reservation_slots,
        "current_reservation_id": current_reservation_id,
        "existing_files": existing_files,     # ✅ 기존 첨부파일 목록
    }
    return render(request, "recruitment/recruitment_update.html", context)







def detail(request, pk):
    # 로그인 체크
    
    res = check_login(request)
    if res:
        return res
    
    user_id = request.session.get("user_id")

    login_member = Member.objects.filter(user_id=user_id).first()

    # 관리자 여부
    
    is_manager_user = is_manager(request)
    
    
    # 모집글 조회 (삭제되지 않은 것만)
    try:
        recruit = Community.objects.get(pk=pk, delete_date__isnull=True)
    except Community.DoesNotExist:
        raise Http404("존재하지 않는 모집글입니다.")

    # 조회수 증가
    recruit.view_cnt += 1
    recruit.save()

    # 참여자 목록
    joins_qs = JoinStat.objects.filter(community_id=recruit)
    waiting_count = joins_qs.filter(join_status=0).count() + joins_qs.filter(join_status=2).count()
    approved_count = joins_qs.filter(join_status=1).count()
    capacity = recruit.num_member or 0

    # -------------------------
    # 자동 마감 처리
    # -------------------------
    end_status, created = EndStatus.objects.get_or_create(
        community=recruit,
        defaults={
            "end_set_date": timezone.now().date(),
            "end_stat": 0,
        },
    )

    if approved_count >= capacity and capacity > 0:
        if end_status.end_stat != 1:
            end_status.end_stat = 1
            end_status.end_date = timezone.now().date()
            end_status.save()

    is_closed = (end_status.end_stat == 1)

    # 작성자 여부
    is_owner = (login_member is not None and recruit.member_id == login_member)

    # 로그인한 유저가 이 모집글에 참여했는지 체크
    my_join = JoinStat.objects.filter(
        community_id=recruit,
        member_id=login_member
    ).first()

    is_applied = (my_join is not None)


    # 상세 참여 리스트 (작성자 / 관리자만)
    join_list = []
    if is_owner or is_manager_user:
        join_list = (
            joins_qs
            .select_related("member_id")
            .order_by("join_status", "member_id__user_id")
        )

    # 댓글
    # comments = (
    #     Comment.objects
    #     .filter(community_id=recruit)
    #     .order_by("reg_date")
    # )
 
    comments = []
    # 댓글: 그냥 Comment queryset 으로 넘김
    comments = (
        Comment.objects
        .select_related("member_id")
        .filter(community_id=recruit)
        .order_by("reg_date")
    )

    # -----------------------------------
    # ✅ 이 모집글의 reservation_id 기준 타임슬롯
    #    - Community.reservation_id 가 있을 때만
    #    - TimeSlot.delete_yn = 0, 예약 soft delete 제외
    # -----------------------------------
    reservation_slots = []

    reservation_obj = recruit.reservation_id  # FK 객체 또는 None
    if reservation_obj is not None:
        slots_qs = (
            TimeSlot.objects
            .filter(
                reservation_id=reservation_obj,
                delete_yn=0,
                reservation_id__delete_date__isnull=True,
            )
            .select_related("reservation_id", "facility_id")
            .order_by("date", "start_time")
        )

        if slots_qs:
            facility = slots_qs[0].facility_id  # 그 예약의 시설 (모든 슬롯이 동일 시설일 거라고 가정)
            grouped = {
                "reservation": reservation_obj,
                "facility": facility,
                "times": [],
            }

            for slot in slots_qs:
                grouped["times"].append({
                    "t_id": slot.t_id,
                    "date": slot.date,
                    "start_time": slot.start_time,
                    "end_time": slot.end_time,
                })

            # detail 템플릿에서 쓰기 쉽게 리스트 형태로 전달
            reservation_slots = [grouped]
    add_info_list = AddInfo.objects.filter(
        community_id=recruit,
        # delete_date__isnull=True
    )
    context = {
        "recruit": recruit,
        "add_info": add_info_list,
        "is_owner": is_owner,
        "is_manager": is_manager_user,
        "join_list": join_list,
        "approved_count": approved_count,
        "capacity": capacity,
        "is_closed": is_closed,
        "comments": comments,
        "waiting_rejected_count": waiting_count,
        # 👇 이걸로 detail 화면에서 예약 시간대 뿌리면 됨
        "reservation_slots": reservation_slots,
        "is_applied":is_applied,
        "my_join":my_join,
    }

    return render(request, "recruitment/recruitment_detail.html", context)



def delete(request, pk):
    
    res = check_login(request)
    if res:
        return res
        

    # 1) 세션 user_id 로 Member 조회
    try:
        user_id = request.session.get("user_id")
        member = Member.objects.get(user_id=user_id)
    except Member.DoesNotExist:
        request.session.flush()
        messages.error(request, "다시 로그인 해주세요.")
        return redirect("/login")

    # 2) 삭제 대상 글 조회
    try:
        community = Community.objects.get(pk=pk)
    except Community.DoesNotExist:
        raise Http404("존재하지 않는 글입니다.")

    # 3) 작성자 본인 확인 (URL로 악의적 접근 방지)
    if member.manager_yn != 1:
        messages.error(request, "관리자만 글을 삭제할 수 있습니다.")
        return redirect("recruitment:recruitment_detail", pk=pk)

    # 4) soft delete
    community.delete_date = timezone.now()
    community.save()

    messages.success(request, "글이 삭제되었습니다.")
    return redirect("recruitment:recruitment_list")







def join(request, pk):

    # 0) 로그인 체크
    
    res = check_login(request)
    if res:
        return res
    
    user_id = request.session.get("user_id")


    # 1) 세션의 user_id 로 Member 찾기
    try:
        member = Member.objects.get(user_id=user_id)
    except Member.DoesNotExist:
        request.session.flush()
        messages.error(request, "다시 로그인 해주세요.")
        return redirect("/login")

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
    
    res = check_login(request)
    if res:
        return res
    
    user_id = request.session.get("user_id")


    # 1) 로그인 유저
    try:
        member = Member.objects.get(user_id=user_id)
    except Member.DoesNotExist:
        request.session.flush()
        messages.error(request, "다시 로그인 해주세요.")
        return redirect("/login")

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
    
    res = check_login(request)
    if res:
        return res
    
    user_id = request.session.get("user_id")


    # 1) 로그인 회원
    try:
        member = Member.objects.get(user_id=user_id)
    except Member.DoesNotExist:
        request.session.flush()
        messages.error(request, "다시 로그인 해주세요.")
        return redirect("/login")

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


# 파일 업로드 처리 함수는 common/utils.py로 이동됨



@require_POST
def delete_comment(request, pk, comment_id):
    """
    모집글 상세에서 댓글 삭제 (soft delete 후 상세 페이지로 redirect)
    - 관리자만 삭제 가능 (현재 is_manager 기준)
    - pk: 모집글 community_id
    - comment_id: 댓글 PK
    """

    # 로그인 / 세션 체크
    res = check_login(request)
    if res:
        return res

    # 관리자 권한 확인
    if not is_manager(request):
        messages.error(request, "댓글을 삭제할 권한이 없습니다.")
        return redirect("recruitment:recruitment_detail", pk=pk)

    # 해당 모집글의 댓글만 대상으로
    comment = get_object_or_404(
        Comment,
        comment_id=comment_id,
        community_id_id=pk,   # FK 이름이 community_id 라고 가정
    )

    # 이미 soft delete 된 경우
    if comment.delete_date:
        messages.info(request, "이미 삭제된 댓글입니다.")
        return redirect("recruitment:recruitment_detail", pk=pk)

    # soft delete
    comment.delete_date = timezone.now()
    # 보여주기 싫으면 주석 유지, 문구 보이게 하고 싶으면 주석 해제
    # comment.comment = "관리자에 의해 삭제된 댓글입니다."
    comment.save()

    messages.success(request, "댓글을 삭제했습니다.")
    return redirect("recruitment:recruitment_detail", pk=pk)



# 모집 마감 여부 체크

def close_recruitment(request, pk):
    # 로그인 체크
    
    res = check_login(request)
    if res:
        return res
    
    user_id = request.session.get("user_id")

    # 글 가져오기 (삭제된 글은 마감 안 하도록)
    try:
        recruit = Community.objects.get(pk=pk, delete_date__isnull=True)
    except Community.DoesNotExist:
        raise Http404("존재하지 않는 모집글입니다.")

    # 작성자 / 관리자 확인
    login_member = Member.objects.filter(user_id=user_id).first()
    is_manager_user = is_manager(request)
    is_owner = (login_member is not None and recruit.member_id == login_member)

    if not (is_owner or is_manager_user):
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


# 시설 선택 시 지역구 자동 셀렉되게

from django.http import JsonResponse

def get_facility_region(request):
    
    res = check_login(request)
    if res:
        return res

    reservation_id = request.GET.get("reservation_id")

    slot = (
        TimeSlot.objects
        .select_related("facility_id", "reservation_id")
        .filter(reservation_id_id=reservation_id)
        .first()
    )

    if not slot:
        return JsonResponse({"error": "not_found"}, status=404)

    facility = slot.facility_id

    return JsonResponse({
        "sido": facility.sido,
        "sigugun": facility.sigugun,
    })