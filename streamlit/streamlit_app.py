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

def get_all_records_with_id(telegram_id):
    """Получить все записи пользователя с ID для отображения"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, date, count, notes FROM eggs WHERE user_id = ? ORDER BY date DESC, id DESC", (telegram_id,))
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

def get_record_by_id(record_id):
    """Получить запись по ID"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, user_id, date, count, notes FROM eggs WHERE id = ?", (record_id,))
    result = c.fetchone()
    conn.close()
    return result

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
st.set_page_config(
    page_title="Десять курочек | Сервис для учёта яйценоскости", 
    page_icon="🐔",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Главная страница до входа
if not st.session_state.get('logged_in'):
    # Сайдбар для навигации и доната
    with st.sidebar:
        st.title("🐔 Десять курочек")
        st.markdown("---")
        menu = st.selectbox("Меню", ["О сервисе", "Вход", "Регистрация", "Забыли пароль?"])
        
        # Блок доната
        st.markdown("---")
        st.subheader("❤️ Поддержать проект")
        st.markdown(
            """
            Если вам нравится наш сервис и вы хотите поддержать его развитие, 
            вы можете сделать это через CloudTips:
            """
        )
        st.link_button(
            "☁️ Поддержать через CloudTips", 
            "https://pay.cloudtips.ru/p/dbed3f9a",
            help="Ваша поддержка помогает развивать проект!",
            type="secondary"
        )
        st.markdown("---")
    
    # Основное содержание в зависимости от выбранного пункта меню
    if menu == "О сервисе":
        st.title("🐔 Десять курочек")
        st.subheader("Умный сервис для учёта яйценоскости ваших кур")
        
        # Блок с преимуществами
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### 📊 Учёт и статистика")
            st.markdown("""
            - Ежедневный учёт яиц
            - Визуальная статистика
            - Анализ продуктивности
            - История за любой период
            """)
            
        with col2:
            st.markdown("### 📈 Аналитика и отчёты")
            st.markdown("""
            - Графики яйценоскости
            - Сравнение периодов
            - Выявление тенденций
            - Экспорт данных
            """)
            
        with col3:
            st.markdown("### 🐓 Управление хозяйством")
            st.markdown("""
            - Заметки и комментарии
            - Поиск по записям
            - Напоминания (в планах)
            - Мультипользовательский режим
            """)
        
        st.markdown("---")
        
        # Как это работает
        st.markdown("## 🚀 Как начать пользоваться?")
        
        steps_col1, steps_col2, steps_col3 = st.columns(3)
        
        with steps_col1:
            st.markdown("### 1. Регистрация")
            st.markdown("""
            Создайте аккаунт, указав:
            - Имя пользователя
            - Telegram ID
            - Пароль
            - Секретный вопрос
            """)
            
        with steps_col2:
            st.markdown("### 2. Настройка")
            st.markdown("""
            Получите Telegram ID через бота:
            - Перейдите в @ten_hens_bot
            - Выполните команду /myid
            - Используйте полученный ID
            """)
            
        with steps_col3:
            st.markdown("### 3. Начало работы")
            st.markdown("""
            Начните добавлять записи:
            - Указывайте количество яиц
            - Добавляйте заметки
            - Анализируйте статистику
            """)
        
        st.markdown("---")
        
        # Для кого подходит
        st.markdown("## 🏡 Для кого этот сервис?")
        
        target_col1, target_col2 = st.columns(2)
        
        with target_col1:
            st.markdown("### 🐔 Частные хозяйства")
            st.markdown("""
            - Владельцы домашних кур
            - Небольшие фермерские хозяйства
            - Любители птицеводства
            - Семейные подворья
            """)
            
        with target_col2:
            st.markdown("### 📚 Образовательные проекты")
            st.markdown("""
            - Школьные проекты
            - Учебные фермы
            - Кружки животноводства
            - Научные наблюдения
            """)
        
        st.markdown("---")
        
        # Отзывы (заглушки)
        st.markdown("## 💬 Отзывы пользователей")
        
        review_col1, review_col2 = st.columns(2)
        
        with review_col1:
            with st.container(border=True):
                st.markdown("**Мария, 15 кур**")
                st.markdown("⭐️⭐️⭐️⭐️⭐️")
                st.markdown("«Очень удобно следить за продуктивностью! Заметила, что куры лучше несутся при определенной температуре.»")
                
        with review_col2:
            with st.container(border=True):
                st.markdown("**Сергей, фермер**")
                st.markdown("⭐️⭐️⭐️⭐️⭐️")
                st.markdown("«Отличная аналитика. Помогло оптимизировать кормление и увеличить яйценоскость на 15%.»")
        
        # Призыв к действию
        st.markdown("---")
        st.markdown("## 🎯 Готовы начать?")
        st.markdown("Присоединяйтесь к сообществу птицеводов уже сегодня!")
        

    elif menu == "Регистрация":
        st.subheader("Создать новый аккаунт")
        new_username = st.text_input("Имя пользователя")
        new_telegram_id = st.number_input("Telegram ID", min_value=1, step=1)
        st.link_button("🆔 Получить Telgram ID", "https://t.me/ten_hens_bot", help="Чтобы получить Telegram ID перейдите в бота и выполните команду /myid", type="secondary")
        new_password = st.text_input("Пароль", type="password")
        security_question = st.text_input("Секретный вопрос (например: Девичья фамилия матери?)")
        security_answer = st.text_input("Ответ на секретный вопрос")
        
        if st.button("Зарегистрироваться"):
            if all([new_username, new_telegram_id, new_password, security_question, security_answer]):
                try:
                    register_user(new_username, new_telegram_id, new_password, 
                                security_question, security_answer)
                    st.success("Аккаунт успешно создан!")
                    st.balloons()
                    st.info("Теперь вы можете войти в систему используя свои учетные данные.")
                except sqlite3.IntegrityError:
                    st.error("Пользователь с таким именем или Telegram ID уже существует!")
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
                st.success("Успешный вход!")
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

    # Автопереход при нажатии кнопки "Начать пользоваться"
    if st.session_state.get('auto_redirect'):
        menu = st.session_state.auto_redirect
        st.session_state.auto_redirect = None

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
        ["Просмотр и управление записями", "Добавить запись", "Статистика", "Аналитика", "График"])
    
    # Блок доната в сайдбаре для авторизованных пользователей
    st.sidebar.markdown("---")
    st.sidebar.subheader("❤️ Поддержать проект")
    st.sidebar.markdown(
        """
        Нравится сервис? Поддержите его развитие!
        """
    )
    st.sidebar.link_button(
        "☁️ Поддержать через CloudTips", 
        "https://pay.cloudtips.ru/p/dbed3f9a",
        help="Ваша поддержка помогает развивать проект!",
        type="secondary",
        use_container_width=True
    )
    
    if action == "Добавить запись":
        st.subheader("📥 Добавить новую запись")
        
        # Используем session_state для хранения состояния формы
        if 'form_submitted' not in st.session_state:
            st.session_state.form_submitted = False
            
        count = st.number_input("Количество яиц", min_value=0, step=1, key="add_count")
        date = st.date_input("Дата", key="add_date")
        notes = st.text_input("Заметки", key="add_notes")
        
        if st.button("Добавить", key="add_button"):
            add_egg_record(st.session_state['telegram_id'], date.strftime("%Y-%m-%d"), count, notes)
            st.success("✅ Запись успешно добавлена!")
            st.session_state.form_submitted = True
            
        # Если форма была отправлена, показываем кнопку для сброса
        if st.session_state.form_submitted:
            if st.button("Добавить еще запись", key="add_another"):
                st.session_state.form_submitted = False
                st.rerun()

    elif action == "Просмотр и управление записями":
        st.subheader("📋 Управление записями")
        
        # Добавляем форму для быстрого добавления записи
        with st.expander("➕ Быстрое добавление записи", expanded=False):
            # Используем форму для предотвращения множественной отправки
            with st.form(key="quick_add_form", clear_on_submit=True):
                col1, col2, col3 = st.columns([2, 2, 4])
                with col1:
                    quick_date = st.date_input("Дата", key="quick_date")
                with col2:
                    quick_count = st.number_input("Количество", min_value=0, step=1, key="quick_count")
                with col3:
                    quick_notes = st.text_input("Заметки", key="quick_notes", placeholder="Необязательно")
                
                submitted = st.form_submit_button("Добавить запись")
                if submitted:
                    if quick_count > 0:
                        add_egg_record(st.session_state['telegram_id'], quick_date.strftime("%Y-%m-%d"), quick_count, quick_notes)
                        st.success("✅ Запись успешно добавлена!")
                    else:
                        st.error("Укажите количество яиц")
        
        # Получаем все записи пользователя с ID
        records = get_all_records_with_id(st.session_state['telegram_id'])
        
        if records:
            # Создаем DataFrame для красивого отображения
            df = pd.DataFrame(records, columns=['ID', 'Дата', 'Количество', 'Заметки'])
            
            # Показываем общее количество записей
            st.info(f"Всего записей: {len(records)}")
            
            # Добавляем фильтры
            st.subheader("🔍 Фильтры и поиск")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                min_date = st.date_input("От даты", value=datetime.now() - timedelta(days=30), key="filter_min_date")
            
            with col2:
                max_date = st.date_input("До даты", value=datetime.now(), key="filter_max_date")
            
            with col3:
                search_notes = st.text_input("Поиск по заметкам", key="search_notes")
            
            # Фильтруем данные
            filtered_df = df[
                (pd.to_datetime(df['Дата']) >= pd.to_datetime(min_date)) & 
                (pd.to_datetime(df['Дата']) <= pd.to_datetime(max_date))
            ]
            
            if search_notes:
                filtered_df = filtered_df[filtered_df['Заметки'].str.contains(search_notes, case=False, na=False)]
            
            st.write(f"Найдено записей: {len(filtered_df)}")
            
            # Отображаем таблицу с записями
            for index, row in filtered_df.iterrows():
                with st.container():
                    col1, col2, col3, col4, col5 = st.columns([1, 2, 2, 4, 3])
                    
                    with col1:
                        st.write(f"**{row['ID']}**")
                    
                    with col2:
                        st.write(row['Дата'])
                    
                    with col3:
                        st.write(f"{row['Количество']} 🥚")
                    
                    with col4:
                        st.write(row['Заметки'] if row['Заметки'] else "-")
                    
                    with col5:
                        # Кнопки действий для каждой записи
                        edit_key = f"edit_{row['ID']}"
                        delete_key = f"delete_{row['ID']}"
                        
                        col_edit, col_del = st.columns(2)
                        with col_edit:
                            if st.button("✏️", key=edit_key, help="Редактировать запись"):
                                st.session_state[f'editing_{row["ID"]}'] = True
                        
                        with col_del:
                            if st.button("🗑️", key=delete_key, help="Удалить запись"):
                                st.session_state[f'deleting_{row["ID"]}'] = True
                    
                    # Форма редактирования для этой записи
                    if st.session_state.get(f'editing_{row["ID"]}'):
                        with st.expander(f"Редактирование записи #{row['ID']}", expanded=True):
                            record_data = get_record_by_id(row['ID'])
                            if record_data:
                                edit_col1, edit_col2, edit_col3 = st.columns([2, 2, 4])
                                
                                with edit_col1:
                                    edit_date = st.date_input("Дата", 
                                                             value=datetime.strptime(record_data[2], "%Y-%m-%d"),
                                                             key=f"edit_date_{row['ID']}")
                                
                                with edit_col2:
                                    edit_count = st.number_input("Количество", 
                                                                min_value=0, 
                                                                value=record_data[3],
                                                                key=f"edit_count_{row['ID']}")
                                
                                with edit_col3:
                                    edit_notes = st.text_input("Заметки", 
                                                              value=record_data[4] if record_data[4] else "",
                                                              key=f"edit_notes_{row['ID']}")
                                
                                col_save, col_cancel = st.columns(2)
                                with col_save:
                                    if st.button("💾 Сохранить", key=f"save_{row['ID']}"):
                                        update_record(row['ID'], edit_count, edit_date.strftime("%Y-%m-%d"), edit_notes)
                                        st.success("✅ Запись успешно обновлена!")
                                        st.session_state[f'editing_{row["ID"]}'] = False
                                        st.rerun()
                                
                                with col_cancel:
                                    if st.button("❌ Отмена", key=f"cancel_{row['ID']}"):
                                        st.session_state[f'editing_{row["ID"]}'] = False
                                        st.rerun()
                    
                    # Подтверждение удаления
                    if st.session_state.get(f'deleting_{row["ID"]}'):
                        with st.expander(f"Подтверждение удаления записи #{row['ID']}", expanded=True):
                            st.warning("Вы уверены, что хотите удалить эту запись? Это действие нельзя отменить!")
                            
                            col_confirm, col_cancel_del = st.columns(2)
                            with col_confirm:
                                if st.button("✅ Да, удалить", key=f"confirm_del_{row['ID']}"):
                                    delete_record(row['ID'])
                                    st.success("✅ Запись успешно удалена!")
                                    st.session_state[f'deleting_{row["ID"]}'] = False
                                    st.rerun()
                            
                            with col_cancel_del:
                                if st.button("❌ Отмена", key=f"cancel_del_{row['ID']}"):
                                    st.session_state[f'deleting_{row["ID"]}'] = False
                                    st.rerun()
                    
                    st.markdown("---")
            
            # Экспорт данных
            st.subheader("📤 Экспорт данных")
            csv = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Скачать отфильтрованные данные в CSV",
                data=csv,
                file_name=f"egg_records_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
            
        else:
            st.warning("У вас пока нет записей о яйценоскости")

    elif action == "Аналитика":
        st.subheader("📈 Аналитика")
        days = st.slider("Анализируемый период (дней)", min_value=7, max_value=90, value=30, key="analytics_days")
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
        days = st.slider("Период отображения (дней)", min_value=7, max_value=180, value=30, key="plot_days")
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