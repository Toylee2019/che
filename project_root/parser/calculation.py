from parser.base_parser import BaseParser
from database.db_manager import insert_question
import re

def parse_block(q_unit, level_id):
    # 1. 头部解析
    header = q_unit[0]
    header_text = header.text if hasattr(header, 'text') else str(header)
    m = re.search(r'\[T\]([A-Z]{2}\d{3})\s+(\d+)\s+(\d+)\s+(\d+)', header_text)
    if not m:
        raise ValueError(f"头部解析失败: {header_text}")
    recognition_code, lvl_code, qtype_code, diff_coef = m.groups()
    lvl_code, qtype_code, diff_coef = map(int, (lvl_code, qtype_code, diff_coef))

    # 2. 拼接并清洗题干（去掉首行）
    blocks = BaseParser().parse_content_blocks(q_unit)
    lines = blocks['T'].splitlines()
    question_text = '\n'.join(lines[1:]).strip() if len(lines) > 1 else ''

    # 3. 解答过程与评分标准
    answer_text      = blocks['D']  # 解答过程
    scoring_standard = blocks['S']  # 评分标准

    # 4. 写入数据库
    return insert_question(
        level_id,
        recognition_code,
        lvl_code,
        qtype_code,
        diff_coef,
        "计算",
        question_text,
        None, None, None, None,
        answer_text,
        has_formula=1,
        answer_explanation=None,
        scoring_criteria=scoring_standard
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
