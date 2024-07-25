var socket = io();
var localConnection;
var remoteConnection;
var sendChannel;
var receiveChannel;

socket.on('connect', function() {
    console.log('Connected');
});

socket.on('user_connected', function(user_id) {
    var userDiv = document.createElement('div');
    userDiv.classList.add('user');
    userDiv.setAttribute('id', user_id);
    userDiv.innerText = user_id.substring(0, 2).toUpperCase();
    userDiv.onclick = function() {
        initiateConnection(user_id);
    };
    document.getElementById('users').appendChild(userDiv);
});

socket.on('user_disconnected', function(user_id) {
    var userDiv = document.getElementById(user_id);
    if (userDiv) {
        userDiv.remove();
    }
});

socket.on('offer', function(data) {
    handleOffer(data.offer, data.from);
});

socket.on('answer', function(data) {
    handleAnswer(data.answer);
});

socket.on('ice-candidate', function(data) {
    handleCandidate(data.candidate);
});

function initiateConnection(user_id) {
    localConnection = new RTCPeerConnection();
    sendChannel = localConnection.createDataChannel('sendDataChannel');

    localConnection.onicecandidate = function(event) {
        if (event.candidate) {
            socket.emit('ice-candidate', {
                candidate: event.candidate,
                to: user_id
            });
        }
    };

    localConnection.createOffer().then(function(offer) {
        return localConnection.setLocalDescription(offer);
    }).then(function() {
        socket.emit('offer', {
            offer: localConnection.localDescription,
            to: user_id
        });
    });
}

function handleOffer(offer, from) {
    remoteConnection = new RTCPeerConnection();
    remoteConnection.ondatachannel = function(event) {
        receiveChannel = event.channel;
        receiveChannel.onmessage = function(event) {
            var downloadLink = document.getElementById('downloadLink');
            var fileBlob = new Blob([event.data]);
            downloadLink.href = URL.createObjectURL(fileBlob);
            downloadLink.download = 'received_file';
            downloadLink.style.display = 'block';
        };
    };

    remoteConnection.onicecandidate = function(event) {
        if (event.candidate) {
            socket.emit('ice-candidate', {
                candidate: event.candidate,
                to: from
            });
        }
    };

    remoteConnection.setRemoteDescription(offer).then(function() {
        return remoteConnection.createAnswer();
    }).then(function(answer) {
        return remoteConnection.setLocalDescription(answer);
    }).then(function() {
        socket.emit('answer', {
            answer: remoteConnection.localDescription,
            to: from
        });
    });
}

function handleAnswer(answer) {
    localConnection.setRemoteDescription(answer);
}

function handleCandidate(candidate) {
    var conn = localConnection || remoteConnection;
    conn.addIceCandidate(candidate);
}

function sendFile() {
    var fileInput = document.getElementById('fileInput');
    var file = fileInput.files[0];
    if (file && sendChannel) {
        sendChannel.send(file);
    }
}
