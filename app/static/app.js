xhr.onload = function() {
    if (xhr.status === 202) {
        const response = JSON.parse(xhr.responseText);
        const taskId = response.task_id;
        uploadStatus.textContent = 'Conversion started, please wait...';
        checkTaskStatus(taskId);
    } else {
        console.error('Error:', xhr.statusText);
        uploadStatus.textContent = 'Failed to start conversion. Status: ' + xhr.status;
        uploadStatus.classList.remove('blink');
    }
};

function checkTaskStatus(taskId) {
    const statusInterval = setInterval(function() {
        fetch(`/status/${taskId}`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'complete') {
                clearInterval(statusInterval);
                const blob = new Blob([data.file], {type: 'audio/mpeg'});
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = 'converted_audio.mp3';
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                uploadStatus.textContent = 'Conversion complete!';
                uploadStatus.classList.remove('blink');
            } else if (data.status === 'failed') {
                clearInterval(statusInterval);
                uploadStatus.textContent = 'Conversion failed.';
                uploadStatus.classList.remove('blink');
            }
        })
        .catch(error => {
            console.error('Error checking task status:', error);
            clearInterval(statusInterval);
            uploadStatus.textContent = 'Error checking conversion status.';
            uploadStatus.classList.remove('blink');
        });
    }, 5000); // Check every 5 seconds
}