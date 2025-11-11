// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeAdminDashboard();
    loadClubsEvents();
});

function initializeAdminDashboard() {
    // Modal functionality
    const modals = document.querySelectorAll('.modal');
    const closeButtons = document.querySelectorAll('.close-modal');
    const addUserBtn = document.getElementById('add-user-btn');
    const uploadStudentsBtn = document.getElementById('upload-students-btn');
    const uploadFacultyBtn = document.getElementById('upload-faculty-btn');
    const addFacultyBtn = document.getElementById('add-faculty-btn');
    const addClubEventBtn = document.getElementById('add-club-event-btn');

    // Open modals
    if (addUserBtn) {
        addUserBtn.addEventListener('click', function() {
            document.getElementById('add-user-modal').style.display = 'flex';
        });
    }

    if (uploadStudentsBtn) {
        uploadStudentsBtn.addEventListener('click', function() {
            document.getElementById('upload-students-modal').style.display = 'flex';
        });
    }

    if (uploadFacultyBtn) {
        uploadFacultyBtn.addEventListener('click', function() {
            document.getElementById('upload-faculty-modal').style.display = 'flex';
        });
    }

    if (addFacultyBtn) {
        addFacultyBtn.addEventListener('click', function() {
            document.getElementById('add-faculty-modal').style.display = 'flex';
        });
    }

    if (addClubEventBtn) {
        addClubEventBtn.addEventListener('click', function() {
            document.getElementById('add-club-event-modal').style.display = 'flex';
        });
    }

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

    // Form submissions
    const addUserForm = document.getElementById('add-user-form');
    const uploadStudentsForm = document.getElementById('upload-students-form');
    const uploadFacultyForm = document.getElementById('upload-faculty-form');
    const addFacultyForm = document.getElementById('add-faculty-form');
    const addClubEventForm = document.getElementById('add-club-event-form');
    const editUserForm = document.getElementById('edit-user-form');
    const editClubEventForm = document.getElementById('edit-club-event-form');

    if (addUserForm) {
        addUserForm.addEventListener('submit', function(e) {
            e.preventDefault();
            addUser();
        });
    }

    if (uploadStudentsForm) {
        uploadStudentsForm.addEventListener('submit', function(e) {
            e.preventDefault();
            uploadStudents(e);
        });
    }

    if (uploadFacultyForm) {
        uploadFacultyForm.addEventListener('submit', function(e) {
            e.preventDefault();
            uploadFaculty(e);
        });
    }

    if (addFacultyForm) {
        addFacultyForm.addEventListener('submit', function(e) {
            e.preventDefault();
            addFaculty(e);
        });
    }

    if (addClubEventForm) {
        addClubEventForm.addEventListener('submit', function(e) {
            e.preventDefault();
            addClubEvent(e);
        });
    }

    if (editUserForm) {
        editUserForm.addEventListener('submit', function(e) {
            e.preventDefault();
            updateUser();
        });
    }

    if (editClubEventForm) {
        editClubEventForm.addEventListener('submit', function(e) {
            e.preventDefault();
            updateClubEvent();
        });
    }
}

function loadClubsEvents() {
    fetch('/api/get_clubs_events')
    .then(response => response.json())
    .then(data => {
        const table = document.getElementById('clubs-events-table');
        if (table) {
            table.innerHTML = '';
            data.forEach(item => {
                table.innerHTML += `
                    <tr>
                        <td>${item.name}</td>
                        <td>${item.type.charAt(0).toUpperCase() + item.type.slice(1)}</td>
                        <td>${item.is_active ? 'Active' : 'Inactive'}</td>
                        <td>
                            <button class="action-btn btn-edit" onclick="editClubEvent(${item.id}, '${item.name}', '${item.type}')">Edit</button>
                            <button class="action-btn btn-delete" onclick="deleteClubEvent(${item.id})">Delete</button>
                        </td>
                    </tr>
                `;
            });
        }
    })
    .catch(error => {
        console.error('Error loading clubs and events:', error);
    });
}

function viewStudent(studentId) {
    window.open(`/student/details/${studentId}`, '_blank');
}

function viewFaculty(facultyId) {
    window.open(`/faculty/details/${facultyId}`, '_blank');
}

function deleteUser(userId, role) {
    if (confirm(`Are you sure you want to delete this ${role}?`)) {
        showLoading(true);
        fetch(`/api/delete_user/${userId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            showLoading(false);
            if (data.success) {
                showNotification(`${role.charAt(0).toUpperCase() + role.slice(1)} deleted successfully`, 'success');
                setTimeout(() => location.reload(), 1000);
            } else {
                showNotification('Error: ' + data.message, 'error');
            }
        })
        .catch(error => {
            showLoading(false);
            showNotification('An error occurred while deleting user.', 'error');
        });
    }
}

function editUser(userId, role) {
    // For now, show a notification. In a real implementation, you would fetch user data and populate the form
    showNotification(`Edit ${role} functionality would fetch user data and populate the edit form`, 'info');
    
    // Example of how it would work:
    fetch(`/api/get_user/${userId}`)
    .then(response => response.json())
    .then(user => {
        document.getElementById('edit-user-id').value = user.id;
        document.getElementById('edit-user-role').value = role;
        document.getElementById('edit-user-title').textContent = `Edit ${role.charAt(0).toUpperCase() + role.slice(1)}`;
        document.getElementById('edit-name').value = user.name;
        document.getElementById('edit-email').value = user.email || '';
        
        if (role === 'student') {
            document.getElementById('student-fields').style.display = 'block';
            document.getElementById('faculty-fields').style.display = 'none';
            document.getElementById('edit-rollno').value = user.rollno || '';
            document.getElementById('edit-section').value = user.section || '';
            document.getElementById('edit-department').value = user.department || '';
            document.getElementById('edit-class').value = user.class || '';
        } else {
            document.getElementById('student-fields').style.display = 'none';
            document.getElementById('faculty-fields').style.display = 'block';
            document.getElementById('edit-faculty-department').value = user.department || '';
        }
        
        document.getElementById('edit-user-modal').style.display = 'flex';
    })
    .catch(error => {
        showNotification('Error loading user data', 'error');
    });
}

function updateUser() {
    const form = document.getElementById('edit-user-form');
    const formData = new FormData(form);
    const data = {
        id: formData.get('id'),
        role: formData.get('role'),
        name: formData.get('name'),
        email: formData.get('email'),
        rollno: formData.get('rollno'),
        section: formData.get('section'),
        department: formData.get('department'),
        class: formData.get('class')
    };
    
    showLoading(true);
    fetch(`/api/update_user/${data.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        showLoading(false);
        if (result.success) {
            document.getElementById('edit-user-modal').style.display = 'none';
            showNotification(result.message, 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            showNotification('Error: ' + result.message, 'error');
        }
    })
    .catch(error => {
        showLoading(false);
        showNotification('An error occurred while updating user.', 'error');
    });
}

function editClubEvent(id, name, type) {
    document.getElementById('edit-club-event-id').value = id;
    document.getElementById('edit-club-event-name').value = name;
    document.getElementById('edit-club-event-type').value = type;
    document.getElementById('edit-club-event-modal').style.display = 'flex';
}

function updateClubEvent() {
    const form = document.getElementById('edit-club-event-form');
    const formData = new FormData(form);
    const data = {
        id: formData.get('id'),
        name: formData.get('name'),
        type: formData.get('type')
    };
    
    showLoading(true);
    fetch(`/api/update_club_event/${data.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        showLoading(false);
        if (result.success) {
            document.getElementById('edit-club-event-modal').style.display = 'none';
            showNotification(result.message, 'success');
            loadClubsEvents();
        } else {
            showNotification('Error: ' + result.message, 'error');
        }
    })
    .catch(error => {
        showLoading(false);
        showNotification('An error occurred while updating club/event.', 'error');
    });
}

function deleteClubEvent(id) {
    if (confirm('Are you sure you want to delete this club/event?')) {
        showLoading(true);
        fetch(`/api/delete_club_event/${id}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(result => {
            showLoading(false);
            if (result.success) {
                showNotification(result.message, 'success');
                loadClubsEvents();
            } else {
                showNotification('Error: ' + result.message, 'error');
            }
        })
        .catch(error => {
            showLoading(false);
            showNotification('An error occurred while deleting club/event.', 'error');
        });
    }
}

// Add new user
function addUser() {
    showLoading(true);
    
    const form = document.getElementById('add-user-form');
    const formData = new FormData(form);
    const data = {
        username: formData.get('username'),
        password: formData.get('password'),
        name: formData.get('name'),
        email: formData.get('email'),
        rollno: formData.get('rollno'),
        section: formData.get('section'),
        department: formData.get('department'),
        class: formData.get('class')
    };
    
    fetch('/api/add_user', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        showLoading(false);
        if (data.success) {
            document.getElementById('add-user-modal').style.display = 'none';
            form.reset();
            showNotification('Student added successfully!', 'success');
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
        showNotification('An error occurred while adding student.', 'error');
    });
}

// Upload students from Excel
function uploadStudents(e) {
    e.preventDefault();
    showLoading(true);
    
    const formData = new FormData(document.getElementById('upload-students-form'));
    
    fetch('/api/upload_students', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        showLoading(false);
        if (data.success) {
            document.getElementById('upload-students-modal').style.display = 'none';
            document.getElementById('upload-students-form').reset();
            showNotification(data.message, 'success');
            setTimeout(() => location.reload(), 2000);
        } else {
            showNotification('Error: ' + data.message, 'error');
            }
    })
    .catch(error => {
        showLoading(false);
        showNotification('An error occurred while uploading students.', 'error');
    });
}

// Upload faculty from Excel
function uploadFaculty(e) {
    e.preventDefault();
    showLoading(true);
    
    const formData = new FormData(document.getElementById('upload-faculty-form'));
    
    fetch('/api/upload_faculty', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        showLoading(false);
        if (data.success) {
            document.getElementById('upload-faculty-modal').style.display = 'none';
            document.getElementById('upload-faculty-form').reset();
            showNotification(data.message, 'success');
            setTimeout(() => location.reload(), 2000);
        } else {
            showNotification('Error: ' + data.message, 'error');
            }
    })
    .catch(error => {
        showLoading(false);
        showNotification('An error occurred while uploading faculty.', 'error');
    });
}

// Add faculty
function addFaculty(e) {
    e.preventDefault();
    showLoading(true);
    
    const form = document.getElementById('add-faculty-form');
    const formData = new FormData(form);
    const data = {
        username: formData.get('username'),
        password: formData.get('password'),
        name: formData.get('name'),
        email: formData.get('email'),
        department: formData.get('department')
    };
    
    fetch('/api/add_faculty', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        showLoading(false);
        if (data.success) {
            document.getElementById('add-faculty-modal').style.display = 'none';
            form.reset();
            showNotification(data.message, 'success');
            setTimeout(() => location.reload(), 2000);
        } else {
            showNotification('Error: ' + data.message, 'error');
            }
    })
    .catch(error => {
        showLoading(false);
        showNotification('An error occurred while adding faculty.', 'error');
    });
}

// Add club/event
function addClubEvent(e) {
    e.preventDefault();
    showLoading(true);
    
    const form = document.getElementById('add-club-event-form');
    const formData = new FormData(form);
    const data = {
        name: formData.get('name'),
        type: formData.get('type')
    };
    
    fetch('/api/add_club_event', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        showLoading(false);
        if (data.success) {
            document.getElementById('add-club-event-modal').style.display = 'none';
            form.reset();
            showNotification(data.message, 'success');
            loadClubsEvents();
        } else {
            showNotification('Error: ' + data.message, 'error');
        }
    })
    .catch(error => {
        showLoading(false);
        showNotification('An error occurred while adding club/event.', 'error');
    });
}

// Show loading state
function showLoading(show) {
    const buttons = document.querySelectorAll('button[type="submit"]');
    buttons.forEach(button => {
        if (show) {
            button.disabled = true;
            button.innerHTML = 'Processing...';
            button.classList.add('loading');
        } else {
            button.disabled = false;
            button.innerHTML = button.getAttribute('data-original-text') || 'Submit';
            button.classList.remove('loading');
        }
    });
}

// Show notification
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