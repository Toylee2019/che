# parse_manager.py

import os
import logging

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

def process_document(file_path, level_id=1):
    """
    解析 Word 文档，按题型分段并调用各解析器，返回每种题型的 (count, errors) 汇总。
    """
    if not os.path.exists(file_path):
        logging.error(f"文件不存在: {file_path}")
        return None

    from preprocessor import preprocess_document
    from utils import process_docx_from_paragraphs
    from parser import single_choice, multiple_choice, judgment, short_answer, calculation

    # 1. 文档预处理
    paragraphs = preprocess_document(file_path)
    if not paragraphs:
        logging.error("预处理失败，未生成段落")
        return None

    logging.info(f"预处理：共生成 {len(paragraphs)} 个段落")

    # 2. 按题型分段
    sections = process_docx_from_paragraphs(paragraphs)

    # —— Debug: 查看分段结果（前 3 个示例） —— 
    for key, section in sections.items():
        logging.info(f"[DEBUG] {key} 有 {len(section)} 个单元，示例前 3 个：")
        for i, unit in enumerate(section[:3]):
            if isinstance(unit, str):
                logging.info(f"  单元{i} 类型: str, 内容: {unit[:50]!r}")
            elif hasattr(unit, 'text'):
                txt = unit.text.strip()
                logging.info(f"  单元{i} 类型: Paragraph, 文本: {txt!r}")
            elif isinstance(unit, list):
                snippet = [ (getattr(p, 'text', str(p))[:30]) for p in unit[:3] ]
                logging.info(f"  单元{i} 类型: list, 段落数: {len(unit)}, 前几段: {snippet}")
            else:
                logging.info(f"  单元{i} 类型: {type(unit)}, 内容: {str(unit)[:50]!r}")
    # —— Debug 结束 —— 

    # —— 额外 Debug：打印所有 single_choice 单元的头部 —— 
    sc_units = sections.get("single_choice", [])
    logging.info(f"[DEBUG] single_choice 单元总数: {len(sc_units)}")
    for idx, unit in enumerate(sc_units, start=1):
        if isinstance(unit, list) and unit:
            first = unit[0]
            header = getattr(first, 'text', str(first)).strip()
        else:
            header = getattr(unit, 'text', str(unit)).strip()
        logging.info(f"[DEBUG] single_choice 单元 {idx} header: {header!r}")
    # —— 额外 Debug 结束 —— 

    # 3. 调用各解析器
    sc_count, sc_errors = single_choice.parse(sections.get("single_choice", []), level_id)
    mc_count, mc_errors = multiple_choice.parse(sections.get("multiple_choice", []), level_id)
    jd_count, jd_errors = judgment.parse(sections.get("judgment", []), level_id)
    sa_count, sa_errors = short_answer.parse(sections.get("short_answer", []), level_id)
    cl_count, cl_errors = calculation.parse(sections.get("calculation", []), level_id)

    logging.info(
        f"解析完成：单选{sc_count} 多选{mc_count} "
        f"判断{jd_count} 简答{sa_count} 计算{cl_count}"
    )

    # 4. 返回汇总
    return {
        "single_choice":   {"count": sc_count, "errors": sc_errors},
        "multiple_choice": {"count": mc_count, "errors": mc_errors},
        "judgment":        {"count": jd_count, "errors": jd_errors},
        "short_answer":    {"count": sa_count, "errors": sa_errors},
        "calculation":     {"count": cl_count, "errors": cl_errors},
    }
