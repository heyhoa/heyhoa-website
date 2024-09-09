const dragDropContainer = document.getElementById('dragDropContainer');
const fileInput = document.getElementById('fileInput');
const fileInfo = document.getElementById('fileInfo');

dragDropContainer.addEventListener('click', () => {
    console.log('Container clicked');
    fileInput.click();
});

fileInput.addEventListener('change', (e) => handleFiles(e.target.files));

dragDropContainer.addEventListener('dragover', (e) => {
    e.preventDefault();
    dragDropContainer.classList.add('dragover');
});

dragDropContainer.addEventListener('dragleave', () => {
    dragDropContainer.classList.remove('dragover');
});

dragDropContainer.addEventListener('drop', (e) => {
    e.preventDefault();
    dragDropContainer.classList.remove('dragover');
    handleFiles(e.dataTransfer.files);
});

function handleFiles(files) {
    const file = files[0];
    if (file) {
        fileInfo.innerHTML = `${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB) <a href="javascript:void(0);" class="remove-file">Remove</a>`;
        document.querySelector('.remove-file').addEventListener('click', removeFile);
    } else {
        fileInfo.textContent = '';
    }
}

function removeFile() {
    // Clear the file input
    fileInput.value = '';

    // Clear the file info display
    fileInfo.textContent = '';
}