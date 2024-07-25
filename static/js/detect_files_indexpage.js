const fileInput = document.getElementById("file-input");
const fileNameDisplay = document.getElementById("file-name")
let selectedFile = null;

fileInput.addEventListener("change", function(event) {
    const files = event.target.files;

    if (files.length > 0) {
        fileNameDisplay.textContent = files[0].name;
        selectedFile = files[0];
    } else {
        fileNameDisplay.textContent = "";
    }
});

const dropArea = document.querySelector(".file-drop-area");

dropArea.addEventListener('dragover', function(event) {
    event.preventDefault();
    dropArea.classList.add('hover');
});

dropArea.addEventListener('dragleave', function(event) {
    dropArea.classList.remove('hover');
});

dropArea.addEventListener('drop', function(event) {
    event.preventDefault();
    dropArea.classList.remove('hover');
    const files = event.dataTransfer.files;
    if (files.length > 0) {
        fileInput.files = files;
        fileNameDisplay.textContent = files[0].name;
        selectedFile = files[0];
    }
});