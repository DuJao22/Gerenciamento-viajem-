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
        # Aqui você pode adicionar lógica de autenticação
        return redirect(url_for('dashboard'))
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

@app.route('/dashboard')
def dashboard():
    # Supondo que o usuário logado tenha ID 1
    user_id = 1
    conn = sqlite3.connect('database.db')
    user = conn.execute('SELECT * FROM usuarios WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    return render_template('dashboard.html', user=user)

@app.route('/inicio_viagem', methods=['GET', 'POST'])
def inicio_viagem():
    if request.method == 'POST':
        user_id = 1  # Supondo que o usuário logado tenha ID 1
        numero_nota = request.form['numero_nota']
        destino = request.form['destino']
        data_inicio = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = sqlite3.connect('database.db')
        conn.execute('INSERT INTO viagens (usuario_id, numero_nota, destino, data_inicio, finalizada) VALUES (?, ?, ?, ?, ?)', (user_id, numero_nota, destino, data_inicio, False))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))
    return render_template('inicio_viagem.html')

@app.route('/registrar', methods=['GET', 'POST'])
def registrar():
    if request.method == 'POST':
        viagem_id = 1  # Supondo que a viagem ativa tenha ID 1
        motivo = request.form['motivo']
        observacao = request.form['observacao']
        valor = request.form['valor']
        conn = sqlite3.connect('database.db')
        conn.execute('INSERT INTO gastos (viagem_id, motivo, observacao, valor) VALUES (?, ?, ?, ?)', (viagem_id, motivo, observacao, valor))
        conn.commit()
        conn.close()
        return redirect(url_for('registrar'))
    conn = sqlite3.connect('database.db')
    gastos = conn.execute('SELECT * FROM gastos WHERE viagem_id = 1').fetchall()  # Supondo que a viagem ativa tenha ID 1
    conn.close()
    return render_template('registrar.html', gastos=gastos)

@app.route('/finalizar')
def finalizar():
    conn = sqlite3.connect('database.db')
    conn.execute('UPDATE viagens SET finalizada = ? WHERE id = ?', (True, 1))  # Supondo que a viagem ativa tenha ID 1
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
