# dump_db.py

import sqlite3
import pprint

def dump_overview(limit=5):
    """
    打印数据库中前几条记录的关键字段：题型、答案、解析、评分标准
    """
    conn = sqlite3.connect("questions.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            id,
            question_type,
            answer,
            answer_explanation,
            scoring_criteria
        FROM questions
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    print(f"---- 前 {limit} 条记录概览 ----")
    pprint.pprint(rows)
    conn.close()

def dump_by_type(qtype, limit=5):
    """
    按题型打印前几条记录，方便针对性验证
    """
    conn = sqlite3.connect("questions.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            id,
            question_type,
            answer,
            answer_explanation,
            scoring_criteria
        FROM questions
        WHERE question_type = ?
        LIMIT ?
    """, (qtype, limit))
    rows = cursor.fetchall()
    print(f"---- {qtype} 前 {limit} 条 ----")
    pprint.pprint(rows)
    conn.close()

if __name__ == "__main__":
    dump_overview(5)
    # 如果需要，也可以按类型单独查看
    for t in ["单选", "多选", "判断", "简答", "计算"]:
        dump_by_type(t, 3)
