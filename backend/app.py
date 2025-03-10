from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins=["http://localhost", "http://176.123.167.178"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Модель для добавления записи
class EggRecord(BaseModel):
    user_id: int
    date: str
    count: int
    notes: str = ""

# Подключение к базе данных
def get_db_connection():
    conn = sqlite3.connect('../data/egg_database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Добавление записи
@app.post("/records/")
def add_record(record: EggRecord):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO eggs (user_id, date, count, notes) VALUES (?, ?, ?, ?)",
        (record.user_id, record.date, record.count, record.notes)
    )
    conn.commit()
    record_id = cursor.lastrowid
    conn.close()
    return {"id": record_id}

# Получение записей
@app.get("/records/{user_id}")
def get_records(user_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM eggs WHERE user_id = ?", (user_id,))
    records = cursor.fetchall()
    conn.close()
    return {"records": records}

# Удаление записи
@app.delete("/records/{record_id}")
def delete_record(record_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM eggs WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()
    return {"message": "Record deleted"}