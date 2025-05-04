# utils.py

import re
import logging

def process_docx_from_paragraphs(paragraphs):
    r"""
    按 [T] 标签里的题型代码对题目块分段归类，支持五种题型：
      1 => 单项选择题(single_choice)
      2 => 多项选择题(multiple_choice)
      3 => 判断题(judgment)
      4 => 简答题(short_answer)
      5 => 计算题(calculation)

    实现思路：
    1. 将所有段落（Paragraph 或 str）转为纯文本，并过滤空行
    2. 用正向零宽断言 (?m)(?=\d+\.\s*\[T\]) 按题号分割出题块
    3. 每块取第一行，匹配题型代码
    4. 根据代码分发到对应 sections
    """
    logging.info("开始按题型分割文档内容（基于[T]标签）")

    # 1. 收集所有非空文本行
    lines = []
    for p in paragraphs:
        txt = p.text if hasattr(p, 'text') else str(p)
        txt = txt.strip()
        if txt:
            lines.append(txt)
    text = "\n".join(lines)

    # 2. 分割成若干题块（允许题号与 [T] 之间有空格）
    blocks = re.split(r'(?m)(?=\d+\.\s*\[T\])', text)
    blocks = [blk for blk in blocks if blk.strip()]

    # 3. 准备存放容器
    sections = {
        "single_choice":   [],
        "multiple_choice": [],
        "judgment":        [],
        "short_answer":    [],
        "calculation":     []
    }
    # 题型代码到 sections 键的映射
    mapping = {
        "1": "single_choice",
        "2": "multiple_choice",
        "3": "judgment",
        "4": "short_answer",
        "5": "calculation"
    }
    # 正则：匹配形如 "800.[T]BG010 5 1 5"（字段由任意空白分隔）
    pattern = re.compile(r'^\s*\d+\.\s*\[T\]\s*\S+\s+\d+\s+([1-5])\s+\d+')

    # 4. 逐块匹配并分发
    for idx, blk in enumerate(blocks, start=1):
        chunk_lines = blk.splitlines()
        first_line = chunk_lines[0]
        m = pattern.match(first_line)
        if not m:
            logging.warning(f"第 {idx} 块无法识别题型代码，头行：{first_line!r}")
            continue

        code = m.group(1)
        sec_key = mapping.get(code)
        if not sec_key:
            logging.warning(f"第 {idx} 块题型代码 {code} 未映射，头行：{first_line!r}")
            continue

        sections[sec_key].append(chunk_lines)

    # 5. 打印各题型数量，便于验证
    for key, lst in sections.items():
        logging.info(f"[DEBUG] 分割后 {key} 共 {len(lst)} 道题")

    return sections
