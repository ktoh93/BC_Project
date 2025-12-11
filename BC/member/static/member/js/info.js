// DOM 로드 후 실행
document.addEventListener("DOMContentLoaded", () => {
    const btn_edit = document.querySelector(".btn-edit");
    const btn_password = document.querySelector(".btn-password");
    const btn_withdraw = document.querySelector(".btn-withdraw");


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
    
    // 2) 회원탈퇴 클릭
    btn_withdraw.addEventListener("click", function() {
        // console.log("비밀번호 변경 클릭됨");
        handle_withdraw();
    });

    // 탈퇴 관련 이벤트
    const withdrawSection = document.getElementById("withdrawSection");
    const cancelWithdrawBtn = document.getElementById("cancelWithdraw");
    const confirmWithdrawBtn = document.getElementById("confirmWithdraw");
    const reasonRadios = document.querySelectorAll('input[name="delete_reason"]');
    const otherReasonBox = document.getElementById("otherReasonBox");
    const otherReasonText = document.getElementById("otherReasonText");

    // 라디오 버튼 변경 시 기타 입력창 표시/숨김
    reasonRadios.forEach(radio => {
        radio.addEventListener("change", function() {
            if (this.value === '6') {
                otherReasonBox.style.display = 'block';
                otherReasonText.required = true;
            } else {
                otherReasonBox.style.display = 'none';
                otherReasonText.required = false;
                otherReasonText.value = '';
            }
        });
    });

    // 취소 버튼
    cancelWithdrawBtn.addEventListener("click", function() {
        withdrawSection.style.display = 'none';
        // 폼 초기화
        document.getElementById("withdrawReasonForm").reset();
        otherReasonBox.style.display = 'none';
        otherReasonText.value = '';
    });

    // 탈퇴 확인 버튼
    confirmWithdrawBtn.addEventListener("click", function() {
        const selectedReason = document.querySelector('input[name="delete_reason"]:checked');
        
        if (!selectedReason) {
            alert('탈퇴 사유를 선택해주세요.');
            return;
        }

        // 6번(기타) 선택 시 입력값 확인
        if (selectedReason.value === '6') {
            const otherText = otherReasonText.value.trim();
            if (!otherText) {
                alert('기타 사유를 입력해주세요.');
                return;
            }
            // "6:직접 입력한 내용" 형태로 저장
            document.getElementById("delete_reason_input").value = '6:' + otherText;
        } else {
            // 1~5번은 번호만 전송 (서버에서 내용으로 변환)
            document.getElementById("delete_reason_input").value = selectedReason.value;
        }

        // 최종 확인
        const ok = confirm('정말 회원 탈퇴를 진행하시겠습니까?');
        if (ok) {
            document.getElementById("withdrawForm").submit();
        }
    });

});

// -----------------------------
// 함수 분리 (필요 시 기능 바로 추가 가능)
// -----------------------------

// 정보 수정 버튼 클릭 시
function handle_edit_profile() {
    // 예시: 수정 페이지로 이동
    window.location.href = typeof MEMBER_EDIT_URL !== 'undefined' ? MEMBER_EDIT_URL : "/member/edit/";
    
    // 또는 모달 열기, 입력 필드 활성화 등 여기 넣으면 됨
    // alert("정보 수정 기능 준비중");
}

// 비밀번호 변경 버튼 클릭 시
function handle_password_change() {
    // 예시: 비밀번호 변경 페이지로 이동
    window.location.href = typeof MEMBER_PASSWORD_URL !== 'undefined' ? MEMBER_PASSWORD_URL : "/member/password/";
    
    // 모달 열기/폼 보여주기 등 수정 가능
    // alert("비밀번호 변경 기능 준비중");
}

function handle_withdraw(){
    // 탈퇴 섹션 표시
    const withdrawSection = document.getElementById("withdrawSection");
    if (withdrawSection.style.display === 'none' || !withdrawSection.style.display) {
        withdrawSection.style.display = 'block';
        // 스크롤 이동
        withdrawSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    } else {
        withdrawSection.style.display = 'none';
    }
}