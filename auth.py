from flask import Blueprint,redirect,url_for,render_template,request,flash,session,abort,jsonify
from key import salt,salt2
from ctokens import generate_otp,create_token,verify_token
from database import execute_query
from sendmail import send_email
import werkzeug.security as bcrypt

auth_bp = Blueprint('auth',__name__,url_prefix='/auth')

@auth_bp.route('/dept_course/<int:dept_id>')
def get_courses_by_department(dept_id):
    courses = execute_query("SELECT course_id, course_name FROM courses WHERE department_id = %s", (dept_id,))
    return jsonify(courses)

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    role_dashboard_map = {"Admin": 'admin.dashboard', "Department Incharge": 'incharge.dashboard', "Faculty": 'faculty.dashboard'}
    if 'role' in session and session['role'] in role_dashboard_map:
        flash("You've Already Logged in")
        return redirect(url_for(role_dashboard_map[session['role']]))

    departments = execute_query("SELECT department_id, department_name FROM departments")
    if request.method == 'POST':
        name = request.form.get('name', None).strip()
        email = request.form.get('email', None).strip()
        password = request.form.get('password', None).strip()
        role = request.form.get('role', None).strip()
        hashed_password = bcrypt.generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)
        department_id = request.form.get('department_id','Null')
        course_id = request.form.get('course_id','Null')
        otp = generate_otp()
        data = {'Name': name, 'Email': email, 'Password': hashed_password, 'OTP': otp, 'Role': role,'Department_id': department_id, 'Course_id': course_id}
        print(role)
        # Handling for Admin role
        if role == 'Admin':
            admin_count = execute_query("SELECT COUNT(*) as count FROM users WHERE role=%s", ('Admin',), fetch_one=True)
            print(admin_count)
            if admin_count['count'] == 1:
                flash('An admin already exists. Only one admin is allowed.')
                return redirect(url_for('auth.signup'))

        # Handling for Department Incharge and Faculty roles
        if role in ['Department Incharge', 'Faculty']:
            # For Department Incharge, check if an incharge already exists
            if role == 'Department Incharge':
                incharge_count = execute_query("SELECT COUNT(*) as count FROM departments WHERE department_id=%s AND incharge_user_id IS NOT NULL", (department_id,), fetch_one=True)
                if incharge_count['count'] == 1:
                    flash('Incharge already assigned for this department.')
                    return redirect(url_for('auth.signup'))

        email_count = execute_query("SELECT COUNT(*) as count FROM users WHERE email=%s", (email,), fetch_one=True)['count']
        if email_count == 1:
            flash('Email Already Exists!')
            return redirect(url_for('auth.signup'))

        subject = 'Verify your OTP to Sign In'
        body = f'Dear User,\nPlease use the following One Time Password (OTP) to complete your verification process:\n{otp}'
        send_email(receiver_email=email, subject=subject, body=body)

        flash('OTP sent to mail! Verify your OTP.')
        return redirect(url_for('auth.otp', token=create_token(data, salt=salt)))
    else:
        return render_template('auth/signup.html', departments=departments)

@auth_bp.route('/otp/<token>', methods=['GET', 'POST'])
def otp(token):
    data = verify_token(token, salt=salt, expiration=600)
    if data:
        # print(data)
        if request.method == 'POST':
            uotp = request.form.get('otp')
            if data['OTP'] == uotp:
                try:
                    user_exists = execute_query("SELECT COUNT(*) as count FROM users WHERE email=%s", (data['Email'],), fetch_one=True)['count']
                    if user_exists == 1:
                        flash('User Already Registered! Please Login to Continue.')
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
                except Exception as e:
                    print(e)
                    return 'Something Happened! Check the server logs.'
            else:
                flash('OTP not matched!')
                return render_template('auth/otp.html', token=token)
        else:
            return render_template('auth/otp.html', token=token)
    else:
        flash('OTP Expired')
        return redirect(url_for('auth.signup'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    role_dashboard_map = {"Admin": 'admin.dashboard',"Department Incharge": 'incharge.dashboard',"Faculty": 'faculty.dashboard'}

    if 'role' in session and session['role'] in role_dashboard_map:
        return redirect(url_for(role_dashboard_map[session['role']]))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        try:
            user = execute_query("SELECT user_id, password_hash, role FROM users WHERE email=%s", (email,), fetch_one=True)

            if user and bcrypt.check_password_hash(user['password_hash'], password):
                session['user_id'] = user['user_id']
                session['role'] = user['role']
                
                flash('Login successful')
                return redirect(url_for(role_dashboard_map[user['role']]))
            else:
                flash('Invalid email or password')
                return redirect(url_for('auth.login'))
        except Exception as e:
            print(e)
            return "Something happened! Check the server logs."
    else:
        return render_template('auth/login.html')

@auth_bp.route('/forget', methods=['GET', 'POST'])
def forget():
    if request.method == 'POST':
        email = request.form.get('email').strip()

        try:
            user = execute_query("SELECT email FROM users WHERE email = %s", (email,), fetch_one=True)

            if user:
                token_url = url_for('verify', token=create_token({'email': email}, salt=salt2), _external=True)
                subject = 'Password Reset Link'
                body = f'Dear User,\nPlease use the following link to reset your password:\n{token_url}'

                send_email(receiver_email=email, subject=subject, body=body)
                flash('Reset link has been sent to your email.')
                return redirect(url_for('auth.login'))
            else:
                flash('User not registered or invalid email')
                return render_template('auth/forget.html')
        except Exception as e:
            print(e)
            return 'Something happened! Check the server logs.'
    else:
        return render_template('auth/forget.html')

@auth_bp.route('/verify/<token>', methods=['GET', 'POST'])
def verify(token):
    email_data = verify_token(token=token, salt=salt2, expiration=600)
    
    if email_data:
        email = email_data['email']
        if request.method == 'POST':
            new_password = request.form.get('npassword')
            confirm_password = request.form.get('cpassword')

            if new_password == confirm_password:
                try:
                    hashed_password = bcrypt.generate_password_hash(new_password, method='pbkdf2:sha256', salt_length=16)
                    execute_query("UPDATE users SET password_hash = %s WHERE email = %s", (hashed_password, email), commit=True)
                    flash("Password reset successful")
                    return redirect(url_for('auth.login'))
                except Exception as e:
                    print(e)
                    return 'Something happened! Check the server logs.'
            else:
                flash('Passwords do not match')
                return render_template('auth/verify.html', token=token)
        else:
            return render_template('auth/verify.html', token=token)
    else:
        flash('Link expired or invalid')
        return redirect(url_for('auth.forget'))

