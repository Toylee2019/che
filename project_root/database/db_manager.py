# database/db_manager.py

import sqlite3
import os

# 数据库文件路径
DB_PATH = "questions.db"

def init_db():
    """
    初始化数据库并创建必要的表。
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    );
    CREATE TABLE IF NOT EXISTS job_levels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER NOT NULL,
        level_name TEXT NOT NULL,
        FOREIGN KEY (job_id) REFERENCES jobs(id)
    );
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        level_id INTEGER NOT NULL,
        recognition_code TEXT,
        level_code INTEGER,
        question_type_code INTEGER,
        difficulty_coefficient INTEGER,
        question_type TEXT,
        content_text TEXT,
        option_a TEXT,
        option_b TEXT,
        option_c TEXT,
        option_d TEXT,
        answer TEXT,
        has_formula INTEGER DEFAULT 0,
        answer_explanation TEXT,
        scoring_criteria TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (level_id) REFERENCES job_levels(id)
    );
    CREATE TABLE IF NOT EXISTS question_images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_id INTEGER NOT NULL,
        image_path TEXT,
        FOREIGN KEY (question_id) REFERENCES questions(id)
    );
    CREATE TABLE IF NOT EXISTS question_formulas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_id INTEGER NOT NULL,
        formula_type TEXT,
        content TEXT,
        FOREIGN KEY (question_id) REFERENCES questions(id)
    );
    """)
    conn.commit()
    conn.close()
    print("✅ 本地 SQLite 数据库已初始化并建表（如尚未存在）")  # 仅在调试时打印

def insert_question(
    level_id,
    recognition_code,
    level_code,
    question_type_code,
    difficulty_coefficient,
    question_type,
    content_text,
    option_a,
    option_b,
    option_c,
    option_d,
    answer,
    has_formula=0,
    answer_explanation=None,
    scoring_criteria=None
):
    """
    将一条题目插入 questions 表中，返回新插入的 question_id。
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO questions (
            level_id,
            recognition_code,
            level_code,
            question_type_code,
            difficulty_coefficient,
            question_type,
            content_text,
            option_a,
            option_b,
            option_c,
            option_d,
            answer,
            has_formula,
            answer_explanation,
            scoring_criteria
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        level_id,
        recognition_code,
        level_code,
        question_type_code,
        difficulty_coefficient,
        question_type,
        content_text,
        option_a,
        option_b,
        option_c,
        option_d,
        answer,
        has_formula,
        answer_explanation,
        scoring_criteria
    ))
    conn.commit()
    qid = cursor.lastrowid
    conn.close()
    return qid

def insert_question_image(question_id: int, image_path: str) -> None:
    """
    将一条题目图片路径写入 question_images 表。
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO question_images(question_id, image_path) VALUES (?, ?)",
        (question_id, image_path)
    )
    conn.commit()
    conn.close()

def insert_question_formula(question_id: int, formula_type: str, content: str) -> None:
    """
    将一段公式（MathML 或文本）写入 question_formulas 表。
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO question_formulas(question_id, formula_type, content) VALUES (?, ?, ?)",
        (question_id, formula_type, content)
    )
    conn.commit()
    conn.close()

def get_job_id(job_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM jobs WHERE name = ?", (job_name,))
    row = cursor.fetchone()
    if row:
        job_id = row[0]
    else:
        cursor.execute("INSERT INTO jobs (name) VALUES (?)", (job_name,))
        job_id = cursor.lastrowid
        conn.commit()
    conn.close()
    return job_id

def get_level_id(job_id, level_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM job_levels WHERE job_id = ? AND level_name = ?",
        (job_id, level_name)
    )
    row = cursor.fetchone()
    if row:
        level_id = row[0]
    else:
        cursor.execute(
            "INSERT INTO job_levels (job_id, level_name) VALUES (?, ?)",
            (job_id, level_name)
        )
        level_id = cursor.lastrowid
        conn.commit()
    conn.close()
    return level_id

def has_questions(level_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(1) FROM questions WHERE level_id = ?", (level_id,))
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0

def count_questions(level_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(1) FROM questions WHERE level_id = ?", (level_id,))
    count = cursor.fetchone()[0]
    conn.close()
    return count

def delete_questions_by_level(level_id):
    """
    删除指定 level_id 下的所有题目及其关联资源，
    并重置 questions 表的自增序列。
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # 先删图片与公式
    cursor.execute(
        "DELETE FROM question_images WHERE question_id IN (SELECT id FROM questions WHERE level_id = ?)",
        (level_id,)
    )
    cursor.execute(
        "DELETE FROM question_formulas WHERE question_id IN (SELECT id FROM questions WHERE level_id = ?)",
        (level_id,)
    )
    # 再删题目
    cursor.execute(
        "DELETE FROM questions WHERE level_id = ?",
        (level_id,)
    )
    # 重置自增序列
    cursor.execute("DELETE FROM sqlite_sequence WHERE name = 'questions';")
    conn.commit()
    conn.close()

def fetch_questions_by_level(level_id):
    """
    从数据库中取出指定 level_id 下所有题目的关键信息，
    返回 list of dict: {recognition_code, question_type, answer, answer_explanation}
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT recognition_code, question_type, answer, answer_explanation
        FROM questions
        WHERE level_id = ?
    """, (level_id,))
    rows = cursor.fetchall()
    conn.close()
    result = []
    for rec_code, qt, ans, exp in rows:
        result.append({
            "recognition_code":    rec_code,
            "question_type":       qt,
            "answer":              ans,
            "answer_explanation":  exp,
        })
    return result

def delete_questions_by_level(level_id):
    """
    删除指定 level_id 下的所有题目及关联的媒体记录，
    并删除对应磁盘上的图片文件，最后重置 questions 表自增序列。
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. 查出所有要删除的图片路径
    cursor.execute(
        "SELECT image_path FROM question_images WHERE question_id IN "
        "(SELECT id FROM questions WHERE level_id = ?)",
        (level_id,)
    )
    img_paths = [row[0] for row in cursor.fetchall()]

    # 2. 删除数据库里的图片和公式关联
    cursor.execute(
        "DELETE FROM question_images WHERE question_id IN "
        "(SELECT id FROM questions WHERE level_id = ?)",
        (level_id,)
    )
    cursor.execute(
        "DELETE FROM question_formulas WHERE question_id IN "
        "(SELECT id FROM questions WHERE level_id = ?)",
        (level_id,)
    )

    # 3. 删除题目主表记录
    cursor.execute(
        "DELETE FROM questions WHERE level_id = ?",
        (level_id,)
    )
    # 4. 重置自增序列
    cursor.execute("DELETE FROM sqlite_sequence WHERE name = 'questions';")

    conn.commit()
    conn.close()

    # 5. 删除磁盘上的图片文件
    for path in img_paths:
        try:
            os.remove(path)
        except Exception:
            # 忽略文件不存在或删除失败
            pass
