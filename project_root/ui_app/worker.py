# ui_app/worker.py

import os
from PyQt6.QtCore import QObject, pyqtSignal
from parse_manager import process_document
from preprocessor import preprocess_document
from utils import process_docx_from_paragraphs
from parser import single_choice, multiple_choice, judgment, short_answer, calculation

class ParseWorker(QObject):
    """
    运行题库解析和入库流程的后台 Worker，
    通过信号向主线程报告进度、完成结果或错误。
    """
    # 进度更新信号：百分比(0-100), 当前状态文本
    progress = pyqtSignal(int, str)
    # 完成信号：返回解析汇总结果 dict
    finished = pyqtSignal(dict)
    # 错误信号：返回错误信息字符串
    error = pyqtSignal(str)

    def __init__(self, file_path: str, level_id: int):
        super().__init__()
        self.file_path = file_path
        self.level_id = level_id

    def run(self):
        """
        在子线程中执行的入口方法：
        1. 预处理
        2. 分段
        3. 各题型解析
        4. 写库
        5. 发出完成信号
        """
        try:
            # 1. 预处理
            self.progress.emit(5, "正在预处理文档…")
            pre_output = preprocess_document(self.file_path)
            paragraphs = pre_output.get('paragraphs', [])
            media_catalog = pre_output.get('media', {})

            # 2. 分段
            self.progress.emit(10, "正在按题型分段…")
            sections = process_docx_from_paragraphs(paragraphs)

            # 3. 各题型解析
            parsers = [
                ("单选", single_choice.parse, "single_choice"),
                ("多选", multiple_choice.parse, "multiple_choice"),
                ("判断", judgment.parse, "judgment"),
                ("简答", short_answer.parse, "short_answer"),
                ("计算", calculation.parse, "calculation"),
            ]
            total = len(parsers)
            all_items = {}
            all_errors = {}
            for idx, (name, parser_func, key) in enumerate(parsers, start=1):
                pct = 10 + int(25 * idx / total)
                self.progress.emit(pct, f"正在解析{ name }…")
                items, errors = parser_func(
                    sections.get(key, []),
                    self.level_id,
                    {m['temp_id']: m for m in media_catalog}
                )
                all_items[key] = items
                all_errors[key] = errors

            # 4. 写库 + 后处理（调用 process_document 完整流程以保持一致性）
            self.progress.emit(35, "正在写入数据库…")
            summary = process_document(self.file_path, self.level_id)

            # 5. 完成
            self.progress.emit(100, "解析完成")
            self.finished.emit(summary)

        except Exception as e:
            # 捕获任何异常，发出错误信号
            self.error.emit(str(e))
