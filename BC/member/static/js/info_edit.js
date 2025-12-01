// DOM 로드 후 실행
document.addEventListener("DOMContentLoaded", () => {
    console.log("info_edit.js 로드됨");
    const form = document.querySelector(".mypage-form");
    
    if (form) {
        console.log("폼 찾음:", form);
        // 폼 제출 이벤트 처리
        form.addEventListener("submit", function(e) {
            console.log("폼 제출 이벤트 발생");
            e.preventDefault();
            e.stopPropagation();
            console.log("기본 제출 방지됨");
            handle_edit_profile(this);
            return false;
        });
    } else {
        console.error("폼을 찾을 수 없습니다!");
    }
    
    // 주소 검색 버튼 이벤트
    const addressSearchBtn = document.getElementById("addressSearchBtn");
    const addressInput = document.getElementById("address");
    
    if (addressSearchBtn && addressInput) {
        addressSearchBtn.addEventListener("click", function () {
            new daum.Postcode({
                oncomplete: function (data) {
                    // 도로명주소 또는 지번주소 선택
                    let addr = '';
                    if (data.userSelectedType === 'R') {
                        // 사용자가 도로명 주소를 선택했을 경우
                        addr = data.roadAddress;
                    } else {
                        // 사용자가 지번 주소를 선택했을 경우
                        addr = data.jibunAddress;
                    }
                    
                    addressInput.value = addr;
                    
                    // 주소 데이터를 hidden input에 저장 (서버에서 파싱용)
                    let addrDataInput = document.getElementById("address_data");
                    if (!addrDataInput) {
                        // hidden input이 없으면 생성
                        const hiddenInput = document.createElement('input');
                        hiddenInput.type = 'hidden';
                        hiddenInput.id = 'address_data';
                        hiddenInput.name = 'address_data';
                        addressInput.parentElement.appendChild(hiddenInput);
                        addrDataInput = hiddenInput;
                    }
                    addrDataInput.value = JSON.stringify({
                        sido: data.sido,
                        sigungu: data.sigungu,
                        roadAddress: data.roadAddress,
                        jibunAddress: data.jibunAddress,
                        userSelectedType: data.userSelectedType
                    });
                    
                    // 파싱된 주소 표시 업데이트
                    updateAddressDisplay(data);
                    
                    const addressDetailInput = document.getElementById("address_detail");
                    if (addressDetailInput) {
                        addressDetailInput.focus();
                    }
                }
            }).open();
        });
    }
});

// 주소 표시 업데이트 함수
function updateAddressDisplay(data) {
    // 간단한 파싱 (서버에서 정확히 파싱)
    const sido = data.sido || '';
    const sigungu = data.sigungu || '';
    
    // 구 추출 시도
    let gu = '';
    let addr1 = sido;
    
    if (sigungu) {
        if (sigungu.endsWith('구')) {
            if (sigungu.includes('시 ')) {
                const parts = sigungu.split('시 ');
                if (parts.length === 2) {
                    addr1 = sido + ' ' + parts[0] + '시';
                    gu = parts[1];
                } else {
                    gu = sigungu;
                }
            } else {
                gu = sigungu;
            }
        } else if (sigungu.endsWith('시') || sigungu.endsWith('군')) {
            addr1 = sido + ' ' + sigungu;
        }
    }
    
    // 표시 업데이트
    const displayAddr1 = document.getElementById("display_addr1");
    const displayAddr2 = document.getElementById("display_addr2");
    
    if (displayAddr1) displayAddr1.textContent = addr1;
    if (displayAddr2) displayAddr2.textContent = gu;
}

// -----------------------------
// 정보 수정 처리 함수 (AJAX)
// -----------------------------

function handle_edit_profile(form) {
    console.log("handle_edit_profile 함수 실행");
    const submitBtn = form.querySelector(".btn-edit-complete");
    const originalText = submitBtn.textContent;
    
    // 버튼 비활성화 및 로딩 상태
    submitBtn.disabled = true;
    submitBtn.textContent = "수정 중...";
    
    // FormData 생성
    const formData = new FormData(form);
    
    // FormData 내용 확인
    console.log("FormData 내용:");
    for (let [key, value] of formData.entries()) {
        console.log(key + ":", value);
    }
    
    // CSRF 토큰 가져오기
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    console.log("CSRF 토큰:", csrftoken ? "존재함" : "없음");
    
    console.log("AJAX 요청 전송 시작");
    // AJAX 요청
    fetch('/member/edit/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': csrftoken
        }
    })
    .then(response => {
        console.log("응답 받음, 상태:", response.status);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log("응답 데이터:", data);
        if (data.success) {
            // 성공 토스트 메시지 표시
            showToast(data.message, 'success');
            
            // 2초 후 내 정보 페이지로 이동 (캐시 무시)
            setTimeout(function() {
                // 캐시를 무시하고 강제로 새로고침
                window.location.href = '/member/info/?_=' + new Date().getTime();
            }, 2000);
        } else {
            // 실패 토스트 메시지 표시
            console.error("서버 오류:", data.message);
            showToast(data.message, 'error');
            
            // 버튼 복원
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        }
    })
    .catch(error => {
        console.error('AJAX 요청 오류:', error);
        showToast('수정 중 오류가 발생했습니다.', 'error');
        
        // 버튼 복원
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
    });
}

// -----------------------------
// 토스트 메시지 표시 함수
// -----------------------------

function showToast(message, type = 'success') {
    // 기존 토스트가 있으면 제거
    const existingToast = document.getElementById('toast');
    if (existingToast) {
        existingToast.remove();
    }
    
    // 토스트 요소 생성
    const toast = document.createElement('div');
    toast.id = 'toast';
    toast.className = `toast toast-${type}`;
    
    // 아이콘 설정
    const icon = type === 'success' ? '✓' : '✕';
    
    toast.innerHTML = `
        <div class="toast-content">
            <span class="toast-icon">${icon}</span>
            <span class="toast-message">${message}</span>
        </div>
    `;
    
    // body에 추가
    document.body.appendChild(toast);
    
    // 애니메이션을 위해 약간의 지연 후 표시
    setTimeout(() => {
        toast.classList.add('show');
    }, 10);
    
    // 3초 후 자동 제거
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }, 3000);
}