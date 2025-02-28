const membersearch = function () {
    const search_name = document.getElementById("search_name").value;
    const apiUrl = "http://127.0.0.1:3000/api/member?username=" + search_name;
    fetch(apiUrl, {
        method: "get",
    })
        .then((res) => res.json())
        .then((data) => {
            const result_text = document.getElementById("resultText");
            result_text.innerHTML = (data == null || data.data == null) ? "查無此人" : data.data.name;
        });
};

const updatename = function () {
    const update_name = document.getElementById("update_name").value;
    const apiUrl = "http://127.0.0.1:3000/api/member";

    fetch(apiUrl, {
        method: "PATCH",
        headers: {
            "content-type": "application/json",
        },
        body: JSON.stringify({
            name: update_name,
        }),
    })
        .then((res) => res.json())
        .then((data) => {
            const result = document.getElementById("updateResult");
            if (data != null && data.ok == true) {
                result.innerHTML = "更新成功";
                document.getElementById("welcome").innerHTML = update_name + ", 歡迎登入系統~";
            } else {
                result.innerHTML = "更新失敗";
            }
        });
};




const deleteMessage = function (index) {
    const result = confirm("你確定要刪除嗎?");
    if (!result) {
        return;
    }
    const apiUrl = "http://127.0.0.1:3000/deleteMessage";
    const formData = new FormData();
    formData.append("message_id", index); // Append data as form data
    fetch(apiUrl, {
        method: "post",
        body: formData, // Send form data
    })
        .then(() => {
            window.location.reload();
        });
}
