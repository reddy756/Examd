from flask import Blueprint, render_template, session, redirect, url_for, flash
from database import execute_query

faculty_bp = Blueprint('faculty', __name__, url_prefix='/faculty')

@faculty_bp.route('/dashboard')
def dashboard():
    if session.get('role') != 'Faculty':
        flash('Access denied. Please log in as a Faculty member.')
        return redirect(url_for('auth.login'))

    faculty_id = session.get('user_id')
    if not faculty_id:
        flash('Faculty ID not found in session.')
        return redirect(url_for('auth.login'))

    # Fetch count of courses the faculty is teaching
    course_count_query = """
    SELECT COUNT(*) AS course_count
    FROM faculty_courses fc
    JOIN courses c ON fc.course_id = c.course_id
    WHERE fc.faculty_id = %s
    """
    course_count = execute_query(course_count_query, (faculty_id,))[0]['course_count']

    # Fetch next invigilation duty
    invigilation_query = """
    SELECT e.exam_name, e.exam_date, e.exam_time, r.room_number
    FROM invigilation_duty i
    JOIN exams e ON i.exam_id = e.exam_id
    JOIN rooms r ON i.room_id = r.room_id
    WHERE i.faculty_id = %s
    ORDER BY e.exam_date, e.exam_time
    LIMIT 1
    """
    next_invigilation = execute_query(invigilation_query, (faculty_id,))

    # Fetch next teaching schedule
    teaching_query = """
    SELECT c.course_name, s.class_time, s.room
    FROM schedule s
    JOIN courses c ON s.course_id = c.course_id
    WHERE s.faculty_id = %s
    ORDER BY s.class_time
    LIMIT 1
    """
    next_teaching = execute_query(teaching_query, (faculty_id,))

    dashboard_data = {
        'course_count': course_count,
        'next_invigilation': next_invigilation,
        'next_teaching': next_teaching
    }

    return render_template('faculty/dashboard.html', dashboard_data=dashboard_data)


@faculty_bp.route('/view_personal_schedule')
def view_personal_schedule():
    if session.get('role') != 'Faculty':
        flash('Access denied. Please log in as a Faculty member.')
        return redirect(url_for('auth.login'))

    faculty_id = session.get('user_id')
    if not faculty_id:
        flash('Faculty ID not found in session.')
        return redirect(url_for('auth.login'))

    # Fetch teaching schedule
    teaching_query = """
    SELECT c.course_name, s.class_time, s.room
    FROM schedule s
    JOIN courses c ON s.course_id = c.course_id
    WHERE s.faculty_id = %s
    ORDER BY s.class_time
    """
    teaching_schedule = execute_query(teaching_query, (faculty_id,))

    # Fetch invigilation schedule
    invigilation_query = """
    SELECT e.exam_name, e.exam_date, e.exam_time, r.room_number
    FROM invigilation_duty i
    JOIN exams e ON i.exam_id = e.exam_id
    JOIN rooms r ON i.room_id = r.room_id
    WHERE i.faculty_id = %s
    ORDER BY e.exam_date, e.exam_time
    """
    invigilation_schedule = execute_query(invigilation_query, (faculty_id,))

    return render_template('faculty/view_personal_schedule.html', teaching_schedule=teaching_schedule, invigilation_schedule=invigilation_schedule)

@faculty_bp.route('/view_personal_info')
def view_personal_info():
    if session.get('role') != 'Faculty':
        flash('Access denied. Please log in as a Faculty member.')
        return redirect(url_for('auth.login'))

    faculty_id = session.get('user_id')
    if not faculty_id:
        flash('Faculty ID not found in session.')
        return redirect(url_for('faculty.dashboard'))

    # Fetch personal information of the faculty member
    query = """
    SELECT u.name, u.email, f.qualifications, f.research_interests
    FROM users u
    JOIN faculty f ON u.user_id = f.user_id
    WHERE u.user_id = %s
    """
    personal_info = execute_query(query, (faculty_id,), fetch_one=True)

    if not personal_info:
        flash('Personal information not found.')
        return redirect(url_for('faculty.dashboard'))

    return render_template('faculty/view_personal_info.html', personal_info=personal_info)

@faculty_bp.route('/edit_personal_info', methods=['GET', 'POST'])
def edit_personal_info():
    if session.get('role') != 'Faculty':
        flash('Access denied. Please log in as a Faculty member.')
        return redirect(url_for('auth.login'))

    faculty_id = session.get('user_id')
    if not faculty_id:
        flash('Faculty ID not found in session.')
        return redirect(url_for('faculty.dashboard'))

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        qualifications = request.form.get('qualifications')
        research_interests = request.form.get('research_interests')

        # Update personal information in the database
        update_query = """
        UPDATE users u
        JOIN faculty f ON u.user_id = f.user_id
        SET u.name = %s, u.email = %s, f.qualifications = %s, f.research_interests = %s
        WHERE u.user_id = %s
        """
        execute_query(update_query, (name, email, qualifications, research_interests, faculty_id), commit=True)

        flash('Personal information updated successfully.')
        return redirect(url_for('faculty.dashboard'))

    # Fetch current personal information to populate the form
    query = """
    SELECT u.name, u.email, f.qualifications, f.research_interests
    FROM users u
    JOIN faculty f ON u.user_id = f.user_id
    WHERE u.user_id = %s
    """
    personal_info = execute_query(query, (faculty_id,), fetch_one=True)

    return render_template('faculty/edit_personal_info.html', personal_info=personal_info)

@faculty_bp.route('/update_personal_info', methods=['POST'])
def update_personal_info():
    if session.get('role') != 'Faculty':
        flash('Access denied. Please log in as a Faculty member.')
        return redirect(url_for('auth.login'))

    faculty_id = session.get('user_id')
    if not faculty_id:
        flash('Faculty ID not found in session.')
        return redirect(url_for('faculty.dashboard'))

    name = request.form.get('name')
    email = request.form.get('email')
    qualifications = request.form.get('qualifications')
    research_interests = request.form.get('research_interests')

    # Update personal information in the database
    update_query = """
    UPDATE users u
    JOIN faculty f ON u.user_id = f.user_id
    SET u.name = %s, u.email = %s, f.qualifications = %s, f.research_interests = %s
    WHERE u.user_id = %s
    """
    execute_query(update_query, (name, email, qualifications, research_interests, faculty_id), commit=True)

    flash('Personal information updated successfully.')
    return redirect(url_for('faculty.dashboard'))

@faculty_bp.route('/request_adjustment', methods=['GET'])
def request_adjustment():
    if session.get('role') != 'Faculty':
        flash('Access denied. Please log in as a Faculty member.')
        return redirect(url_for('auth.login'))

    faculty_id = session.get('user_id')
    if not faculty_id:
        flash('Faculty ID not found in session.')
        return redirect(url_for('faculty.dashboard'))

    # Fetch relevant data for the form, like courses and exam schedules
    courses_query = """
    SELECT c.course_id, c.course_name
    FROM faculty_courses fc
    JOIN courses c ON fc.course_id = c.course_id
    WHERE fc.faculty_id = %s
    """
    courses = execute_query(courses_query, (faculty_id,))

    exams_query = """
    SELECT e.exam_id, e.exam_name, e.exam_date
    FROM invigilation_duty i
    JOIN exams e ON i.exam_id = e.exam_id
    WHERE i.faculty_id = %s
    ORDER BY e.exam_date
    """
    exams = execute_query(exams_query, (faculty_id,))

    return render_template('faculty/request_adjustment.html', courses=courses, exams=exams)

@faculty_bp.route('/submit_adjustment_request', methods=['POST'])
def submit_adjustment_request():
    if session.get('role') != 'Faculty':
        flash('Access denied. Please log in as a Faculty member.')
        return redirect(url_for('auth.login'))

    faculty_id = session.get('user_id')
    if not faculty_id:
        flash('Faculty ID not found in session.')
        return redirect(url_for('faculty.dashboard'))

    # Get form data
    course_id = request.form.get('course_id')
    exam_id = request.form.get('exam_id')
    reason = request.form.get('reason')

    # Perform validation and check if the faculty is actually associated with the course and exam
    is_valid_course = execute_query("SELECT COUNT(*) FROM faculty_courses WHERE faculty_id = %s AND course_id = %s", (faculty_id, course_id))[0]
    is_valid_exam = execute_query("SELECT COUNT(*) FROM invigilation_duty WHERE faculty_id = %s AND exam_id = %s", (faculty_id, exam_id))[0]

    if not is_valid_course or not is_valid_exam:
        flash('Invalid course or exam selection.')
        return redirect(url_for('faculty.request_adjustment'))

    # Insert adjustment request into the database
    insert_query = """
    INSERT INTO adjustment_requests (faculty_id, course_id, exam_id, reason, status)
    VALUES (%s, %s, %s, %s, 'Pending')
    """
    execute_query(insert_query, (faculty_id, course_id, exam_id, reason), commit=True)

    flash('Adjustment request submitted successfully.')
    return redirect(url_for('faculty.view_personal_schedule'))

@faculty_bp.route('/view_adjustment_requests')
def view_adjustment_requests():
    if session.get('role') != 'Faculty':
        flash('Access denied. Please log in as a Faculty member.')
        return redirect(url_for('auth.login'))

    faculty_id = session.get('user_id')
    if not faculty_id:
        flash('Faculty ID not found in session.')
        return redirect(url_for('faculty.dashboard'))

    # Fetch adjustment requests made by the faculty member
    query = """
    SELECT ar.request_id, ar.status, ar.request_date, ar.response_date, 
           c.course_name, e.exam_name, ar.reason
    FROM adjustment_requests ar
    JOIN faculty f ON ar.faculty_id = f.faculty_id
    JOIN courses c ON ar.course_id = c.course_id
    JOIN exams e ON ar.exam_id = e.exam_id
    WHERE ar.faculty_id = %s
    ORDER BY ar.request_date DESC
    """
    adjustment_requests = execute_query(query, (faculty_id,))

    return render_template('faculty/view_adjustment_requests.html', adjustment_requests=adjustment_requests)

@faculty_bp.route('/view_student_performance')
def view_student_performance():
    if session.get('role') != 'Faculty':
        flash('Access denied. Please log in as a Faculty member.')
        return redirect(url_for('auth.login'))

    faculty_id = session.get('user_id')
    if not faculty_id:
        flash('Faculty ID not found in session.')
        return redirect(url_for('faculty.dashboard'))

    # Fetch courses taught by the faculty
    courses_query = """
    SELECT c.course_id, c.course_name
    FROM faculty_courses fc
    JOIN courses c ON fc.course_id = c.course_id
    WHERE fc.faculty_id = %s
    """
    courses = execute_query(courses_query, (faculty_id,))

    # Collect performance data for each course
    performance_data = []
    for course in courses:
        course_id = course['course_id']
        performance_query = """
        SELECT s.student_id, st.name AS student_name, sc.grade, sc.attendance
        FROM student_courses sc
        JOIN students st ON sc.student_id = st.student_id
        WHERE sc.course_id = %s
        """
        course_performance = execute_query(performance_query, (course_id,))
        performance_data.append({
            'course_name': course['course_name'],
            'performance': course_performance
        })

    return render_template('faculty/view_student_performance.html', performance_data=performance_data)


@faculty_bp.route('/analyze_student_feedback')
def analyze_student_feedback():
    if session.get('role') != 'Faculty':
        flash('Access denied. Please log in as a Faculty member.')
        return redirect(url_for('auth.login'))

    faculty_id = session.get('user_id')
    if not faculty_id:
        flash('Faculty ID not found in session.')
        return redirect(url_for('faculty.dashboard'))

    # Fetch courses taught by the faculty to analyze feedback
    courses_query = """
    SELECT c.course_id, c.course_name
    FROM faculty_courses fc
    JOIN courses c ON fc.course_id = c.course_id
    WHERE fc.faculty_id = %s
    """
    courses = execute_query(courses_query, (faculty_id,))

    feedback_data = []
    for course in courses:
        course_id = course['course_id']
        feedback_query = """
        SELECT sf.feedback, sf.rating
        FROM student_feedback sf
        WHERE sf.course_id = %s
        """
        feedbacks = execute_query(feedback_query, (course_id,))
        feedback_data.append({
            'course_name': course['course_name'],
            'feedbacks': feedbacks
        })

    return render_template('faculty/analyze_student_feedback.html', feedback_data=feedback_data)
