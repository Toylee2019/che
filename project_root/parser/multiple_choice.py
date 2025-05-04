from parser.base_parser import BaseParser
from database.db_manager import insert_question
import re

def parse_block(q_unit, level_id):
    # 1. 解析头部
    header = q_unit[0]
    header_text = header if isinstance(header, str) else header.text
    m = re.search(r'\[T\]([A-Z]{2}\d{3})\s+(\d+)\s+(\d+)\s+(\d+)', header_text)
    if not m:
        raise ValueError(f"头部解析失败: {header_text}")
    recognition_code, lvl_code, qtype_code, diff_coef = m.groups()
    lvl_code, qtype_code, diff_coef = map(int, (lvl_code, qtype_code, diff_coef))

    # 2. 拼接原始题干+选项
    blocks = BaseParser().parse_content_blocks(q_unit)
    raw = blocks['T']

    # 3. 删除首行，剥离选项
    lines = raw.splitlines()
    body = lines[1:] if len(lines) > 1 else []
    stem = []
    for line in body:
        if re.match(r'^[A-D][、\.]\s*', line):
            continue
        stem.append(line)
    question_text = '\n'.join(stem).strip()

    # 4. 提取选项
    option_pattern = re.compile(r'^([A-D])[、\.]\s*(.+)$')
    option_a = option_b = option_c = option_d = None

    segments = []
    for para in q_unit:
        text = para if isinstance(para, str) else para.text
        text = text.strip()
        if any(text.startswith(f"{l}、") or text.startswith(f"{l}.") for l in "ABCD"):
            parts = text.split('\t')
            for seg in parts:
                segments.append(seg.strip())

    for seg in segments:
        m2 = option_pattern.match(seg)
        if not m2:
            continue
        letter, content = m2.groups()
        if letter == 'A':
            option_a = content
        elif letter == 'B':
            option_b = content
        elif letter == 'C':
            option_c = content
        elif letter == 'D':
            option_d = content

    # 5. 答案
    answer_text = blocks['D']

    # 6. 写入
    return insert_question(
        level_id,
        recognition_code,
        lvl_code,
        qtype_code,
        diff_coef,
        "多选",
        question_text,
        option_a, option_b, option_c, option_d,
        answer_text,
        has_formula=0,
        answer_explanation=None,
        scoring_criteria=None
    )

def parse(paragraphs, level_id=1):
    count, errors = 0, []
    for idx, unit in enumerate(paragraphs):
        try:
            if parse_block(unit, level_id):
                count += 1
            else:
                errors.append(f"第{idx+1}题 写入失败")
        except Exception as e:
            errors.append(f"第{idx+1}题 解析错误: {e}")
    return count, errors
