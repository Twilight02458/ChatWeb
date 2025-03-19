function setReceiver(receiverId, username) {
    document.getElementById('receiver_id').value = receiverId;
    document.getElementById('chat-box').innerHTML = `<h5>Chat với ${username}</h5>`;
}