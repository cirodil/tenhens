from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import sqlite3
import hashlib
import os
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from scipy import stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

app = Flask(__name__, static_folder='../frontend/build', static_url_path='')
CORS(app)

# Конфигурация JWT
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
jwt = JWTManager(app)

# Настройки базы данных
DB_NAME = "/app/data/egg_database.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Таблица для записей о яйценоскости
    c.execute('''CREATE TABLE IF NOT EXISTS eggs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  date TEXT,
                  count INTEGER,
                  notes TEXT)''')
                  
    # Таблица пользователей с простой регистрацией (без telegram_id)
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE,
                  password TEXT,
                  security_question TEXT,
                  security_answer TEXT,
                  created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
    
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# ==================== AUTH ENDPOINTS ====================

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '')
    security_question = data.get('security_question', '').strip()
    security_answer = data.get('security_answer', '').strip().lower()
    
    if not all([username, password, security_question, security_answer]):
        return jsonify({'error': 'Все поля обязательны для заполнения'}), 400
    
    if len(password) < 6:
        return jsonify({'error': 'Пароль должен быть не менее 6 символов'}), 400
    
    conn = get_db_connection()
    try:
        hashed_password = hash_password(password)
        hashed_answer = hash_password(security_answer)
        conn.execute(
            "INSERT INTO users (username, password, security_question, security_answer) VALUES (?, ?, ?, ?)",
            (username, hashed_password, security_question, hashed_answer)
        )
        conn.commit()
        return jsonify({'message': 'Аккаунт успешно создан!'}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Пользователь с таким именем уже существует'}), 409
    finally:
        conn.close()

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if not all([username, password]):
        return jsonify({'error': 'Введите имя пользователя и пароль'}), 400
    
    conn = get_db_connection()
    user = conn.execute(
        "SELECT id, username, password FROM users WHERE username = ?",
        (username,)
    ).fetchone()
    conn.close()
    
    if user and hash_password(password) == user['password']:
        access_token = create_access_token(identity={'id': user['id'], 'username': user['username']})
        return jsonify({
            'access_token': access_token,
            'user': {'id': user['id'], 'username': user['username']}
        }), 200
    
    return jsonify({'error': 'Неверные учетные данные'}), 401

@app.route('/api/auth/me', methods=['GET'])
@jwt_required()
def get_current_user():
    current_user = get_jwt_identity()
    return jsonify({'user': current_user}), 200

@app.route('/api/auth/recovery-question', methods=['POST'])
def get_recovery_question():
    data = request.json
    username = data.get('username', '').strip()
    
    conn = get_db_connection()
    user = conn.execute(
        "SELECT security_question FROM users WHERE username = ?",
        (username,)
    ).fetchone()
    conn.close()
    
    if user:
        return jsonify({'security_question': user['security_question']}), 200
    return jsonify({'error': 'Пользователь не найден'}), 404

@app.route('/api/auth/reset-password', methods=['POST'])
def reset_password():
    data = request.json
    username = data.get('username', '').strip()
    security_answer = data.get('security_answer', '').strip().lower()
    new_password = data.get('new_password', '')
    
    if not all([username, security_answer, new_password]):
        return jsonify({'error': 'Все поля обязательны для заполнения'}), 400
    
    if len(new_password) < 6:
        return jsonify({'error': 'Пароль должен быть не менее 6 символов'}), 400
    
    conn = get_db_connection()
    user = conn.execute(
        "SELECT id, security_answer FROM users WHERE username = ?",
        (username,)
    ).fetchone()
    
    if user and hash_password(security_answer) == user['security_answer']:
        hashed_password = hash_password(new_password)
        conn.execute("UPDATE users SET password = ? WHERE username = ?", (hashed_password, username))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Пароль успешно изменен!'}), 200
    
    conn.close()
    return jsonify({'error': 'Неверный ответ на секретный вопрос'}), 401

# ==================== EGG RECORDS ENDPOINTS ====================

@app.route('/api/records', methods=['GET'])
@jwt_required()
def get_records():
    current_user = get_jwt_identity()
    user_id = current_user['id']
    
    # Параметры фильтрации
    min_date = request.args.get('min_date')
    max_date = request.args.get('max_date')
    search_notes = request.args.get('search_notes', '')
    
    conn = get_db_connection()
    
    query = "SELECT id, date, count, notes FROM eggs WHERE user_id = ?"
    params = [user_id]
    
    if min_date:
        query += " AND date >= ?"
        params.append(min_date)
    if max_date:
        query += " AND date <= ?"
        params.append(max_date)
    
    query += " ORDER BY date DESC, id DESC"
    
    records = conn.execute(query, params).fetchall()
    conn.close()
    
    # Фильтрация по заметкам на стороне Python
    if search_notes:
        records = [r for r in records if search_notes.lower() in (r['notes'] or '').lower()]
    
    return jsonify({
        'records': [dict(r) for r in records]
    }), 200

@app.route('/api/records', methods=['POST'])
@jwt_required()
def add_record():
    current_user = get_jwt_identity()
    user_id = current_user['id']
    data = request.json
    
    date = data.get('date')
    count = data.get('count', 0)
    notes = data.get('notes', '')
    
    if not date:
        return jsonify({'error': 'Дата обязательна'}), 400
    
    conn = get_db_connection()
    cursor = conn.execute(
        "INSERT INTO eggs (user_id, date, count, notes) VALUES (?, ?, ?, ?)",
        (user_id, date, count, notes)
    )
    conn.commit()
    record_id = cursor.lastrowid
    conn.close()
    
    return jsonify({
        'message': 'Запись успешно добавлена!',
        'record': {'id': record_id, 'date': date, 'count': count, 'notes': notes}
    }), 201

@app.route('/api/records/<int:record_id>', methods=['PUT'])
@jwt_required()
def update_record(record_id):
    current_user = get_jwt_identity()
    user_id = current_user['id']
    data = request.json
    
    conn = get_db_connection()
    record = conn.execute(
        "SELECT * FROM eggs WHERE id = ? AND user_id = ?",
        (record_id, user_id)
    ).fetchone()
    
    if not record:
        conn.close()
        return jsonify({'error': 'Запись не найдена'}), 404
    
    updates = []
    params = []
    
    if 'count' in data:
        updates.append("count = ?")
        params.append(data['count'])
    if 'date' in data:
        updates.append("date = ?")
        params.append(data['date'])
    if 'notes' in data:
        updates.append("notes = ?")
        params.append(data['notes'])
    
    if updates:
        query = f"UPDATE eggs SET {', '.join(updates)} WHERE id = ?"
        params.append(record_id)
        conn.execute(query, params)
        conn.commit()
    
    conn.close()
    return jsonify({'message': 'Запись успешно обновлена!'}), 200

@app.route('/api/records/<int:record_id>', methods=['DELETE'])
@jwt_required()
def delete_record(record_id):
    current_user = get_jwt_identity()
    user_id = current_user['id']
    
    conn = get_db_connection()
    record = conn.execute(
        "SELECT * FROM eggs WHERE id = ? AND user_id = ?",
        (record_id, user_id)
    ).fetchone()
    
    if not record:
        conn.close()
        return jsonify({'error': 'Запись не найдена'}), 404
    
    conn.execute("DELETE FROM eggs WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Запись успешно удалена!'}), 200

# ==================== STATISTICS ENDPOINTS ====================

@app.route('/api/stats', methods=['GET'])
@jwt_required()
def get_stats():
    current_user = get_jwt_identity()
    user_id = current_user['id']
    days = int(request.args.get('days', 7))
    
    conn = get_db_connection()
    start_date = (datetime.now() - timedelta(days=days-1)).strftime("%Y-%m-%d")
    
    data = conn.execute(
        '''SELECT date, SUM(count) as total
           FROM eggs
           WHERE user_id = ? AND date >= ?
           GROUP BY date
           ORDER BY date''',
        (user_id, start_date)
    ).fetchall()
    conn.close()
    
    return jsonify({
        'stats': [{'date': row['date'], 'count': row['total']} for row in data]
    }), 200

@app.route('/api/analytics', methods=['GET'])
@jwt_required()
def get_analytics():
    current_user = get_jwt_identity()
    user_id = current_user['id']
    days = int(request.args.get('days', 7))
    
    conn = get_db_connection()
    all_data = conn.execute(
        '''SELECT date, count, notes FROM eggs 
           WHERE user_id = ? 
           ORDER BY date''',
        (user_id,)
    ).fetchall()
    conn.close()
    
    if not all_data or len(all_data) < 2:
        return jsonify({'analytics': None}), 200
    
    df = pd.DataFrame(all_data, columns=['date', 'count', 'notes'])
    
    if len(df) < days:
        days = len(df)
    
    current_data = df.tail(days)
    
    if len(df) >= days * 2:
        previous_data = df.iloc[-days*2:-days]
    else:
        previous_data = df.iloc[:-days] if len(df) > days else pd.DataFrame()
    
    current_counts = current_data['count'].tolist()
    avg_current = np.mean(current_counts)
    avg_previous = np.mean(previous_data['count']) if not previous_data.empty else 0
    
    if len(current_counts) > 1:
        slope, _, _, _, _ = stats.linregress(np.arange(len(current_counts)), current_counts)
        trend = slope * len(current_counts)
    else:
        trend = 0
    
    max_day_idx = current_data['count'].idxmax()
    min_day_idx = current_data['count'].idxmin()
    
    max_day = (current_data.loc[max_day_idx, 'date'], current_data.loc[max_day_idx, 'count'])
    min_day = (current_data.loc[min_day_idx, 'date'], current_data.loc[min_day_idx, 'count'])
    
    notes = [note.lower() for note in current_data['notes'].dropna().tolist()]
    word_analysis = {}
    for note in notes:
        for word in note.split():
            if len(word) > 2:
                word_analysis[word] = word_analysis.get(word, 0) + 1
    
    top_words = sorted(word_analysis.items(), key=lambda x: x[1], reverse=True)[:3]
    
    return jsonify({
        'analytics': {
            'current_avg': avg_current,
            'previous_avg': avg_previous,
            'trend': trend,
            'max_day': max_day,
            'min_day': min_day,
            'top_words': top_words
        }
    }), 200

@app.route('/api/plot', methods=['GET'])
@jwt_required()
def get_plot():
    current_user = get_jwt_identity()
    user_id = current_user['id']
    days = int(request.args.get('days', 7))
    
    conn = get_db_connection()
    start_date = (datetime.now() - timedelta(days=days-1)).strftime("%Y-%m-%d")
    
    data = conn.execute(
        '''SELECT date, SUM(count) as total
           FROM eggs
           WHERE user_id = ? AND date >= ?
           GROUP BY date
           ORDER BY date''',
        (user_id, start_date)
    ).fetchall()
    
    if not data:
        all_data = conn.execute(
            '''SELECT date, count FROM eggs 
               WHERE user_id = ? 
               ORDER BY date''',
            (user_id,)
        ).fetchall()
        if all_data:
            df = pd.DataFrame(all_data, columns=['date', 'count'])
            if len(df) < days:
                days = len(df)
            recent_data = df.tail(days)
            dates = pd.to_datetime(recent_data['date']).tolist()
            counts = recent_data['count'].tolist()
        else:
            conn.close()
            return jsonify({'error': 'Нет данных для построения графика'}), 404
    else:
        dates = [datetime.strptime(row['date'], "%Y-%m-%d") for row in data]
        counts = [row['total'] for row in data]
    
    conn.close()
    
    plt.figure(figsize=(10, 6))
    plt.plot(dates, counts, marker='o', linestyle='-', color='#ff6b6b')
    plt.title(f'Яйценоскость за {len(dates)} дней')
    plt.xlabel('Дата')
    plt.ylabel('Количество яиц')
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    filename = f"/tmp/egg_stats_{user_id}_{days}days.png"
    plt.savefig(filename, dpi=100)
    plt.close()
    
    return send_from_directory('/tmp', f"egg_stats_{user_id}_{days}days.png", mimetype='image/png')

@app.route('/api/summary', methods=['GET'])
@jwt_required()
def get_summary():
    current_user = get_jwt_identity()
    user_id = current_user['id']
    
    conn = get_db_connection()
    
    total_eggs = conn.execute(
        'SELECT SUM(count) FROM eggs WHERE user_id = ?',
        (user_id,)
    ).fetchone()[0] or 0
    
    records_count = conn.execute(
        'SELECT COUNT(*) FROM eggs WHERE user_id = ?',
        (user_id,)
    ).fetchone()[0]
    
    conn.close()
    
    avg_per_record = total_eggs / records_count if records_count > 0 else 0
    
    return jsonify({
        'total_eggs': total_eggs,
        'records_count': records_count,
        'avg_per_record': avg_per_record
    }), 200

# Serve React app
@app.route('/')
@app.route('/<path:path>')
def serve(path=''):
    if path and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
