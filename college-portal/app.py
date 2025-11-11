from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
from datetime import datetime, date
import os
import pandas as pd
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
DATABASE = 'college_portal.db'
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Initialize database with proper schema
def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    # Create tables with updated schema
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            name TEXT NOT NULL,
            email TEXT,
            rollno TEXT,
            section TEXT,
            department TEXT,
            class TEXT
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            faculty_id INTEGER,
            date DATE NOT NULL,
            reason TEXT NOT NULL,
            proof TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES users (id),
            FOREIGN KEY (faculty_id) REFERENCES users (id)
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            class_id INTEGER,
            date DATE NOT NULL,
            status TEXT NOT NULL,
            marked_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES users (id),
            FOREIGN KEY (marked_by) REFERENCES users (id)
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            faculty_id INTEGER,
            schedule TEXT,
            room TEXT,
            FOREIGN KEY (faculty_id) REFERENCES users (id)
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            date DATE NOT NULL,
            time TEXT,
            venue TEXT,
            description TEXT
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS student_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            event_id INTEGER,
            FOREIGN KEY (student_id) REFERENCES users (id),
            FOREIGN KEY (event_id) REFERENCES events (id)
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS clubs_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Check if columns exist and add them if they don't
    c.execute("PRAGMA table_info(users)")
    columns = [column[1] for column in c.fetchall()]
    
    # Add missing columns
    if 'rollno' not in columns:
        c.execute("ALTER TABLE users ADD COLUMN rollno TEXT")
    if 'section' not in columns:
        c.execute("ALTER TABLE users ADD COLUMN section TEXT")
    if 'department' not in columns:
        c.execute("ALTER TABLE users ADD COLUMN department TEXT")
    if 'class' not in columns:
        c.execute("ALTER TABLE users ADD COLUMN class TEXT")
    
    # Insert default data only if tables are empty
    c.execute("SELECT COUNT(*) FROM users")
    user_count = c.fetchone()[0]
    
    if user_count == 0:
        # Insert default admin
        c.execute("INSERT INTO users (username, password, role, name, email) VALUES (?, ?, ?, ?, ?)",
                 ('admin', 'admin123', 'admin', 'System Administrator', 'admin@college.edu'))
        
        # Add sample faculty
        c.execute("INSERT INTO users (username, password, role, name, email, department) VALUES (?, ?, ?, ?, ?, ?)",
                 ('faculty1', 'faculty123', 'faculty', 'Dr. Robert Brown', 'robert@college.edu', 'Computer Science'))
        c.execute("INSERT INTO users (username, password, role, name, email, department) VALUES (?, ?, ?, ?, ?, ?)",
                 ('faculty2', 'faculty123', 'faculty', 'Dr. Sarah Wilson', 'sarah@college.edu', 'Electronics'))
        
        # Add sample students with roll numbers
        c.execute("INSERT INTO users (username, password, role, name, email, class, rollno, section, department) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                 ('student1', 'student123', 'student', 'John Doe', 'john@college.edu', 'B.Tech CSE', '001', 'A', 'Computer Science'))
        c.execute("INSERT INTO users (username, password, role, name, email, class, rollno, section, department) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                 ('student2', 'student123', 'student', 'Jane Smith', 'jane@college.edu', 'B.Tech ECE', '002', 'B', 'Electronics'))
        
        # Add sample classes
        c.execute("INSERT INTO classes (name, faculty_id, schedule, room) VALUES (?, ?, ?, ?)",
                 ('Mathematics', 2, 'Mon, Wed 9:00-10:00', 'Room 101'))
        c.execute("INSERT INTO classes (name, faculty_id, schedule, room) VALUES (?, ?, ?, ?)",
                 ('Physics', 3, 'Tue, Thu 11:00-12:00', 'Room 205'))
        
        # Add sample events
        c.execute("INSERT INTO events (name, date, time, venue, description) VALUES (?, ?, ?, ?, ?)",
                 ('Tech Fest 2023', '2023-11-15', '10:00 AM', 'Main Auditorium', 'Annual technical festival'))
        c.execute("INSERT INTO events (name, date, time, venue, description) VALUES (?, ?, ?, ?, ?)",
                 ('Career Guidance Workshop', '2023-11-20', '2:00 PM', 'Seminar Hall', 'Workshop on career opportunities'))
        
        # Add default clubs
        clubs = [
            ('Coders Club – Code Architects', 'club'),
            ('Creators Club', 'club'),
            ('Cultural Club – Prathiba Yogyata', 'club'),
            ('Eco Club', 'club'),
            ('Fitness Club – Yogyata', 'club'),
            ('Gamers Club', 'club'),
            ('Handlers Club – Robo Tech', 'club'),
            ('Literary and Fine Arts Club – Literati & Euphoria', 'club'),
            ('Multimedia Club – Trinetra', 'club'),
            ('NSS Club – Devna', 'club'),
            ('SPHN Radio Club', 'club'),
            ('Sports Club – Sankalp', 'club'),
            ('Women’s Chapter Club', 'club')
        ]
        for name, type in clubs:
            c.execute("INSERT INTO clubs_events (name, type) VALUES (?, ?)", (name, type))
        
        # Add sample attendance
        today = date.today().isoformat()
        c.execute("INSERT INTO attendance (student_id, class_id, date, status, marked_by) VALUES (?, ?, ?, ?, ?)",
                 (4, 1, today, 'present', 2))
        c.execute("INSERT INTO attendance (student_id, class_id, date, status, marked_by) VALUES (?, ?, ?, ?, ?)",
                 (5, 1, today, 'present', 2))
        
        # Add sample permissions
        c.execute("INSERT INTO permissions (student_id, faculty_id, date, reason, status) VALUES (?, ?, ?, ?, ?)",
                 (4, 2, '2023-10-25', 'Medical appointment', 'pending'))
    
    # Create uploads directory if it doesn't exist
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    
    conn.commit()
    conn.close()

# Database helper function
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    role = request.form['role']
    
    conn = get_db_connection()
    user = conn.execute(
        'SELECT * FROM users WHERE username = ? AND password = ? AND role = ?',
        (username, password, role)
    ).fetchone()
    conn.close()
    
    if user:
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role']
        session['name'] = user['name']
        
        if role == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif role == 'faculty':
            return redirect(url_for('faculty_dashboard'))
        else:
            return redirect(url_for('student_dashboard'))
    else:
        flash('Invalid credentials. Please try again.', 'error')
        return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    
    # Get statistics
    students_count = conn.execute('SELECT COUNT(*) FROM users WHERE role = "student"').fetchone()[0]
    faculty_count = conn.execute('SELECT COUNT(*) FROM users WHERE role = "faculty"').fetchone()[0]
    pending_permissions = conn.execute('SELECT COUNT(*) FROM permissions WHERE status = "pending"').fetchone()[0]
    events_count = conn.execute('SELECT COUNT(*) FROM events').fetchone()[0]
    
    # Get users
    students = conn.execute('SELECT * FROM users WHERE role = "student"').fetchall()
    faculty = conn.execute('SELECT * FROM users WHERE role = "faculty"').fetchall()
    
    conn.close()
    
    return render_template('admin_dashboard.html', 
                         students_count=students_count,
                         faculty_count=faculty_count,
                         pending_permissions=pending_permissions,
                         events_count=events_count,
                         students=students,
                         faculty=faculty)

@app.route('/faculty/dashboard')
def faculty_dashboard():
    if 'user_id' not in session or session['role'] != 'faculty':
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    faculty_id = session['user_id']
    
    # Get statistics
    classes_count = conn.execute('SELECT COUNT(*) FROM classes WHERE faculty_id = ?', (faculty_id,)).fetchone()[0]
    students_count = conn.execute('SELECT COUNT(*) FROM users WHERE role = "student"').fetchone()[0]
    pending_permissions = conn.execute('SELECT COUNT(*) FROM permissions WHERE faculty_id = ? AND status = "pending"', (faculty_id,)).fetchone()[0]
    
    # Get permissions - FIXED QUERY
    permissions = conn.execute('''
        SELECT p.*, u.name as student_name, u.rollno 
        FROM permissions p 
        JOIN users u ON p.student_id = u.id 
        WHERE p.faculty_id = ?
    ''', (faculty_id,)).fetchall()
    
    # Get classes
    classes = conn.execute('SELECT * FROM classes WHERE faculty_id = ?', (faculty_id,)).fetchall()
    
    # Get students for attendance
    students = conn.execute('''
        SELECT id, rollno, name, section, department, class 
        FROM users 
        WHERE role = "student" 
        ORDER BY rollno
    ''').fetchall()
    
    # Get today's attendance
    today = date.today().isoformat()
    today_attendance = conn.execute('''
        SELECT student_id, status 
        FROM attendance 
        WHERE date = ? AND marked_by = ?
    ''', (today, faculty_id)).fetchall()
    
    attendance_dict = {row['student_id']: row['status'] for row in today_attendance}
    
    conn.close()
    
    return render_template('faculty_dashboard.html',
                         classes_count=classes_count,
                         students_count=students_count,
                         pending_permissions=pending_permissions,
                         permissions=permissions,
                         classes=classes,
                         students=students,
                         today_attendance=attendance_dict)

@app.route('/student/dashboard')
def student_dashboard():
    if 'user_id' not in session or session['role'] != 'student':
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    student_id = session['user_id']
    
    # Get clubs and events for permission form
    clubs_events = conn.execute('SELECT * FROM clubs_events WHERE is_active = 1').fetchall()
    clubs = [ce for ce in clubs_events if ce['type'] == 'club']
    events = [ce for ce in clubs_events if ce['type'] == 'event']
    
    # Get statistics
    attendance_percentage = conn.execute('''
        SELECT 
            COUNT(CASE WHEN status = 'present' THEN 1 END) * 100.0 / COUNT(*) as percentage
        FROM attendance 
        WHERE student_id = ?
    ''', (student_id,)).fetchone()[0] or 0
    
    pending_permissions = conn.execute('SELECT COUNT(*) FROM permissions WHERE student_id = ? AND status = "pending"', (student_id,)).fetchone()[0]
    events_count = conn.execute('SELECT COUNT(*) FROM student_events WHERE student_id = ?', (student_id,)).fetchone()[0]
    
    # Get attendance history - FIXED QUERY
    attendance = conn.execute('''
        SELECT 
            a.date,
            c.name as subject,
            a.status,
            u.name as marked_by
        FROM attendance a
        LEFT JOIN classes c ON a.class_id = c.id
        LEFT JOIN users u ON a.marked_by = u.id
        WHERE a.student_id = ?
        ORDER BY a.date DESC
        LIMIT 50
    ''', (student_id,)).fetchall()
    
    # Get permissions
    permissions = conn.execute('''
        SELECT p.*, u.name as faculty_name 
        FROM permissions p 
        LEFT JOIN users u ON p.faculty_id = u.id 
        WHERE p.student_id = ?
    ''', (student_id,)).fetchall()
    
    # Get student details
    student = conn.execute('SELECT * FROM users WHERE id = ?', (student_id,)).fetchone()
    
    conn.close()
    
    return render_template('student_dashboard.html',
                         clubs=clubs,
                         events=events,
                         attendance_percentage=attendance_percentage,
                         pending_permissions=pending_permissions,
                         events_count=events_count,
                         attendance=attendance,
                         permissions=permissions,
                         student=student)

# API Routes for AJAX operations
@app.route('/api/add_user', methods=['POST'])
def add_user():
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    data = request.json
    conn = get_db_connection()
    
    try:
        conn.execute('''INSERT INTO users (username, password, role, name, email, class, rollno, section, department) 
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (data['username'], data['password'], 'student', data['name'], 
                     data.get('email'), data.get('class'), data.get('rollno'), 
                     data.get('section'), data.get('department'), user_id))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Student added successfully'})
    except sqlite3.IntegrityError as e:
        conn.close()
        return jsonify({'success': False, 'message': f'Username already exists: {str(e)}'})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': f'Error adding student: {str(e)}'})

@app.route('/api/update_permission_status', methods=['POST'])
def update_permission_status():
    if 'user_id' not in session or session['role'] != 'faculty':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    data = request.json
    conn = get_db_connection()
    try:
        conn.execute('UPDATE permissions SET status = ? WHERE id = ?', (data['status'], data['permission_id']))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Permission updated successfully'})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': f'Error updating permission: {str(e)}'})

@app.route('/api/add_permission', methods=['POST'])
def add_permission():
    if 'user_id' not in session or session['role'] != 'student':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    data = request.json
    conn = get_db_connection()
    
    try:
        # Get faculty for the student's class (simplified - in real app would need proper mapping)
        faculty = conn.execute('SELECT id FROM users WHERE role = "faculty" LIMIT 1').fetchone()
        
        if faculty:
            conn.execute('INSERT INTO permissions (student_id, faculty_id, date, reason, proof) VALUES (?, ?, ?, ?, ?)',
                        (session['user_id'], faculty['id'], data['date'], data['reason'], data.get('proof', '')))
            conn.commit()
            conn.close()
            return jsonify({'success': True, 'message': 'Permission request submitted successfully'})
        
        conn.close()
        return jsonify({'success': False, 'message': 'No faculty found'})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': f'Error submitting permission: {str(e)}'})

@app.route('/api/upload_students', methods=['POST'])
def upload_students():
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file uploaded'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'})
    
    if file and allowed_file(file.filename):
        try:
            # Read Excel file
            df = pd.read_excel(file)
            
            # Map column names to handle different variations
            column_mapping = {
                'name': ['Name', 'name', 'Student Name', 'student_name'],
                'rollno': ['RollNo', 'rollno', 'Roll Number', 'roll_number', 'ID', 'Id'],
                'email': ['Email Id', 'Email', 'email', 'Email ID'],
                'section': ['Section', 'section'],
                'department': ['Dept', 'Department', 'department', 'dept'],
                'password': ['Password', 'password']
            }
            
            # Find actual column names
            actual_columns = {}
            for standard_col, possible_names in column_mapping.items():
                for possible_name in possible_names:
                    if possible_name in df.columns:
                        actual_columns[standard_col] = possible_name
                        break
            
            # Check required columns
            required_columns = ['name', 'rollno', 'email', 'section', 'department', 'password']
            missing_columns = [col for col in required_columns if col not in actual_columns]
            
            if missing_columns:
                return jsonify({'success': False, 'message': f'Missing required columns: {", ".join(missing_columns)}'})
            
            conn = get_db_connection()
            success_count = 0
            error_count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    # Generate username from roll number
                    username = str(row[actual_columns['rollno']]).strip()
                    
                    # Check if user already exists
                    existing_user = conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
                    if existing_user:
                        error_count += 1
                        errors.append(f"Row {index + 2}: Username {username} already exists")
                        continue
                    
                    conn.execute(
                        'INSERT INTO users (username, password, role, name, email, rollno, section, department) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                        (username, 
                         str(row[actual_columns['password']]).strip(), 
                         'student', 
                         str(row[actual_columns['name']]).strip(),
                         str(row[actual_columns['email']]).strip(),
                         str(row[actual_columns['rollno']]).strip(),
                         str(row[actual_columns['section']]).strip(),
                         str(row[actual_columns['department']]).strip())
                    )
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    errors.append(f"Row {index + 2}: {str(e)}")
            
            conn.commit()
            conn.close()
            
            message = f'Successfully added {success_count} students.'
            if error_count > 0:
                message += f' {error_count} failed.'
                if errors:
                    message += ' Errors: ' + '; '.join(errors[:5])  # Show first 5 errors
            
            return jsonify({'success': True, 'message': message})
            
        except Exception as e:
            return jsonify({'success': False, 'message': f'Error processing file: {str(e)}'})
    
    return jsonify({'success': False, 'message': 'Invalid file type'})

@app.route('/api/upload_faculty', methods=['POST'])
def upload_faculty():
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file uploaded'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'})
    
    if file and allowed_file(file.filename):
        try:
            df = pd.read_excel(file)
            
            # Map column names to handle different variations
            column_mapping = {
                'name': ['Name', 'name', 'Faculty Name', 'faculty_name'],
                'email': ['Email Id', 'Email', 'email', 'Email ID'],
                'department': ['Dept', 'Department', 'department', 'dept'],
                'password': ['Password', 'password']
            }
            
            # Find actual column names
            actual_columns = {}
            for standard_col, possible_names in column_mapping.items():
                for possible_name in possible_names:
                    if possible_name in df.columns:
                        actual_columns[standard_col] = possible_name
                        break
            
            required_columns = ['name', 'email', 'department', 'password']
            missing_columns = [col for col in required_columns if col not in actual_columns]
            
            if missing_columns:
                return jsonify({'success': False, 'message': f'Missing required columns: {", ".join(missing_columns)}'})
            
            conn = get_db_connection()
            success_count = 0
            error_count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    # Generate username from name
                    name = str(row[actual_columns['name']]).strip()
                    username = name.lower().replace(' ', '.') + str(index)
                    
                    # Check if user already exists
                    existing_user = conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
                    if existing_user:
                        error_count += 1
                        errors.append(f"Row {index + 2}: Username {username} already exists")
                        continue
                    
                    conn.execute(
                        'INSERT INTO users (username, password, role, name, email, department) VALUES (?, ?, ?, ?, ?, ?)',
                        (username, 
                         str(row[actual_columns['password']]).strip(), 
                         'faculty', 
                         name,
                         str(row[actual_columns['email']]).strip(),
                         str(row[actual_columns['department']]).strip())
                    )
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    errors.append(f"Row {index + 2}: {str(e)}")
            
            conn.commit()
            conn.close()
            
            message = f'Successfully added {success_count} faculty members.'
            if error_count > 0:
                message += f' {error_count} failed.'
                if errors:
                    message += ' Errors: ' + '; '.join(errors[:5])
            
            return jsonify({'success': True, 'message': message})
            
        except Exception as e:
            return jsonify({'success': False, 'message': f'Error processing file: {str(e)}'})
    
    return jsonify({'success': False, 'message': 'Invalid file type'})

@app.route('/api/add_faculty', methods=['POST'])
def add_faculty():
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    data = request.json
    conn = get_db_connection()
    
    try:
        conn.execute(
            'INSERT INTO users (username, password, role, name, email, department) VALUES (?, ?, ?, ?, ?, ?)',
            (data['username'], data['password'], 'faculty', data['name'], 
             data.get('email'), data.get('department'))
        )
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Faculty added successfully'})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'success': False, 'message': 'Username already exists'})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': f'Error adding faculty: {str(e)}'})

@app.route('/api/delete_user/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'User deleted successfully'})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': f'Error deleting user: {str(e)}'})

@app.route('/api/get_clubs_events')
def get_clubs_events():
    conn = get_db_connection()
    clubs_events = conn.execute('SELECT * FROM clubs_events WHERE is_active = 1 ORDER BY type, name').fetchall()
    conn.close()
    
    return jsonify([dict(ce) for ce in clubs_events])

@app.route('/api/add_club_event', methods=['POST'])
def add_club_event():
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    data = request.json
    conn = get_db_connection()
    
    try:
        conn.execute(
            'INSERT INTO clubs_events (name, type) VALUES (?, ?)',
            (data['name'], data['type'])
        )
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': f'{data["type"].title()} added successfully'})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/api/update_club_event/<int:club_event_id>', methods=['PUT'])
def update_club_event(club_event_id):
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    data = request.json
    conn = get_db_connection()
    
    try:
        conn.execute(
            'UPDATE clubs_events SET name = ?, type = ? WHERE id = ?',
            (data['name'], data['type'], club_event_id)
        )
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Updated successfully'})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/api/delete_club_event/<int:club_event_id>', methods=['DELETE'])
def delete_club_event(club_event_id):
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM clubs_events WHERE id = ?', (club_event_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Deleted successfully'})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/api/change_password', methods=['POST'])
def change_password():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    data = request.json
    user_id = session['user_id']
    
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    
    if not user or user['password'] != data['current_password']:
        conn.close()
        return jsonify({'success': False, 'message': 'Current password is incorrect'})
    
    if data['new_password'] != data['confirm_password']:
        conn.close()
        return jsonify({'success': False, 'message': 'New passwords do not match'})
    
    try:
        conn.execute('UPDATE users SET password = ? WHERE id = ?', (data['new_password'], user_id))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Password changed successfully'})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': f'Error changing password: {str(e)}'})

@app.route('/api/update_user/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    data = request.json
    conn = get_db_connection()
    
    try:
        if data.get('role') == 'student':
            conn.execute(
                'UPDATE users SET name = ?, email = ?, class = ?, rollno = ?, section = ?, department = ? WHERE id = ?',
                (data['name'], data.get('email'), data.get('class'), data.get('rollno'), 
                 data.get('section'), data.get('department'), user_id)
            )
        else:
            conn.execute(
                'UPDATE users SET name = ?, email = ?, department = ? WHERE id = ?',
                (data['name'], data.get('email'), data.get('department'), user_id)
            )
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'User updated successfully'})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': f'Error updating user: {str(e)}'})

@app.route('/api/get_user/<int:user_id>')
def get_user(user_id):
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    
    if user:
        return jsonify({'success': True, 'user': dict(user)})
    else:
        return jsonify({'success': False, 'message': 'User not found'})

@app.route('/api/mark_attendance', methods=['POST'])
def mark_attendance():
    if 'user_id' not in session or session['role'] != 'faculty':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    data = request.json
    faculty_id = session['user_id']
    
    conn = get_db_connection()
    try:
        # Get class_id for the faculty (simplified - in real app would need proper class mapping)
        class_info = conn.execute('SELECT id FROM classes WHERE faculty_id = ? LIMIT 1', (faculty_id,)).fetchone()
        
        if not class_info:
            conn.close()
            return jsonify({'success': False, 'message': 'No classes assigned to faculty'})
        
        class_id = class_info['id']
        today = date.today().isoformat()
        
        # Delete existing attendance for today to avoid duplicates
        conn.execute('DELETE FROM attendance WHERE date = ? AND marked_by = ?', (today, faculty_id))
        
        # Insert new attendance records
        for student_id, status in data['attendance'].items():
            if status in ['present', 'absent']:
                conn.execute(
                    'INSERT INTO attendance (student_id, class_id, date, status, marked_by) VALUES (?, ?, ?, ?, ?)',
                    (int(student_id), class_id, today, status, faculty_id)
                )
        
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Attendance marked successfully'})
        
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': f'Error marking attendance: {str(e)}'})

if __name__ == '__main__':
    init_db()
    app.run(debug=True)