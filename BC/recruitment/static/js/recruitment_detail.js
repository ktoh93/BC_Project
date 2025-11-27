document.addEventListener("DOMContentLoaded", function () {


    const btn_list = document.querySelector(".btn-list");
    const btn_update = document.querySelector(".btn-update");



    // 1) 수정 클릭
    btn_update.addEventListener("click", function() {
        // console.log("list 클릭됨");
        handle_update();
    });
    // 2) 목록 클릭
    btn_list.addEventListener("click", function() {
        // console.log("list 클릭됨");
        handle_list();
    });


});







function handle_list() {
    window.location.href = "/recruitment";

    // 또는 모달 열기, 입력 필드 활성화 등 여기 넣으면 됨
    // alert("정보 수정 기능 준비중");
};
function handle_update() {
    // 예시: 수정 페이지로 이동
    window.location.href = "/recruitment/update/1";

    // 또는 모달 열기, 입력 필드 활성화 등 여기 넣으면 됨
    // alert("정보 수정 기능 준비중");
};



