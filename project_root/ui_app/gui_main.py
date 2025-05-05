# ui_app/gui_main.py

import sys
import os
import logging
from collections import defaultdict
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QComboBox,
    QPushButton, QTextEdit, QListWidget, QFileDialog,
    QVBoxLayout, QHBoxLayout, QTabWidget, QSplitter, QMessageBox,
    QProgressBar
)
from PyQt6.QtCore import Qt, QThread, QTimer
from ui_utils import apply_dark_theme, apply_light_theme

from config.requirements import EXPECT_COUNTS
from database.db_manager import (
    init_db, get_job_id, get_level_id,
    has_questions, count_questions, delete_questions_by_level,
    fetch_questions_by_level
)
from ui_app.worker import ParseWorker


logging.basicConfig(
    filename="logs/gui.log",
    filemode="a",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("题库管理系统")
        self.setGeometry(100, 100, 1000, 600)
        self.selected_file = ""
        self.dark_mode = True

        # 保存上下文
        self.current_job_name = ""
        self.current_level_text = ""
        self.current_level_id = None

        # 假进度定时器（慢进度）
        self.fake_timer = QTimer(self)
        self.fake_timer.setInterval(150)
        self.fake_timer.timeout.connect(self._on_fake_tick)

        # 炫光色相定时器
        self.hue_timer = QTimer(self)
        self.hue_timer.setInterval(50)
        self.hue_timer.timeout.connect(self._on_hue_tick)
        self.current_hue = 0

        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_param_log_tab(), "参数与日志")
        self.tabs.addTab(self.create_question_tab(), "题库与文档生成")
        self.setCentralWidget(self.tabs)

        apply_dark_theme(self)

    def toggle_theme(self):
        if self.dark_mode:
            apply_light_theme(self)
            self.theme_btn.setText("☀️")
        else:
            apply_dark_theme(self)
            self.theme_btn.setText("🌙")
        self.dark_mode = not self.dark_mode

    def create_param_log_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 第一行：工种名称 + 级别
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("工种名称："))
        self.job_input = QLineEdit()
        row1.addWidget(self.job_input)
        row1.addWidget(QLabel("级别："))
        self.level_combo = QComboBox()
        self.level_combo.addItems(["初级工", "中级工", "高级工", "技师", "高级技师"])
        row1.addWidget(self.level_combo)
        layout.addLayout(row1)

        # 第二行：按钮组
        row2 = QHBoxLayout()
        self.theme_btn = QPushButton("🌙")
        self.theme_btn.setFixedSize(50, 32)
        self.theme_btn.clicked.connect(self.toggle_theme)
        row2.addWidget(self.theme_btn)

        file_btn = QPushButton("选择文件")
        file_btn.setFixedHeight(32)
        file_btn.clicked.connect(self.select_file)
        row2.addWidget(file_btn)

        self.file_label = QLabel("未选择文件")
        row2.addWidget(self.file_label)
        row2.addStretch()

        parse_btn = QPushButton("开始解析")
        parse_btn.setFixedHeight(32)
        parse_btn.clicked.connect(self.start_parsing)
        row2.addWidget(parse_btn)

        clear_btn = QPushButton("清除日志")
        clear_btn.setFixedHeight(32)
        clear_btn.clicked.connect(self.clear_log_output)
        row2.addWidget(clear_btn)

        export_btn = QPushButton("生成新文件")
        export_btn.setFixedHeight(32)
        export_btn.clicked.connect(self.export_file_placeholder)
        row2.addWidget(export_btn)

        upload_btn = QPushButton("提交服务器")
        upload_btn.setFixedHeight(32)
        upload_btn.clicked.connect(self.upload_to_server_placeholder)
        row2.addWidget(upload_btn)

        layout.addLayout(row2)

        # 第三行：日志输出 + 细进度条 + 百分比 + 状态
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        # 进度条高度设为1px
        self.progress_bar.setFixedHeight(1)

        self.percent_label = QLabel("0%")
        self.percent_label.setFixedWidth(40)

        self.status_label = QLabel("")
        self.status_label.setMinimumWidth(120)

        row3 = QHBoxLayout()
        row3.addStretch()
        row3.addWidget(QLabel("日志输出："))
        row3.addWidget(self.progress_bar, stretch=1)
        row3.addWidget(self.percent_label)
        row3.addWidget(self.status_label)
        layout.addLayout(row3)

        # 日志输出区
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)

        return tab

    def create_question_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        splitter = QSplitter(Qt.Orientation.Vertical)
        self.question_list = QListWidget()
        splitter.addWidget(self.question_list)
        self.question_preview = QTextEdit()
        self.question_preview.setReadOnly(True)
        splitter.addWidget(self.question_preview)
        layout.addWidget(splitter)
        return tab

    def select_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择试卷文件", "", "Word 文档 (*.docx)"
        )
        if path:
            self.selected_file = path
            self.file_label.setText(os.path.basename(path))
            self.log_output.append(f"[INFO] 已选择文件：{path}")

    def start_parsing(self):
        if not self.selected_file:
            self.log_output.append("[ERROR] 未选择文件")
            return

        self.tabs.setEnabled(False)
        init_db()

        job_name = self.job_input.text().strip()
        level_text = self.level_combo.currentText().strip()
        if not job_name:
            QMessageBox.warning(self, "缺少工种名称", "请先输入“工种名称”再继续")
            self.tabs.setEnabled(True)
            return

        job_id = get_job_id(job_name)
        level_id = get_level_id(job_id, level_text)

        self.current_job_name = job_name
        self.current_level_text = level_text
        self.current_level_id = level_id

        if has_questions(level_id):
            old_cnt = count_questions(level_id)
            reply = QMessageBox.question(
                self,
                "确认删除旧题库",
                f"{job_name} 工种已有 {level_text} 级别题库（共 {old_cnt} 题），删除后才能上传新题库，是否继续？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                self.log_output.append("[INFO] 用户取消上传新题库")
                self.tabs.setEnabled(True)
                return
            delete_questions_by_level(level_id)
            new_cnt = count_questions(level_id)
            self.log_output.append(
                f"[INFO] 已删除旧题库：共删除 {old_cnt - new_cnt} 题（原 {old_cnt} 题，现 {new_cnt} 题）"
            )

        # 启动炫光与假进度
        self.hue_timer.start()
        self.fake_timer.stop()

        self.thread = QThread()
        self.worker = ParseWorker(self.selected_file, level_id)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.error.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.error.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def update_progress(self, value: int, message: str):
        # 假进度阈值恢复到 35%
        if value < 35:
            self.progress_bar.setValue(value)
            self.percent_label.setText(f"{value}%")
        elif value == 35:
            self.progress_bar.setValue(35)
            self.percent_label.setText("35%")
            self.fake_timer.start()
        else:
            self.fake_timer.stop()
            self.progress_bar.setValue(100)
            self.percent_label.setText("100%")

        self.status_label.setText(message)
        # 仅在进度 <100 时写日志
        if value < 100:
            self.log_output.append(f"[INFO] {message} ({value}%)")

    def _on_fake_tick(self):
        cur = int(self.percent_label.text().rstrip("%"))
        if cur < 95:
            cur += 1
            self.progress_bar.setValue(cur)
            self.percent_label.setText(f"{cur}%")
        else:
            self.fake_timer.stop()

    def _on_hue_tick(self):
        self.current_hue = (self.current_hue + 5) % 360
        style = f"""
            QProgressBar::chunk {{
                background: hsl({self.current_hue}, 100%, 50%);
            }}
        """
        self.progress_bar.setStyleSheet(style)

    def on_finished(self, summary: dict):
        self.tabs.setEnabled(True)
        self.fake_timer.stop()
        self.hue_timer.stop()

        # 只写一次“解析完成”
        self.progress_bar.setValue(100)
        self.percent_label.setText("100%")
        self.status_label.setText("解析完成")
        self.log_output.append("[INFO] 解析完成 (100%)")

        text = "[INFO] 解析结果汇总：\n"
        type_map = {
            "single_choice": "单项选择题",
            "multiple_choice": "多项选择题",
            "judgment": "判断题",
            "short_answer": "简答题",
            "calculation": "计算题"
        }
        for key in ["single_choice", "multiple_choice", "judgment", "short_answer", "calculation"]:
            res = summary.get(key, {"count": 0, "errors": []})
            cnt = res["count"]
            errs = res["errors"]
            text += f"{type_map[key]}：成功 {cnt} 失败 {len(errs)}\n"
            for e in errs:
                text += f"  ⚠️ {e}\n"

        qs_all = fetch_questions_by_level(self.current_level_id)
        for label in ["单选", "多选", "判断"]:
            expected = EXPECT_COUNTS[self.current_level_text].get(label, 0)
            codes = {q["recognition_code"] for q in qs_all if q["question_type"] == label}
            if not codes:
                continue
            errs = []
            for code in sorted(codes):
                group = [q for q in qs_all if q["recognition_code"] == code and q["question_type"] == label]
                actual = len(group)
                if actual != expected:
                    errs.append(f"认定点 {code}：{label} 数量不符，要求 {expected}，实际 {actual}")
                if label == "判断":
                    trues = [q for q in group if q["answer"] == "√"]
                    falses = [q for q in group if q["answer"] == "×"]
                    if not trues:
                        errs.append(f"认定点 {code}：判断题中“√”题数不足")
                    if not falses:
                        errs.append(f"认定点 {code}：判断题中“×”题数不足")
                    for q in falses:
                        if not q.get("answer_explanation"):
                            errs.append(f"认定点 {code}：判断题“×”题缺少解析")
            if errs:
                text += f"\n[ERROR] —— {label}题 校验错误 ——\n"
                for e in errs:
                    text += f"[ERROR] {e}\n"

        self.log_output.append(text)

    def on_error(self, msg: str):
        self.tabs.setEnabled(True)
        self.fake_timer.stop()
        self.hue_timer.stop()
        self.log_output.append(f"[ERROR] {msg}")
        QMessageBox.critical(self, "错误", f"发生异常：{msg}")

    def clear_log_output(self):
        self.log_output.clear()
        log_path = os.path.join("logs", "parsing.log")
        try:
            if os.path.exists(log_path):
                logging.shutdown()
                os.remove(log_path)
                self.log_output.append("[INFO] 日志文件已删除。")
        except Exception as e:
            self.log_output.append(f"[ERROR] 无法删除日志文件: {e}")

    def export_file_placeholder(self):
        self.log_output.append("[提示] 功能待实现：生成新文件")

    def upload_to_server_placeholder(self):
        self.log_output.append("[提示] 功能待实现：提交服务器")


def launch_gui():
    """供 gui_launcher.py 导入启动"""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    launch_gui()
