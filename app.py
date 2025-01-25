from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'super_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/profile_pics/'

def init_db():
    conn = sqlite3.connect('database.db')
    conn.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER, birthdate TEXT, profile_pic TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS travel_records (id INTEGER PRIMARY KEY, user_id INTEGER, reason TEXT, observation TEXT, value REAL)')
    conn.close()

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def do_login():
    username = request.form['username']
    password = request.form['password']
    if username == 'DUJAO22' and password == '20E10':
        session['user'] = 'admin'
        return redirect(url_for('admin'))
    else:
        # Check if the user exists in the database
        conn = sqlite3.connect('database.db')
        user = conn.execute('SELECT * FROM users WHERE name = ?', (username,)).fetchone()
        conn.close()
        if user:
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
        age = request.form['age']
        birthdate = request.form['birthdate']
        profile_pic = 'default_user.png'  # Default profile picture
        conn = sqlite3.connect('database.db')
        conn.execute('INSERT INTO users (name, age, birthdate, profile_pic) VALUES (?, ?, ?, ?)', (name, age, birthdate, profile_pic))
        conn.commit()
        conn.close()
        return redirect(url_for('admin'))
    else:
        return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
