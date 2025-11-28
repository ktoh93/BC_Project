// 파일 선택 시 파일 목록 표시
document.addEventListener('DOMContentLoaded', function() {
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

