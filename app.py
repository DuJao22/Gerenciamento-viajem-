from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
import psycopg2
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'super_secret_key'

DATABASE_URL = "postgresql://database_shki_user:m0QsRSe6eUWAj70RuxAUJzmcj2dymZoO@dpg-cud3bjd6l47c7385qecg-a/database_shki"

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            nome TEXT,
            idade INTEGER,
            data_nascimento TEXT,
            login TEXT UNIQUE,
            senha TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS viagens (
            id SERIAL PRIMARY KEY,
            usuario_id INTEGER,
            numero_nota TEXT,
            destino TEXT,
            data_inicio TEXT,
            finalizada BOOLEAN,
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gastos (
            id SERIAL PRIMARY KEY,
            viagem_id INTEGER,
            motivo TEXT,
            observacao TEXT,
            valor REAL,
            FOREIGN KEY(viagem_id) REFERENCES viagens(id)
        )
    ''')
    conn.commit()
    cursor.close()
    conn.close()

def generate_report(viagem_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM viagens WHERE id = %s', (viagem_id,))
    viagem = cursor.fetchone()
    cursor.execute('SELECT * FROM gastos WHERE viagem_id = %s', (viagem_id,))
    gastos = cursor.fetchall()
    cursor.execute('SELECT * FROM usuarios WHERE id = %s', (viagem[1],))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    total_gastos = sum(gasto[4] for gasto in gastos)

    report_content = f"""
Relatorio de Viagem
===================
Usuario: {user[1]}
Idade: {user[2]}
Data de Nascimento: {user[3]}

Viagem
------
Nota: {viagem[2]}
Destino: {viagem[3]}
Data de Inicio: {viagem[4]}
Finalizada: {"Sim" if viagem[5] else "Não"}

Gastos
------
"""
    for gasto in gastos:
        report_content += f"""
Motivo: {gasto[2]}
Observacao: {gasto[3]}
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
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM usuarios WHERE login = %s AND senha = %s', (login, senha))
            user = cursor.fetchone()
            cursor.close()
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
        conn = get_db_connection()
        cursor = conn.cursor()
        if request.method == 'POST':
            nome = request.form['nome']
            idade = request.form['idade']
            data_nascimento = request.form['data_nascimento']
            login = request.form['login']
            senha = request.form['senha']
            cursor.execute('INSERT INTO usuarios (nome, idade, data_nascimento, login, senha) VALUES (%s, %s, %s, %s, %s)', (nome, idade, data_nascimento, login, senha))
            conn.commit()
        cursor.execute('SELECT * FROM usuarios')
        usuarios = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('admin.html', usuarios=usuarios)
    else:
        return redirect(url_for('login'))

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' in session:
        user_id = session['user_id']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM usuarios WHERE id = %s', (user_id,))
        user = cursor.fetchone()
        
        # Check for an ongoing trip
        cursor.execute('SELECT * FROM viagens WHERE usuario_id = %s AND finalizada = 0', (user_id,))
        viagem = cursor.fetchone()

        if viagem:
            if request.method == 'POST':
                if 'registrar' in request.form:
                    motivo = request.form['motivo']
                    observacao = request.form['observacao']
                    valor = request.form['valor']
                    cursor.execute('INSERT INTO gastos (viagem_id, motivo, observacao, valor) VALUES (%s, %s, %s, %s)', (viagem[0], motivo, observacao, valor))
                    conn.commit()
                elif 'finalizar' in request.form:
                    cursor.execute('UPDATE viagens SET finalizada = 1 WHERE id = %s', (viagem[0],))
                    conn.commit()
                    report_path = generate_report(viagem[0])
                    return redirect(url_for('download_report', viagem_id=viagem[0]))

            cursor.execute('SELECT * FROM gastos WHERE viagem_id = %s', (viagem[0],))
            gastos = cursor.fetchall()
            cursor.close()
            conn.close()
            return render_template('dashboard.html', user=user, viagem=viagem, gastos=gastos)
        else:
            cursor.close()
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
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('INSERT INTO viagens (usuario_id, numero_nota, destino, data_inicio, finalizada) VALUES (%s, %s, %s, %s, %s)', (user_id, numero_nota, destino, data_inicio, False))
            conn.commit()
            cursor.close()
            conn.close()
            return redirect(url_for('dashboard'))
        return render_template('inicio_viagem.html')
    else:
        return redirect(url_for('login'))

@app.route('/finalizar_viagem/<int:viagem_id>', methods=['POST'])
def finalizar_viagem(viagem_id):
    if 'user_id' in session:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE viagens SET finalizada = 1 WHERE id = %s', (viagem_id,))
        conn.commit()
        cursor.close()
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
