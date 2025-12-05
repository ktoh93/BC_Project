// recruitment_update.js

// DOM 로드 후 실행
document.addEventListener("DOMContentLoaded", () => {
    const btn_submit   = document.querySelector(".btn-submit");
    const btn_list     = document.querySelector(".btn-list");
    const recruit_form = document.querySelector("#recruit_form");  // 폼이 있으면 여기로

    // 1) 작성(수정 완료) 버튼
    if (btn_submit && recruit_form) {
        btn_submit.addEventListener("click", function (e) {
            // 기본 동작 그대로 쓰려면 막을 필요 없음
            // e.preventDefault();
            recruit_form.submit();   // -> Django update view 로 POST
        });
    }

    // 2) 목록 버튼
    if (btn_list) {
        btn_list.addEventListener("click", function (e) {
            e.preventDefault();
            handle_list();
        });
    }

    
    //  3) 파일 2MB 이상 등록 방지
    const fileInput = document.querySelector('input[type="file"]');
    if (!fileInput) return;

    fileInput.addEventListener("change", function() {
        const maxSize = 2 * 1024 * 1024; // 2MB
        const files = this.files;

        for (let f of files) {
            if (f.size > maxSize) {
                alert(`"${f.name}" 은(는) 2MB를 초과하여 업로드할 수 없습니다.`);
                this.value = "";  // 선택한 파일 전체 초기화
                return;
            }
        }
    });
});

// 목록 이동
function handle_list() {
    // 실제 리스트 URL에 맞게 수정해서 쓰시면 됩니다.
    window.location.href = "/recruitment";
}
