from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'super_secret_key'

def init_db():
    conn = sqlite3.connect('database.db')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY,
            nome TEXT,
            idade INTEGER,
            data_nascimento TEXT
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS viagens (
            id INTEGER PRIMARY KEY,
            usuario_id INTEGER,
            numero_nota TEXT,
            destino TEXT,
            data_inicio TEXT,
            finalizada BOOLEAN,
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS gastos (
            id INTEGER PRIMARY KEY,
            viagem_id INTEGER,
            motivo TEXT,
            observacao TEXT,
            valor REAL,
            FOREIGN KEY(viagem_id) REFERENCES viagens(id)
        )
    ''')
    conn.close()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nome = request.form['login']
        conn = sqlite3.connect('database.db')
        user = conn.execute('SELECT * FROM usuarios WHERE nome = ?', (nome,)).fetchone()
        conn.close()
        if user:
            session['user_id'] = user[0]
            return redirect(url_for('dashboard'))
        else:
            flash('Usuário não encontrado')
    return render_template('login.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    conn = sqlite3.connect('database.db')
    if request.method == 'POST':
        nome = request.form['nome']
        idade = request.form['idade']
        data_nascimento = request.form['data_nascimento']
        conn.execute('INSERT INTO usuarios (nome, idade, data_nascimento) VALUES (?, ?, ?)', (nome, idade, data_nascimento))
        conn.commit()
    usuarios = conn.execute('SELECT * FROM usuarios').fetchall()
    conn.close()
    return render_template('admin.html', usuarios=usuarios)

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    if request.method == 'POST':
        numero_nota = request.form['numero_nota']
        destino = request.form.get('destino', '')
        data_inicio = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = sqlite3.connect('database.db')
        conn.execute('INSERT INTO viagens (usuario_id, numero_nota, destino, data_inicio, finalizada) VALUES (?, ?, ?, ?, ?)', (user_id, numero_nota, destino, data_inicio, False))
        conn.commit()
        conn.close()
        return redirect(url_for('viagem', numero_nota=numero_nota))

    conn = sqlite3.connect('database.db')
    user = conn.execute('SELECT * FROM usuarios WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    return render_template('dashboard.html', user=user)

@app.route('/viagem/<numero_nota>', methods=['GET', 'POST'])
def viagem(numero_nota):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    conn = sqlite3.connect('database.db')
    viagem_id = conn.execute('SELECT id FROM viagens WHERE numero_nota = ? AND usuario_id = ?', (numero_nota, user_id)).fetchone()[0]

    if request.method == 'POST':
        if 'registrar' in request.form:
            motivo = request.form['motivo']
            observacao = request.form['observacao']
            valor = request.form['valor']
            conn.execute('INSERT INTO gastos (viagem_id, motivo, observacao, valor) VALUES (?, ?, ?, ?)', (viagem_id, motivo, observacao, valor))
        elif 'finalizar' in request.form:
            conn.execute('UPDATE viagens SET finalizada = ? WHERE id = ?', (True, viagem_id))
        conn.commit()

    gastos = conn.execute('SELECT * FROM gastos WHERE viagem_id = ?', (viagem_id,)).fetchall()
    conn.close()
    return render_template('viagem.html', numero_nota=numero_nota, gastos=gastos)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
