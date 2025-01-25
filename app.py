from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'super_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/profile_pics/'

def init_db():
    conn = sqlite3.connect('database.db')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT,
            login TEXT UNIQUE,
            password TEXT,
            age INTEGER,
            birthdate TEXT,
            profile_pic TEXT
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS travel_records (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            reason TEXT,
            observation TEXT,
            value REAL
        )
    ''')
    conn.close()

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def do_login():
    login = request.form['login']
    password = request.form['password']
    if login == 'DUJAO22' and password == '20E10':
        session['user'] = 'admin'
        return redirect(url_for('admin'))
    else:
        conn = sqlite3.connect('database.db')
        user = conn.execute('SELECT * FROM users WHERE login = ?', (login,)).fetchone()
        conn.close()
        if user and check_password_hash(user[3], password):
            session['user'] = user[0]
            return redirect(url_for('user', user_id=user[0]))
        else:
            return redirect(url_for('login'))

@app.route('/admin')
def admin():
    if 'user' in session and session['user'] == 'admin':
        conn = sqlite3.connect('database.db')
        users = conn.execute('SELECT * FROM users').fetchall()
        conn.close()
        return render_template('admin.html', users=users)
    else:
        return redirect(url_for('login'))

@app.route('/user/<int:user_id>')
def user(user_id):
    if 'user' in session and session['user'] == user_id:
        conn = sqlite3.connect('database.db')
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        records = conn.execute('SELECT * FROM travel_records WHERE user_id = ?', (user_id,)).fetchall()
        conn.close()
        return render_template('user.html', user=user, records=records)
    else:
        return redirect(url_for('login'))

@app.route('/edit_profile/<int:user_id>', methods=['POST'])
def edit_profile(user_id):
    if 'user' in session and session['user'] == user_id:
        name = request.form['name']
        age = request.form['age']
        birthdate = request.form['birthdate']
        conn = sqlite3.connect('database.db')
        conn.execute('UPDATE users SET name = ?, age = ?, birthdate = ? WHERE id = ?', (name, age, birthdate, user_id))
        conn.commit()
        conn.close()
        return redirect(url_for('user', user_id=user_id))
    else:
        return redirect(url_for('login'))

@app.route('/upload_photo/<int:user_id>', methods=['POST'])
def upload_photo(user_id):
    if 'user' in session and session['user'] == user_id:
        file = request.files['profile_pic']
        if file:
            filename = f'{user_id}.png'
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            conn = sqlite3.connect('database.db')
            conn.execute('UPDATE users SET profile_pic = ? WHERE id = ?', (filename, user_id))
            conn.commit()
            conn.close()
        return redirect(url_for('user', user_id=user_id))
    else:
        return redirect(url_for('login'))

@app.route('/add_record/<int:user_id>', methods=['POST'])
def add_record(user_id):
    if 'user' in session and session['user'] == user_id:
        reason = request.form['reason']
        observation = request.form['observation']
        value = request.form['value']
        conn = sqlite3.connect('database.db')
        conn.execute('INSERT INTO travel_records (user_id, reason, observation, value) VALUES (?, ?, ?, ?)', (user_id, reason, observation, value))
        conn.commit()
        conn.close()
        return redirect(url_for('user', user_id=user_id))
    else:
        return redirect(url_for('login'))

@app.route('/add_user', methods=['POST'])
def add_user():
    if 'user' in session and session['user'] == 'admin':
        name = request.form['name']
        login = request.form['login']
        password = request.form['password']
        age = request.form['age']
        birthdate = request.form['birthdate']
        
        # Verificação dos campos obrigatórios
        if not name or not login or not password or not age or not birthdate:
            return redirect(url_for('admin', error='Todos os campos são obrigatórios'))

        hashed_password = generate_password_hash(password)
        profile_pic = 'default_user.png'  # Default profile picture

        try:
            conn = sqlite3.connect('database.db')
            conn.execute('INSERT INTO users (name, login, password, age, birthdate, profile_pic) VALUES (?, ?, ?, ?, ?, ?)', 
                         (name, login, hashed_password, age, birthdate, profile_pic))
            conn.commit()
            conn.close()
        except sqlite3.IntegrityError:
            return redirect(url_for('admin', error='Login já existe'))
        
        return redirect(url_for('admin'))
    else:
        return redirect(url_for('login'))

@app.route('/end_record/<int:user_id>', methods=['POST'])
def end_record(user_id):
    if 'user' in session and session['user'] == user_id:
        conn = sqlite3.connect('database.db')
        records = conn.execute('SELECT * FROM travel_records WHERE user_id = ?', (user_id,)).fetchall()
        total_value = sum(record[4] for record in records)
        conn.execute('DELETE FROM travel_records WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
        return render_template('report.html', records=records, total_value=total_value)
    else:
        return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
