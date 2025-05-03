# parse_manager.py

import os, logging

def process_document(file_path):
    if not os.path.exists(file_path):
        logging.error(f"文件不存在: {file_path}")
        return None

    from preprocessor import preprocess_document
    from utils import process_docx_from_paragraphs
    from parser import single_choice, multiple_choice, judgment, short_answer, calculation

    paragraphs = preprocess_document(file_path)
    if not paragraphs:
        logging.error("预处理失败，未生成段落")
        return None

    sections = process_docx_from_paragraphs(paragraphs)

    sc = single_choice.parse(sections.get("single_choice", []))
    mc = multiple_choice.parse(sections.get("multiple_choice", []))
    jd = judgment.parse(sections.get("judgment", []))
    sa = short_answer.parse(sections.get("short_answer", []))
    cl = calculation.parse(sections.get("calculation", []))

    logging.info(f"解析完成：单选{len(sc)} 多选{len(mc)} 判断{len(jd)} 简答{len(sa)} 计算{len(cl)}")

    return {
        "single_choice": sc,
        "multiple_choice": mc,
        "judgment": jd,
        "short_answer": sa,
        "calculation": cl,
    }

# 初始化日志
log_file = os.path.join("logs", "parsing.log")
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename=log_file,
    filemode="w",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)
