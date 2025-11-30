import os
import requests
from django.core.management.base import BaseCommand
from django.db import transaction
from facility.models import Facility


class Command(BaseCommand):
    help = "전국체육시설 안전점검 API 데이터 → Facility 테이블 업데이트 방식으로 저장"

    def handle(self, *args, **options):
        API_KEY = os.getenv("DATA_API_KEY")
        if not API_KEY:
            self.stderr.write(self.style.ERROR("❌ DATA_API_KEY 환경변수가 없습니다."))
            return

        base_url = "https://apis.data.go.kr/B551014/SRVC_API_FACI_SCHK_RESULT/TODZ_API_FACI_SAFETY"

        page_no = 1
        num_of_rows = 1000
        total_count = 0

        self.stdout.write("📡 API 데이터 업데이트 중...")

        while True:
            params = {
                "serviceKey": API_KEY,
                "pageNo": page_no,
                "numOfRows": num_of_rows,
                "resultType": "json",
            }

            response = requests.get(base_url, params=params, timeout=10)
            data = response.json()

            body = data.get("response", {}).get("body", {})
            items = body.get("items", {}).get("item")

            # item이 없는 경우 종료
            if not items:
                break

            # 단일 dict → 리스트로 변환
            if isinstance(items, dict):
                items = [items]

            self.stdout.write(f"  - {page_no} 페이지 처리 ({len(items)}개)")

            # 트랜잭션 단위로 처리
            with transaction.atomic():
                for item in items:
                    faci_cd = item.get("faci_cd")
                    if not faci_cd:
                        print(f"⚠ faci_cd 없음 → 스킵 ({item.get('faci_nm')})")
                        continue

                    # UPDATE or INSERT
                    Facility.objects.update_or_create(
                        faci_cd=faci_cd,  # unique key
                        defaults={
                            "faci_nm": item.get("faci_nm"),
                            "faci2_nm": item.get("faci2_nm"),
                            "cp_nm": item.get("cp_nm"),
                            "cpb_nm": item.get("cpb_nm"),
                            "fcob_nm": item.get("fcob_nm"),
                            "ftype_nm": item.get("ftype_nm"),

                            "faci_addr": item.get("faci_addr"),
                            "faci_road_addr": item.get("faci_road_addr"),
                            "faci_daddr": item.get("faci_daddr"),
                            "faci_road_daddr": item.get("faci_road_daddr"),
                            "faci_zip": item.get("faci_zip"),

                            "faci_lat": item.get("faci_lat"),
                            "faci_lot": item.get("faci_lot"),

                            "faci_stat_nm": item.get("faci_stat_nm"),
                            "schk_tot_grd_nm": item.get("schk_tot_grd_nm"),
                            "schk_tot_grd_cd": item.get("schk_tot_grd_cd"),

                            "faci_mng_type_cd": item.get("faci_mng_type_cd"),
                            "inout_gbn_nm": item.get("inout_gbn_nm"),
                            "atnm_chk_yn": item.get("atnm_chk_yn"),
                            "faci_tel_no": item.get("faci_tel_no"),
                            "faci_homepage": item.get("faci_homepage"),

                            "faci_gfa": item.get("faci_gfa"),

                            "base_ymd": item.get("base_ymd"),
                            "reg_dt": item.get("reg_dt"),
                            "faci_reg_ymd": item.get("faci_reg_ymd"),
                            "faci_upd_ymd": item.get("faci_upd_ymd"),
                            "schk_visit_ymd": item.get("schk_visit_ymd"),
                            "schk_open_ymd": item.get("schk_open_ymd"),
                            "sdwn_ymd": item.get("sdwn_ymd"),
                            "th_ymd": item.get("th_ymd"),

                            "row_num": item.get("row_num"),
                        }
                    )

                    total_count += 1

            # 마지막 페이지인지 체크
            total_items = body.get("totalCount")
            if page_no * num_of_rows >= total_items:
                break

            page_no += 1

        self.stdout.write(self.style.SUCCESS(
            f"🎉 Facility 업데이트 완료! 총 {total_count}개 업데이트/삽입됨"
        ))
