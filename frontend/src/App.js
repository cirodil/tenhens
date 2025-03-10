import React, { useState, useEffect } from "react";
import "./App.css";

function App() {
  const [records, setRecords] = useState([]);
  const [count, setCount] = useState("");
  const [date, setDate] = useState("");
  const [notes, setNotes] = useState("");
  const userId = 391566450; // Замените на реальный ID пользователя

  // Загрузка записей
  useEffect(() => {
    fetch(`http://176.123.167.178/api/records/${userId}`)
      .then((response) => response.json())
      .then((data) => setRecords(data.records));
  }, []);

  // Добавление записи
  const addRecord = () => {
    fetch("http://176.123.167.178/api/records/", {
      mode: "no-cors",
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        user_id: userId,
        date: date || new Date().toISOString().split("T")[0],
        count: parseInt(count),
        notes: notes,
      }),
    })
      .then((response) => response.json())
      .then((data) => {
        alert(`Запись добавлена! ID: ${data.id}`);
        setCount("");
        setDate("");
        setNotes("");
        // Обновляем список записей
        fetch(`http://176.123.167.178/api/records/${userId}`, {
          mode: "no-cors",
        })
          .then((response) => response.json())
          .then((data) => setRecords(data.records));
      });
  };

  return (
    <div className="App">
      <h1>🐔 Учет яйценоскости кур</h1>

      <div className="form">
        <input
          type="number"
          placeholder="Количество яиц"
          value={count}
          onChange={(e) => setCount(e.target.value)}
        />
        <input
          type="date"
          placeholder="Дата"
          value={date}
          onChange={(e) => setDate(e.target.value)}
        />
        <input
          type="text"
          placeholder="Комментарий"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
        />
        <button onClick={addRecord}>Добавить запись</button>
      </div>

      <h2>📋 Список записей</h2>
      <table>
        <thead>
          <tr>
            <th>Дата</th>
            <th>Количество</th>
            <th>Комментарий</th>
          </tr>
        </thead>
        <tbody>
          {records.map((record) => (
            <tr key={record.id}>
              <td>{record.date}</td>
              <td>{record.count}</td>
              <td>{record.notes}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default App;
