from flask import Flask,render_template
from key import secret_key
from auth import auth_bp
from admin import admin_bp
from incharge import incharge_bp
from faculty import faculty_bp
from database import execute_query

app = Flask(__name__)
app.config['SECRET_KEY'] = secret_key
app.config['SESSION_TYPE'] = 'FILESYSTEM'

@app.route('/')
def index():
    execute_query("update users set Role='Faculty' where user_id in (SELECT u.user_id FROM (SELECT name, user_id,department_id FROM users WHERE role != 'Admin') AS u LEFT JOIN departments d ON u.user_id != d.incharge_user_id where u.department_id=d.department_id)",commit=True)
    return render_template('index.html')

# Registering blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(incharge_bp)
app.register_blueprint(faculty_bp)

if __name__ == "__main__":
    app.run(debug=True)