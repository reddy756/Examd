from flask import Blueprint, render_template, session, redirect, url_for, flash
from database import execute_query

incharge_bp = Blueprint('incharge', __name__, url_prefix='/incharge')


@incharge_bp.route('/dashboard')
def dashboard():
    if session.get('role') != 'Department Incharge':
        flash('Access denied. Please log in as a Department Incharge.')
        return redirect(url_for('auth.login'))

    department_id = session.get('department_id')
    if not department_id:
        flash('No department associated with your account.')
        return redirect(url_for('auth.login'))

    # Fetch department details, number of faculty, and number of courses
    department_details = execute_query("SELECT department_name FROM departments WHERE department_id = %s", (department_id,))
    faculty_count = execute_query("SELECT COUNT(*) AS count FROM users WHERE department_id = %s AND (role = 'Faculty' OR role = 'Department Incharge')", (department_id,))
    course_count = execute_query("SELECT COUNT(*) AS count FROM courses WHERE department_id = %s", (department_id,))

    dashboard_data = {
        'department_name': department_details.get('department_name') if department_details else 'N/A',
        'faculty_count': faculty_count[0]['count'] if faculty_count else 0,
        'course_count': course_count[0]['count'] if course_count else 0,
    }

    return render_template('incharge/dashboard.html', dashboard_data=dashboard_data)


@incharge_bp.route('/view_department_faculty')
def view_department_faculty():
    if session.get('role') != 'Department Incharge':
        flash('Access denied. Please log in as a Department Incharge.')
        return redirect(url_for('auth.login'))

    department_id = session.get('department_id')
    if not department_id:
        flash('Department not found for your account.')
        return redirect(url_for('incharge.dashboard'))

    query = """
    SELECT u.user_id, u.name, u.email, u.role
    FROM users u
    JOIN faculty f ON u.user_id = f.user_id
    WHERE u.department_id = %s
    ORDER BY u.name
    """
    faculty_members = execute_query(query, (department_id,))

    return render_template('incharge/view_department_faculty.html', faculty_members=faculty_members)

@incharge_bp.route('/view_department_courses')
def view_department_courses():
    if session.get('role') != 'Department Incharge':
        flash('Access denied. Please log in as a Department Incharge.')
        return redirect(url_for('auth.login'))

    department_id = session.get('department_id')
    if not department_id:
        flash('Department not found for your account.')
        return redirect(url_for('incharge.dashboard'))

    query = """
    SELECT c.course_id, c.course_name
    FROM courses c
    WHERE c.department_id = %s
    ORDER BY c.course_name
    """
    courses = execute_query(query, (department_id,))

    return render_template('incharge/view_department_courses.html', courses=courses)

@incharge_bp.route('/view_assignments')
def view_assignments():
    if session.get('role') != 'Department Incharge':
        flash('Access denied. Please log in as a Department Incharge.')
        return redirect(url_for('auth.login'))

    department_id = session.get('department_id')
    if not department_id:
        flash('No department associated with your account.')
        return redirect(url_for('incharge.dashboard'))

    # Fetch assignments of faculty to courses within the department
    query = """
    SELECT c.course_name, u.name AS faculty_name
    FROM courses c
    LEFT JOIN faculty_courses fc ON c.course_id = fc.course_id
    LEFT JOIN faculty f ON fc.faculty_id = f.faculty_id
    LEFT JOIN users u ON f.user_id = u.user_id
    WHERE c.department_id = %s
    ORDER BY c.course_name
    """
    assignments = execute_query(query, (department_id,))

    return render_template('incharge/view_assignments.html', assignments=assignments)

@incharge_bp.route('/assign_faculty', methods=['GET', 'POST'])
def assign_faculty():
    if session.get('role') != 'Department Incharge':
        flash('Access denied. Please log in as a Department Incharge.')
        return redirect(url_for('auth.login'))

    department_id = session.get('department_id')
    if not department_id:
        flash('No department associated with your account.')
        return redirect(url_for('incharge.dashboard'))

    if request.method == 'POST':
        faculty_id = request.form.get('faculty_id')
        course_id = request.form.get('course_id')

        # Validate faculty and course are within the same department and not already assigned
        faculty_exists = execute_query("SELECT COUNT(*) FROM faculty WHERE faculty_id = %s AND department_id = %s", (faculty_id, department_id))[0]
        course_exists = execute_query("SELECT COUNT(*) FROM courses WHERE course_id = %s AND department_id = %s", (course_id, department_id))[0]
        already_assigned = execute_query("SELECT COUNT(*) FROM faculty_courses WHERE faculty_id = %s AND course_id = %s", (faculty_id, course_id))[0]

        if faculty_exists and course_exists and not already_assigned:
            execute_query("INSERT INTO faculty_courses (faculty_id, course_id) VALUES (%s, %s)", (faculty_id, course_id), commit=True)
            flash('Faculty successfully assigned to course.')
            return redirect(url_for('incharge.view_assignments'))
        else:
            flash('Invalid assignment or already exists.')

    # Fetch faculties and courses for selection
    faculties = execute_query("SELECT f.faculty_id, u.name FROM faculty f JOIN users u ON f.user_id = u.user_id WHERE f.department_id = %s", (department_id,))
    courses = execute_query("SELECT course_id, course_name FROM courses WHERE department_id = %s", (department_id,))

    return render_template('incharge/assign_faculty.html', faculties=faculties, courses=courses)

@incharge_bp.route('/reassign_faculty/<int:assignment_id>', methods=['GET', 'POST'])
def reassign_faculty(assignment_id):
    if session.get('role') != 'Department Incharge':
        flash('Access denied. Please log in as a Department Incharge.')
        return redirect(url_for('auth.login'))

    department_id = session.get('department_id')
    if not department_id:
        flash('No department associated with your account.')
        return redirect(url_for('incharge.dashboard'))

    assignment_details = execute_query(
        "SELECT fc.id as assignment_id, f.faculty_id, c.course_id, u.name as faculty_name, c.course_name "
        "FROM faculty_courses fc "
        "JOIN faculty f ON fc.faculty_id = f.faculty_id "
        "JOIN courses c ON fc.course_id = c.course_id "
        "JOIN users u ON f.user_id = u.user_id "
        "WHERE fc.id = %s AND f.department_id = %s", 
        (assignment_id, department_id), fetch_one=True)

    if not assignment_details:
        flash('Assignment not found.')
        return redirect(url_for('incharge.view_assignments'))

    if request.method == 'POST':
        new_course_id = request.form.get('course_id')

        # Validate the new course is within the same department and not already assigned to the faculty
        course_exists = execute_query("SELECT COUNT(*) FROM courses WHERE course_id = %s AND department_id = %s", (new_course_id, department_id))[0]
        already_assigned = execute_query("SELECT COUNT(*) FROM faculty_courses WHERE faculty_id = %s AND course_id = %s", (assignment_details['faculty_id'], new_course_id))[0]

        if course_exists and not already_assigned:
            execute_query("UPDATE faculty_courses SET course_id = %s WHERE id = %s", (new_course_id, assignment_id), commit=True)
            flash('Faculty successfully reassigned to new course.')
            return redirect(url_for('incharge.view_assignments'))
        else:
            flash('Invalid course selection or faculty already assigned.')

    # Fetch courses for selection excluding the current course to avoid reassigning to the same course
    courses = execute_query("SELECT course_id, course_name FROM courses WHERE department_id = %s AND course_id != %s", (department_id, assignment_details['course_id']))

    return render_template('incharge/reassign_faculty.html', assignment_details=assignment_details, courses=courses)


@incharge_bp.route('/view_schedule')
def view_schedule():
    if session.get('role') != 'Department Incharge':
        flash('Access denied. Please log in as a Department Incharge.')
        return redirect(url_for('auth.login'))

    department_id = session.get('department_id')
    if not department_id:
        flash('No department associated with your account.')
        return redirect(url_for('incharge.dashboard'))

    # Fetch the schedule including course details, faculty name, and assigned class times and rooms
    query = """
    SELECT sc.id AS schedule_id, c.course_name, u.name AS faculty_name, sc.class_time, sc.room
    FROM schedule sc
    JOIN courses c ON sc.course_id = c.course_id
    JOIN faculty f ON sc.faculty_id = f.faculty_id
    JOIN users u ON f.user_id = u.user_id
    WHERE c.department_id = %s
    ORDER BY sc.class_time
    """
    schedule = execute_query(query, (department_id,))

    return render_template('incharge/view_schedule.html', schedule=schedule)

@incharge_bp.route('/create_schedule', methods=['GET', 'POST'])
def create_schedule():
    if session.get('role') != 'Department Incharge':
        flash('Access denied. Please log in as a Department Incharge.')
        return redirect(url_for('auth.login'))

    department_id = session.get('department_id')
    if not department_id:
        flash('No department associated with your account.')
        return redirect(url_for('incharge.dashboard'))

    if request.method == 'POST':
        course_id = request.form.get('course_id')
        faculty_id = request.form.get('faculty_id')
        class_time = request.form.get('class_time')
        room = request.form.get('room')

        # Ensure the selected faculty and course belong to the Department Incharge's department
        # and validate other business logic as needed
        faculty_belongs = execute_query("SELECT COUNT(*) FROM faculty WHERE user_id = %s AND department_id = %s", (faculty_id, department_id))[0]
        course_belongs = execute_query("SELECT COUNT(*) FROM courses WHERE course_id = %s AND department_id = %s", (course_id, department_id))[0]

        if faculty_belongs and course_belongs:
            execute_query("INSERT INTO schedule (course_id, faculty_id, class_time, room) VALUES (%s, %s, %s, %s)", (course_id, faculty_id, class_time, room), commit=True)
            flash('Schedule created successfully.')
            return redirect(url_for('incharge.view_schedule'))
        else:
            flash('Faculty or course does not belong to your department.')

    # Fetch courses and faculties for the selection options in the form
    courses = execute_query("SELECT course_id, course_name FROM courses WHERE department_id = %s", (department_id,))
    faculties = execute_query("SELECT f.user_id, u.name FROM faculty f JOIN users u ON f.user_id = u.user_id WHERE f.department_id = %s", (department_id,))

    return render_template('incharge/create_schedule.html', courses=courses, faculties=faculties)

@incharge_bp.route('/update_schedule/<int:schedule_id>', methods=['GET', 'POST'])
def update_schedule(schedule_id):
    if session.get('role') != 'Department Incharge':
        flash('Access denied. Please log in as a Department Incharge.')
        return redirect(url_for('auth.login'))

    department_id = session.get('department_id')
    if not department_id:
        flash('No department associated with your account.')
        return redirect(url_for('incharge.dashboard'))

    schedule_details = execute_query("SELECT * FROM schedule WHERE id = %s AND department_id = %s", (schedule_id, department_id), fetch_one=True)
    if not schedule_details:
        flash('Schedule not found.')
        return redirect(url_for('incharge.view_schedule'))

    if request.method == 'POST':
        course_id = request.form.get('course_id')
        faculty_id = request.form.get('faculty_id')
        class_time = request.form.get('class_time')
        room = request.form.get('room')

        # Validate faculty and course are within the same department
        faculty_belongs = execute_query("SELECT COUNT(*) FROM faculty WHERE user_id = %s AND department_id = %s", (faculty_id, department_id))[0]
        course_belongs = execute_query("SELECT COUNT(*) FROM courses WHERE course_id = %s AND department_id = %s", (course_id, department_id))[0]

        if faculty_belongs and course_belongs:
            execute_query("UPDATE schedule SET course_id = %s, faculty_id = %s, class_time = %s, room = %s WHERE id = %s", (course_id, faculty_id, class_time, room, schedule_id), commit=True)
            flash('Schedule updated successfully.')
            return redirect(url_for('incharge.view_schedule'))
        else:
            flash('Faculty or course does not belong to your department.')

    courses = execute_query("SELECT course_id, course_name FROM courses WHERE department_id = %s", (department_id,))
    faculties = execute_query("SELECT f.user_id, u.name FROM faculty f JOIN users u ON f.user_id = u.user_id WHERE f.department_id = %s", (department_id,))

    return render_template('incharge/update_schedule.html', schedule=schedule_details, courses=courses, faculties=faculties)

@incharge_bp.route('/delete_schedule/<int:schedule_id>', methods=['POST'])
def delete_schedule(schedule_id):
    if session.get('role') != 'Department Incharge':
        flash('Access denied. Please log in as a Department Incharge.')
        return redirect(url_for('auth.login'))

    department_id = session.get('department_id')
    if not department_id:
        flash('No department associated with your account.')
        return redirect(url_for('incharge.dashboard'))

    schedule_exists = execute_query("SELECT COUNT(*) FROM schedule WHERE id = %s AND department_id = %s", (schedule_id, department_id))[0]

    if schedule_exists:
        execute_query("DELETE FROM schedule WHERE id = %s", (schedule_id,), commit=True)
        flash('Schedule deleted successfully.')
    else:
        flash('Schedule not found or does not belong to your department.')

    return redirect(url_for('incharge.view_schedule'))

@incharge_bp.route('/view_adjustment_requests')
def view_adjustment_requests():
    if session.get('role') != 'Department Incharge':
        flash('Access denied. Please log in as a Department Incharge.')
        return redirect(url_for('auth.login'))

    department_id = session.get('department_id')
    if not department_id:
        flash('No department associated with your account.')
        return redirect(url_for('incharge.dashboard'))

    # Fetch adjustment requests related to the department
    query = """
    SELECT ar.request_id, ar.status, ar.request_date, ar.response_date,
           f.name AS from_faculty_name, t.name AS to_faculty_name,
           c.course_name, r.room_number
    FROM adjustment_requests ar
    JOIN faculty f ON ar.from_faculty_id = f.faculty_id
    JOIN faculty t ON ar.to_faculty_id = t.faculty_id
    JOIN courses c ON ar.course_id = c.course_id
    JOIN rooms r ON ar.room_id = r.room_id
    WHERE c.department_id = %s
    ORDER BY ar.request_date DESC
    """
    adjustment_requests = execute_query(query, (department_id,))

    return render_template('incharge/view_adjustment_requests.html', adjustment_requests=adjustment_requests)

@incharge_bp.route('/approve_adjustment_request/<int:request_id>', methods=['POST'])
def approve_adjustment_request(request_id):
    if session.get('role') != 'Department Incharge':
        flash('Access denied. Please log in as a Department Incharge.')
        return redirect(url_for('auth.login'))

    department_id = session.get('department_id')
    if not department_id:
        flash('No department associated with your account.')
        return redirect(url_for('incharge.dashboard'))

    # Fetch the adjustment request to ensure it belongs to the incharge's department
    query = """
    SELECT ar.request_id
    FROM adjustment_requests ar
    JOIN courses c ON ar.course_id = c.course_id
    WHERE ar.request_id = %s AND c.department_id = %s
    """
    request_exists = execute_query(query, (request_id, department_id))

    if not request_exists:
        flash('Adjustment request not found or not under your department.')
        return redirect(url_for('incharge.view_adjustment_requests'))

    # Approve the adjustment request
    update_query = """
    UPDATE adjustment_requests
    SET status = 'Approved', response_date = CURRENT_DATE()
    WHERE request_id = %s
    """
    execute_query(update_query, (request_id,), commit=True)

    flash('Adjustment request approved successfully.')
    return redirect(url_for('incharge.view_adjustment_requests'))

@incharge_bp.route('/reject_adjustment_request/<int:request_id>', methods=['POST'])
def reject_adjustment_request(request_id):
    if session.get('role') != 'Department Incharge':
        flash('Access denied. Please log in as a Department Incharge.')
        return redirect(url_for('auth.login'))

    department_id = session.get('department_id')
    if not department_id:
        flash('No department associated with your account.')
        return redirect(url_for('incharge.dashboard'))

    # Fetch the adjustment request to ensure it belongs to the incharge's department
    query = """
    SELECT ar.request_id
    FROM adjustment_requests ar
    JOIN courses c ON ar.course_id = c.course_id
    WHERE ar.request_id = %s AND c.department_id = %s
    """
    request_exists = execute_query(query, (request_id, department_id))

    if not request_exists:
        flash('Adjustment request not found or not under your department.')
        return redirect(url_for('incharge.view_adjustment_requests'))

    # Reject the adjustment request
    update_query = """
    UPDATE adjustment_requests
    SET status = 'Rejected', response_date = CURRENT_DATE()
    WHERE request_id = %s
    """
    execute_query(update_query, (request_id,), commit=True)

    flash('Adjustment request rejected successfully.')
    return redirect(url_for('incharge.view_adjustment_requests'))

@incharge_bp.route('/view_course_completion_reports')
def view_course_completion_reports():
    if session.get('role') != 'Department Incharge':
        flash('Access denied. Please log in as a Department Incharge.')
        return redirect(url_for('auth.login'))

    department_id = session.get('department_id')
    if not department_id:
        flash('No department associated with your account.')
        return redirect(url_for('incharge.dashboard'))

    # Fetch course completion rates within the department
    query = """
    SELECT c.course_name, 
           COUNT(*) AS total_students,
           SUM(CASE WHEN s.status = 'Completed' THEN 1 ELSE 0 END) AS completed_students
    FROM courses c
    LEFT JOIN student_courses s ON c.course_id = s.course_id
    WHERE c.department_id = %s
    GROUP BY c.course_name
    ORDER BY c.course_name
    """
    course_completion = execute_query(query, (department_id,))

    return render_template('incharge/view_course_completion_reports.html', course_completion=course_completion)

# @incharge_bp.route('/view_faculty_performance_reports')
# def view_faculty_performance_reports():
#     if session.get('role') != 'Department Incharge':
#         flash('Access denied. Please log in as a Department Incharge.')
#         return redirect(url_for('auth.login'))

#     department_id = session.get('department_id')
#     if not department_id:
#         flash('No department associated with your account.')
#         return redirect(url_for('incharge.dashboard'))

#     # Fetch faculty performance data within the department
#     query = """
#     SELECT u.name AS faculty_name, 
#            COUNT(c.course_id) AS total_courses,
#            AVG(sc.performance_rating) AS average_performance_rating
#     FROM faculty f
#     JOIN users u ON f.user_id = u.user_id
#     LEFT JOIN faculty_courses fc ON f.faculty_id = fc.faculty_id
#     LEFT JOIN courses c ON fc.course_id = c.course_id
#     LEFT JOIN student_courses sc ON c.course_id = sc.course_id
#     WHERE f.department_id = %s
#     GROUP BY u.name
#     ORDER BY average_performance_rating DESC
#     """
#     faculty_performance = execute_query(query, (department_id,))

#     return render_template('incharge/view_faculty_performance_reports.html', faculty_performance=faculty_performance)

@incharge_bp.route('/view_faculty_performance_reports')
def view_faculty_performance_reports():
    if session.get('role') != 'Department Incharge':
        flash('Access denied. Please log in as a Department Incharge.')
        return redirect(url_for('auth.login'))

    department_id = session.get('department_id')
    if not department_id:
        flash('No department associated with your account.')
        return redirect(url_for('incharge.dashboard'))

    # Fetch faculty performance data within the department
    query = """
    SELECT u.name AS faculty_name, 
           COUNT(c.course_id) AS total_courses,
           AVG(sc.performance_rating) AS average_performance_rating
    FROM faculty f
    JOIN users u ON f.user_id = u.user_id
    LEFT JOIN faculty_courses fc ON f.faculty_id = fc.faculty_id
    LEFT JOIN courses c ON fc.course_id = c.course_id
    LEFT JOIN student_courses sc ON c.course_id = sc.course_id
    WHERE f.department_id = %s
    GROUP BY u.name
    ORDER BY average_performance_rating DESC
    """
    faculty_performance = execute_query(query, (department_id,))

    return render_template('incharge/view_faculty_performance_reports.html', faculty_performance=faculty_performance)


@incharge_bp.route('/view_invigilation_schedule')
def view_invigilation_schedule():
    if session.get('role') != 'Department Incharge':
        flash('Access denied. Please log in as a Department Incharge.')
        return redirect(url_for('auth.login'))

    department_id = session.get('department_id')
    if not department_id:
        flash('No department associated with your account.')
        return redirect(url_for('incharge.dashboard'))

    # Fetch the invigilation schedule for the department
    query = """
    SELECT is.schedule_id, c.course_name, u.name AS faculty_name, is.date, is.time, r.room_number
    FROM invigilation_schedule is
    JOIN courses c ON is.course_id = c.course_id
    JOIN faculty f ON is.faculty_id = f.faculty_id
    JOIN users u ON f.user_id = u.user_id
    JOIN rooms r ON is.room_id = r.room_id
    WHERE c.department_id = %s
    ORDER BY is.date, is.time
    """
    invigilation_schedule = execute_query(query, (department_id,))

    return render_template('incharge/view_invigilation_schedule.html', invigilation_schedule=invigilation_schedule)

@incharge_bp.route('/assign_invigilation_duty', methods=['GET', 'POST'])
def assign_invigilation_duty():
    if session.get('role') != 'Department Incharge':
        flash('Access denied. Please log in as a Department Incharge.')
        return redirect(url_for('auth.login'))

    department_id = session.get('department_id')
    if not department_id:
        flash('No department associated with your account.')
        return redirect(url_for('incharge.dashboard'))

    if request.method == 'POST':
        faculty_id = request.form.get('faculty_id')
        course_id = request.form.get('course_id')
        date = request.form.get('date')
        time = request.form.get('time')
        room_id = request.form.get('room_id')

        # Validate the faculty, course, and room belong to the department
        faculty_belongs = execute_query("SELECT COUNT(*) FROM faculty WHERE faculty_id = %s AND department_id = %s", (faculty_id, department_id))[0]
        course_belongs = execute_query("SELECT COUNT(*) FROM courses WHERE course_id = %s AND department_id = %s", (course_id, department_id))[0]
        room_belongs = execute_query("SELECT COUNT(*) FROM rooms WHERE room_id = %s AND department_id = %s", (room_id, department_id))[0]

        if faculty_belongs and course_belongs and room_belongs:
            execute_query("INSERT INTO invigilation_schedule (faculty_id, course_id, date, time, room_id) VALUES (%s, %s, %s, %s, %s)", (faculty_id, course_id, date, time, room_id), commit=True)
            flash('Invigilation duty assigned successfully.')
            return redirect(url_for('incharge.view_invigilation_schedule'))
        else:
            flash('Invalid data or entities do not belong to your department.')

    faculties = execute_query("SELECT faculty_id, name FROM faculty WHERE department_id = %s", (department_id,))
    courses = execute_query("SELECT course_id, course_name FROM courses WHERE department_id = %s", (department_id,))
    rooms = execute_query("SELECT room_id, room_number FROM rooms WHERE department_id = %s", (department_id,))

    return render_template('incharge/assign_invigilation_duty.html', faculties=faculties, courses=courses, rooms=rooms)

@incharge_bp.route('/update_invigilation_duty/<int:duty_id>', methods=['GET', 'POST'])
def update_invigilation_duty(duty_id):
    if session.get('role') != 'Department Incharge':
        flash('Access denied. Please log in as a Department Incharge.')
        return redirect(url_for('auth.login'))

    department_id = session.get('department_id')
    if not department_id:
        flash('No department associated with your account.')
        return redirect(url_for('incharge.dashboard'))

    invigilation_duty = execute_query("SELECT * FROM invigilation_schedule WHERE id = %s AND department_id = %s", (duty_id, department_id), fetch_one=True)
    if not invigilation_duty:
        flash('Invigilation duty not found.')
        return redirect(url_for('incharge.view_invigilation_schedule'))

    if request.method == 'POST':
        faculty_id = request.form.get('faculty_id')
        course_id = request.form.get('course_id')
        date = request.form.get('date')
        time = request.form.get('time')
        room_id = request.form.get('room_id')

        # Validate the faculty, course, and room belong to the department
        faculty_belongs = execute_query("SELECT COUNT(*) FROM faculty WHERE faculty_id = %s AND department_id = %s", (faculty_id, department_id))[0]
        course_belongs = execute_query("SELECT COUNT(*) FROM courses WHERE course_id = %s AND department_id = %s", (course_id, department_id))[0]
        room_belongs = execute_query("SELECT COUNT(*) FROM rooms WHERE room_id = %s AND department_id = %s", (room_id, department_id))[0]

        if faculty_belongs and course_belongs and room_belongs:
            execute_query("UPDATE invigilation_schedule SET faculty_id = %s, course_id = %s, date = %s, time = %s, room_id = %s WHERE id = %s", (faculty_id, course_id, date, time, room_id, duty_id), commit=True)
            flash('Invigilation duty updated successfully.')
            return redirect(url_for('incharge.view_invigilation_schedule'))
        else:
            flash('Invalid data or entities do not belong to your department.')

    faculties = execute_query("SELECT faculty_id, name FROM faculty WHERE department_id = %s", (department_id,))
    courses = execute_query("SELECT course_id, course_name FROM courses WHERE department_id = %s", (department_id,))
    rooms = execute_query("SELECT room_id, room_number FROM rooms WHERE department_id = %s", (department_id,))

    return render_template('incharge/update_invigilation_duty.html', duty=invigilation_duty, faculties=faculties, courses=courses, rooms=rooms)

@incharge_bp.route('/delete_invigilation_duty/<int:duty_id>', methods=['POST'])
def delete_invigilation_duty(duty_id):
    if session.get('role') != 'Department Incharge':
        flash('Access denied. Please log in as a Department Incharge.')
        return redirect(url_for('auth.login'))

    department_id = session.get('department_id')
    if not department_id:
        flash('No department associated with your account.')
        return redirect(url_for('incharge.dashboard'))

    # Ensure the invigilation duty exists and belongs to the Department Incharge's department
    duty_exists = execute_query("SELECT COUNT(*) FROM invigilation_schedule WHERE id = %s AND department_id = %s", (duty_id, department_id))[0]

    if duty_exists:
        execute_query("DELETE FROM invigilation_schedule WHERE id = %s", (duty_id,), commit=True)
        flash('Invigilation duty deleted successfully.')
    else:
        flash('Invigilation duty not found or does not belong to your department.')

    return redirect(url_for('incharge.view_invigilation_schedule'))
