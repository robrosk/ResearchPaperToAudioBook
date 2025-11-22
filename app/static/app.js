document.addEventListener('DOMContentLoaded', () => {
    // Fix legacy data
    migrateTasks();

    // Initialize UI
    renderQueues();

    // Clear Queue Handler (re-added for safety/debug)
    const clearQueueBtn = document.getElementById('clearQueueBtn');
    if (clearQueueBtn) {
        clearQueueBtn.addEventListener('click', () => {
            if (confirm('Clear entire history?')) {
                localStorage.removeItem('audioTasks');
                renderQueues();
            }
        });
    }

    const uploadForm = document.getElementById('uploadForm');
    if (uploadForm) {
        uploadForm.addEventListener('submit', handleUpload);
    }
});

function migrateTasks() {
    let tasks = JSON.parse(localStorage.getItem('audioTasks') || '[]');
    let modified = false;
    tasks = tasks.map(t => {
        // Fix ID (legacy 'taskId' to 'id')
        if (!t.id && t.taskId) {
            t.id = t.taskId;
            delete t.taskId;
            modified = true;
        }
        // Fix Status (undefined status)
        if (!t.status) {
            t.status = 'UNKNOWN';
            modified = true;
        }
        return t;
    });
    
    if (modified) {
        localStorage.setItem('audioTasks', JSON.stringify(tasks));
    }
}

// --- Upload Handler ---
function handleUpload(e) {
    e.preventDefault();
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    const btn = e.target.querySelector('button');
    const originalText = btn.textContent;
    btn.disabled = true;
    btn.textContent = 'Uploading...';

    fetch('/', { method: 'POST', body: formData })
    .then(res => res.ok ? res.json() : Promise.reject('Upload failed'))
    .then(data => {
        if (data.task_id) {
            addTask(file.name, data.task_id);
            fileInput.value = ''; 
        }
    })
    .catch(err => {
        console.error(err);
        alert('Upload failed.');
    })
    .finally(() => {
        btn.disabled = false;
        btn.textContent = originalText;
    });
}

// --- Data Management ---
function getTasks() {
    return JSON.parse(localStorage.getItem('audioTasks') || '[]');
}

function saveTasks(tasks) {
    localStorage.setItem('audioTasks', JSON.stringify(tasks));
    renderQueues();
}

function addTask(filename, taskId) {
    const tasks = getTasks();
    tasks.unshift({
        id: taskId,
        filename: filename,
        status: 'PENDING', // PENDING, PROCESSING, SUCCESS, FAILURE, CANCELLED
        date: new Date().toISOString(),
        resultFilename: null
    });
    saveTasks(tasks);
    pollStatus(taskId);
}

function updateTaskStatus(taskId, newStatus, resultFilename = null) {
    const tasks = getTasks();
    const taskIndex = tasks.findIndex(t => t.id === taskId);
    if (taskIndex > -1) {
        tasks[taskIndex].status = newStatus;
        if (resultFilename) {
            tasks[taskIndex].resultFilename = resultFilename;
            tasks[taskIndex].filename = resultFilename; // Update display name to output file
        }
        saveTasks(tasks);
    }
}

function removeTask(taskId) {
    const tasks = getTasks();
    // Filter out task with matching ID
    const newTasks = tasks.filter(t => t.id !== taskId);
    saveTasks(newTasks);
}

// --- Polling ---
function pollStatus(taskId) {
    const poll = () => {
        // Check if task still exists in our local list (wasn't deleted)
        const currentTask = getTasks().find(t => t.id === taskId);
        if (!currentTask || ['SUCCESS', 'FAILURE', 'CANCELLED', 'UNKNOWN'].includes(currentTask.status)) {
            return; // Stop polling
        }

        fetch(`/status/${taskId}`)
        .then(res => res.json())
        .then(data => {
            if (data.state === 'SUCCESS') {
                updateTaskStatus(taskId, 'SUCCESS', data.filename);
            } else if (data.state === 'FAILURE') {
                updateTaskStatus(taskId, 'FAILURE');
            } else if (data.state === 'REVOKED') {
                updateTaskStatus(taskId, 'CANCELLED');
            } else {
                // Update UI for progress but don't change main status state unless changed
                // We rely on renderQueues to show the status text
            }

            if (!['SUCCESS', 'FAILURE', 'REVOKED'].includes(data.state)) {
                setTimeout(poll, 2000);
            }
        })
        .catch(() => setTimeout(poll, 5000));
    };
    poll();
}

// --- Actions ---
function cancelTask(taskId) {
    if (!confirm('Stop this conversion?')) return;
    
    fetch(`/cancel/${taskId}`, { method: 'POST' })
    .then(() => {
        updateTaskStatus(taskId, 'CANCELLED');
    });
}

function deleteTask(taskId, filename) {
    if (!confirm('Delete this audiobook?')) return;

    // Optimistically update UI immediately
    removeTask(taskId);

    // Call backend to delete file in background (don't wait for it to update UI)
    // If filename is undefined or null (legacy data), just skip the server call
    if (filename && filename !== 'undefined') {
        fetch(`/delete/${filename}`, { method: 'DELETE' })
        .catch(err => console.error('Failed to delete file on server:', err));
    }
}

// --- Rendering ---
function renderQueues() {
    const tasks = getTasks();
    const activeBody = document.getElementById('activeQueueBody');
    const completedBody = document.getElementById('completedQueueBody');
    const activeContainer = document.getElementById('activeQueueContainer');
    const emptyMsg = document.getElementById('emptyLibraryMsg');

    activeBody.innerHTML = '';
    completedBody.innerHTML = '';

    let activeCount = 0;
    let completedCount = 0;

    // Resume polling for any pending tasks on page load/render
    // This calls pollStatus safely (it checks if already finished inside)
    
    tasks.forEach(task => {
        if (['PENDING', 'PROCESSING', 'STARTED', 'RETRY'].includes(task.status)) {
            // Active Task
            activeCount++;
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${task.filename}</td>
                <td><span class="status-badge status-processing">Processing</span></td>
                <td>
                    <button onclick="cancelTask('${task.id}')" class="btn-icon btn-danger" title="Stop">
                        Stop
                    </button>
                </td>
            `;
            activeBody.appendChild(row);
            // Ensure polling is running
            pollStatus(task.id);

        } else {
            // Completed/Failed/Cancelled Task
            completedCount++;
            const row = document.createElement('tr');
            const dateStr = new Date(task.date).toLocaleDateString();
            
            let statusHtml = '';
            let actionHtml = '';
            let filenameDisplay = task.resultFilename || task.filename;

            if (task.status === 'SUCCESS') {
                actionHtml = `
                    <a href="/download/${task.resultFilename}" class="btn-icon btn-download" title="Download">Download</a>
                    <button onclick="deleteTask('${task.id}', '${task.resultFilename}')" class="btn-icon btn-delete" title="Delete">Delete</button>
                `;
            } else {
                statusHtml = `<span class="status-badge status-error">${task.status}</span>`;
                actionHtml = `
                    <button onclick="deleteTask('${task.id}', '${task.filename}')" class="btn-icon btn-delete" title="Remove">Remove</button>
                `;
            }

            row.innerHTML = `
                <td>
                    <div class="file-info">
                        <span class="file-name">${filenameDisplay}</span>
                        ${statusHtml}
                    </div>
                </td>
                <td class="text-muted">${dateStr}</td>
                <td><div class="action-group">${actionHtml}</div></td>
            `;
            completedBody.appendChild(row);
        }
    });

    // Toggle Visibility
    activeContainer.style.display = activeCount > 0 ? 'block' : 'none';
    emptyMsg.style.display = completedCount === 0 ? 'block' : 'none';
    if (completedCount > 0) document.getElementById('completedQueueTable').style.display = 'table';
    else document.getElementById('completedQueueTable').style.display = 'none';
}
