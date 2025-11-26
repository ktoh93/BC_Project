// DOM 로드 후 실행
document.addEventListener("DOMContentLoaded", () => {
    const btn_edit = document.querySelector(".btn-edit");
    const btn_password = document.querySelector(".btn-password");


    // 1) 정보 수정 클릭
    btn_edit.addEventListener("click", function() {
        // console.log("정보 수정 클릭됨");
        handle_edit_profile();
    });
    
    // 2) 비밀번호 변경 클릭
    btn_password.addEventListener("click", function() {
        // console.log("비밀번호 변경 클릭됨");
        handle_password_change();
    });

});

// -----------------------------
// 함수 분리 (필요 시 기능 바로 추가 가능)
// -----------------------------

// 정보 수정 버튼 클릭 시
function handle_edit_profile() {
    // 예시: 수정 페이지로 이동
    window.location.href = "/member/edit/";

    // 또는 모달 열기, 입력 필드 활성화 등 여기 넣으면 됨
    // alert("정보 수정 기능 준비중");
}

// 비밀번호 변경 버튼 클릭 시
function handle_password_change() {
    // 예시: 비밀번호 변경 페이지로 이동
    window.location.href = "/member/password/";
    
    // 모달 열기/폼 보여주기 등 수정 가능
    // alert("비밀번호 변경 기능 준비중");
}
