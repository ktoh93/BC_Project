import os
import time
import requests
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from facility.models import Facility
from django.utils import timezone


class Command(BaseCommand):
    help = "전국체육시설 안전점검 API → Facility 테이블 업데이트 (t2.micro 최적화 / 안정화 버전)"

    def handle(self, *args, **options):
        API_KEY = os.getenv("DATA_API_KEY")
        if not API_KEY:
            self.stderr.write(self.style.ERROR("❌ DATA_API_KEY 환경변수가 없습니다."))
            return

        base_url = "https://apis.data.go.kr/B551014/SRVC_API_FACI_SCHK_RESULT/TODZ_API_FACI_SAFETY"

        page_no = 1
        num_of_rows = 1000
        all_items = []

        self.stdout.write("📡 API 데이터 로드 시작")

        # -----------------------------
        # 1) API 데이터 페이지 단위 수집 (502 자동 재시도 포함)
        # -----------------------------
        max_retry = 3
        retry = 0

        while True:
            params = {
                "serviceKey": API_KEY,
                "pageNo": page_no,
                "numOfRows": num_of_rows,
                "resultType": "json",
            }

            try:
                res = requests.get(base_url, params=params, timeout=10)

                # 서버 오류 (502/503 등)
                if res.status_code >= 500:
                    raise requests.exceptions.HTTPError(
                        f"Server error {res.status_code}"
                    )

                res.raise_for_status()

            except requests.exceptions.HTTPError as e:
                retry += 1
                if retry > max_retry:
                    self.stderr.write(
                        self.style.ERROR(f"❌ API 요청 반복 실패 → 중단: {e}")
                    )
                    return

                self.stdout.write(
                    self.style.WARNING(f"⚠ API 오류({e}), {retry}회 재시도... 1초 대기")
                )
                time.sleep(1)
                continue

            # 정상 응답 → retry 초기화
            retry = 0

            data = res.json()
            body = data.get("response", {}).get("body", {})
            items = body.get("items", {}).get("item")

            if not items:
                break

            if isinstance(items, dict):
                items = [items]

            all_items.extend(items)
            total_count = body.get("totalCount", 0)

            self.stdout.write(f"  - {page_no} 페이지 로드 (누적 {len(all_items)}개)")

            if page_no * num_of_rows >= int(total_count):
                break

            page_no += 1

        total = len(all_items)
        if total == 0:
            self.stdout.write(self.style.WARNING("⚠ 수신된 데이터가 없습니다."))
            return

        self.stdout.write(f"📦 총 {total}건 수신 → 변환 시작")

        # -----------------------------
        # 2) INSERT 컬럼 목록 정의
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

        # -----------------------------
        # 3) 데이터 변환 (row list 생성)
        # -----------------------------
        rows = []
        now = timezone.now()

        for idx, item in enumerate(all_items, start=1):
            faci_cd = item.get("faci_cd")
            if not faci_cd:
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

            # 공백 문자열은 None 처리
            row = [None if (v == "" or v == " ") else v for v in row]
            rows.append(tuple(row))

            if idx % 5000 == 0:
                self.stdout.write(f"  - 변환 중: {idx}/{total}")

        self.stdout.write(f"🧮 변환 완료! INSERT 대상: {len(rows)}건")

        # -----------------------------
        # 4) RAW SQL bulk insert
        # -----------------------------
        table_name = Facility._meta.db_table
        col_sql = ", ".join(f"`{c}`" for c in columns)
        placeholders = ", ".join(["%s"] * len(columns))
        insert_sql = f"INSERT INTO `{table_name}` ({col_sql}) VALUES ({placeholders})"
        batch_size = 5000

        with transaction.atomic():
            with connection.cursor() as cursor:
                self.stdout.write("🧹 TRUNCATE 실행 중...")
                cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
                cursor.execute(f"TRUNCATE TABLE `{table_name}`;")
                cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

                self.stdout.write("🚀 INSERT 시작...")

                total_rows = len(rows)
                for start in range(0, total_rows, batch_size):
                    batch = rows[start:start + batch_size]
                    cursor.executemany(insert_sql, batch)

                    self.stdout.write(
                        f"  - INSERT: {min(start + batch_size, total_rows)}/{total_rows}"
                    )

        self.stdout.write(self.style.SUCCESS("🎉 완료! Facility 데이터 갱신 성공"))
