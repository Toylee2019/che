# utils.py
import logging

def process_docx_from_paragraphs(paragraphs):
    """
    接受预处理后的段落列表（每个段落为一个字符串），
    按题型（单项选择题、多项选择题、判断题、简答题、计算题）分割内容，
    返回一个字典，键为题型标识，值为对应题目段落列表。
    """
    logging.info("开始按题型分割文档内容")
    current_type = None
    sections = {
        "single_choice": [],
        "multiple_choice": [],
        "judgment": [],
        "short_answer": [],
        "calculation": []
    }
    for line in paragraphs:
        if line == "":
            continue
        prefix = line[:10]
        if "单项选择题" in prefix:
            current_type = "single_choice"
            logging.info("切换到题型: single_choice")
            continue
        elif "多项选择题" in prefix:
            current_type = "multiple_choice"
            logging.info("切换到题型: multiple_choice")
            continue
        elif "判断题" in prefix:
            current_type = "judgment"
            logging.info("切换到题型: judgment")
            continue
        elif "简答题" in prefix:
            current_type = "short_answer"
            logging.info("切换到题型: short_answer")
            continue
        elif "计算题" in prefix:
            current_type = "calculation"
            logging.info("切换到题型: calculation")
            continue
        if current_type:
            sections[current_type].append(line)
        else:
            logging.warning(f"未归类的文本: {line}")
    return sections
