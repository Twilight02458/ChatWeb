
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
// Kết nối đến WebSocket Server (Socket.IO)
const socket = io("http://127.0.0.1:5000", {
    transports: ["websocket"],  // Chỉ sử dụng WebSocket, tránh polling
});

// Lưu user hiện tại từ Flask vào biến `currentUserId`
const currentUserId = document.getElementById("current_user_id")?.value || null;

// Gán sự kiện cho danh sách bạn bè
document.querySelectorAll(".friend-item").forEach(item => {
    let name = item.querySelector(".friend-name").innerText.trim();
    let initial = name.charAt(0).toUpperCase();
    let avatar = item.querySelector(".avatar");

    // Gán chữ cái đầu làm avatar
    avatar.innerText = initial;

    // Kiểm tra màu trong LocalStorage
    let savedColor = localStorage.getItem(`avatarColor-${name}`);
    if (!savedColor) {
        savedColor = `#${Math.floor(Math.random() * 16777215).toString(16)}`;
        localStorage.setItem(`avatarColor-${name}`, savedColor);
    }
    avatar.style.backgroundColor = savedColor;
});

// Khôi phục trạng thái khi tải lại trang
document.addEventListener("DOMContentLoaded", function () {
    let savedReceiverId = localStorage.getItem("currentReceiverId");
    let savedReceiverName = localStorage.getItem("currentReceiverName");

    if (savedReceiverId && savedReceiverName) {
        setReceiver(savedReceiverId, savedReceiverName, true);
    } else {
        document.querySelector(".chat-container").classList.add("hidden"); // Ẩn hộp chat khi chưa chọn ai
    }
});

// Chọn người nhận tin nhắn
function setReceiver(receiverId, username, isReload = false) {
    document.getElementById('receiver_id').value = receiverId;
    document.getElementById('chat-title').innerText = `Chat với ${username}`;
    document.querySelector(".chat-container").classList.remove("hidden");

    // Lưu trạng thái vào localStorage (trừ khi đang khôi phục từ lần trước)
    if (!isReload) {
        localStorage.setItem("currentReceiverId", receiverId);
        localStorage.setItem("currentReceiverName", username);
    }

    // Ẩn tin nhắn cũ và chỉ hiển thị tin nhắn liên quan
    document.querySelectorAll(".chat-message").forEach(msg => msg.style.display = "none");
    document.querySelectorAll(`.chat-message[data-sender="${receiverId}"], .chat-message[data-receiver="${receiverId}"]`)
        .forEach(msg => msg.style.display = "block");
}

// Tìm kiếm bạn bè
document.addEventListener("DOMContentLoaded", function () {
    let searchInput = document.getElementById("search-friend");
    let friendsList = document.querySelectorAll(".friend-item");

    searchInput.addEventListener("keyup", function () {
        let filter = searchInput.value.toLowerCase();
        friendsList.forEach(friend => {
            let friendName = friend.querySelector(".friend-name").innerText.toLowerCase();
            friend.style.display = friendName.includes(filter) ? "flex" : "none";
        });
    });
});

// Xử lý gửi tin nhắn
document.querySelector(".chat-input").addEventListener("submit", function (e) {
    e.preventDefault();
    let messageInput = document.getElementById("message");
    let receiverId = document.getElementById("receiver_id").value;

    if (messageInput.value.trim() !== "") {
        // Gửi tin nhắn qua WebSocket
        socket.emit("message", {
            sender_id: currentUserId,
            receiver_id: receiverId,
            message: messageInput.value
        });

        // Hiển thị tin nhắn ngay trên UI
        appendMessage({
            sender_id: currentUserId,
            receiver_id: receiverId,
            username: "Bạn",
            message: messageInput.value,
            sent_at: new Date().toLocaleTimeString()
        });

        messageInput.value = ""; // Xóa nội dung input sau khi gửi
    }
});

// Nhận tin nhắn từ WebSocket Server
socket.on("message", (data) => {
    console.log("📩 Tin nhắn nhận được:", data);

    if (!data || !data.message) {
        console.error("❌ Dữ liệu tin nhắn không hợp lệ:", data);
        return;
    }

    let currentReceiverId = document.getElementById("receiver_id").value;

    // Luôn hiển thị tin nhắn nếu người dùng là người nhận
    if (data.receiver_id == currentUserId || data.sender_id == currentReceiverId) {
        appendMessage(data);
    } else {
        console.warn("🚫 Tin nhắn không dành cho cuộc trò chuyện này.");
    }
});


function appendMessage(data) {
    let chatBox = document.getElementById("chat-box");

    let messageElement = document.createElement("div");
    messageElement.classList.add("chat-message");
    messageElement.classList.add(data.sender_id == currentUserId ? "sent" : "received");
    messageElement.dataset.sender = data.sender_id;
    messageElement.dataset.receiver = data.receiver_id;

    // Kiểm tra nếu username hoặc sent_at bị undefined, thay thế bằng giá trị mặc định
    let displayUsername = data.username ? data.username : "Người dùng";
    let displayTime = data.sent_at ? data.sent_at : new Date().toLocaleTimeString();

    messageElement.innerHTML = `<strong>${displayUsername}:</strong> ${data.message}
                                <small class="timestamp">${displayTime}</small>`;

    chatBox.appendChild(messageElement);
    chatBox.scrollTop = chatBox.scrollHeight;  // Cuộn xuống tin nhắn mới nhất
}
document.querySelector('/logout').addEventListener('click', function() {
    // Xóa tất cả dữ liệu localStorage khi người dùng đăng xuất
    localStorage.clear();
    window.location.href = '/login';
});

