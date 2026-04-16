import os
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import sqlite3
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def init_db():
    conn = sqlite3.connect("piano.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lessons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            duration INTEGER,
            level TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contact (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()

@app.get("/")
async def root():
    return FileResponse("index.html")

@app.get("/api/lessons")
async def get_lessons():
    conn = sqlite3.connect("piano.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM lessons")
    lessons = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return lessons

@app.post("/api/lessons")
async def add_lesson(lesson: dict):
    conn = sqlite3.connect("piano.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO lessons (title, description, duration, level) VALUES (?, ?, ?, ?)",
        (lesson.get("title"), lesson.get("description"), lesson.get("duration"), lesson.get("level"))
    )
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Lesson added"}

@app.post("/api/contact")
async def submit_contact(contact: dict):
    conn = sqlite3.connect("piano.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO contact (name, email, message) VALUES (?, ?, ?)",
        (contact.get("name"), contact.get("email"), contact.get("message"))
    )
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Message received"}

@app.get("/api/contact")
async def get_contacts():
    conn = sqlite3.connect("piano.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM contact ORDER BY created_at DESC")
    contacts = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return contacts

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)