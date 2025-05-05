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

# 导入并初始化数据库（使用模块级函数）
import database.db_manager as db
db.init_db()

def process_document(file_path, level_id=1):
    """
    解析 Word 文档，按题型分段并调用解析器，
    然后将题目与媒体写入数据库，返回写库汇总。
    """
    if not os.path.exists(file_path):
        logging.error(f"文件不存在: {file_path}")
        return None

    # 延迟导入，避免循环依赖
    from preprocessor import preprocess_document
    from utils import process_docx_from_paragraphs
    from parser import single_choice, multiple_choice, judgment, short_answer, calculation

    # 1. 文档预处理
    pre_output = preprocess_document(file_path)
    paragraphs = pre_output.get('paragraphs', [])
    media_list = pre_output.get('media', [])

    if not paragraphs:
        logging.error("预处理失败，未生成段落")
        return None

    logging.info(f"预处理：共生成 {len(paragraphs)} 个段落，媒体 {len(media_list)} 条")

    # 建立 temp_id → 媒体元数据 映射
    media_catalog = {m['temp_id']: m for m in media_list}

    # 2. 按题型分段
    sections = process_docx_from_paragraphs(paragraphs)

    # —— 保留原有 Debug 输出来排查分段正确性 —— 
    for key, section in sections.items():
        logging.info(f"[DEBUG] {key} 共 {len(section)} 个单元，示例前 3 个：")
        for i, unit in enumerate(section[:3]):
            txt = unit if isinstance(unit, str) else getattr(unit, 'text', str(unit))
            logging.info(f"  单元 {i}: {txt[:50]!r}")
    # —— Debug 结束 —— 

    # 3. 调用各解析器，获取 (items, errors)
    sc_items, sc_errors = single_choice.parse(
        sections.get("single_choice", []), level_id, media_catalog
    )
    mc_items, mc_errors = multiple_choice.parse(
        sections.get("multiple_choice", []), level_id, media_catalog
    )
    jd_items, jd_errors = judgment.parse(
        sections.get("judgment", []), level_id, media_catalog
    )
    sa_items, sa_errors = short_answer.parse(
        sections.get("short_answer", []), level_id, media_catalog
    )
    cl_items, cl_errors = calculation.parse(
        sections.get("calculation", []), level_id, media_catalog
    )

    # 4. 写库：题目 + 媒体
    def write_items(items):
        for qdict, media_refs in items:
            # 插入题目，获取新 question_id
            qid = db.insert_question(**qdict)
            # 插入对应媒体
            for temp_id in media_refs:
                m = media_catalog.get(temp_id)
                if not m:
                    logging.warning(f"未找到 media temp_id={temp_id}")
                    continue
                if m['type'] == 'image':
                    db.insert_question_image(qid, m['path'])
                    logging.info(f"[INFO] 已写入图片：question_id={qid}, path={m['path']}")
                else:
                    db.insert_question_formula(qid, m['type'], m['content'])
                    logging.info(f"[INFO] 已写入公式：question_id={qid}, type={m['type']}")

    # 分题型写库
    write_items(sc_items)
    write_items(mc_items)
    write_items(jd_items)
    write_items(sa_items)
    write_items(cl_items)

    # 写库完成日志
    logging.info(
        f"写库完成：单选{len(sc_items)} 多选{len(mc_items)} "
        f"判断{len(jd_items)} 简答{len(sa_items)} 计算{len(cl_items)}"
    )

    # 5. 返回写库汇总
    return {
        "single_choice":   {"count": len(sc_items),   "errors": sc_errors},
        "multiple_choice": {"count": len(mc_items),   "errors": mc_errors},
        "judgment":        {"count": len(jd_items),   "errors": jd_errors},
        "short_answer":    {"count": len(sa_items),   "errors": sa_errors},
        "calculation":     {"count": len(cl_items),   "errors": cl_errors}
    }

if __name__ == "__main__":
    # 命令行快速测试
    result = process_document("test_questions.docx", level_id=1)
    print("处理结果：", result)
    print("详见日志：", log_file)
