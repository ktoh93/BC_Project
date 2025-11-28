// static/js/facility_list.js

document.addEventListener("DOMContentLoaded", function () {
    /* 대한민국 시/도 + 시/군/구 전체 데이터 */
    const regionData = {
        "서울특별시": [
            "강남구", "강동구", "강북구", "강서구", "관악구", "광진구", "구로구",
            "금천구", "노원구", "도봉구", "동대문구", "동작구", "마포구",
            "서대문구", "서초구", "성동구", "성북구", "송파구", "양천구",
            "영등포구", "용산구", "은평구", "종로구", "중구", "중랑구"
        ],

        "부산광역시": [
            "강서구", "금정구", "기장군", "남구", "동구", "동래구", "부산진구",
            "북구", "사상구", "사하구", "서구", "수영구", "연제구", "영도구",
            "중구", "해운대구"
        ],

        "대구광역시": [
            "남구", "달서구", "달성군", "동구", "북구", "서구",
            "수성구", "중구"
        ],

        "인천광역시": [
            "강화군", "계양구", "남동구", "동구", "미추홀구",
            "부평구", "서구", "연수구", "옹진군", "중구"
        ],

        "광주광역시": [
            "광산구", "남구", "동구", "북구", "서구"
        ],

        "대전광역시": [
            "대덕구", "동구", "서구", "유성구", "중구"
        ],

        "울산광역시": [
            "남구", "동구", "북구", "울주군", "중구"
        ],

        "세종특별자치시": [
            "세종시"
        ],

        "경기도": [
            "가평군", "고양시 덕양구", "고양시 일산동구", "고양시 일산서구",
            "과천시", "광명시", "광주시", "구리시", "군포시",
            "김포시", "남양주시", "동두천시", "부천시", "성남시 분당구",
            "성남시 수정구", "성남시 중원구", "수원시 권선구", "수원시 영통구",
            "수원시 장안구", "수원시 팔달구", "시흥시", "안산시 단원구",
            "안산시 상록구", "안성시", "안양시 동안구", "안양시 만안구",
            "양주시", "양평군", "여주시", "연천군", "오산시", "용인시 기흥구",
            "용인시 수지구", "용인시 처인구", "의왕시", "의정부시",
            "이천시", "파주시", "평택시", "포천시", "하남시",
            "화성시"
        ],

        "강원특별자치도": [
            "강릉시", "고성군", "동해시", "삼척시", "속초시",
            "양구군", "양양군", "영월군", "원주시", "인제군",
            "정선군", "철원군", "춘천시", "태백시", "평창군",
            "홍천군", "화천군", "횡성군"
        ],

        "충청북도": [
            "괴산군", "단양군", "보은군", "영동군", "옥천군",
            "음성군", "제천시", "증평군", "진천군", "청주시 상당구",
            "청주시 서원구", "청주시 청원구", "청주시 흥덕구", "충주시"
        ],

        "충청남도": [
            "계룡시", "공주시", "금산군", "논산시", "당진시",
            "보령시", "부여군", "서산시", "서천군", "아산시",
            "예산군", "천안시 동남구", "천안시 서북구", "청양군",
            "태안군", "홍성군"
        ],

        "전북특별자치도": [
            "고창군", "군산시", "김제시", "남원시", "무주군",
            "부안군", "순창군", "완주군", "익산시", "임실군",
            "장수군", "전주시 덕진구", "전주시 완산구", "정읍시",
            "진안군"
        ],

        "전라남도": [
            "강진군", "고흥군", "곡성군", "광양시", "구례군",
            "나주시", "담양군", "목포시", "무안군", "보성군",
            "순천시", "신안군", "여수시", "영광군", "영암군",
            "완도군", "장성군", "장흥군", "진도군", "함평군",
            "해남군", "화순군"
        ],

        "경상북도": [
            "경산시", "경주시", "고령군", "구미시", "군위군",
            "김천시", "문경시", "봉화군", "상주시", "성주군",
            "안동시", "영덕군", "영양군", "영주시", "영천시",
            "예천군", "울릉군", "울진군", "의성군", "청도군",
            "청송군", "칠곡군", "포항시 남구", "포항시 북구"
        ],

        "경상남도": [
            "거제시", "거창군", "고성군", "김해시", "남해군",
            "밀양시", "사천시", "산청군", "양산시", "의령군",
            "진주시", "창녕군", "창원시 마산합포구", "창원시 마산회원구",
            "창원시 성산구", "창원시 의창구", "창원시 진해구",
            "통영시", "하동군", "함안군", "함양군", "합천군"
        ],

        "제주특별자치도": [
            "서귀포시", "제주시"
        ]
    };

    // 공통 URL 파라미터 객체
    const params = new URLSearchParams(window.location.search);

    /* ---------- 요소 가져오기 ---------- */
    const sidoEl = document.getElementById("sido");
    const sigunguEl = document.getElementById("sigungu");
    const perPageEl = document.getElementById("perPageSelect");
    const sortEl = document.getElementById("sortSelect");
    const searchKeywordEl = document.getElementById("searchKeyword");

    /* ===========================
       1) 시/도 / 구·군 셀렉터 처리
       =========================== */
    if (sidoEl && sigunguEl) {

        // 1-1. 시/도 목록 채우기
        Object.keys(regionData).forEach((sido) => {
            const option = document.createElement("option");
            option.value = sido;
            option.textContent = sido;
            sidoEl.appendChild(option);
        });

        // 1-2. 시/도 변경 시 구/군 목록 갱신
        sidoEl.addEventListener("change", function () {
            const selected = this.value;

            // 기본 옵션으로 초기화
            sigunguEl.innerHTML = `<option value="">구/군 선택</option>`;

            if (!selected || !regionData[selected]) return;

            regionData[selected].forEach((gu) => {
                const option = document.createElement("option");
                option.value = gu;
                option.textContent = gu;
                sigunguEl.appendChild(option);
            });
        });

        // 1-3. URL에 시/도(cpNm), 구/군(cpbNm)이 있을 경우 기존 값 복원
        const nowSido = params.get("cpNm") || "";
        const nowSigungu = params.get("cpbNm") || "";

        if (nowSido && regionData[nowSido]) {
            // 시/도 선택 복원
            sidoEl.value = nowSido;

            // 구/군 목록 채우기
            sigunguEl.innerHTML = `<option value="">구/군 선택</option>`;
            regionData[nowSido].forEach((gu) => {
                const option = document.createElement("option");
                option.value = gu;
                option.textContent = gu;
                sigunguEl.appendChild(option);
            });

            // 구/군 선택 복원
            if (nowSigungu) {
                sigunguEl.value = nowSigungu;
            }
        }
    }

    /* ===========================
       1-4) 검색어 value 복원
       =========================== */
    if (searchKeywordEl) {
        const nowKeyword = params.get("keyword") || "";
        searchKeywordEl.value = nowKeyword;
    }

    /* ===========================
       2) 페이지당 개수(per_page) 처리
       =========================== */
    if (perPageEl) {
        const nowPer = params.get("per_page") || "10";
        perPageEl.value = nowPer;

        perPageEl.addEventListener("change", function () {
            const newParams = new URLSearchParams(window.location.search);
            newParams.set("per_page", this.value);
            newParams.set("page", 1);
            window.location.search = newParams.toString();
        });
    }

    /* ===========================
       3) sort 처리 (정렬 유지)
       =========================== */
    if (sortEl) {
        const nowSort = params.get("sort") || "recent";
        sortEl.value = nowSort;

        sortEl.addEventListener("change", function () {
            const newParams = new URLSearchParams(window.location.search);
            newParams.set("sort", this.value);
            newParams.set("page", 1); // 정렬 바꾸면 1페이지로
            window.location.search = newParams.toString();
        });
    }

    /* ===========================
       4) 검색 submit 처리
       =========================== */
    $("#facilitySearchForm").on("submit", function (e) {
        e.preventDefault();

        const sido = $('#sido').val();
        const sigungu = $('#sigungu').val();

        if (sido === '') {
            alert('시/도 선택해주세요');
            $('#sido').focus();
            return;
        }

        if (sigungu === '') {
            alert('구/군 선택 해주세요');
            $('#sigungu').focus();
            return;
        }

        // 검증 통과하면 실제 submit
        this.submit();
    });

    /* ===========================
       5) 카카오 지도 + 마커 + 인포윈도우
       =========================== */
    var container = document.getElementById("map");
    if (!container || typeof kakao === "undefined") {
        return;
    }

    var map = new kakao.maps.Map(container, {
        center: new kakao.maps.LatLng(37.5665, 126.9780),
        level: 7,
        draggable: false,                    // 드래그 금지
        scrollwheel: false,                  // 휠 확대/축소 금지
        disableDoubleClickZoom: true,        // 더블클릭 확대 금지
        keyboardShortcuts: false             // 키보드 이동 금지
    });

    var bounds = new kakao.maps.LatLngBounds();
    var markerMap = {};
    var fixedInfoWindow = null;  // ⭐ 고정된 인포윈도우 저장

    facilities.forEach(function (item) {
        var lat = parseFloat(item.lat);
        var lng = parseFloat(item.lng);

        if (isNaN(lat) || isNaN(lng)) return;

        var pos = new kakao.maps.LatLng(lat, lng);

        var marker = new kakao.maps.Marker({
            map: map,
            position: pos
        });

        var iwContent =
            `<div style="padding:5px 8px;font-size:13px;white-space:nowrap;">
                <a href="/facility/detail/${item.id}?fName=${encodeURIComponent(item.name)}"
                   style="text-decoration:none;color:#1A2A43;font-weight:600;">
                    ${item.name}
                </a>
             </div>`;

        var infowindow = new kakao.maps.InfoWindow({
            content: iwContent
        });

        // hover 시에는 임시로 띄우되, 고정창이 아닌 경우만 닫힘
        kakao.maps.event.addListener(marker, "mouseover", function () {
            infowindow.open(map, marker);
        });

        kakao.maps.event.addListener(marker, "mouseout", function () {
            // ⭐ 고정된 창(fixedInfoWindow)이 아니면 닫기
            if (fixedInfoWindow !== infowindow) {
                infowindow.close();
            }
        });

        markerMap[item.id] = {
            marker: marker,
            infowindow: infowindow,
            position: pos
        };

        bounds.extend(pos);
    });

    if (!bounds.isEmpty()) {
        map.setBounds(bounds);
    }

    // ⭐ 리스트 클릭 → 지도 포커스 + 인포윈도우 "고정"
    document.querySelectorAll(".facility-link").forEach(function (link) {
        link.addEventListener("click", function (e) {
            e.preventDefault();  // a 태그 기본 이동 막고, 상세는 말풍선 링크로만

            var id = this.dataset.id;
            var obj = markerMap[id];

            if (!obj) {
                alert("해당 시설의 위치 정보가 없습니다.");
                return;
            }

            // 지도 이동
            map.setCenter(obj.position);
            map.setLevel(5);

            // 이전 고정 인포윈도우 닫기
            if (fixedInfoWindow) {
                fixedInfoWindow.close();
            }

            // 새 인포윈도우 열고 고정
            obj.infowindow.open(map, obj.marker);
            fixedInfoWindow = obj.infowindow;

            // 스크롤을 지도 가까이로
            const mapRect = container.getBoundingClientRect();
            window.scrollTo({
                top: window.pageYOffset + mapRect.top - 100,
                behavior: "smooth"
            });
        });
    });
});
