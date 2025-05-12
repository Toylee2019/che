# ui_app/worker.py

import os
from PyQt6.QtCore import QObject, pyqtSignal
from parse_manager import process_document
from preprocessor import preprocess_document
from utils import process_docx_from_paragraphs
from parser import single_choice, multiple_choice, judgment, short_answer, calculation

class ParseWorker(QObject):
    """
    后台解析题库并写入数据库的 Worker。
    - progress: 发射 (0-100, 文本) 用于更新进度条和日志
    - warning:  发射 str(msg) 用于解析错误的警告
    - finished: 发射 dict(summary) 完成后传递写库摘要
    - error:    发射 str(msg) 异常时传递错误信息
    """
    progress = pyqtSignal(int, str)
    warning  = pyqtSignal(str)       # 新增：用于逐条发出解析错误
    finished = pyqtSignal(dict)
    error    = pyqtSignal(str)

    def __init__(self, file_path: str, level_id: int):
        super().__init__()
        self.file_path = file_path
        self.level_id = level_id

    def run(self):
        try:
            # 1. 预处理
            self.progress.emit(5, "正在预处理文档…")
            pre = preprocess_document(self.file_path)
            paragraphs    = pre.get('paragraphs', [])
            media_catalog = pre.get('media', {})

            # 2. 分段
            self.progress.emit(10, "正在按题型分段…")
            sections = process_docx_from_paragraphs(paragraphs)

            # 3. 各题型解析（仅收集 errors，不立即输出）
            parsers = [
                ("单选", single_choice.parse,   "single_choice"),
                ("多选", multiple_choice.parse, "multiple_choice"),
                ("判断", judgment.parse,        "judgment"),
                ("简答", short_answer.parse,     "short_answer"),
                ("计算", calculation.parse,     "calculation"),
            ]
            total = len(parsers)
            all_errors = {}  # 暂存所有解析阶段的错误
            for idx, (name, func, key) in enumerate(parsers, start=1):
                pct = 10 + int(25 * idx / total)
                self.progress.emit(pct, f"正在解析{name}…")
                items, errors = func(
                    sections.get(key, []),
                    self.level_id,
                    {m['temp_id']: m for m in media_catalog}
                )
                all_errors[key] = errors
                # 不在此处输出 errors，避免重复

            # 4. 写库阶段
            self.progress.emit(35, "正在写入数据库…")
            summary = process_document(self.file_path, self.level_id)

            # 5. 合并解析阶段的 errors 到 summary 并去重
            for key, errs in all_errors.items():
                existing = summary.get(key, {}).get("errors", [])
                combined = errs + existing
                unique = []
                for e in combined:
                    if e not in unique:
                        unique.append(e)
                if key in summary:
                    summary[key]["errors"] = unique
                else:
                    summary[key] = {"count": 0, "errors": unique}

            # 5.1 逐条发出 warning
            type_map = {
                "single_choice":   "单选",
                "multiple_choice": "多选",
                "judgment":        "判断",
                "short_answer":    "简答",
                "calculation":     "计算"
            }
            for key, info in summary.items():
                for e in info.get("errors", []):
                    self.warning.emit(f"[警告] {type_map[key]}题解析错误：{e}")

            # 6. 写库阶段统计
            for key, info in summary.items():
                name = type_map.get(key, key)
                cnt  = info.get("count", 0)
                self.progress.emit(35, f"已写入{name}{cnt}题")

            # 7. 完成
            self.progress.emit(100, "解析完成")
            self.finished.emit(summary)

        except Exception as e:
            self.error.emit(str(e))
