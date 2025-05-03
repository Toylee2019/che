import sqlite3
import os

DB_PATH = "questions.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS question_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id TEXT,
            image_path TEXT
        )
    """)
    conn.commit()
    conn.close()

def insert_image_record(question_id, image_path):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO question_images (question_id, image_path)
        VALUES (?, ?)
    """, (question_id, image_path))
    conn.commit()
    conn.close()
