// sport_type_manager.js

document.addEventListener("DOMContentLoaded", function () {

    const openBtn = document.getElementById("openModal");
    const closeBtn = document.getElementById("closeModal");
    const modal = document.getElementById("modalOverlay");

    // Modal 열기
    if (openBtn) {
        openBtn.onclick = function () {
            modal.classList.add("show");
        };
    }

    // Modal 닫기
    if (closeBtn) {
        closeBtn.onclick = function () {
            modal.classList.remove("show");
        };
    }
});
