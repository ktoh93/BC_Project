import os
import time
import requests
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from facility.models import Facility
from django.utils import timezone


class Command(BaseCommand):
    help = "전국체육시설 안전점검 API → Facility 테이블 업데이트 (페이지 단위 INSERT / AWS micro 안정화)"

    def handle(self, *args, **options):
        API_KEY = os.getenv("DATA_API_KEY")
        if not API_KEY:
            self.stderr.write(self.style.ERROR("❌ DATA_API_KEY 환경변수가 없습니다."))
            return

        base_url = "https://apis.data.go.kr/B551014/SRVC_API_FACI_SCHK_RESULT/TODZ_API_FACI_SAFETY"

        page_no = 1
        num_of_rows = 1000
        now = timezone.now()

        self.stdout.write("📡 API 데이터 로드 시작")

        # -----------------------------
        # INSERT 준비
        # -----------------------------
        columns = [
            "faci_cd", "faci_nm", "faci2_nm",
            "cp_nm", "cpb_nm", "fcob_nm", "ftype_nm",

            "faci_addr", "faci_road_addr", "faci_daddr", "faci_road_daddr",
            "faci_zip", "faci_gb_nm", "faci_lat", "faci_lot",

            "faci_stat_nm", "schk_tot_grd_nm", "schk_tot_grd_cd",

            "faci_mng_type_cd", "inout_gbn_nm", "atnm_chk_yn",
            "faci_tel_no", "faci_homepage",

            "faci_gfa",
            "base_ymd", "reg_dt", "faci_reg_ymd", "faci_upd_ymd",
            "schk_visit_ymd", "schk_open_ymd", "sdwn_ymd", "th_ymd",

            "row_num",
            "reg_date",
            "view_cnt",
        ]

        table_name = Facility._meta.db_table
        col_sql = ", ".join(f"`{c}`" for c in columns)
        placeholders = ", ".join(["%s"] * len(columns))
        insert_sql = f"INSERT INTO `{table_name}` ({col_sql}) VALUES ({placeholders})"

        # -----------------------------
        # 1) TRUNCATE (한 번만)
        # -----------------------------
        with connection.cursor() as cursor:
            self.stdout.write("🧹 TRUNCATE 실행 중...")
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
            cursor.execute(f"TRUNCATE TABLE `{table_name}`;")
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

        # -----------------------------
        # 2) 페이지 단위 INSERT
        # -----------------------------
        total_inserted = 0
        max_retry = 3

        while True:
            params = {
                "serviceKey": API_KEY,
                "pageNo": page_no,
                "numOfRows": num_of_rows,
                "resultType": "json",
            }

            retry = 0
            while True:
                try:
                    res = requests.get(base_url, params=params, timeout=10)
                    if res.status_code >= 500:
                        raise requests.exceptions.HTTPError(f"Server error {res.status_code}")
                    res.raise_for_status()
                    break
                except requests.exceptions.HTTPError as e:
                    retry += 1
                    if retry > max_retry:
                        self.stderr.write(self.style.ERROR(f"❌ API 요청 실패 → 중단: {e}"))
                        return
                    self.stdout.write(self.style.WARNING(f"⚠ API 오류, 재시도 {retry}/{max_retry}"))
                    time.sleep(1)

            body = res.json().get("response", {}).get("body", {})
            items = body.get("items", {}).get("item")

            if not items:
                break

            if isinstance(items, dict):
                items = [items]

            rows = []
            for item in items:
                if not item.get("faci_cd"):
                    continue

                row = [
                    item.get("faci_cd"),
                    item.get("faci_nm"),
                    item.get("faci2_nm"),

                    item.get("cp_nm"),
                    item.get("cpb_nm"),
                    item.get("fcob_nm"),
                    item.get("ftype_nm"),

                    item.get("faci_addr"),
                    item.get("faci_road_addr"),
                    item.get("faci_daddr"),
                    item.get("faci_road_daddr"),
                    item.get("faci_zip"),
                    item.get("faci_gb_nm"),
                    item.get("faci_lat"),
                    item.get("faci_lot"),

                    item.get("faci_stat_nm"),
                    item.get("schk_tot_grd_nm"),
                    item.get("schk_tot_grd_cd"),

                    item.get("faci_mng_type_cd"),
                    item.get("inout_gbn_nm"),
                    item.get("atnm_chk_yn"),
                    item.get("faci_tel_no"),
                    item.get("faci_homepage"),

                    item.get("faci_gfa"),

                    item.get("base_ymd"),
                    item.get("reg_dt"),
                    item.get("faci_reg_ymd"),
                    item.get("faci_upd_ymd"),
                    item.get("schk_visit_ymd"),
                    item.get("schk_open_ymd"),
                    item.get("sdwn_ymd"),
                    item.get("th_ymd"),

                    item.get("row_num"),
                    now,
                    0,
                ]

                row = [None if (v == "" or v == " ") else v for v in row]
                rows.append(tuple(row))

            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.executemany(insert_sql, rows)

            total_inserted += len(rows)
            self.stdout.write(f"  - {page_no} 페이지 INSERT 완료 (누적 {total_inserted})")

            page_no += 1

        self.stdout.write(self.style.SUCCESS(f"🎉 완료! 총 {total_inserted}건 INSERT 성공"))
