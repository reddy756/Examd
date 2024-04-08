from flask import Blueprint,redirect,url_for,render_template,request,flash,session,abort,jsonify
from database import execute_query
from sendmail import send_email
from key import add_faculty_verify,update_faculty_verify
from ctokens import create_token,verify_token
import werkzeug.security as bcrypt

admin_bp = Blueprint('admin',__name__,url_prefix='/admin')

@admin_bp.route('/dashboard')   
def dashboard():
    if session.get('role') == 'Admin':
        return render_template('admin/dashboard.html')
    else:
        return redirect(url_for('auth.login'))

@admin_bp.route('/view_departments')
def view_departments():
    if session.get('role') == 'Admin':
        query = """
        SELECT d.department_id, d.department_name, u.name AS incharge_name
        FROM departments d
        LEFT JOIN users u ON d.incharge_user_id = u.user_id
        """
        departments_details = execute_query(query)
        return render_template('admin/view_departments.html', departments_details=departments_details)
    else:
        flash('Please Login to Continue!')
        return redirect(url_for('auth.login'))

@admin_bp.route('/view_courses')
def view_courses():
    if session.get('role') == 'Admin':
        query = """
        SELECT c.course_id, c.course_name, d.department_name
        FROM courses c
        LEFT JOIN departments d ON c.department_id = d.department_id
        """
        course_details = execute_query(query)
        return render_template('admin/view_courses.html', course_details=course_details)
    else:
        flash('Please Login to Continue!')
        return redirect(url_for('auth.login'))

@admin_bp.route('/add_departments', methods=['GET', 'POST'])
def add_departments():
    if session.get('role') == 'Admin':
        faculty_details = execute_query("SELECT user_id, name FROM users WHERE role = 'Faculty' OR role = 'Department Incharge'")
        if request.method == 'POST':
            dept_name = request.form.get('dept_name').strip()
            incharge_id = request.form.get('incharge_id',type=int)

            if dept_name:
                existing_dept = execute_query("SELECT COUNT(*) as count FROM departments WHERE department_name = %s", (dept_name,),fetch_one=True)
                if existing_dept['count'] == 1:
                    flash('Department name already exists.')
                    return redirect(url_for('admin.add_departments'))
                existing_incharge = execute_query("Select COUNT(*) as count FROM departments WHERE incharge_user_id=%s",(incharge_id,),fetch_one=True)
                if existing_incharge ==1:
                    flash('Incharge Already Assigned to the other Department.')
                    return(redirect(url_for('admin.add_departments')))
                execute_query("INSERT INTO departments (department_name, incharge_user_id) VALUES (%s, %s)", (dept_name, incharge_id), commit=True)

                if incharge_id:
                    execute_query("UPDATE users SET role = 'Department Incharge' WHERE user_id = %s", (incharge_id,), commit=True)
                
                flash('Department added successfully.')
                return redirect(url_for('admin.view_departments'))
            else:
                flash('Department name is required.')
                return redirect(url_for('admin.add_departments'))
        return render_template('admin/add_departments.html', faculty_details=faculty_details)
    else:
        flash('Please Login to Continue.')
        return redirect(url_for('auth.login'))

@admin_bp.route('/add_courses', methods=['GET', 'POST'])
def add_courses():
    if session.get('role') == 'Admin':
        departments = execute_query("SELECT department_id, department_name FROM departments")
        if request.method == 'POST':
            course_name = request.form.get('course_name').strip()
            dept_id = request.form.get('dept_id',type=int)

            if not course_name:
                flash('Course name is required.')
                return redirect(url_for('admin.add_courses'))

            if not dept_id:
                flash('Valid department is required.')
                return redirect(url_for('admin.add_courses'))

            existing_course = execute_query("SELECT COUNT(*) as count FROM courses WHERE course_name = %s AND department_id = %s", (course_name, dept_id),fetch_one=True)
            
            if existing_course['count'] == 1:
                flash('Course already exists in the selected department.')
                return redirect(url_for('admin.add_courses'))

            execute_query("INSERT INTO courses (course_name, department_id) VALUES (%s, %s)", (course_name, dept_id), commit=True)
            flash('Course added successfully.')
            return redirect(url_for('admin.view_courses'))
        
        return render_template('admin/add_courses.html', departments=departments)
    else:
        flash('Please Login to Continue.')
        return redirect(url_for('auth.login'))

@admin_bp.route('/update_department/<int:dept_id>', methods=['GET', 'POST'])
def update_department(dept_id):
    if session.get('role') == 'Admin':
        dept_details = execute_query("SELECT department_id, department_name, incharge_user_id FROM departments WHERE department_id = %s", (dept_id,), fetch_one=True)
        faculty = execute_query("SELECT user_id, name FROM users WHERE role IN ('Faculty', 'Department Incharge')")

        if request.method == 'POST':
            dept_name = request.form.get('dept_name').strip()
            incharge_id = request.form.get('incharge_id',type=int)

            if not dept_name:
                flash('Department name is required.')
                return render_template('admin/update_department.html', dept_details=dept_details, faculty=faculty)

            # Check if incharge is already assigned to another department
            if incharge_id:
                existing_incharge = execute_query("SELECT COUNT(*) as count FROM departments WHERE incharge_user_id = %s AND department_id != %s", (incharge_id, dept_id),fetch_one=True)
                if existing_incharge['count'] == 1:
                    flash('This incharge is already assigned to another department.')
                    return render_template('admin/update_department.html', dept_details=dept_details, faculty=faculty)

            # Update department name and incharge
            execute_query("UPDATE departments SET department_name = %s, incharge_user_id = %s WHERE department_id = %s", (dept_name, incharge_id, dept_id), commit=True)

            # Update the role of the new incharge
            if incharge_id:
                execute_query("UPDATE users SET role = 'Department Incharge' WHERE user_id = %s", (incharge_id,), commit=True)

            # Reset the role of the old incharge if changed
            if dept_details['incharge_user_id'] and dept_details['incharge_user_id'] != incharge_id:
                execute_query("UPDATE users SET role = 'Faculty' WHERE user_id = %s", (dept_details['incharge_user_id'],), commit=True)

            flash('Department updated successfully.')
            return redirect(url_for('admin.view_departments'))
        
        return render_template('admin/update_department.html', dept_details=dept_details, faculty=faculty)
    else:
        flash('Please Login to Continue.')
        return redirect(url_for('auth.login'))

@admin_bp.route('/update_course/<int:course_id>', methods=['GET', 'POST'])
def update_course(course_id):
    if session.get('role') == 'Admin':
        course_details = execute_query("SELECT c.course_id, c.course_name, c.department_id, d.department_name FROM courses c LEFT JOIN departments d ON c.department_id = d.department_id WHERE c.course_id = %s", (course_id,), fetch_one=True)
        departments = execute_query("SELECT department_id, department_name FROM departments")

        if request.method == 'POST':
            course_name = request.form.get('course_name').strip()
            dept_id = request.form.get('dept_id',type=int)

            if not course_name:
                flash('Course name is required.')
                return render_template('admin/update_course.html', course_details=course_details, departments=departments)

            if not dept_id:
                flash('Valid department is required.')
                return render_template('admin/update_course.html', course_details=course_details, departments=departments)

            # Update the course details
            execute_query("UPDATE courses SET course_name = %s, department_id = %s WHERE course_id = %s", (course_name, dept_id, course_id), commit=True)
            flash('Course updated successfully.')
            return redirect(url_for('admin.view_courses'))
        
        return render_template('admin/update_course.html', course_details=course_details, departments=departments)
    else:
        flash('Please Login to Continue.')
        return redirect(url_for('auth.login'))

@admin_bp.route('/view_faculty')
def view_faculty():
    if session.get('role') == 'Admin':
        query = """
        SELECT f.faculty_id, u.name, u.email, u.role, d.department_name, c.course_name,c.course_id
        FROM faculty f
        JOIN users u ON f.user_id = u.user_id
        LEFT JOIN departments d ON f.department_id = d.department_id
        LEFT JOIN courses c ON f.course_id = c.course_id;
        """
        faculty_details = execute_query(query)
        return render_template('admin/view_faculty.html', faculty_details=faculty_details)
    else:
        flash('Please Login to Continue!')
        return redirect(url_for('auth.login'))

@admin_bp.route('/dept_course/<int:dept_id>')
def get_courses_by_department(dept_id):
    if session.get('role') == 'Admin':
        courses = execute_query("SELECT course_id, course_name FROM courses WHERE department_id = %s", (dept_id,))
        return jsonify([{'course_id': course['course_id'], 'course_name': course['course_name']} for course in courses])
    else:
        return abort(403, 'Unauthorized access')
       
@admin_bp.route('/add_faculty', methods=['GET', 'POST'])
def add_faculty():
    if session.get('role') == 'Admin':
        departments = execute_query("SELECT department_id, department_name FROM departments")
        if request.method == 'POST':
            name = request.form.get('name', None).strip()
            email = request.form.get('email', None).strip()
            role = request.form.get('role', None).strip()
            department_id = request.form.get('department_id','Null',type=int)
            course_id = request.form.get('course_id','Null',type=int)
            hashed_password = bcrypt.generate_password_hash('asdf1234', method='pbkdf2:sha256', salt_length=16)

            # Handling for Department Incharge and Faculty roles
            if role in ['Department Incharge', 'Faculty']:
                # For Department Incharge, check if an incharge already exists
                if role == 'Department Incharge':
                    incharge_count = execute_query("SELECT COUNT(*) as count FROM departments WHERE department_id=%s AND incharge_user_id IS NOT NULL", (department_id,), fetch_one=True)
                    if incharge_count['count'] == 1:
                        flash('Incharge already assigned for this department.')
                        return redirect(url_for('admin.add_faculty'))

            email_count = execute_query("SELECT COUNT(*) as count FROM users WHERE email=%s", (email,), fetch_one=True)['count']
            if email_count== 1:
                flash('Email Already Exists!')
                return redirect(url_for('admin.add_faculty'))
                
            data = {'Name': name, 'Email': email, 'Password': hashed_password, 'Role': role,'Department_id': department_id, 'Course_id': course_id}
            
            token = create_token(data, salt=add_faculty_verify)
            verify_url = url_for('admin.faculty_verify', token=token, _external=True)
            subject = 'Activate Your Account'
            body = f"Dear {name},\n\nYour account has been created with the temporary password: asdf1234\n\nPlease activate your account and set your own password by clicking the following link:\n{verify_url}"
            send_email(receiver_email=email, subject=subject, body=body)

            flash('Faculty added and verification email sent.')
            return redirect(url_for('admin.view_faculty'))

        return render_template('admin/add_faculty.html', departments=departments)
    else:
        flash('Please Login to Continue.')
        return redirect(url_for('auth.login'))
    
@admin_bp.route('/faculty_verify/<token>', methods=['GET', 'POST'])
def faculty_verify(token):
    data = verify_token(token, salt=add_faculty_verify, expiration=86400)  # 24 hours for token expiration
    if data:
        user_exists = execute_query("SELECT COUNT(*) as count FROM users WHERE email = %s", (data['Email'],),fetch_one=True)['count']
        if user_exists==1:
            flash('User Already Registered! Please Login.')
            return redirect(url_for('auth.login'))

        # Insert into users table
        execute_query("INSERT INTO users (name, email, password_hash, role) VALUES (%s, %s, %s, %s)", (data['Name'], data['Email'], data['Password'], data['Role']), commit=True)

        user_id = execute_query("SELECT user_id FROM users WHERE email=%s", (data['Email'],), fetch_one=True)['user_id']

        # Handle Department Incharge and Faculty specific actions
        if data['Role'] in ['Department Incharge', 'Faculty']:
            # Insert into faculty table
            execute_query("INSERT INTO faculty (user_id,department_id,course_id) VALUES (%s,%s,%s)", (user_id,data['Department_id'],data['Course_id']), commit=True)

        if data['Role'] == 'Department Incharge':
            # Update department with incharge_user_id
            execute_query("UPDATE departments SET incharge_user_id=%s WHERE department_id=%s", (user_id, data['Department_id']), commit=True)
            flash('You were added as Department Incharge')

        flash(f"You've successfully registered as {data['Role']}")
        return redirect(url_for('auth.login'))
    else:
        flash('Verification link expired or invalid.')
        return redirect(url_for('admin.add_faculty'))

@admin_bp.route('/update_faculty/<int:faculty_id>', methods=['GET', 'POST'])
def update_faculty(faculty_id):
    if session.get('role') == 'Admin':
        faculty_details = execute_query("SELECT f.faculty_id, u.name,u.user_id, u.email, u.role, d.department_name, c.course_name,c.course_id,f.department_id,f.course_id FROM faculty f JOIN users u ON f.user_id = u.user_id LEFT JOIN departments d ON f.department_id = d.department_id LEFT JOIN courses c ON f.course_id = c.course_id where faculty_id=%s", (faculty_id,), fetch_one=True)
        departments = execute_query("SELECT department_id, department_name FROM departments")
        print(faculty_details['course_id'])
        if request.method == 'POST':
            name = request.form.get('name').strip()
            email = request.form.get('email').strip()
            role = request.form.get('role').strip()
            department_id = request.form.get('department_id', type=int)
            course_id = request.form.get('course_id',type=int)
            data = {'Name': name,'Email': email,'Role': role,'Department_id': department_id,'Course_id':course_id,'Existing_user_id': faculty_details['user_id']}

            # Handling for Department Incharge and Faculty roles
            if role in ['Department Incharge', 'Faculty']:
                # For Department Incharge, check if an incharge already exists
                if role == 'Department Incharge':
                    incharge_count = execute_query("SELECT COUNT(*) as count FROM departments WHERE department_id=%s AND incharge_user_id IS NOT NULL", (department_id,), fetch_one=True)
                    if incharge_count['count'] == 1:
                        flash('Incharge already assigned for this department.')
                        return redirect(url_for('admin.update_faculty',faculty_id=faculty_id))
                    else:
                        execute_query("update departments set incharge_user_id=%s where department_id=%s",(faculty_details['user_id'],data['Department_id']),commit=True)
            if department_id==faculty_details['department_id'] and course_id!=faculty_details['course_id']:
                execute_query("UPDATE faculty set course_id=%s where department_id=%s and faculty_id=%s",(data['Course_id'],data['Department_id'],faculty_id),commit=True)
            elif department_id!=faculty_details['department_id'] and course_id==faculty_details['course_id']:
                execute_query("UPDATE faculty set department_id=%s where course_id=%s and faculty_id=%s",(data['Department_id'],data['Course_id'],faculty_id),commit=True)
            elif department_id!=faculty_details['department_id'] and course_id!=faculty_details['course_id']:
                execute_query("UPDATE faculty set department_id=%s, course_id=%s where faculty_id=%s",(data['Department_id'],data['Course_id'],faculty_id),commit=True)

            if email != faculty_details['email']:  # Check if email has changed
                # Ensure the new email doesn't already exist in the system
                email_count = execute_query("SELECT COUNT(*) as count FROM users WHERE email = %s AND user_id != %s", (email, faculty_details['user_id']),fetch_one=True)['count']# Send email to verify the email change
                data['Email'] = email
                if email_count == 1:
                    flash('Email Already Exists!')
                    return render_template('admin/update_faculty.html', faculty_details=faculty_details, departments=departments)
                token = create_token(data, salt=update_faculty_verify)
                verify_url = url_for('admin.faculty_update_verify', token=token, _external=True)
                subject = 'Confirm Your Email Update'
                body = f"Dear {name},\n\nPlease confirm your email update by clicking the following link:\n{verify_url}"
                send_email(receiver_email=email, subject=subject, body=body)

                flash('Email Sent to Faculty new Email to update through the link Within 24 Hours.')
                return redirect(url_for('admin.view_faculty'))

            # Update faculty details without changing email
            execute_query("UPDATE users SET name = %s, role = %s WHERE user_id = %s", (name, role,data['Existing_user_id']), commit=True)
            flash('Faculty details updated successfully.')
            return redirect(url_for('admin.view_faculty'))

        return render_template('admin/update_faculty.html', faculty_details=faculty_details, departments=departments)
    else:
        flash('Please Login to Continue.')
        return redirect(url_for('auth.login'))

@admin_bp.route('/faculty_update_verify/<token>', methods=['GET', 'POST'])
def faculty_update_verify(token):
    data = verify_token(token, salt=update_faculty_verify, expiration=86400)  # 24 hours for token expiration
    if data:
        # Check if the new email is already registered
        email_count = execute_query("SELECT COUNT(*) as count FROM users WHERE email = %s AND user_id = %s", (data['Email'], data['Existing_user_id']),fetchone=True)['count']
        if email_count ==1:
            flash('New Email Already Updated.')
            return redirect(url_for('auth.login'))

        # Update the user details in the database
        execute_query("UPDATE users SET email = %s WHERE user_id = %s",
                      (data['Email'], data['Existing_user_id']), commit=True)

        flash('Faculty email update verified successfully.')
        return redirect(url_for('auth.login'))
    else:
        flash('Verification link expired or invalid.')
        return redirect(url_for('auth.login'))

@admin_bp.route('/delete_department/<int:dept_id>', methods=['POST'])
def delete_department(dept_id):
    if session.get('role') == 'Admin':
        # Reset incharge_user_id before deleting the department
        execute_query("UPDATE departments SET incharge_user_id = NULL WHERE department_id = %s", (dept_id,), commit=True)
        execute_query("DELETE FROM departments WHERE department_id = %s", (dept_id,), commit=True)
        flash("Department deleted successfully.")
        return redirect(url_for('admin.view_departments'))
    else:
        flash("Please login to continue.")
        return redirect(url_for('auth.login'))

@admin_bp.route('/delete_course/<int:course_id>', methods=['POST'])
def delete_course(course_id):
    if session.get('role') == 'Admin':
        execute_query("DELETE FROM courses WHERE course_id = %s", (course_id,), commit=True)
        flash("Course deleted successfully.")
        return redirect(url_for('admin.view_courses'))
    else:
        flash("Please login to continue.")
        return redirect(url_for('auth.login'))

@admin_bp.route('/delete_faculty/<int:faculty_id>', methods=['POST'])
def delete_faculty(faculty_id):
    if session.get('role') == 'Admin':
        # Check if the faculty is an incharge, if so, reset the department's incharge_user_id   
        user_id = execute_query("Select user_id FROM faculty WHERE faculty_id = %s", (faculty_id,), fetch_one=True)['user_id']
        execute_query("DELETE FROM users WHERE user_id = %s AND role IN ('Faculty', 'Department Incharge')", (user_id,), commit=True)
        flash("Faculty member deleted successfully.")
        return redirect(url_for('admin.view_faculty'))
    else:
        flash("Please login to continue.")
        return redirect(url_for('auth.login'))

@admin_bp.route('/create_schedule', methods=['GET', 'POST'])
def create_schedule():
    if session.get('role') != 'Admin':
        flash('Access denied. Please log in as an admin.')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        course_id = request.form.get('course_id', type=int)
        faculty_id = request.form.get('faculty_id', type=int)
        room_id = request.form.get('room_id', type=int)
        date = request.form.get('date')
        time = request.form.get('time')

        # Additional validation can be performed here

        execute_query(
            "INSERT INTO invigilation_schedules (faculty_id, room_id, course_id, date, time) VALUES (%s, %s, %s, %s, %s)",
            (faculty_id, room_id, course_id, date, time),
            commit=True
        )
        flash('Invigilation schedule created successfully.')
        return redirect(url_for('admin.dashboard'))

    # Load data for form selections
    faculties = execute_query("SELECT user_id, name FROM users WHERE role = 'Faculty' OR role = 'Department Incharge'")
    courses = execute_query("SELECT course_id, course_name FROM courses")
    rooms = execute_query("SELECT room_id, room_number FROM rooms")

    return render_template('admin/create_schedule.html', faculties=faculties, courses=courses, rooms=rooms)

@admin_bp.route('/view_schedules')
def view_schedules():
    if session.get('role') != 'Admin':
        flash('Access denied. Please log in as an admin.')
        return redirect(url_for('auth.login'))

    query = """
    SELECT is.schedule_id, f.name AS faculty_name, c.course_name, r.room_number, is.date, is.time
    FROM invigilation_schedules is
    JOIN faculty f ON is.faculty_id = f.faculty_id
    JOIN courses c ON is.course_id = c.course_id
    JOIN rooms r ON is.room_id = r.room_id
    ORDER BY is.date, is.time
    """
    schedules = execute_query(query)
    return render_template('admin/view_schedules.html', schedules=schedules)

@admin_bp.route('/update_schedule/<int:schedule_id>', methods=['GET', 'POST'])
def update_schedule(schedule_id):
    if session.get('role') != 'Admin':
        flash('Access denied. Please log in as an admin.')
        return redirect(url_for('auth.login'))

    schedule_details = execute_query(
        "SELECT faculty_id, course_id, room_id, date, time FROM invigilation_schedules WHERE schedule_id = %s",
        (schedule_id,),
        fetch_one=True
    )

    if request.method == 'POST':
        faculty_id = request.form.get('faculty_id', type=int)
        course_id = request.form.get('course_id', type=int)
        room_id = request.form.get('room_id', type=int)
        date = request.form.get('date')
        time = request.form.get('time')

        execute_query(
            "UPDATE invigilation_schedules SET faculty_id = %s, course_id = %s, room_id = %s, date = %s, time = %s WHERE schedule_id = %s",
            (faculty_id, course_id, room_id, date, time, schedule_id),
            commit=True
        )
        flash('Invigilation schedule updated successfully.')
        return redirect(url_for('admin.view_schedules'))

    faculties = execute_query("SELECT faculty_id, name FROM faculty")
    courses = execute_query("SELECT course_id, course_name FROM courses")
    rooms = execute_query("SELECT room_id, room_number FROM rooms")

    return render_template('admin/update_schedule.html', schedule=schedule_details, faculties=faculties, courses=courses, rooms=rooms)

@admin_bp.route('/delete_schedule/<int:schedule_id>', methods=['POST'])
def delete_schedule(schedule_id):
    if session.get('role') != 'Admin':
        flash('Access denied. Please log in as an admin.')
        return redirect(url_for('auth.login'))

    execute_query("DELETE FROM invigilation_schedules WHERE schedule_id = %s", (schedule_id,), commit=True)
    flash('Invigilation schedule deleted successfully.')
    return redirect(url_for('admin.view_schedules'))

@admin_bp.route('/list_faculties')
def list_faculties():
    if session.get('role') != 'Admin':
        flash('Access denied. Please log in as an admin.')
        return redirect(url_for('auth.login'))

    query = """
    SELECT u.user_id, u.name, u.email, u.role, d.department_name
    FROM users u
    LEFT JOIN departments d ON u.department_id = d.department_id
    WHERE u.role = 'Faculty' OR u.role = 'Department Incharge'
    ORDER BY u.name
    """
    faculties = execute_query(query)
    return render_template('admin/list_faculties.html', faculties=faculties)

@admin_bp.route('/list_courses')
def list_courses():
    if session.get('role') != 'Admin':
        flash('Access denied. Please log in as an admin.')
        return redirect(url_for('auth.login'))

    query = """
    SELECT c.course_id, c.course_name, d.department_name
    FROM courses c
    LEFT JOIN departments d ON c.department_id = d.department_id
    ORDER BY c.course_name
    """
    courses = execute_query(query)
    return render_template('admin/list_courses.html', courses=courses)

@admin_bp.route('/list_rooms')
def list_rooms():
    if session.get('role') != 'Admin':
        flash('Access denied. Please log in as an admin.')
        return redirect(url_for('auth.login'))

    query = "SELECT room_id, room_number, building FROM rooms ORDER BY building, room_number"
    rooms = execute_query(query)
    return render_template('admin/list_rooms.html', rooms=rooms)

@admin_bp.route('/view_adjustment_requests')
def view_adjustment_requests():
    if session.get('role') != 'Admin':
        flash('Access denied. Please log in as an admin.')
        return redirect(url_for('auth.login'))

    query = """
    SELECT ar.request_id, ar.status, f.name AS from_faculty_name, t.name AS to_faculty_name, 
           c.course_name, r.room_number, ar.request_date, ar.response_date
    FROM adjustment_requests ar
    JOIN faculty f ON ar.from_faculty_id = f.faculty_id
    JOIN faculty t ON ar.to_faculty_id = t.faculty_id
    JOIN courses c ON ar.course_id = c.course_id
    JOIN rooms r ON ar.room_id = r.room_id
    ORDER BY ar.request_date DESC
    """
    adjustment_requests = execute_query(query)
    return render_template('admin/view_adjustment_requests.html', adjustment_requests=adjustment_requests)

@admin_bp.route('/approve_adjustment_request/<int:request_id>', methods=['POST'])
def approve_adjustment_request(request_id):
    if session.get('role') != 'Admin':
        flash('Access denied. Please log in as an admin.')
        return redirect(url_for('auth.login'))

    # Start a transaction to ensure data integrity
    execute_query("BEGIN")

    try:
        # Fetch the details of the adjustment request
        adjustment_request = execute_query(
            "SELECT from_faculty_id, to_faculty_id, schedule_id FROM adjustment_requests WHERE request_id = %s",
            (request_id,),
            fetch_one=True
        )

        # Update the invigilation schedule with the new faculty (to_faculty)
        execute_query(
            "UPDATE invigilation_schedules SET faculty_id = %s WHERE schedule_id = %s",
            (adjustment_request['to_faculty_id'], adjustment_request['schedule_id']),
            commit=False  # Delay commit until all operations are successful
        )

        # Update the status of the adjustment request to 'Accepted'
        execute_query(
            "UPDATE adjustment_requests SET status = 'Accepted', response_date = CURRENT_DATE() WHERE request_id = %s",
            (request_id,),
            commit=False
        )

        # Commit the transaction
        execute_query("COMMIT")

        # Fetch email addresses of the involved faculties to notify them
        faculty_emails = execute_query(
            "SELECT email FROM users WHERE user_id IN (%s, %s)",
            (adjustment_request['from_faculty_id'], adjustment_request['to_faculty_id'])
        )

        # Send notification emails (assuming a send_email function is available)
        for faculty_email in faculty_emails:
            send_email(
                receiver_email=faculty_email['email'],
                subject='Invigilation Duty Adjustment Approved',
                body='Your adjustment request for invigilation duty has been approved.'
            )

        flash('Adjustment request approved and invigilation schedule updated successfully.')
    except Exception as e:
        execute_query("ROLLBACK")  # Rollback the transaction on error
        flash(f'An error occurred: {e}')
    
    return redirect(url_for('admin.view_adjustment_requests'))

@admin_bp.route('/reject_adjustment_request/<int:request_id>', methods=['POST'])
def reject_adjustment_request(request_id):
    if session.get('role') != 'Admin':
        flash('Access denied. Please log in as an admin.')
        return redirect(url_for('auth.login'))

    # Update the status of the adjustment request to 'Rejected'
    execute_query(
        "UPDATE adjustment_requests SET status = 'Rejected', response_date = CURRENT_DATE() WHERE request_id = %s",
        (request_id,),
        commit=True
    )

    # Fetch email addresses of the involved faculties to notify them
    faculty_emails = execute_query(
        "SELECT u.email FROM adjustment_requests ar JOIN users u ON ar.from_faculty_id = u.user_id OR ar.to_faculty_id = u.user_id WHERE ar.request_id = %s",
        (request_id,)
    )

    # Send notification emails to the involved faculties
    subject = 'Invigilation Duty Adjustment Request Rejected'
    body = 'Your request for adjustment of invigilation duty has been rejected.'
    for faculty_email in faculty_emails:
        send_email(
            receiver_email=faculty_email['email'],
            subject=subject,
            body=body
        )

    flash('Adjustment request rejected successfully.')
    return redirect(url_for('admin.view_adjustment_requests'))

@admin_bp.route('/view_users')
def view_users():
    if session.get('role') != 'Admin':
        flash('Access denied. Please log in as an admin.')
        return redirect(url_for('auth.login'))

    query = """
    SELECT user_id, name, email, role, department_id
    FROM users
    ORDER BY role, name
    """
    users = execute_query(query)
    departments = {dept['department_id']: dept['department_name'] for dept in execute_query("SELECT department_id, department_name FROM departments")}

    # Enhance user data with department names
    for user in users:
        user['department_name'] = departments.get(user['department_id'], 'N/A')

    return render_template('admin/view_users.html', users=users)

@admin_bp.route('/update_user_role/<int:user_id>', methods=['GET', 'POST'])
def update_user_role(user_id):
    if session.get('role') != 'Admin':
        flash('Access denied. Please log in as an admin.')
        return redirect(url_for('auth.login'))

    user = execute_query(
        "SELECT user_id, name, email, role FROM users WHERE user_id = %s",
        (user_id,),
        fetch_one=True
    )

    if request.method == 'POST':
        new_role = request.form.get('role')
        if new_role not in ['Admin', 'Department Incharge', 'Faculty']:
            flash('Invalid role specified.')
            return redirect(url_for('admin.update_user_role', user_id=user_id))

        execute_query(
            "UPDATE users SET role = %s WHERE user_id = %s",
            (new_role, user_id),
            commit=True
        )

        flash(f"User role updated successfully to {new_role}.")
        return redirect(url_for('admin.view_users'))

    return render_template('admin/update_user_role.html', user=user)

@admin_bp.route('/reset_user_password/<int:user_id>', methods=['POST'])
def reset_user_password(user_id):
    if session.get('role') != 'Admin':
        flash('Access denied. Please log in as an admin.')
        return redirect(url_for('auth.login'))

    user = execute_query(
        "SELECT user_id, email FROM users WHERE user_id = %s",
        (user_id,),
        fetch_one=True
    )

    if user:
        # Generate a one-time password reset token
        reset_token = create_token({'user_id': user['user_id']}, salt=salt, expiration=3600)  # 1 hour expiration
        reset_url = url_for('auth.reset_password', token=reset_token, _external=True)

        # Send the password reset email
        subject = 'Password Reset Request'
        body = f"Dear user,\n\nA password reset request has been made for your account. Please click the following link to reset your password:\n{reset_url}\n\nIf you did not request a password reset, please ignore this email."
        send_email(receiver_email=user['email'], subject=subject, body=body)

        flash('Password reset email sent successfully.')
    else:
        flash('User not found.')

    return redirect(url_for('admin.view_users'))


@admin_bp.route('/logout')
def logout():
    if session.get('role')=='Admin':
        session.pop('role')
        session.pop('user_id')
        flash('logout Success!')
        return redirect(url_for('auth.login'))
    else:
        return redirect(url_for('auth.login'))

