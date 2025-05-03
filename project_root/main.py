# main.py

import os
import logging
from parse_manager import process_document

# ========== 日志配置 ==========
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
log_file = os.path.join(LOG_DIR, "parsing.log")

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 清除旧的处理器
if logger.hasHandlers():
    logger.handlers.clear()

# 设置 UTF-8 日志写入
file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# ========== 主程序 ==========
def main():
    input_file = "all_questions.docx"

    if not os.path.exists(input_file):
        print("❌ 无法找到试卷文件，请确保 all_questions.docx 位于项目根目录。")
        logging.error(f"文件不存在：{input_file}")
        return

    logging.info(f"开始处理文件：{input_file}")
    results = process_document(input_file)

    if results is None:
        print("❌ 解析失败，请检查 logs/parsing.log 查看详细错误信息。")
        return

    # ✅ 控制台输出总结信息（不再写入日志）
    print("✅ 解析完成，各题型数量：")
    print(f"单选题：{len(results.get('single_choice', []))}")
    print(f"多选题：{len(results.get('multiple_choice', []))}")
    print(f"判断题：{len(results.get('judgment', []))}")
    print(f"简答题：{len(results.get('short_answer', []))}")
    print(f"计算题：{len(results.get('calculation', []))}")

if __name__ == "__main__":
    main()
