# ui_app/gui_main.py

import sys
import os
import logging
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QComboBox,
    QPushButton, QTextEdit, QListWidget, QListWidgetItem, QFileDialog,
    QVBoxLayout, QHBoxLayout, QTabWidget, QSplitter, QMessageBox
)
from PyQt6.QtCore import Qt
from ui_utils import apply_dark_theme, apply_light_theme

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("题库管理系统")
        self.setGeometry(100, 100, 1000, 600)
        self.selected_file = ""
        self.dark_mode = True

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

        # 第二行：主题切换、选择文件、解析、清除日志、导出、上传
        row2 = QHBoxLayout()
        self.theme_btn = QPushButton("🌙")
        self.theme_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_btn.setFixedHeight(32)
        self.theme_btn.setMinimumWidth(50)
        self.theme_btn.setStyleSheet("font-size: 16px; padding: 4px 10px;")
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

        clear_log_btn = QPushButton("清除日志")
        clear_log_btn.setFixedHeight(32)
        clear_log_btn.clicked.connect(self.clear_log_output)
        row2.addWidget(clear_log_btn)

        export_btn = QPushButton("生成新文件")
        export_btn.setFixedHeight(32)
        export_btn.clicked.connect(self.export_file_placeholder)
        row2.addWidget(export_btn)

        upload_btn = QPushButton("提交服务器")
        upload_btn.setFixedHeight(32)
        upload_btn.clicked.connect(self.upload_to_server_placeholder)
        row2.addWidget(upload_btn)

        # 日志输出区
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)

        layout.addLayout(row1)
        layout.addLayout(row2)
        layout.addWidget(QLabel("日志输出："))
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

        from database.db_manager import (
            init_db, get_job_id, get_level_id,
            has_questions, count_questions, delete_questions_by_level
        )

        # 1. 确保数据库和表创建完成
        init_db()

        job_name = self.job_input.text().strip()
        level_text = self.level_combo.currentText().strip()
        if not job_name:
            self.log_output.append("[ERROR] 请先输入工种名称")
            return

        job_id = get_job_id(job_name)
        level_id = get_level_id(job_id, level_text)

        # 2. 如果已有旧题库，提示删除并打印删除前后数量
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
                return
            delete_questions_by_level(level_id)
            new_cnt = count_questions(level_id)
            self.log_output.append(
                f"[INFO] 已删除旧题库：共删除 {old_cnt - new_cnt} 题（原 {old_cnt} 题，现 {new_cnt} 题）"
            )

        # 3. 调用解析流程
        try:
            from parse_manager import process_document
            results = process_document(self.selected_file, level_id)
            if results is None:
                self.log_output.append("[ERROR] 解析失败，请查看日志文件")
                return

            type_map = {
                "single_choice": "单项选择题",
                "multiple_choice": "多项选择题",
                "judgment": "判断题",
                "short_answer": "简答题",
                "calculation": "计算题"
            }

            # 4. 正确获取 count/errors，避免字符串误用
            self.log_output.append("[INFO] 解析结果汇总：")
            for key in ["single_choice", "multiple_choice", "judgment", "short_answer", "calculation"]:
                res  = results.get(key, {"count": 0, "errors": []})
                cnt  = res.get("count", 0)
                errs = res.get("errors", [])
                self.log_output.append(f"{type_map[key]}：成功 {cnt} 题，失败 {len(errs)} 题")
                for e in errs:
                    self.log_output.append(f"  ⚠️ {e}")

        except Exception as e:
            self.log_output.append(f"[EXCEPTION] {e}")

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
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
