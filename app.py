from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'super_secret_key'

def init_db():
    conn = sqlite3.connect('database.db')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY,
            nome TEXT,
            idade INTEGER,
            data_nascimento TEXT,
            login TEXT UNIQUE,
            senha TEXT
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

def generate_report(viagem_id):
    conn = sqlite3.connect('database.db')
    viagem = conn.execute('SELECT * FROM viagens WHERE id = ?', (viagem_id,)).fetchone()
    gastos = conn.execute('SELECT * FROM gastos WHERE viagem_id = ?', (viagem_id,)).fetchall()
    user = conn.execute('SELECT * FROM usuarios WHERE id = ?', (viagem[1],)).fetchone()
    conn.close()

    total_gastos = sum(gasto[4] for gasto in gastos)

    report_content = f"""
    Relatório de Viagem
    ===================
    Usuário: {user[1]}
    Idade: {user[2]}
    Data de Nascimento: {user[3]}
    
    Viagem
    ------
    Nota: {viagem[2]}
    Destino: {viagem[3]}
    Data de Início: {viagem[4]}
    Finalizada: {viagem[5]}
    
    Gastos
    ------
    """
    for gasto in gastos:
        report_content += f"""
        Motivo: {gasto[2]}
        Observação: {gasto[3]}
        Valor: {gasto[4]}
        """

    report_content += f"\nTotal dos Gastos: {total_gastos}\n"

    report_path = f'report_viagem_{viagem_id}.txt'
    with open(report_path, 'w', encoding='utf-8') as report_file:
        report_file.write(report_content)
    
    return report_path

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login = request.form['login']
        senha = request.form['senha']
        if login == 'DUJAO22' and senha == '20E10':
            session['user'] = 'admin'
            return redirect(url_for('admin'))
        else:
            conn = sqlite3.connect('database.db')
            user = conn.execute('SELECT * FROM usuarios WHERE login = ? AND senha = ?', (login, senha)).fetchone()
            conn.close()
            if user:
                session['user_id'] = user[0]
                return redirect(url_for('dashboard'))
            else:
                flash('Login ou senha incorretos')
    return render_template('login.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'user' in session and session['user'] == 'admin':
        conn = sqlite3.connect('database.db')
        if request.method == 'POST':
            nome = request.form['nome']
            idade = request.form['idade']
            data_nascimento = request.form['data_nascimento']
            login = request.form['login']
            senha = request.form['senha']
            conn.execute('INSERT INTO usuarios (nome, idade, data_nascimento, login, senha) VALUES (?, ?, ?, ?, ?)', (nome, idade, data_nascimento, login, senha))
            conn.commit()
        usuarios = conn.execute('SELECT * FROM usuarios').fetchall()
        conn.close()
        return render_template('admin.html', usuarios=usuarios)
    else:
        return redirect(url_for('login'))

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' in session:
        user_id = session['user_id']
        conn = sqlite3.connect('database.db')
        user = conn.execute('SELECT * FROM usuarios WHERE id = ?', (user_id,)).fetchone()
        
        # Check for an ongoing trip
        viagem = conn.execute('SELECT * FROM viagens WHERE usuario_id = ? AND finalizada = 0', (user_id,)).fetchone()

        if viagem:
            if request.method == 'POST':
                if 'registrar' in request.form:
                    motivo = request.form['motivo']
                    observacao = request.form['observacao']
                    valor = request.form['valor']
                    conn.execute('INSERT INTO gastos (viagem_id, motivo, observacao, valor) VALUES (?, ?, ?, ?)', (viagem[0], motivo, observacao, valor))
                    conn.commit()
                elif 'finalizar' in request.form:
                    conn.execute('UPDATE viagens SET finalizada = 1 WHERE id = ?', (viagem[0],))
                    conn.commit()
                    report_path = generate_report(viagem[0])
                    return redirect(url_for('download_report', viagem_id=viagem[0]))

            gastos = conn.execute('SELECT * FROM gastos WHERE viagem_id = ?', (viagem[0],)).fetchall()
            conn.close()
            return render_template('dashboard.html', user=user, viagem=viagem, gastos=gastos)
        else:
            conn.close()
            return render_template('dashboard.html', user=user, viagem=None)
    else:
        return redirect(url_for('login'))

@app.route('/inicio_viagem', methods=['GET', 'POST'])
def inicio_viagem():
    if 'user_id' in session:
        user_id = session['user_id']
        if request.method == 'POST':
            numero_nota = request.form['numero_nota']
            destino = request.form['destino']
            data_inicio = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn = sqlite3.connect('database.db')
            conn.execute('INSERT INTO viagens (usuario_id, numero_nota, destino, data_inicio, finalizada) VALUES (?, ?, ?, ?, ?)', (user_id, numero_nota, destino, data_inicio, False))
            conn.commit()
            conn.close()
            return redirect(url_for('dashboard'))
        return render_template('inicio_viagem.html')
    else:
        return redirect(url_for('login'))

@app.route('/finalizar_viagem/<int:viagem_id>', methods=['POST'])
def finalizar_viagem(viagem_id):
    if 'user_id' in session:
        conn = sqlite3.connect('database.db')
        conn.execute('UPDATE viagens SET finalizada = 1 WHERE id = ?', (viagem_id,))
        conn.commit()
        conn.close()
        report_path = generate_report(viagem_id)
        return redirect(url_for('download_report', viagem_id=viagem_id))
    else:
        return redirect(url_for('login'))

@app.route('/download_report/<int:viagem_id>')
def download_report(viagem_id):
    report_path = f'report_viagem_{viagem_id}.txt'
    if os.path.exists(report_path):
        return send_file(report_path, as_attachment=True)
    else:
        flash('Relatório não encontrado')
        return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('user_id', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
