

// DOM 로드 후 실행
document.addEventListener("DOMContentLoaded", () => {
    const btn_submit = document.querySelector(".btn-submit");
    const btn_list = document.querySelector(".btn-list");


    // 1) 등록 클릭
    if (btn_submit && recruit_form) {
        btn_submit.addEventListener("click", function (e) {
            // 기본 submit 쓰고 싶으면 이 preventDefault 는 지워도 됨
            // e.preventDefault();
            recruit_form.submit();  // -> Django view 로 POST 날아감
        });
    }
    
    // 2) 목록 클릭
    btn_list.addEventListener("click", function() {
        // console.log("list 클릭됨");
        handle_list();
    });


    const fileInput = document.getElementById('fileInput');
    const fileList = document.getElementById('fileList');

    if (fileInput && fileList) {
        fileInput.addEventListener('change', function(e) {
            fileList.innerHTML = ''; // 기존 목록 초기화

            if (e.target.files.length > 0) {
                Array.from(e.target.files).forEach((file, index) => {
                    const fileItem = document.createElement('div');
                    fileItem.className = 'file-item';
                    fileItem.innerHTML = `
                        <span class="file-item-name">${file.name}</span>
                        <button type="button" class="file-item-remove" data-index="${index}">✕</button>
                    `;
                    fileList.appendChild(fileItem);

                    // 파일 제거 버튼 클릭 이벤트
                    fileItem.querySelector('.file-item-remove').addEventListener('click', function() {
                        // FileList는 직접 수정할 수 없으므로, 새로운 DataTransfer 객체를 사용
                        const dt = new DataTransfer();
                        const files = Array.from(fileInput.files);
                        files.splice(index, 1);
                        files.forEach(file => dt.items.add(file));
                        fileInput.files = dt.files;
                        
                        // 파일 목록에서 제거
                        fileItem.remove();
                        
                        // 파일이 없으면 목록 숨김
                        if (fileInput.files.length === 0) {
                            fileList.innerHTML = '';
                        }
                    });
                });
            }
        });
    }















});

function handle_submit() {
    // 예시: 수정 페이지로 이동
    window.location.href = "/recruitment/detail/2";

    // 또는 모달 열기, 입력 필드 활성화 등 여기 넣으면 됨
    // alert("정보 수정 기능 준비중");
}
function handle_list() {
    // 예시: 수정 페이지로 이동
    window.location.href = "/recruitment";

    // 또는 모달 열기, 입력 필드 활성화 등 여기 넣으면 됨
    // alert("정보 수정 기능 준비중");
}