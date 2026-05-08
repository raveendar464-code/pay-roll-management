from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "secret123"

# ---------- DATABASE ----------
def init_db():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute('''
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT,
        basic REAL
    )
    ''')

    cur.execute("PRAGMA table_info(employees)")
    existing_columns = [row[1] for row in cur.fetchall()]
    if "password" not in existing_columns:
        cur.execute("ALTER TABLE employees ADD COLUMN password TEXT")

    conn.commit()
    conn.close()

def parse_basic(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0

init_db()

# ---------- LOGIN ----------
@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        role = request.form.get('role', 'admin')
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if role == 'admin':
            if username == 'admin' and password == 'admin':
                session.clear()
                session['user'] = 'admin'
                session['role'] = 'admin'
                return redirect('/dashboard')
            error = 'Admin username or password is incorrect.'
        else:
            conn = sqlite3.connect("database.db")
            cur = conn.cursor()
            cur.execute("SELECT * FROM employees WHERE email=? AND password=?", (username, password))
            user = cur.fetchone()
            conn.close()

            if user:
                session.clear()
                session['user'] = user[1]
                session['role'] = 'staff'
                session['emp_id'] = user[0]
                return redirect('/staff_dashboard')
            error = 'Employee email or password is incorrect.'

    return render_template('login.html', error=error)


# ---------- ADMIN DASHBOARD ----------
@app.route('/dashboard')
def dashboard():
    if session.get('role') != 'admin':
        return redirect('/')

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM employees")
    employees = cur.fetchall()
    conn.close()

    return render_template('dashboard.html', employees=employees)


# ---------- ADD EMPLOYEE ----------
@app.route('/add', methods=['GET', 'POST'])
def add_employee():
    if session.get('role') != 'admin':
        return redirect('/')

    error = None
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        basic_raw = request.form.get('basic', '').strip()

        if not name or not email or not password:
            error = 'Name, email, and password are required.'
        else:
            try:
                basic_value = float(basic_raw) if basic_raw else 0.0
            except ValueError:
                error = 'Basic salary must be a number.'
                basic_value = None

        if error is None:
            try:
                conn = sqlite3.connect("database.db")
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO employees (name,email,password,basic) VALUES (?,?,?,?)",
                    (name, email, password, basic_value)
                )
                conn.commit()
                conn.close()
                return redirect('/dashboard')
            except sqlite3.IntegrityError:
                conn.close()
                error = 'This email is already registered. Use a different email.'

    return render_template('add_employee.html', error=error)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error = None
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        basic_raw = request.form.get('basic', '').strip()

        if not name or not email or not password:
            error = 'Name, email, and password are required.'
        else:
            basic_value = 0.0
            if basic_raw:
                try:
                    basic_value = float(basic_raw)
                except ValueError:
                    error = 'Basic salary must be a number.'

        if error is None:
            conn = sqlite3.connect("database.db")
            cur = conn.cursor()
            try:
                cur.execute(
                    "INSERT INTO employees (name,email,password,basic) VALUES (?,?,?,?)",
                    (name, email, password, basic_value)
                )
                conn.commit()
                conn.close()
                return redirect('/')
            except sqlite3.IntegrityError:
                conn.close()
                error = 'This email is already registered. Use a different email.'

    return render_template('signup.html', error=error)


# ---------- ADMIN PAYSLIP ----------
@app.route('/payslip/<int:id>')
def payslip(id):
    if session.get('role') != 'admin':
        return redirect('/')

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM employees WHERE id=?", (id,))
    emp = cur.fetchone()
    conn.close()

    if not emp:
        return "Employee not found"

    basic = parse_basic(emp[4])
    hra = basic * 0.20
    da = basic * 0.10
    gross = basic + hra + da
    tax = gross * 0.05
    net = gross - tax

    return render_template('payslip.html',
                           emp=emp,
                           hra=hra,
                           da=da,
                           gross=gross,
                           tax=tax,
                           net=net)


# ---------- STAFF DASHBOARD ----------
@app.route('/staff_dashboard')
def staff_dashboard():
    if session.get('role') != 'staff':
        return redirect('/')

    emp_id = session.get('emp_id')

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM employees WHERE id=?", (emp_id,))
    emp = cur.fetchone()
    conn.close()

    basic = parse_basic(emp[4])
    hra = basic * 0.20
    da = basic * 0.10
    gross = basic + hra + da
    tax = gross * 0.05
    net = gross - tax

    return render_template('staff_dashboard.html',
                           emp=emp,
                           hra=hra,
                           da=da,
                           gross=gross,
                           tax=tax,
                           net=net)


# ---------- LOGOUT ----------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True)