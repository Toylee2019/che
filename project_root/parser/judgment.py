# parser/judgment.py

import re
from parser.base_parser import BaseParser

def parse_block(q_unit, level_id, media_catalog=None):
    """
    解析单条判断题，返回 question_dict 和 media_refs。
    """
    # 1. 头部解析
    header = q_unit[0]
    header_text = header.text if hasattr(header, 'text') else str(header)
    m = re.search(r'\[T\]([A-Z]{2}\d{3})\s+(\d+)\s+(\d+)\s+(\d+)', header_text)
    if not m:
        raise ValueError(f"头部解析失败: {header_text}")
    recognition_code, lvl_code, qtype_code, diff_coef = m.groups()
    lvl_code, qtype_code, diff_coef = map(int, (lvl_code, qtype_code, diff_coef))

    # 2. 内容块解析
    blocks = BaseParser().parse_content_blocks(q_unit)

    # 3. 清洗题干（去掉首行）
    lines = blocks['T'].splitlines()
    question_text = '\n'.join(lines[1:]).strip() if len(lines) > 1 else ''

    # 4. 答案与解析
    answer_text        = blocks['D']
    answer_explanation = blocks['S']

    # 5. 构造 question_dict
    question_dict = {
        'level_id': level_id,
        'recognition_code': recognition_code,
        'level_code': lvl_code,
        'question_type_code': qtype_code,
        'difficulty_coefficient': diff_coef,
        'question_type': "判断",
        'content_text': question_text,
        'option_a': None,
        'option_b': None,
        'option_c': None,
        'option_d': None,
        'answer': answer_text,
        'has_formula': 0,
        'answer_explanation': answer_explanation,
        'scoring_criteria': None
    }

    # 6. 提取媒体引用
    full_text = "\n".join(
        para if isinstance(para, str) else (para.text or "")
        for para in q_unit
    )
    media_refs = [int(x) for x in re.findall(r'\[IMAGE_(\d+)\]', full_text)]
    media_refs += [int(x) for x in re.findall(r'\[MATH_(\d+)\]', full_text)]

    return question_dict, media_refs

def parse(paragraphs, level_id=1, media_catalog=None):
    """
    解析判断题列表，对每道题：
    - 检查答案必须是“√”或“×”
    - 如果答案是“×”，必须有解析
    """
    items, errors = [], []

    # 逐题解析，并附带认定点编码的错误收集
    for idx, unit in enumerate(paragraphs):
        header = unit[0]
        header_text = header.text if hasattr(header, 'text') else str(header)
        m_code = re.search(r'\[T\]([A-Z]{2}\d{3})', header_text)
        rec_code = m_code.group(1) if m_code else f"第{idx+1}题"

        try:
            qdict, media_refs = parse_block(unit, level_id, media_catalog)
            items.append((qdict, media_refs))
        except Exception as e:
            errors.append(f"解析错误：判断题{rec_code} {e}")
    
    # 对每道题再做格式校验
    for qdict, _ in items:
        code = qdict['recognition_code']
        ans  = qdict['answer']
        if ans not in ("√", "×"):
            errors.append(f"{code} 判断题: 非法答案 '{ans}'")
        if ans == "×" and not qdict.get('answer_explanation'):
            errors.append(f"{code} 判断题: 错误选项缺少解析")

    return items, errors
