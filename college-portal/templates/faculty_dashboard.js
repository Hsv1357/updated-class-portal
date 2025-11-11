// faculty_dashboard.js
document.addEventListener('DOMContentLoaded', function() {
    initializeFacultyDashboard();
});

function initializeFacultyDashboard() {
    // Modal functionality
    const modals = document.querySelectorAll('.modal');
    const closeButtons = document.querySelectorAll('.close-modal');
    
    // Close modals
    closeButtons.forEach(button => {
        button.addEventListener('click', function() {
            modals.forEach(modal => {
                modal.style.display = 'none';
            });
        });
    });
    
    // Close modal when clicking outside
    window.addEventListener('click', function(e) {
        modals.forEach(modal => {
            if (e.target === modal) {
                modal.style.display = 'none';
            }
        });
    });

    // Save attendance functionality
    const saveAttendanceBtn = document.getElementById('save-attendance-btn');
    if (saveAttendanceBtn) {
        saveAttendanceBtn.addEventListener('click', saveAttendance);
    }

    // Permission approval/rejection
    const approveButtons = document.querySelectorAll('.btn-approve');
    const rejectButtons = document.querySelectorAll('.btn-reject');
    
    approveButtons.forEach(button => {
        button.addEventListener('click', function() {
            const permissionId = this.getAttribute('data-id');
            updatePermissionStatus(permissionId, 'approved');
        });
    });
    
    rejectButtons.forEach(button => {
        button.addEventListener('click', function() {
            const permissionId = this.getAttribute('data-id');
            updatePermissionStatus(permissionId, 'rejected');
        });
    });
}

function saveAttendance() {
    showLoading(true, 'save-attendance-btn');
    
    const attendanceData = {};
    const radioGroups = document.querySelectorAll('input[type="radio"]:checked');
    
    if (radioGroups.length === 0) {
        showNotification('Please mark attendance for at least one student', 'error');
        showLoading(false, 'save-attendance-btn');
        return;
    }
    
    radioGroups.forEach(radio => {
        const studentId = radio.name.replace('attendance_', '');
        attendanceData[studentId] = radio.value;
    });
    
    fetch('/api/mark_attendance', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            attendance: attendanceData
        })
    })
    .then(response => response.json())
    .then(data => {
        showLoading(false, 'save-attendance-btn');
        if (data.success) {
            showNotification('Attendance saved successfully!', 'success');
        } else {
            showNotification('Error: ' + data.message, 'error');
        }
    })
    .catch(error => {
        showLoading(false, 'save-attendance-btn');
        console.error('Error:', error);
        showNotification('An error occurred while saving attendance.', 'error');
    });
}

function updatePermissionStatus(permissionId, status) {
    showLoading(true);
    
    fetch('/api/update_permission_status', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            permission_id: permissionId,
            status: status
        })
    })
    .then(response => response.json())
    .then(data => {
        showLoading(false);
        if (data.success) {
            showNotification(`Permission ${status} successfully!`, 'success');
            // Reload after 1 second to show updated status
            setTimeout(() => {
                location.reload();
            }, 1000);
        } else {
            showNotification('Error: ' + data.message, 'error');
        }
    })
    .catch(error => {
        showLoading(false);
        console.error('Error:', error);
        showNotification('An error occurred while updating permission status.', 'error');
    });
}

function showLoading(show, buttonId = null) {
    let buttons;
    if (buttonId) {
        buttons = [document.getElementById(buttonId)];
    } else {
        buttons = document.querySelectorAll('button');
    }
    
    buttons.forEach(button => {
        if (button) {
            if (show) {
                button.disabled = true;
                const originalText = button.textContent;
                button.setAttribute('data-original-text', originalText);
                button.innerHTML = 'Processing...';
                button.classList.add('loading');
            } else {
                button.disabled = false;
                const originalText = button.getAttribute('data-original-text') || 'Submit';
                button.innerHTML = originalText;
                button.classList.remove('loading');
            }
        }
    });
}

function showNotification(message, type = 'info') {
    // Remove any existing notifications
    const existingNotifications = document.querySelectorAll('.custom-notification');
    existingNotifications.forEach(notification => notification.remove());

    const notification = document.createElement('div');
    notification.className = `custom-notification flash-message ${type}`;
    notification.textContent = message;
    notification.style.position = 'fixed';
    notification.style.top = '80px';
    notification.style.right = '20px';
    notification.style.zIndex = '1000';
    notification.style.maxWidth = '400px';
    notification.style.padding = '16px 20px';
    notification.style.borderRadius = '10px';
    notification.style.color = 'white';
    notification.style.boxShadow = '0 10px 30px rgba(0, 0, 0, 0.08)';
    notification.style.fontSize = '14px';
    
    if (type === 'success') {
        notification.style.background = '#06d6a0';
    } else if (type === 'error') {
        notification.style.background = '#ef476f';
    } else {
        notification.style.background = '#4361ee';
    }
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transition = 'opacity 0.5s ease';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 500);
    }, 5000);
}