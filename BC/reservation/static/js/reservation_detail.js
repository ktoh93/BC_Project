document.addEventListener("DOMContentLoaded", function () {

    /* ---------------------------
        0) 로그인 체크
    ---------------------------- */
    const isAuth = document.getElementById("is-authenticated").value;
    if (isAuth !== "1") {
        alert("로그인 후 이용 가능합니다.");
        location.href = "/login/";
        return; 
    }


    const rsPossible = document.getElementById("rs-possible").value;
    if (rsPossible !== "1") {
        return;
    }
    /* ---------------------------
        1) 데이터 로드
    ---------------------------- */
    const reservationTime = JSON.parse(
        document.getElementById("reservation-json").textContent
    );

    const reservedData = JSON.parse(
        document.getElementById("reserved-json").textContent
    );

    const facilityId = document.getElementById("facility-id").value;

    const slotGrid = document.getElementById("time-slot-grid");
    const selectedDateEl = document.getElementById("selected-date");
    const selectedTimeEl = document.getElementById("selected-time");

    /* ---------------------------
        2) 캘린더 설정
    ---------------------------- */
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const calendar = new FullCalendar.Calendar(document.getElementById('calendar'), {
        initialView: 'dayGridMonth',
        locale: 'ko',
        headerToolbar: { left: 'prev', center: 'title', right: 'next' },

        dateClick: function (info) {

            const clicked = new Date(info.dateStr);
            clicked.setHours(0, 0, 0, 0);
            if (clicked < today) return;

            document.querySelectorAll('.fc-day-selected')
                .forEach(cell => cell.classList.remove('fc-day-selected'));

            info.dayEl.classList.add('fc-day-selected');
            selectedDateEl.textContent = info.dateStr;

            const dayOfWeek = clicked.toLocaleString("en-US", { weekday: "long" }).toLowerCase();
            const dayInfo = reservationTime[dayOfWeek];

            slotGrid.innerHTML = "";

            if (!dayInfo || !dayInfo.active) {
                slotGrid.innerHTML = `<div style="grid-column:1/-1; text-align:center; color:#777;">휴무일입니다</div>`;
                selectedTimeEl.textContent = "-";
                return;
            }

            generateSlots(dayInfo.open, dayInfo.close, dayInfo.interval);
        },

        dayCellDidMount: function (arg) {
            const cellDate = new Date(arg.date);
            cellDate.setHours(0, 0, 0, 0);

            const dayOfWeek = cellDate.toLocaleString("en-US", { weekday: "long" }).toLowerCase();
            const dayInfo = reservationTime[dayOfWeek];

            if (cellDate < today) {
                arg.el.classList.add("fc-day-disabled");
                return;
            }

            if (!dayInfo || !dayInfo.active) {
                arg.el.classList.add("fc-day-unavailable");
                return;
            }

            arg.el.classList.add("fc-day-available");
        }
    });

    calendar.render();


    /* ---------------------------
        3) 슬롯 생성 함수
    ---------------------------- */
    function generateSlots(openTime, closeTime, interval) {
        slotGrid.innerHTML = "";

        let [oh, om] = openTime.split(":").map(Number);
        let [ch, cm] = closeTime.split(":").map(Number);

        let start = new Date();
        start.setHours(oh, om, 0, 0);

        let end = new Date();
        end.setHours(ch, cm, 0, 0);

        const selectedDate = selectedDateEl.textContent;

        while (start < end) {
            const next = new Date(start.getTime() + interval * 60000);
            if (next > end) break;

            const slotText = `${formatTime(start)} ~ ${formatTime(next)}`;
            const slotStart = formatTime(start);
            const slotEnd = formatTime(next);

            let div = document.createElement("div");
            div.classList.add("slot");
            div.textContent = slotText;

            const isReserved = reservedData.some(r =>
                r.date === selectedDate &&
                r.start === slotStart &&
                r.end === slotEnd
            );

            if (isReserved) {
                div.classList.add("disabled");
                div.style.pointerEvents = "none";
            } else {
                div.addEventListener("click", function () {

                    if (div.classList.contains("selected")) {
                        div.classList.remove("selected");
                    } else {
                        div.classList.add("selected");
                    }

                    const selectedSlots = Array.from(document.querySelectorAll(".slot.selected"))
                        .map(s => s.textContent);

                    selectedTimeEl.textContent =
                        selectedSlots.length === 0 ? "-" : selectedSlots.join(", ");
                });
            }

            slotGrid.appendChild(div);
            start = next;
        }
    }

    /* ---------------------------
        4) 시간 format
    ---------------------------- */
    function formatTime(date) {
        let h = String(date.getHours()).padStart(2, "0");
        let m = String(date.getMinutes()).padStart(2, "0");
        return `${h}:${m}`;
    }

    /* ---------------------------
        5) 예약 버튼
    ---------------------------- */
    document.getElementById("reserve-button").addEventListener("click", function () {

        const date = selectedDateEl.textContent;
        const selected = selectedTimeEl.textContent;

        if (date === "-" || selected === "-") {
            alert("날짜와 시간을 선택해주세요.");
            return;
        }

        const slotList = selected.split(", ").map(t => {
            const [s, e] = t.split(" ~ ");
            return { start: s, end: e };
        });

        fetch("/reservation/save/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken")
            },
            body: JSON.stringify({
                date: date,
                slots: slotList,
                facility_id: facilityId
            })
        })
            .then(res => res.json())
            .then(data => {
                if (data.result === "ok") {
                    alert("예약이 완료되었습니다!");
                    window.location.href = `/reservation/${facilityId}`;
                } else {
                    alert(data.msg);
                }
            });
    });

    /* ---------------------------
        6) CSRF
    ---------------------------- */
    function getCookie(name) {
        let cookieValue = null;
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
        return cookieValue;
    }

    /* ---------------------------
        7) 오늘 날짜 자동 선택
    ---------------------------- */
    (function selectToday() {
        const today = new Date();
        const yyyy = today.getFullYear();
        const mm = String(today.getMonth() + 1).padStart(2, "0");
        const dd = String(today.getDate()).padStart(2, "0");
        const todayStr = `${yyyy}-${mm}-${dd}`;

        const todayCell = document.querySelector(`[data-date="${todayStr}"]`);
        if (todayCell) {
            calendar.trigger('dateClick', {
                date: today,
                dateStr: todayStr,
                dayEl: todayCell
            });
        }
    })();
});
