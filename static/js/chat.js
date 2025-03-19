
    function setReceiver(receiverId, username) {
        document.getElementById('receiver_id').value = receiverId;
        document.getElementById('chat-title').innerText = `Chat với ${username}`;
    }
document.querySelectorAll(".friend-item").forEach(item => {
    let name = item.querySelector(".friend-name").innerText.trim();
    let initial = name.charAt(0).toUpperCase();

    let avatar = item.querySelector(".avatar");
    avatar.innerText = initial;

    // Kiểm tra xem đã lưu màu chưa
    let savedColor = localStorage.getItem(`avatarColor-${name}`);

    if (!savedColor) {
        // Nếu chưa có màu, tạo màu ngẫu nhiên và lưu lại
        savedColor = `#${Math.floor(Math.random() * 16777215).toString(16)}`;
        localStorage.setItem(`avatarColor-${name}`, savedColor);
    }

    // Gán màu nền
    avatar.style.backgroundColor = savedColor;
});


document.addEventListener("DOMContentLoaded", function () {
    let savedReceiverId = localStorage.getItem("currentReceiverId");
    let savedReceiverName = localStorage.getItem("currentReceiverName");

    if (savedReceiverId && savedReceiverName) {
        setReceiver(savedReceiverId, savedReceiverName, true);
    } else {
        document.querySelector(".chat-container").classList.add("hidden"); // Ẩn hộp chat khi vào trang
    }
});

function setReceiver(receiverId, username, isReload = false) {
    document.getElementById('receiver_id').value = receiverId;
    document.getElementById('chat-title').innerText = `Chat với ${username}`;
    document.querySelector(".chat-container").classList.remove("hidden"); // Hiện hộp chat

    // Lưu trạng thái người nhắn tin vào localStorage (trừ khi đang khôi phục từ lần trước)
    if (!isReload) {
        localStorage.setItem("currentReceiverId", receiverId);
        localStorage.setItem("currentReceiverName", username);
    }

    // Ẩn tất cả tin nhắn trước đó
    document.querySelectorAll(".chat-message").forEach(msg => msg.style.display = "none");

    // Hiển thị tin nhắn liên quan đến người nhận được chọn
    document.querySelectorAll(`.chat-message[data-sender="${receiverId}"], .chat-message[data-receiver="${receiverId}"]`)
        .forEach(msg => msg.style.display = "block");
}
document.addEventListener("DOMContentLoaded", function () {
    let searchInput = document.getElementById("search-friend");
    let friendsList = document.querySelectorAll(".friend-item");

    searchInput.addEventListener("keyup", function () {
        let filter = searchInput.value.toLowerCase();

        friendsList.forEach(friend => {
            let friendName = friend.querySelector(".friend-name").innerText.toLowerCase();
            if (friendName.includes(filter)) {
                friend.style.display = "flex";
            } else {
                friend.style.display = "none";
            }
        });
    });
});


