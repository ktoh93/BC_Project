/**
 * 전역 Toast 알림 함수
 * @param {string} message - 표시할 메시지
 * @param {string} type - 알림 타입 ('success', 'error', 'info', 'warning')
 */
function showToast(message, type = "success") {
    const existingToast = document.getElementById("toast");
    if (existingToast) existingToast.remove();

    const toast = document.createElement("div");
    toast.id = "toast";
    toast.className = `toast toast-${type}`;

    // 타입별 아이콘 설정
    let icon = "✓";
    if (type === "error") icon = "✕";
    else if (type === "info") icon = "ℹ";
    else if (type === "warning") icon = "⚠";

    toast.innerHTML = `
        <div class="toast-content">
            <span class="toast-icon">${icon}</span>
            <span class="toast-message">${message}</span>
        </div>
    `;

    document.body.appendChild(toast);

    // 애니메이션 표시
    setTimeout(() => toast.classList.add("show"), 10);
    
    // 5초 후 자동 사라짐
    setTimeout(() => {
        toast.classList.remove("show");
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

/**
 * Django messages를 Toast로 자동 변환
 * 페이지 로드 시 Django messages를 감지하여 Toast로 표시
 */
document.addEventListener("DOMContentLoaded", function() {
    let toastIndex = 0;
    
    // 모든 alert 요소 찾기 (message-area 내부 또는 직접 표시된 것)
    const allAlerts = document.querySelectorAll(".alert, [class*='alert-']");
    
    allAlerts.forEach(function(alert) {
        // 이미 숨겨진 것은 건너뛰기
        if (alert.style.display === "none") return;
        
        const message = alert.textContent.trim();
        if (!message) return;
        
        let type = "info";
        
        // 클래스에서 타입 추출
        if (alert.classList.contains("alert-success") || alert.className.includes("alert-success")) {
            type = "success";
        } else if (alert.classList.contains("alert-error") || alert.className.includes("alert-error")) {
            type = "error";
        } else if (alert.classList.contains("alert-warning") || alert.className.includes("alert-warning")) {
            type = "warning";
        } else if (alert.classList.contains("alert-info") || alert.className.includes("alert-info")) {
            type = "info";
        } else {
            // 클래스명에서 타입 추출 시도
            const classMatch = alert.className.match(/alert-(\w+)/);
            if (classMatch) {
                type = classMatch[1];
            }
        }
        
        // Toast 표시 (여러 개일 경우 순차적으로)
        setTimeout(function() {
            showToast(message, type);
        }, toastIndex * 200);
        
        toastIndex++;
        
        // 원본 메시지 숨기기
        alert.style.display = "none";
        
        // 부모 message-area도 숨기기 (비어있으면)
        const messageArea = alert.closest(".message-area");
        if (messageArea) {
            const remainingAlerts = messageArea.querySelectorAll(".alert:not([style*='display: none'])");
            if (remainingAlerts.length === 0) {
                messageArea.style.display = "none";
            }
        }
    });
});

