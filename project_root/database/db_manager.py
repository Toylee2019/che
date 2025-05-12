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
    print("✅ 本地 SQLite 数据库已初始化并建表（如尚未存在）")

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
        level_id, recognition_code, level_code, question_type_code,
        difficulty_coefficient, question_type, content_text,
        option_a, option_b, option_c, option_d,
        answer, has_formula, answer_explanation, scoring_criteria
    ))
    conn.commit()
    qid = cursor.lastrowid
    conn.close()
    return qid

def insert_question_image(question_id: int, image_path: str) -> None:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO question_images(question_id, image_path) VALUES (?, ?)",
        (question_id, image_path)
    )
    conn.commit()
    conn.close()

def insert_question_formula(question_id: int, formula_type: str, content: str) -> None:
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
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT image_path FROM question_images WHERE question_id IN "
        "(SELECT id FROM questions WHERE level_id = ?)",
        (level_id,)
    )
    img_paths = [row[0] for row in cursor.fetchall()]

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
    cursor.execute(
        "DELETE FROM questions WHERE level_id = ?",
        (level_id,)
    )
    cursor.execute("DELETE FROM sqlite_sequence WHERE name = 'questions';")
    conn.commit()
    conn.close()

    for path in img_paths:
        try:
            os.remove(path)
        except:
            pass

def fetch_questions_by_level(level_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
          id,
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
          answer_explanation,
          scoring_criteria
        FROM questions
        WHERE level_id = ?
    """, (level_id,))
    rows = cursor.fetchall()
    conn.close()
    result = []
    for (qid, rec_code, level_code, question_type_code, difficulty_coefficient,
         qt, text, a, b, c, d, ans, exp, score) in rows:
        result.append({
            "id":                     qid,
            "recognition_code":       rec_code,
            "level_code":             level_code,
            "question_type_code":     question_type_code,
            "difficulty_coefficient": difficulty_coefficient,
            "question_type":          qt,
            "content_text":           text,
            "option_a":               a,
            "option_b":               b,
            "option_c":               c,
            "option_d":               d,
            "answer":                 ans,
            "answer_explanation":     exp,
            "scoring_criteria":       score
        })
    return result

def fetch_jobs():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM jobs ORDER BY name")
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

def fetch_questions_by_codes(codes: list[str]):
    if not codes:
        return []
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    placeholders = ",".join("?" for _ in codes)
    query = f"""
        SELECT
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
          answer_explanation,
          scoring_criteria
        FROM questions
        WHERE recognition_code IN ({placeholders})
    """
    cursor.execute(query, codes)
    rows = cursor.fetchall()
    conn.close()

    mapping = {}
    for (rec_code, level_code, question_type_code, difficulty_coefficient,
         qt, text, a, b, c, d, ans, exp, score) in rows:
        mapping.setdefault(rec_code, []).append({
            "recognition_code":       rec_code,
            "level_code":             level_code,
            "question_type_code":     question_type_code,
            "difficulty_coefficient": difficulty_coefficient,
            "question_type":          qt,
            "content_text":           text,
            "option_a":               a,
            "option_b":               b,
            "option_c":               c,
            "option_d":               d,
            "answer":                 ans,
            "answer_explanation":     exp,
            "scoring_criteria":       score
        })

    result = []
    for code in codes:
        items = mapping.get(code, [])
        if items:
            result.append(items[0])
    return result

def fetch_questions_by_ids(ids: list[int]):
    """
    根据 questions.id 列表查询详情，返回完整记录，并附带图片路径与公式图片路径。
    """
    if not ids:
        return []
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    placeholders = ",".join("?" for _ in ids)

    # 1) 查询主表字段
    query = f"""
        SELECT
          id,
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
          answer_explanation,
          scoring_criteria
        FROM questions
        WHERE id IN ({placeholders})
    """
    cursor.execute(query, ids)
    rows = cursor.fetchall()

    # 2) 查询所有图片路径
    cursor.execute(f"""
        SELECT question_id, image_path
        FROM question_images
        WHERE question_id IN ({placeholders})
    """, ids)
    images_map = {}
    for qid, path in cursor.fetchall():
        images_map.setdefault(qid, []).append(path)

    # 3) 查询所有公式“内容” —— 这里 content 实际就是你存的公式图片路径
    cursor.execute(f"""
        SELECT question_id, content
        FROM question_formulas
        WHERE question_id IN ({placeholders})
    """, ids)
    formulas_map = {}
    for qid, content in cursor.fetchall():
        formulas_map.setdefault(qid, []).append(content)

    conn.close()

    # 4) 组装结果
    result = []
    for (qid, rec_code, lvl_c, qt_c, diff, qt, text,
         a, b, c, d, ans, exp, score) in rows:
        result.append({
            "id":                     qid,
            "recognition_code":       rec_code,
            "level_code":             lvl_c,
            "question_type_code":     qt_c,
            "difficulty_coefficient": diff,
            "question_type":          qt,
            "content_text":           text,
            "option_a":               a,
            "option_b":               b,
            "option_c":               c,
            "option_d":               d,
            "answer":                 ans,
            "answer_explanation":     exp,
            "scoring_criteria":       score,
            # 把查询到的两组路径放到这两个字段里
            "image_paths":            images_map.get(qid, []),
            "formula_image_paths":    formulas_map.get(qid, []),
        })
    return result

