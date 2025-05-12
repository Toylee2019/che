# parser/short_answer.py

import re
from parser.base_parser import BaseParser

def parse_block(q_unit, level_id, media_catalog=None):
    # 1. 头部解析
    header = q_unit[0]
    header_text = header.text if hasattr(header, 'text') else str(header)
    m = re.search(r'\[T\]([A-Z]{2}\d{3})\s+(\d+)\s+(\d+)\s+(\d+)', header_text)
    if not m:
        raise ValueError(f"头部解析失败: {header_text}")
    recognition_code, lvl_code, qtype_code, diff_coef = m.groups()
    lvl_code, qtype_code, diff_coef = map(int, (lvl_code, qtype_code, diff_coef))

    # 2. 拼接并清洗题干
    blocks = BaseParser().parse_content_blocks(q_unit)
    lines = blocks['T'].splitlines()
    question_text = '\n'.join(lines[1:]).strip() if len(lines) > 1 else ''

    # 3. 答案与评分标准
    answer_text      = blocks['D']
    scoring_standard = blocks['S']

    # 4. 构造返回值
    question_dict = {
        'level_id': level_id,
        'recognition_code': recognition_code,
        'level_code': lvl_code,
        'question_type_code': qtype_code,
        'difficulty_coefficient': diff_coef,
        'question_type': "简答",
        'content_text': question_text,
        'option_a': None,
        'option_b': None,
        'option_c': None,
        'option_d': None,
        'answer': answer_text,
        'has_formula': 0,
        'answer_explanation': None,
        'scoring_criteria': scoring_standard
    }

    # 5. 提取媒体引用
    full_text = "\n".join(
        para if isinstance(para, str) else (para.text or "")
        for para in q_unit
    )
    media_refs = [int(x) for x in re.findall(r'\[IMAGE_(\d+)\]', full_text)]
    media_refs += [int(x) for x in re.findall(r'\[MATH_(\d+)\]', full_text)]

    return question_dict, media_refs

def parse(paragraphs, level_id=1, media_catalog=None):
    """
    解析简答题，并在出错时附带认定点编码。
    """
    items, errors = [], []
    for idx, unit in enumerate(paragraphs):
        # 预提取认定点编码
        header = unit[0]
        header_text = header.text if hasattr(header, 'text') else str(header)
        m_code = re.search(r'\[T\]([A-Z]{2}\d{3})', header_text)
        rec_code = m_code.group(1) if m_code else f"第{idx+1}题"

        try:
            qdict, media_refs = parse_block(unit, level_id, media_catalog)
            items.append((qdict, media_refs))
        except Exception as e:
            errors.append(f"解析错误：简答题{rec_code} {e}")

    return items, errors
