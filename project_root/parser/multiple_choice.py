import re
from parser.base_parser import BaseParser

def parse_block(q_unit, level_id, media_catalog=None):
    # 1. 解析头部
    header = q_unit[0]
    header_text = header if isinstance(header, str) else header.text or ""
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
    stem = [line for line in lines[1:] if not re.match(r'^[A-D][、\.]\s*', line)]
    question_text = '\n'.join(stem).strip()

    # 4. 提取选项
    option_pattern = re.compile(r'^([A-D])[、\.]\s*(.+)$')
    option_a = option_b = option_c = option_d = None
    segments = []
    for para in q_unit:
        text = para if isinstance(para, str) else para.text or ""
        for seg in text.strip().split('\t'):
            if re.match(r'^[A-D][、\.]\s*', seg):
                segments.append(seg.strip())
    for seg in segments:
        m2 = option_pattern.match(seg)
        if not m2:
            continue
        letter, content = m2.groups()
        if letter == 'A': option_a = content
        elif letter == 'B': option_b = content
        elif letter == 'C': option_c = content
        elif letter == 'D': option_d = content

    # 5. 答案
    answer_text = blocks['D']

    # 6. 构造返回值
    question_dict = {
        'level_id': level_id,
        'recognition_code': recognition_code,
        'level_code': lvl_code,
        'question_type_code': qtype_code,
        'difficulty_coefficient': diff_coef,
        'question_type': "多选",
        'content_text': question_text,
        'option_a': option_a,
        'option_b': option_b,
        'option_c': option_c,
        'option_d': option_d,
        'answer': answer_text,
        'has_formula': 0,
        'answer_explanation': None,
        'scoring_criteria': None
    }

    # 7. 提取媒体引用
    full_text = "\n".join(
        para if isinstance(para, str) else (para.text or "")
        for para in q_unit
    )
    media_refs = [int(x) for x in re.findall(r'\[IMAGE_(\d+)\]', full_text)]
    media_refs += [int(x) for x in re.findall(r'\[MATH_(\d+)\]', full_text)]

    return question_dict, media_refs

def parse(paragraphs, level_id=1, media_catalog=None):
    items, errors = [], []
    for idx, unit in enumerate(paragraphs):
        try:
            qdict, media_refs = parse_block(unit, level_id, media_catalog)
            items.append((qdict, media_refs))
        except Exception as e:
            errors.append(f"第{idx+1}题 解析错误: {e}")
    return items, errors
