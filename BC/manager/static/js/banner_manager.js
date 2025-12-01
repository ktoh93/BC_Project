function getCSRFToken() {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'csrftoken') return value;
    }
    return '';
}

function deleteBanners() {
    const checked = document.querySelectorAll('input[name="delete_ids"]:checked');

    if (checked.length === 0) {
        alert("삭제할 항목을 선택하세요.");
        return;
    }

    const ids = Array.from(checked).map(el => el.value);

    fetch("/manager/banner_delete/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCSRFToken()
        },
        body: JSON.stringify({ ids: ids })
    })
    .then(response => {
        if (response.ok) {
            location.reload();
        } else {
            alert("삭제 실패");
        }
    });
}
