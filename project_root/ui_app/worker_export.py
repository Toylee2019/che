# ui_app/worker_export.py

import os
from PyQt6.QtCore import QObject, pyqtSignal

class ExportWorker(QObject):
    """
    后台文档导出 Worker。
    接收题目 code 列表和导出选项，run() 会发出 progress，最后发出 finished。
    """
    progress = pyqtSignal(int, str)
    finished = pyqtSignal()

    def __init__(self, codes: list[str], opts: dict):
        super().__init__()
        self.codes = codes
        self.opts = opts

    def run(self):
        # 确保输出目录存在
        out_dir = "output"
        os.makedirs(out_dir, exist_ok=True)

        total = len(self.codes)
        # 这里简单模拟导出：你可以替换为真正的 docx 生成逻辑
        for idx, code in enumerate(self.codes, start=1):
            pct = int((idx - 1) / total * 100)
            self.progress.emit(pct, f"正在导出题目 {code}")
            # 模拟一点延迟
            import time; time.sleep(0.1)

        # 最后写入文件（示例：空白 docx）
        from docx import Document
        doc = Document()
        doc.add_heading("导出题库", level=1)
        for code in self.codes:
            doc.add_paragraph(f"{code} ... （内容省略）")
        # 模板选择逻辑可接入 self.opts["template"]
        out_path = os.path.join(out_dir, f"导出_{self.opts.get('template','default')}.docx")
        doc.save(out_path)

        # 完成 100%
        self.progress.emit(100, "导出完成")
        self.finished.emit()
