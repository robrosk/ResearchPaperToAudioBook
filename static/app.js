document.getElementById('uploadForm').addEventListener('submit', function(event) {
    event.preventDefault(); // Prevent the default form submission

    const fileInput = document.getElementById('fileInput');
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    const uploadStatus = document.getElementById('uploadStatus');
    uploadStatus.classList.remove('hidden');
    uploadStatus.textContent = 'Preparing upload...';
    uploadStatus.style.display = 'block'; // Ensure the status is visible

    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/', true);

    xhr.upload.onprogress = function(e) {
        if (e.lengthComputable) {
            const percentage = (e.loaded / e.total) * 100;
            if (percentage >= 100) {
                uploadStatus.textContent = 'Conversion in progress...';
            } else { 
                uploadStatus.textContent = 'Uploading... ' + percentage.toFixed(2) + '%';
            }
            uploadStatus.classList.add('blink');
        }
    };

    xhr.onload = function() {
        if (xhr.status === 200) {
            const filename = xhr.getResponseHeader('X-Filename') || 'default_filename.mp3'; // Get the filename from the header or use a default
            const blob = new Blob([xhr.response], {type: 'audio/mpeg'});
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = filename; // Set the filename from the header
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            uploadStatus.textContent = 'Upload complete!';
            uploadStatus.classList.remove('blink');
        } else {
            console.error('Error:', xhr.statusText);
            uploadStatus.textContent = 'Failed to upload. Status: ' + xhr.status;
            uploadStatus.classList.remove('blink');
        }
    };

    xhr.onerror = function() {
        console.error('Error during the upload process.');
        uploadStatus.textContent = 'Upload failed due to a network error.';
        uploadStatus.classList.remove('blink');
    };

    xhr.responseType = 'blob'; // Expect a binary blob response
    xhr.send(formData);
});