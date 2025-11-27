document.addEventListener("DOMContentLoaded", function () {
    /* 대한민국 시/도 + 시/군/구 전체 데이터 */
    const regionData = {
        "서울특별시": [
            "강남구","강동구","강북구","강서구","관악구","광진구","구로구","금천구",
            "노원구","도봉구","동대문구","동작구","마포구","서대문구","서초구","성동구",
            "성북구","송파구","양천구","영등포구","용산구","은평구","종로구","중구","중랑구"
        ],

        "부산광역시": [
            "강서구","금정구","남구","동구","동래구","부산진구","북구","사상구","사하구",
            "서구","수영구","연제구","영도구","중구","해운대구","기장군"
        ],

        "대구광역시": [
            "남구","달서구","동구","북구","서구","수성구","중구","달성군"
        ],

        "인천광역시": [
            "계양구","남동구","동구","미추홀구","부평구","서구","연수구","중구","강화군","옹진군"
        ],

        "광주광역시": ["광산구","남구","동구","북구","서구"],
        "대전광역시": ["대덕구","동구","서구","유성구","중구"],
        "울산광역시": ["남구","동구","북구","중구","울주군"],

        "세종특별자치시": ["세종시"],

        "경기도": [
            "수원시","용인시","고양시","성남시","화성시","부천시","안산시",
            "남양주시","안양시","평택시","시흥시","파주시","의정부시","김포시","광주시",
            "광명시","군포시","하남시","오산시","이천시","안성시","의왕시","양평군",
            "여주시","양주시","포천시","가평군","동두천시"
        ],

        "강원도": [
            "춘천시","원주시","강릉시","동해시","속초시","삼척시","홍천군","횡성군",
            "영월군","평창군","정선군","철원군","화천군","양구군","인제군","고성군","양양군"
        ],

        "충청북도": [
            "청주시","충주시","제천시","보은군","옥천군","영동군","진천군","괴산군",
            "음성군","단양군","증평군"
        ],

        "충청남도": [
            "천안시","아산시","서산시","당진시","공주시","보령시","논산시","계룡시",
            "금산군","부여군","서천군","청양군","홍성군","예산군","태안군"
        ],

        "전라북도": [
            "전주시","익산시","군산시","정읍시","남원시","김제시","완주군",
            "진안군","무주군","장수군","임실군","순창군","고창군","부안군"
        ],

        "전라남도": [
            "목포시","여수시","순천시","나주시","광양시","담양군","곡성군","구례군",
            "고흥군","보성군","화순군","장흥군","강진군","해남군","영암군","무안군",
            "함평군","영광군","장성군","완도군","진도군","신안군"
        ],

        "경상북도": [
            "포항시","경주시","김천시","안동시","구미시","영주시","영천시","상주시","문경시",
            "경산시","의성군","청송군","영양군","영덕군","청도군","고령군","성주군","칠곡군",
            "예천군","봉화군","울진군","울릉군"
        ],

        "경상남도": [
            "창원시","김해시","진주시","양산시","거제시","통영시",
            "사천시","밀양시","함안군","창녕군","고성군","남해군",
            "하동군","산청군","함양군","거창군","합천군"
        ],

        "제주특별자치도": ["제주시","서귀포시"]
    };

  const params = new URLSearchParams(window.location.search);

    const sidoEl = document.getElementById("sido");
    const sigunguEl = document.getElementById("sigungu");
    const perPageEl = document.getElementById("perPageSelect");

    // 시/도 목록 채우기
    Object.keys(regionData).forEach((sido) => {
        const option = document.createElement("option");
        option.value = sido;
        option.textContent = sido;
        sidoEl.appendChild(option);
    });

    // URL 파라미터 기반 선택값 복원
    const nowSido = params.get("cpNm") || "";
    const nowSigungu = params.get("cpbNm") || "";

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

    sidoEl.addEventListener("change", function () {
        const selected = this.value;

        sigunguEl.innerHTML = `<option value="">구/군 선택</option>`;

        if (!selected || !regionData[selected]) return;

        regionData[selected].forEach((gu) => {
            const option = document.createElement("option");
            option.value = gu;
            option.textContent = gu;
            sigunguEl.appendChild(option);
        });
    });

    // perPage 처리
    if (perPageEl) {
        const nowPer = params.get("per_page") || "15";
        perPageEl.value = nowPer;

        perPageEl.addEventListener("change", function () {
            params.set("per_page", this.value);
            params.set("page", 1);
            window.location.search = params.toString();
        });
    }

    function renderFacilityList(data) {
        const listBox = document.getElementById("facilityList");
        listBox.innerHTML = "";

        if (!data || data.length === 0) {
            listBox.innerHTML = `
                <tr>
                    <td colspan="4" style="text-align:center; padding:20px;">검색 결과가 없습니다.</td>
                </tr>
            `;
            return;
        }

        data.forEach((item, index) => {
            const rowNumber = item.row_no ?? (index + 1);
            listBox.innerHTML += `
                <tr>
                    <td>${rowNumber}</td>
                    <td><input type="checkbox" class="facility-check" value="${item.id}"></td>
                    <td>${item.name}</td>
                    <td>${item.address}</td>
                </tr>
            `;
        });
    }   // ← 🔥 renderFacilityList 함수는 여기서 끝나는 것이 정답!

    // 🔥 그리고 renderFacilityList 밖에서 JSON 로드하는 코드가 와야 함
    const raw = document.getElementById("facilityData").textContent.trim();

    try {
        const facilityList = JSON.parse(raw);
        renderFacilityList(facilityList);
    } catch (e) {
        console.error("JSON 파싱 오류:", e);
    }
});