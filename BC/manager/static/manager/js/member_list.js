document.addEventListener("DOMContentLoaded", function () {

    // 전체 선택
    document.getElementById("checkAll").addEventListener("change", function () {
        document.querySelectorAll("input[name='ids']").forEach(c => c.checked = this.checked);
    });

    // 삭제 confirm
    document.getElementById("deleteForm").addEventListener("submit", function (e) {
        const checked = document.querySelectorAll("input[name='ids']:checked");
        const selected = checked.length;

        if (selected === 0) {
            alert("삭제할 회원을 선택하세요.");
            e.preventDefault();
        } else if (!confirm(selected + "명 회원을 삭제하시겠습니까?")) {
            e.preventDefault();
        }

         for (const item of checked) {
            const status = item.dataset.status;   

            if (status === "1" || status === "2") {
                alert("이미 탈퇴한 회원입니다.");
                return;
            }
        }

    });
    // 복구 버튼
    document.getElementById("restoreBtn").addEventListener("click", function () {

        const checked = document.querySelectorAll("input[name='ids']:checked");

        if (checked.length === 0) {
            alert("복구할 회원을 선택하세요.");
            return;
        }

        // 현재 회원 체크
        for (const item of checked) {
            const status = item.dataset.status;  

            if (status === "0") {
                alert("이미 현재 회원입니다.");
                return;
            }
        }


        if (!confirm(checked.length + "명 회원을 복구하시겠습니까?")) return;

        const form = document.createElement("form");
        form.method = "POST";
        form.action = "/manager/member/restore/";

        const csrf = document.querySelector("input[name='csrfmiddlewaretoken']").cloneNode();
        form.appendChild(csrf);

        checked.forEach(chk => {
            const input = document.createElement("input");
            input.type = "hidden";
            input.name = "ids";
            input.value = chk.value;
            form.appendChild(input);
        });

        document.body.appendChild(form);
        form.submit();
    });
    // 페이징
    const perPageSelect = document.getElementById("perPageSelect");
    const current = perPageSelect.dataset.current;

    if (current) {
        perPageSelect.value = current;
    }

    perPageSelect.addEventListener("change", function () {
        const params = new URLSearchParams(window.location.search);

        params.set("per_page", this.value);
        params.set("page", 1); // 첫 페이지로 이동

        window.location.search = params.toString();
    });

});
