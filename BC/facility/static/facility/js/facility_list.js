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
        "대구광역시": ["남구", "달서구", "달성군", "동구", "북구", "서구", "수성구", "중구"],
        "인천광역시": [
            "강화군", "계양구", "남동구", "동구", "미추홀구", "부평구",
            "서구", "연수구", "옹진군", "중구"
        ],
        "광주광역시": ["광산구", "남구", "동구", "북구", "서구"],
        "대전광역시": ["대덕구", "동구", "서구", "유성구", "중구"],
        "울산광역시": ["남구", "동구", "북구", "울주군", "중구"],
        "세종특별자치시": ["세종시"],
        "경기도": [
            "가평군", "고양시 덕양구", "고양시 일산동구", "고양시 일산서구",
            "과천시", "광명시", "광주시", "구리시", "군포시", "김포시",
            "남양주시", "동두천시", "부천시", "성남시 분당구", "성남시 수정구",
            "성남시 중원구", "수원시 권선구", "수원시 영통구", "수원시 장안구",
            "수원시 팔달구", "시흥시", "안산시 단원구", "안산시 상록구",
            "안성시", "안양시 동안구", "안양시 만안구", "양주시", "양평군",
            "여주시", "연천군", "오산시", "용인시 기흥구", "용인시 수지구",
            "용인시 처인구", "의왕시", "의정부시", "이천시", "파주시",
            "평택시", "포천시", "하남시", "화성시"
        ],
        "강원특별자치도": [
            "강릉시", "고성군", "동해시", "삼척시", "속초시", "양구군", "양양군",
            "영월군", "원주시", "인제군", "정선군", "철원군", "춘천시", "태백시",
            "평창군", "홍천군", "화천군", "횡성군"
        ],
        "충청북도": [
            "괴산군", "단양군", "보은군", "영동군", "옥천군", "음성군", "제천시",
            "증평군", "진천군", "청주시 상당구", "청주시 서원구", "청주시 청원구",
            "청주시 흥덕구", "충주시"
        ],
        "충청남도": [
            "계룡시", "공주시", "금산군", "논산시", "당진시", "보령시", "부여군",
            "서산시", "서천군", "아산시", "예산군", "천안시 동남구", "천안시 서북구",
            "청양군", "태안군", "홍성군"
        ],
        "전북특별자치도": [
            "고창군", "군산시", "김제시", "남원시", "무주군", "부안군",
            "순창군", "완주군", "익산시", "임실군", "장수군", "전주시 덕진구",
            "전주시 완산구", "정읍시", "진안군"
        ],
        "전라남도": [
            "강진군", "고흥군", "곡성군", "광양시", "구례군", "나주시",
            "담양군", "목포시", "무안군", "보성군", "순천시", "신안군",
            "여수시", "영광군", "영암군", "완도군", "장성군", "장흥군",
            "진도군", "함평군", "해남군", "화순군"
        ],
        "경상북도": [
            "경산시", "경주시", "고령군", "구미시", "군위군", "김천시", "문경시",
            "봉화군", "상주시", "성주군", "안동시", "영덕군", "영양군",
            "영주시", "영천시", "예천군", "울릉군", "울진군", "의성군",
            "청도군", "청송군", "칠곡군", "포항시 남구", "포항시 북구"
        ],
        "경상남도": [
            "거제시", "거창군", "고성군", "김해시", "남해군", "밀양시",
            "사천시", "산청군", "양산시", "의령군", "진주시",
            "창녕군", "창원시 마산합포구", "창원시 마산회원구",
            "창원시 성산구", "창원시 의창구", "창원시 진해구",
            "통영시", "하동군", "함안군", "함양군", "합천군"
        ],
        "제주특별자치도": ["서귀포시", "제주시"]
    };

    // URL 파라미터
    const params = new URLSearchParams(window.location.search);

    // 요소들
    const sidoEl = document.getElementById("sido");
    const sigunguEl = document.getElementById("sigungu");
    const perPageEl = document.getElementById("perPageSelect");
    const sortEl = document.getElementById("sortSelect");
    const searchKeywordEl = document.getElementById("searchKeyword");

    /* ===========================
        검색 UI 설정
    =========================== */
    if (sidoEl && sigunguEl) {
        Object.keys(regionData).forEach((sido) => {
            const option = document.createElement("option");
            option.value = sido;
            option.textContent = sido;
            sidoEl.appendChild(option);
        });

        sidoEl.addEventListener("change", function () {
            const selected = this.value;
            sigunguEl.innerHTML = `<option value="">구/군 선택</option>`;
            if (!regionData[selected]) return;

            regionData[selected].forEach((gu) => {
                const option = document.createElement("option");
                option.value = gu;
                option.textContent = gu;
                sigunguEl.appendChild(option);
            });
        });

        const nowSido = document.getElementById("hiddenSido").value;
        const nowSigungu = document.getElementById("hiddenSigungu").value;

        if (nowSido && regionData[nowSido]) {
            sidoEl.value = nowSido;
            sigunguEl.innerHTML = `<option value="">구/군 선택</option>`;

            regionData[nowSido].forEach((gu) => {
                const option = document.createElement("option");
                option.value = gu;
                option.textContent = gu;
                sigunguEl.appendChild(option);
            });

            if (nowSigungu) sigunguEl.value = nowSigungu;
        }
    }

    if (searchKeywordEl) {
        searchKeywordEl.value = params.get("keyword") || "";
    }

    if (perPageEl) {
        perPageEl.value = params.get("per_page") || "10";
        perPageEl.addEventListener("change", function () {
            const newParams = new URLSearchParams(window.location.search);
            newParams.set("per_page", this.value);
            newParams.set("page", 1);
            window.location.search = newParams.toString();
        });
    }

    if (sortEl) {
        sortEl.value = params.get("sort") || "recent";
        sortEl.addEventListener("change", function () {
            const newParams = new URLSearchParams(window.location.search);
            newParams.set("sort", this.value);
            newParams.set("page", 1);
            window.location.search = newParams.toString();
        });
    }

    /* ===========================
        지도 생성
    =========================== */
    var container = document.getElementById("map");
    if (!container || typeof kakao === "undefined") return;

    var map = new kakao.maps.Map(container, {
        center: new kakao.maps.LatLng(37.5665, 126.9780),
        level: 5,
        draggable: false,
        scrollwheel: false,
        disableDoubleClickZoom: true,
        keyboardShortcuts: false
    });

    var bounds = new kakao.maps.LatLngBounds();
    var markerMap = {};
    var fixedInfoWindow = null;

    /* ===========================
        마커 & InfoWindow 생성
    =========================== */
    facilities.forEach(function (item) {
        var lat = parseFloat(item.lat);
        var lng = parseFloat(item.lng);
        if (isNaN(lat) || isNaN(lng)) return;

        var pos = new kakao.maps.LatLng(lat, lng);

        var marker = new kakao.maps.Marker({
            map: map,
            position: pos
        });

        // 🔥 빈칸 완전 제거된 InfoWindow content
        var iwContent = `<div class="overlay-wrap">
    <div class="overlay-box">
        <div class="overlay-title">
            <a href="/facility/detail/${item.id}?fName=${encodeURIComponent(item.name)}">
                ${item.name}
            </a>
        </div>
        <div class="overlay-btn">
            <a href="/facility/detail/${item.id}?fName=${encodeURIComponent(item.name)}">▶</a>
        </div>
    </div>
    <div class="overlay-tail"></div>
</div>`;

        var infowindow = new kakao.maps.InfoWindow({
            content: iwContent
        });

        // 마커 클릭 → 상세 페이지 이동
        kakao.maps.event.addListener(marker, "click", function () {
            window.location.href = `/facility/detail/${item.id}?fName=${encodeURIComponent(item.name)}`;
        });

        // 마커 hover
        kakao.maps.event.addListener(marker, "mouseover", function () {
            infowindow.open(map, marker);
        });

        kakao.maps.event.addListener(marker, "mouseout", function () {
            if (fixedInfoWindow !== infowindow) {
                infowindow.close();
            }
        });

        markerMap[item.id] = { marker, infowindow, position: pos };
        bounds.extend(pos);
    });

    if (!bounds.isEmpty()) map.setBounds(bounds);

    /* ===========================
        리스트 클릭 → 지도 이동 + InfoWindow 열기
    =========================== */
    document.querySelectorAll(".facility-link").forEach(function (link) {
        link.addEventListener("click", function (e) {
            e.preventDefault();

            var id = this.dataset.id;
            var obj = markerMap[id];
            if (!obj) return;

            map.setCenter(obj.position);
            map.setLevel(7);

            if (fixedInfoWindow) fixedInfoWindow.close();

            obj.infowindow.open(map, obj.marker);
            fixedInfoWindow = obj.infowindow;

            const mapRect = container.getBoundingClientRect();
            window.scrollTo({
                top: window.pageYOffset + mapRect.top - 100,
                behavior: "smooth"
            });
        });
    });
});
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
        "대구광역시": ["남구", "달서구", "달성군", "동구", "북구", "서구", "수성구", "중구"],
        "인천광역시": [
            "강화군", "계양구", "남동구", "동구", "미추홀구", "부평구",
            "서구", "연수구", "옹진군", "중구"
        ],
        "광주광역시": ["광산구", "남구", "동구", "북구", "서구"],
        "대전광역시": ["대덕구", "동구", "서구", "유성구", "중구"],
        "울산광역시": ["남구", "동구", "북구", "울주군", "중구"],
        "세종특별자치시": ["세종시"],
        "경기도": [
            "가평군", "고양시 덕양구", "고양시 일산동구", "고양시 일산서구",
            "과천시", "광명시", "광주시", "구리시", "군포시", "김포시",
            "남양주시", "동두천시", "부천시", "성남시 분당구", "성남시 수정구",
            "성남시 중원구", "수원시 권선구", "수원시 영통구", "수원시 장안구",
            "수원시 팔달구", "시흥시", "안산시 단원구", "안산시 상록구",
            "안성시", "안양시 동안구", "안양시 만안구", "양주시", "양평군",
            "여주시", "연천군", "오산시", "용인시 기흥구", "용인시 수지구",
            "용인시 처인구", "의왕시", "의정부시", "이천시", "파주시",
            "평택시", "포천시", "하남시", "화성시"
        ],
        "강원특별자치도": [
            "강릉시", "고성군", "동해시", "삼척시", "속초시", "양구군", "양양군",
            "영월군", "원주시", "인제군", "정선군", "철원군", "춘천시", "태백시",
            "평창군", "홍천군", "화천군", "횡성군"
        ],
        "충청북도": [
            "괴산군", "단양군", "보은군", "영동군", "옥천군", "음성군", "제천시",
            "증평군", "진천군", "청주시 상당구", "청주시 서원구", "청주시 청원구",
            "청주시 흥덕구", "충주시"
        ],
        "충청남도": [
            "계룡시", "공주시", "금산군", "논산시", "당진시", "보령시", "부여군",
            "서산시", "서천군", "아산시", "예산군", "천안시 동남구", "천안시 서북구",
            "청양군", "태안군", "홍성군"
        ],
        "전북특별자치도": [
            "고창군", "군산시", "김제시", "남원시", "무주군", "부안군",
            "순창군", "완주군", "익산시", "임실군", "장수군", "전주시 덕진구",
            "전주시 완산구", "정읍시", "진안군"
        ],
        "전라남도": [
            "강진군", "고흥군", "곡성군", "광양시", "구례군", "나주시",
            "담양군", "목포시", "무안군", "보성군", "순천시", "신안군",
            "여수시", "영광군", "영암군", "완도군", "장성군", "장흥군",
            "진도군", "함평군", "해남군", "화순군"
        ],
        "경상북도": [
            "경산시", "경주시", "고령군", "구미시", "군위군", "김천시", "문경시",
            "봉화군", "상주시", "성주군", "안동시", "영덕군", "영양군",
            "영주시", "영천시", "예천군", "울릉군", "울진군", "의성군",
            "청도군", "청송군", "칠곡군", "포항시 남구", "포항시 북구"
        ],
        "경상남도": [
            "거제시", "거창군", "고성군", "김해시", "남해군", "밀양시",
            "사천시", "산청군", "양산시", "의령군", "진주시",
            "창녕군", "창원시 마산합포구", "창원시 마산회원구",
            "창원시 성산구", "창원시 의창구", "창원시 진해구",
            "통영시", "하동군", "함안군", "함양군", "합천군"
        ],
        "제주특별자치도": ["서귀포시", "제주시"]
    };

    // URL 파라미터
    const params = new URLSearchParams(window.location.search);

    // 요소들
    const sidoEl = document.getElementById("sido");
    const sigunguEl = document.getElementById("sigungu");
    const perPageEl = document.getElementById("perPageSelect");
    const sortEl = document.getElementById("sortSelect");
    const searchKeywordEl = document.getElementById("searchKeyword");

    /* ===========================
        검색 UI 설정
    =========================== */
    if (sidoEl && sigunguEl) {
        Object.keys(regionData).forEach((sido) => {
            const option = document.createElement("option");
            option.value = sido;
            option.textContent = sido;
            sidoEl.appendChild(option);
        });

        sidoEl.addEventListener("change", function () {
            const selected = this.value;
            sigunguEl.innerHTML = `<option value="">구/군 선택</option>`;
            if (!regionData[selected]) return;

            regionData[selected].forEach((gu) => {
                const option = document.createElement("option");
                option.value = gu;
                option.textContent = gu;
                sigunguEl.appendChild(option);
            });
        });

        const nowSido = document.getElementById("hiddenSido").value;
        const nowSigungu = document.getElementById("hiddenSigungu").value;

        if (nowSido && regionData[nowSido]) {
            sidoEl.value = nowSido;
            sigunguEl.innerHTML = `<option value="">구/군 선택</option>`;

            regionData[nowSido].forEach((gu) => {
                const option = document.createElement("option");
                option.value = gu;
                option.textContent = gu;
                sigunguEl.appendChild(option);
            });

            if (nowSigungu) sigunguEl.value = nowSigungu;
        }
    }

    if (searchKeywordEl) {
        searchKeywordEl.value = params.get("keyword") || "";
    }

    if (perPageEl) {
        perPageEl.value = params.get("per_page") || "10";
        perPageEl.addEventListener("change", function () {
            const newParams = new URLSearchParams(window.location.search);
            newParams.set("per_page", this.value);
            newParams.set("page", 1);
            window.location.search = newParams.toString();
        });
    }

    if (sortEl) {
        sortEl.value = params.get("sort") || "recent";
        sortEl.addEventListener("change", function () {
            const newParams = new URLSearchParams(window.location.search);
            newParams.set("sort", this.value);
            newParams.set("page", 1);
            window.location.search = newParams.toString();
        });
    }

    /* ===========================
        지도 생성
    =========================== */
    var container = document.getElementById("map");
    if (!container || typeof kakao === "undefined") return;

    var map = new kakao.maps.Map(container, {
        center: new kakao.maps.LatLng(37.5665, 126.9780),
        level: 5,
        draggable: false,
        scrollwheel: false,
        disableDoubleClickZoom: true,
        keyboardShortcuts: false
    });

    var bounds = new kakao.maps.LatLngBounds();
    var markerMap = {};
    var fixedInfoWindow = null;

    /* ===========================
        마커 & InfoWindow 생성
    =========================== */
    facilities.forEach(function (item) {
        var lat = parseFloat(item.lat);
        var lng = parseFloat(item.lng);
        if (isNaN(lat) || isNaN(lng)) return;

        var pos = new kakao.maps.LatLng(lat, lng);

        var marker = new kakao.maps.Marker({
            map: map,
            position: pos
        });

        // 🔥 빈칸 완전 제거된 InfoWindow content
        var iwContent = `
<div style="
    background:#fff;
    border:1px solid #d7dbe3;
    border-radius:14px;
    display:flex;
    align-items:center;
    box-shadow:0 4px 12px rgba(0,0,0,0.25);
    overflow:hidden;
">
    <div style="
        padding:10px 14px;
        font-size:16px;
        font-weight:700;
        color:#1A2A43;
        white-space:nowrap;
    ">
        <a href="/facility/detail/${item.id}?fName=${encodeURIComponent(item.name)}"
           style="text-decoration:none;color:#1A2A43;">
           ${item.name}
        </a>
    </div>
    <div style="
        background:#e74a3b;
        padding:10px 14px;
        color:#fff;
        font-size:18px;
        font-weight:bold;
    ">
        ▶
    </div>
</div>`;

        var infowindow = new kakao.maps.InfoWindow({
            content: iwContent
        });

        // 마커 클릭 → 상세 페이지 이동
        kakao.maps.event.addListener(marker, "click", function () {
            window.location.href = `/facility/detail/${item.id}?fName=${encodeURIComponent(item.name)}`;
        });

        // 마커 hover
        kakao.maps.event.addListener(marker, "mouseover", function () {
            infowindow.open(map, marker);
        });

        kakao.maps.event.addListener(marker, "mouseout", function () {
            if (fixedInfoWindow !== infowindow) {
                infowindow.close();
            }
        });

        markerMap[item.id] = { marker, infowindow, position: pos };
        bounds.extend(pos);
    });

    if (!bounds.isEmpty()) map.setBounds(bounds);

    /* ===========================
        리스트 클릭 → 지도 이동 + InfoWindow 열기
    =========================== */
    document.querySelectorAll(".facility-link").forEach(function (link) {
        link.addEventListener("click", function (e) {
            e.preventDefault();

            var id = this.dataset.id;
            var obj = markerMap[id];
            if (!obj) return;

            map.setCenter(obj.position);
            map.setLevel(7);

            if (fixedInfoWindow) fixedInfoWindow.close();

            obj.infowindow.open(map, obj.marker);
            fixedInfoWindow = obj.infowindow;

            const mapRect = container.getBoundingClientRect();
            window.scrollTo({
                top: window.pageYOffset + mapRect.top - 100,
                behavior: "smooth"
            });
        });
    });
});
