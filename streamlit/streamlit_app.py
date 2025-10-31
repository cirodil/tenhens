import streamlit as st
import sqlite3
import hashlib
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats
from datetime import datetime, timedelta
import pandas as pd

# Настройки базы данных
DB_NAME = "/app/data/egg_database.db"
# DB_NAME = "../chicken_bot/data/egg_database.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS eggs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  date TEXT,
                  count INTEGER,
                  notes TEXT)''')
                  
    c.execute('''CREATE TABLE IF NOT EXISTS streamlit_users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE,
                  telegram_id INTEGER UNIQUE,
                  password TEXT,
                  security_question TEXT,
                  security_answer TEXT)''')
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, telegram_id, password, security_question, security_answer):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    hashed_password = hash_password(password)
    hashed_answer = hash_password(security_answer.lower().strip())
    c.execute("""INSERT INTO streamlit_users 
                 (username, telegram_id, password, security_question, security_answer) 
                 VALUES (?, ?, ?, ?, ?)""",
              (username, telegram_id, hashed_password, security_question, hashed_answer))
    conn.commit()
    conn.close()

def authenticate_user(username, password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT password, telegram_id FROM streamlit_users WHERE username = ?", (username,))
    result = c.fetchone()
    conn.close()
    if result and hash_password(password) == result[0]:
        st.session_state['telegram_id'] = result[1]
        return True
    return False

def reset_password(username, new_password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    hashed_password = hash_password(new_password)
    c.execute("UPDATE streamlit_users SET password = ? WHERE username = ?",
              (hashed_password, username))
    conn.commit()
    conn.close()

def verify_security_answer(username, answer):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT security_question, security_answer FROM streamlit_users WHERE username = ?", (username,))
    result = c.fetchone()
    conn.close()
    if result and hash_password(answer.lower().strip()) == result[1]:
        return result[0]
    return None

def get_user_data(telegram_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, date, count, notes FROM eggs WHERE user_id = ? ORDER BY date DESC", (telegram_id,))
    data = c.fetchall()
    conn.close()
    return data

def add_egg_record(user_id, date, count, notes=""):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO eggs (user_id, date, count, notes) VALUES (?, ?, ?, ?)",
              (user_id, date, count, notes))
    conn.commit()
    conn.close()

def delete_record(record_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM eggs WHERE id=?", (record_id,))
    conn.commit()
    conn.close()

def update_record(record_id, count=None, date=None, notes=None):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    updates = []
    params = []
    if count is not None:
        updates.append("count = ?")
        params.append(count)
    if date is not None:
        updates.append("date = ?")
        params.append(date)
    if notes is not None:
        updates.append("notes = ?")
        params.append(notes)
    if updates:
        query = f"UPDATE eggs SET {', '.join(updates)} WHERE id = ?"
        params.append(record_id)
        c.execute(query, params)
        conn.commit()
    conn.close()

def get_stats(user_id, days=7):
    """Получить статистику за указанный период"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Получаем начальную дату
    start_date = (datetime.now() - timedelta(days=days-1)).strftime("%Y-%m-%d")
    
    # Получаем данные за период
    c.execute('''SELECT date, SUM(count)
                 FROM eggs
                 WHERE user_id = ? AND date >= ?
                 GROUP BY date
                 ORDER BY date''', (user_id, start_date))
    data = c.fetchall()
    
    conn.close()
    return data

def get_total_eggs(user_id):
    """Получить общее количество яиц для пользователя"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''SELECT SUM(count) FROM eggs WHERE user_id = ?''', (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result[0] is not None else 0

def get_egg_records_count(user_id):
    """Получить количество записей пользователя"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''SELECT COUNT(*) FROM eggs WHERE user_id = ?''', (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result[0] is not None else 0

def get_all_user_records(user_id):
    """Получить все записи пользователя для аналитики"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''SELECT date, count, notes FROM eggs WHERE user_id = ? ORDER BY date''', (user_id,))
    data = c.fetchall()
    conn.close()
    return data

def generate_plot(user_id, days=7):
    """Сгенерировать график яйценоскости"""
    data = get_stats(user_id, days)
    if not data:
        # Если нет данных за период, попробуем получить все данные пользователя
        all_data = get_all_user_records(user_id)
        if not all_data:
            return None
        
        # Преобразуем все данные в DataFrame для удобства
        df = pd.DataFrame(all_data, columns=['date', 'count', 'notes'])
        df['date'] = pd.to_datetime(df['date'])
        
        # Если данных меньше чем days, используем все доступные данные
        if len(df) < days:
            days = len(df)
        
        # Берем последние days записей
        recent_data = df.tail(days)
        dates = recent_data['date'].tolist()
        counts = recent_data['count'].tolist()
    else:
        dates = [datetime.strptime(row[0], "%Y-%m-%d") for row in data]
        counts = [row[1] for row in data]
    
    plt.figure(figsize=(10, 6))
    plt.plot(dates, counts, marker='o', linestyle='-', color='#ff6b6b')
    plt.title(f'Яйценоскость за {len(dates)} дней')
    plt.xlabel('Дата')
    plt.ylabel('Количество яиц')
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    filename = f"egg_stats_{user_id}_{days}days.png"
    plt.savefig(filename, dpi=100)
    plt.close()
    return filename

def calculate_analytics(user_id, days=7):
    """Рассчитать аналитику по яйценоскости"""
    # Получаем все данные пользователя
    all_data = get_all_user_records(user_id)
    if not all_data or len(all_data) < 2:
        return None
    
    # Преобразуем в DataFrame
    df = pd.DataFrame(all_data, columns=['date', 'count', 'notes'])
    df['date'] = pd.to_datetime(df['date'])
    
    # Если данных меньше чем days, используем все доступные данные
    if len(df) < days:
        days = len(df)
    
    # Берем последние days записей для текущего периода
    current_data = df.tail(days)
    
    # Берем предыдущие days записей для сравнения (если есть)
    if len(df) >= days * 2:
        previous_data = df.iloc[-days*2:-days]
    else:
        # Если нет достаточного количества данных для сравнения, берем все что есть до текущего периода
        previous_data = df.iloc[:-days] if len(df) > days else pd.DataFrame()
    
    # Рассчитываем статистики
    current_counts = current_data['count'].tolist()
    avg_current = np.mean(current_counts)
    
    if not previous_data.empty:
        avg_previous = np.mean(previous_data['count'])
    else:
        avg_previous = 0
    
    # Рассчитываем тренд
    if len(current_counts) > 1:
        x = np.arange(len(current_counts))
        slope, _, _, _, _ = stats.linregress(x, current_counts)
        trend = slope * len(current_counts)
    else:
        trend = 0
    
    # Находим дни с максимальным и минимальным количеством яиц
    max_day_idx = current_data['count'].idxmax()
    min_day_idx = current_data['count'].idxmin()
    
    max_day = (current_data.loc[max_day_idx, 'date'].strftime("%Y-%m-%d"), 
               current_data.loc[max_day_idx, 'count'])
    min_day = (current_data.loc[min_day_idx, 'date'].strftime("%Y-%m-%d"), 
               current_data.loc[min_day_idx, 'count'])
    
    # Анализ заметок
    notes = [note.lower() for note in current_data['notes'].dropna().tolist()]
    word_analysis = {}
    for note in notes:
        for word in note.split():
            if len(word) > 2:  # Игнорируем короткие слова
                word_analysis[word] = word_analysis.get(word, 0) + 1
    
    top_words = sorted(word_analysis.items(), key=lambda x: x[1], reverse=True)[:3]
    
    return {
        'current_avg': avg_current,
        'previous_avg': avg_previous,
        'trend': trend,
        'max_day': max_day,
        'min_day': min_day,
        'top_words': top_words
    }

# Остальной код остается без изменений...
init_db()
st.set_page_config(page_title="Десять курочек | Сервис для учёта яйценоскости" , page_icon="🐔")

st.title("🐔 Десять курочек")
st.subheader("Сервис для учёта яйценоскости")

if not st.session_state.get('logged_in'):
    auth_container = st.container()
    with auth_container:
        menu = st.sidebar.selectbox("Меню", ["Вход", "Регистрация", "Забыли пароль?"])
        
        if menu == "Регистрация":
            st.subheader("Создать новый аккаунт")
            new_username = st.text_input("Имя пользователя")
            new_telegram_id = st.number_input("Telegram ID", min_value=1, step=1)
            st.link_button("🆔 Получить Telgram ID", "https://t.me/testhens_bot", help="Чтобы получить Telegram ID перейдите в бота и выполните команду /myid", type="secondary")
            new_password = st.text_input("Пароль", type="password")
            security_question = st.text_input("Секретный вопрос (например: Девичья фамилия матери?)")
            security_answer = st.text_input("Ответ на секретный вопрос")
            
            if st.button("Зарегистрироваться"):
                if all([new_username, new_telegram_id, new_password, security_question, security_answer]):
                    register_user(new_username, new_telegram_id, new_password, 
                                security_question, security_answer)
                    st.success("Аккаунт успешно создан!")
                else:
                    st.error("Все поля обязательны для заполнения")

        elif menu == "Вход":
            st.subheader("Вход в аккаунт")
            username = st.text_input("Имя пользователя")
            password = st.text_input("Пароль", type="password")
            if st.button("Войти"):
                if authenticate_user(username, password):
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = username
                    st.rerun()
                else:
                    st.error("Неверные учетные данные")

        elif menu == "Забыли пароль?":
            st.subheader("Восстановление пароля")
            username = st.text_input("Введите ваше имя пользователя")
            
            if username:
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute("SELECT security_question FROM streamlit_users WHERE username = ?", (username,))
                result = c.fetchone()
                conn.close()
                
                if result:
                    question = result[0]
                    answer = st.text_input(f"Введите ответ на вопрос: '{question}'")
                    new_password = st.text_input("Новый пароль", type="password")
                    
                    if st.button("Сбросить пароль"):
                        if verify_security_answer(username, answer):
                            reset_password(username, new_password)
                            st.success("Пароль успешно изменен!")
                        else:
                            st.error("Неверный ответ на секретный вопрос")
                else:
                    st.error("Пользователь не найден")

else:
    # Получаем статистику пользователя для сайдбара
    total_eggs = get_total_eggs(st.session_state['telegram_id'])
    records_count = get_egg_records_count(st.session_state['telegram_id'])
    
    # Отображаем информацию в сайдбаре
    st.sidebar.subheader(f"👋 Добро пожаловать, {st.session_state['username']}!")
    
    # Блок с общей статистикой
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Общая статистика")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.metric("Всего яиц", f"{total_eggs}")
    with col2:
        st.metric("Записей", f"{records_count}")
    
    # Показываем среднее количество яиц на запись, если есть записи
    if records_count > 0:
        avg_per_record = total_eggs / records_count
        st.sidebar.metric("В среднем на запись", f"{avg_per_record:.1f}")
    
    st.sidebar.markdown("---")
    
    action = st.sidebar.selectbox("Выберите действие", 
        ["Добавить запись", "Редактировать запись", "Удалить запись", 
         "Статистика", "Аналитика", "График"])
    
    if action == "Добавить запись":
        st.subheader("📥 Добавить новую запись")
        count = st.number_input("Количество яиц", min_value=0, step=1)
        date = st.date_input("Дата")
        notes = st.text_input("Заметки")
        if st.button("Добавить"):
            add_egg_record(st.session_state['telegram_id'], date.strftime("%Y-%m-%d"), count, notes)
            st.success("✅ Запись успешно добавлена!")
            # Обновляем статистику после добавления записи
            st.rerun()

    elif action == "Редактировать запись":
        st.subheader("✏️ Редактировать запись")
        record_id = st.number_input("ID записи", min_value=1, step=1)
        count = st.number_input("Новое количество яиц", min_value=0, step=1)
        date = st.date_input("Новая дата")
        notes = st.text_input("Новые заметки")
        if st.button("Обновить"):
            update_record(record_id, count, date.strftime("%Y-%m-%d"), notes)
            st.success("✅ Запись успешно обновлена!")
            # Обновляем статистику после редактирования записи
            st.rerun()

    elif action == "Удалить запись":
        st.subheader("❌ Удалить запись")
        record_id = st.number_input("ID записи", min_value=1, step=1)
        if st.button("Удалить"):
            delete_record(record_id)
            st.success("✅ Запись успешно удалена!")
            # Обновляем статистику после удаления записи
            st.rerun()

    elif action == "Статистика":
        st.subheader("📊 Статистика")
        days = st.slider("Период (дней)", min_value=1, max_value=365, value=7)
        data = get_stats(st.session_state['telegram_id'], days)
        if data:
            st.write(f"**Всего яиц за {days} дней:** {sum(x[1] for x in data)}")
            st.dataframe(
                data=[{"Дата": date, "Количество": count} for date, count in data],
                use_container_width=True,
                column_config={
                    "Дата": st.column_config.DateColumn(format="YYYY-MM-DD"),
                    "Количество": st.column_config.NumberColumn(format="%d 🥚")
                }
            )
        else:
            # Если нет данных за выбранный период, показываем все доступные данные
            all_data = get_all_user_records(st.session_state['telegram_id'])
            if all_data:
                st.info(f"Нет данных за выбранный период. Показаны все доступные записи ({len(all_data)} записей):")
                st.dataframe(
                    data=[{"Дата": date, "Количество": count, "Заметки": notes} for date, count, notes in all_data],
                    use_container_width=True,
                    column_config={
                        "Дата": st.column_config.DateColumn(format="YYYY-MM-DD"),
                        "Количество": st.column_config.NumberColumn(format="%d 🥚")
                    }
                )
            else:
                st.warning("У вас пока нет записей о яйценоскости")

    elif action == "Аналитика":
        st.subheader("📈 Аналитика")
        days = st.slider("Анализируемый период (дней)", min_value=7, max_value=90, value=30)
        analytics = calculate_analytics(st.session_state['telegram_id'], days)
        
        if analytics:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Среднее в день", f"{analytics['current_avg']:.1f} яиц",
                        delta=f"{analytics['trend']:+.1f} тренд")
                st.metric("Максимальный день", 
                        f"{analytics['max_day'][1]} яиц",
                        help=f"Дата: {analytics['max_day'][0]}")
                
            with col2:
                st.metric("Сравнение с прошлым периодом", 
                        f"{analytics['current_avg'] - analytics['previous_avg']:+.1f}",
                        help=f"Пред. период: {analytics['previous_avg']:.1f}")
                st.metric("Минимальный день", 
                        f"{analytics['min_day'][1]} яиц",
                        help=f"Дата: {analytics['min_day'][0]}")
            
            if analytics['top_words']:
                st.subheader("🔍 Частые упоминания в заметках")
                cols = st.columns(3)
                for i, (word, count) in enumerate(analytics['top_words']):
                    cols[i].metric(f"Слово #{i+1}", word, f"{count} упоминаний")

        else:
            st.warning("Недостаточно данных для анализа. Добавьте больше записей.")

    elif action == "График":
        st.subheader("📈 График яйценоскости")
        days = st.slider("Период отображения (дней)", min_value=7, max_value=180, value=30)
        filename = generate_plot(st.session_state['telegram_id'], days)
        if filename:
            st.image(filename)
            with open(filename, "rb") as file:
                st.download_button(
                    label="Скачать график",
                    data=file,
                    file_name=f"egg_production_{days}_days.png",
                    mime="image/png"
                )
        else:
            st.warning("Нет данных для построения графика. Добавьте записи о яйценоскости.")

    if st.sidebar.button("🚪 Выйти из системы"):
        st.session_state.clear()
        st.rerun()