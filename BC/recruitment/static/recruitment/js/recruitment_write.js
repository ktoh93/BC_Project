document.addEventListener("DOMContentLoaded", function () {
/* 대한민국 시/도 + 시/군/구 전체 데이터 */
    const regionData = {
        "서울특별시": [
            "강남구","강동구","강북구","강서구","관악구","광진구","구로구","금천구",
            "노원구","도봉구","동대문구","동작구","마포구","서대문구","서초구","성동구",
            "성북구","송파구","양천구","영등포구","용산구","은평구","종로구","중구","중랑구"
        ],

        "부산광역시": [
            "강서구","금정구","남구","동구","동래구","부산진구","북구","사상구","사하구",
            "서구","수영구","연제구","영도구","중구","해운대구","기장군"
        ],

        "대구광역시": [
            "남구","달서구","동구","북구","서구","수성구","중구","달성군"
        ],

        "인천광역시": [
            "계양구","남동구","동구","미추홀구","부평구","서구","연수구","중구","강화군","옹진군"
        ],

        "광주광역시": ["광산구","남구","동구","북구","서구"],
        "대전광역시": ["대덕구","동구","서구","유성구","중구"],
        "울산광역시": ["남구","동구","북구","중구","울주군"],

        "세종특별자치시": ["세종시"],

        "경기도": [
            "수원시","용인시","고양시","성남시","화성시","부천시","안산시",
            "남양주시","안양시","평택시","시흥시","파주시","의정부시","김포시","광주시",
            "광명시","군포시","하남시","오산시","이천시","안성시","의왕시","양평군",
            "여주시","양주시","포천시","가평군","동두천시"
        ],

        "강원도": [
            "춘천시","원주시","강릉시","동해시","속초시","삼척시","홍천군","횡성군",
            "영월군","평창군","정선군","철원군","화천군","양구군","인제군","고성군","양양군"
        ],

        "충청북도": [
            "청주시","충주시","제천시","보은군","옥천군","영동군","진천군","괴산군",
            "음성군","단양군","증평군"
        ],

        "충청남도": [
            "천안시","아산시","서산시","당진시","공주시","보령시","논산시","계룡시",
            "금산군","부여군","서천군","청양군","홍성군","예산군","태안군"
        ],

        "전라북도": [
            "전주시","익산시","군산시","정읍시","남원시","김제시","완주군",
            "진안군","무주군","장수군","임실군","순창군","고창군","부안군"
        ],

        "전라남도": [
            "목포시","여수시","순천시","나주시","광양시","담양군","곡성군","구례군",
            "고흥군","보성군","화순군","장흥군","강진군","해남군","영암군","무안군",
            "함평군","영광군","장성군","완도군","진도군","신안군"
        ],

        "경상북도": [
            "포항시","경주시","김천시","안동시","구미시","영주시","영천시","상주시","문경시",
            "경산시","의성군","청송군","영양군","영덕군","청도군","고령군","성주군","칠곡군",
            "예천군","봉화군","울진군","울릉군"
        ],

        "경상남도": [
            "창원시","김해시","진주시","양산시","거제시","통영시",
            "사천시","밀양시","함안군","창녕군","고성군","남해군",
            "하동군","산청군","함양군","거창군","합천군"
        ],

        "제주특별자치도": ["제주시","서귀포시"]
    };


    // HTML 요소 불러오기
    const sidoEl = document.getElementById("sido");
    const sigunguEl = document.getElementById("sigungu");
    const timeslotSelect = document.getElementById("reservation_choice");

    /* 1) 시/도 목록 자동 삽입 */
    Object.keys(regionData).forEach(sido => {
        const option = document.createElement("option");
        option.value = sido;
        option.textContent = sido;
        sidoEl.appendChild(option);
    });

    /* 2) 시/도 선택 → 구/군 업데이트 */
    sidoEl.addEventListener("change", function () {
        const selected = this.value;

        // 기존 구/군 초기화
        sigunguEl.innerHTML = `<option value="">구/군 선택</option>`;

        if (!selected) return;

        // 선택된 시/도의 구/군 채우기
        regionData[selected].forEach(gu => {
            const option = document.createElement("option");
            option.value = gu;
            option.textContent = gu;
            sigunguEl.appendChild(option);
        });
    });

const reservationSelect = document.getElementById("reservation_choice");

if (reservationSelect) {
    reservationSelect.addEventListener("change", function () {
        const reservationId = this.value;

        if (!reservationId) {
            sidoEl.disabled = false;
            sigunguEl.disabled = false;
            return;
        }

        // 🔥 여기만 수정
        fetch(`/recruitment/ajax/facility-region/?reservation_id=${reservationId}`)
            .then(res => res.json())
            .then(data => {
                if (data.error) return;

                const sido = data.sido;
                const sigugun = data.sigugun;

                sidoEl.value = sido;

                sigunguEl.innerHTML = `<option value="">구/군 선택</option>`;
                regionData[sido].forEach(gu => {
                    const option = document.createElement("option");
                    option.value = gu;
                    option.textContent = gu;
                    sigunguEl.appendChild(option);
                });

                sigunguEl.value = sigugun;

                sidoEl.disabled = true;
                sigunguEl.disabled = true;
            });
    });
}



});


// DOM 로드 후 실행
document.addEventListener("DOMContentLoaded", () => {
    const btn_submit = document.querySelector(".btn-submit");
    const btn_list = document.querySelector(".btn-list");


    // 1) 등록 클릭

    btn_submit.addEventListener("click", function (e) {
        // 기본 submit 쓰고 싶으면 이 preventDefault 는 지워도 됨
        // e.preventDefault();
        recruit_form.submit();  // -> Django view 로 POST 날아감
    });

    
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


function handle_list() {
    // 예시: 수정 페이지로 이동
    window.location.href = "/recruitment";

    // 또는 모달 열기, 입력 필드 활성화 등 여기 넣으면 됨
    // alert("정보 수정 기능 준비중");
}


document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("recruit-form");
  const contentInput = document.getElementById("contentInput");
  if (!form || !contentInput) return;

  form.addEventListener("submit", (e) => {
    const editor = window.editorInstance;
    if (!editor) {
      e.preventDefault();
      alert("에디터 초기화가 아직 안 됐습니다.");
      return;
    }

    const md = (editor.getMarkdown() || "");
    // ✅ 실제 글자(한글/영문/숫자)가 하나라도 있는지 체크
    const has_real_text = /[0-9A-Za-z가-힣ㄱ-ㅎㅏ-ㅣ]/.test(md);
    const html = editor.getHTML();
    const text = html
        .replace(/<br\s*\/?>/gi, "")
        .replace(/<p>\s*<\/p>/gi, "")
        .replace(/&nbsp;/gi, "")
        .replace(/<[^>]*>/g, "")
        .trim();
    if (!has_real_text || !text) {
      e.preventDefault();
      alert("내용은 필수입니다. 글자를 1자 이상 입력해 주세요.");
      editor.focus();
      return;
    }

    // 저장값 (원하시면 getHTML()로 바꾸세요)
    contentInput.value = md;
  }, true);
});