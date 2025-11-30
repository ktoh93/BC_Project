// sport_type_manager.js

// document.addEventListener("DOMContentLoaded", function () {

//     const openBtn = document.getElementById("openModal");
//     const closeBtn = document.getElementById("closeModal");
//     const modal = document.getElementById("modalOverlay");

//     // Modal 열기
//     if (openBtn) {
//         openBtn.onclick = function () {
//             modal.classList.add("show");
//         };
//     }

//     // Modal 닫기
//     if (closeBtn) {
//         closeBtn.onclick = function () {
//             modal.classList.remove("show");
//         };
//     }
// });

// 팝업 열기/닫기
document.getElementById("openSportsPopup").onclick = function () {
    document.getElementById("sportsPopup").style.display = "flex";
};

document.getElementById("closeSportsPopup").onclick = function () {
    document.getElementById("sportsPopup").style.display = "none";
};


//
//  종목 추가 기능 (Enter 입력)
//
const newSportInput = document.getElementById("newSportInput");

newSportInput.addEventListener("keypress", function (e) {
    if (e.key === "Enter") {
        e.preventDefault();

        const name = newSportInput.value.trim();
        if (!name) return;

        fetch("/manager/sports/add/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken"),
            },
            body: JSON.stringify({ name: name }),
        })
        .then((res) => res.json())
        .then((data) => {
            if (data.status === "ok") {
                alert("종목이 추가되었습니다!");
                location.reload();
            } else {
                alert(data.msg || "추가 실패");
            }
        });
    }
});


//
//  종목 삭제 (체크된 항목 삭제)
//
document.getElementById("deleteSportsBtn").onclick = function() {
    const checked = document.querySelectorAll(".sport-check:checked");

    if (checked.length === 0) {
        alert("삭제할 종목을 선택하세요.");
        return;
    }

    if (!confirm("정말 삭제하시겠습니까?")) return;

    const ids = Array.from(checked).map(chk => 
        chk.closest(".sport-card").dataset.id
    );

    fetch("/manager/sports/delete/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken"),
        },
        body: JSON.stringify({ ids: ids }),
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === "ok") {
            alert("삭제 완료!");
            location.reload();
        } else {
            alert(data.msg || "삭제 실패");
        }
    });
};


//
//  CSRF Cookie 가져오기
//
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === name + "=") {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
