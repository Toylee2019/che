import logging
import re

def process_docx_from_paragraphs(paragraphs):
    """
    接受预处理后的段落列表（每个段落为一个字符串），
    按题型（单项选择题、多项选择题、判断题、简答题、计算题）分割内容，
    并把每道题的多行内容合并成一个列表单元返回。
    返回字典：{ 'single_choice': [[line1, line2,...], ...], ... }
    """
    logging.info("开始按题型分割文档内容")
    # 题型关键字映射
    type_map = {
        "single_choice": "单项选择题",
        "multiple_choice": "多项选择题",
        "judgment": "判断题",
        "short_answer": "简答题",
        "calculation": "计算题"
    }
    sections = {k: [] for k in type_map}
    current_type = None
    current_unit = []

    for line in paragraphs:
        line = line.strip()
        if not line:
            continue

        # 检测题型切换
        for key, title in type_map.items():
            if title in line:
                current_type = key
                logging.info(f"切换到题型: {key}")
                current_unit = []
                break
        else:
            if current_type is None:
                logging.warning(f"未归类的文本: {line}")
                continue

            # 若行以题号开头或包含 [T]，则视为新题开始
            if re.match(r'^\d+\.', line) or '[T]' in line:
                # 把上一个题单元存入
                if current_unit:
                    sections[current_type].append(current_unit)
                current_unit = [line]
            else:
                # 续写当前题单元
                current_unit.append(line)

    # 把最后一个单元也存入
    if current_type and current_unit:
        sections[current_type].append(current_unit)

    return sections
