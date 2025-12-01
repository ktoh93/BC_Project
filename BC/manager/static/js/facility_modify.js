document.addEventListener("DOMContentLoaded", function () {

    /* -------------------------------
     * 1. 기존 시간 JSON 파싱
     * ------------------------------- */
    let raw = document.getElementById("timeJson").textContent.trim();
    let timeData = {};

    try {
        timeData = raw ? JSON.parse(raw) : {};
    } catch (e) {
        console.warn("시간 JSON 파싱 실패. 기본값으로 진행");
        timeData = {};
    }

    /* -------------------------------
     * 2. 요일 리스트
     * ------------------------------- */
    const days = [
        { key: "monday", label: "월요일" },
        { key: "tuesday", label: "화요일" },
        { key: "wednesday", label: "수요일" },
        { key: "thursday", label: "목요일" },
        { key: "friday", label: "금요일" },
        { key: "saturday", label: "토요일" },
        { key: "sunday", label: "일요일" }
    ];

    const container = document.getElementById("timeSettingContainer");


    /* -------------------------------
     * 3. UI 자동 생성
     * ------------------------------- */
    days.forEach(day => {

        // 기본값 설정 (DB에 없거나 비었을 경우)
        if (!timeData[day.key]) {
            timeData[day.key] = {
                open: null,
                close: null,
                interval: 60,
                active: false
            };
        }

        const d = timeData[day.key];
        const isActive = d.active === true;

        const html = `
            <div class="day-row" data-day="${day.key}">
                <h3 class="day-title">${day.label}</h3>

                <label class="active-wrap">
                    <input type="checkbox" class="active-check" ${isActive ? "checked" : ""}>
                    운영함
                </label>

                <div class="time-inputs">
                    <label>시작</label>
                    <input type="time" class="open-time"
                        value="${d.open ?? ""}"
                        ${isActive ? "" : "disabled"}>

                    <label>종료</label>
                    <input type="time" class="close-time"
                        value="${d.close ?? ""}"
                        ${isActive ? "" : "disabled"}>

                    <label>간격(분)</label>
                    <input type="number" class="interval-time"
                        value="${d.interval ?? 60}"
                        min="10" step="10"
                        ${isActive ? "" : "disabled"}>
                </div>
            </div>
        `;

        container.insertAdjacentHTML("beforeend", html);
    });


    /* -------------------------------
     * 4. active 체크 → input 활성/비활성
     * ------------------------------- */
    container.addEventListener("change", function (e) {

        if (!e.target.classList.contains("active-check")) return;

        const row = e.target.closest(".day-row");
        const key = row.dataset.day;
        const isActive = e.target.checked;

        // input disabled 처리
        row.querySelectorAll(".open-time, .close-time, .interval-time")
            .forEach(inp => inp.disabled = !isActive);

        // 데이터 업데이트
        timeData[key].active = isActive;

        if (!isActive) {
            timeData[key].open = null;
            timeData[key].close = null;
            timeData[key].interval = null;
        }
    });


    /* -------------------------------
     * 5. input 입력 시 timeData 갱신
     * ------------------------------- */
    container.addEventListener("input", function (e) {

        const row = e.target.closest(".day-row");
        if (!row) return;

        const key = row.dataset.day;

        timeData[key].open = row.querySelector(".open-time").value || null;
        timeData[key].close = row.querySelector(".close-time").value || null;

        let intervalVal = parseInt(row.querySelector(".interval-time").value);
        timeData[key].interval = isNaN(intervalVal) ? null : intervalVal;
    });


    /* -------------------------------
     * 6. 전체 저장 버튼 → JSON 쓰고 submit
     * ------------------------------- */
    const saveBtn = document.querySelector(".btn-save-all");
    saveBtn.addEventListener("click", function (e) {

        // 저장 직전 JSON 입력
        document.getElementById("reservationTimeInput").value =
            JSON.stringify(timeData);

        console.log("🔥 최종 저장 JSON", timeData);
        // form은 기본적으로 submit됨
    });

});
