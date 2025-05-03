import sys, os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QComboBox,
    QPushButton, QTextEdit, QListWidget, QListWidgetItem, QFileDialog,
    QVBoxLayout, QHBoxLayout, QTabWidget, QSplitter
)
from PyQt6.QtCore import Qt
from ui_utils import apply_dark_theme, apply_light_theme
from format_utils import format_question_preview

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

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("工种名称："))
        self.job_input = QLineEdit()
        row1.addWidget(self.job_input)
        row1.addWidget(QLabel("级别："))
        self.level_combo = QComboBox()
        self.level_combo.addItems(["初级工", "中级工", "高级工", "技师", "高级技师"])
        row1.addWidget(self.level_combo)

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
        self.question_list.setWordWrap(True)
        self.question_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.question_list.itemClicked.connect(self.show_question_details)
        splitter.addWidget(self.question_list)

        self.question_preview = QTextEdit()
        self.question_preview.setReadOnly(True)
        splitter.addWidget(self.question_preview)

        layout.addWidget(splitter)
        return tab

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择试卷文件", "", "Word 文档 (*.docx)"
        )
        if file_path:
            self.selected_file = file_path
            self.file_label.setText(os.path.basename(file_path))
            self.log_output.append(f"[INFO] 已选择文件：{file_path}")
        else:
            self.selected_file = ""
            self.file_label.setText("未选择文件")

    def start_parsing(self):
        if not self.selected_file:
            self.log_output.append("[ERROR] 未选择文件")
            return
        try:
            from parse_manager import process_document
            results = process_document(self.selected_file)
            if results is None:
                self.log_output.append("[ERROR] 解析失败，请查看日志文件")
                return
            self.question_list.clear()
            index = 1
            for key, lst in results.items():
                for q in lst:
                    q["类别"] = key
                    display_text = q.get("question_text", "").strip()
                    if not display_text:
                        display_text = "（未提取题干）"
                    item = QListWidgetItem(f"{index}. {q.get('code', '')} - {display_text[:50]}")
                    item.setData(Qt.ItemDataRole.UserRole, q)
                    self.question_list.addItem(item)
                    index += 1
            self.update_log_from_file()
        except Exception as e:
            self.log_output.append(f"[EXCEPTION] {str(e)}")

    def update_log_from_file(self):
        path = os.path.join("logs", "parsing.log")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                self.log_output.setPlainText(f.read())

    def show_question_details(self, item):
        q = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(q, dict):
            formatted = format_question_preview(q, self.job_input.text(), self.level_combo.currentText())
            self.question_preview.setText(formatted)

    def clear_log_output(self):
        self.log_output.clear()
        log_path = os.path.join("logs", "parsing.log")
        try:
            if os.path.exists(log_path):
                os.remove(log_path)
                self.log_output.append("[INFO] 日志文件已删除。")
            else:
                self.log_output.append("[INFO] 日志文件不存在，无需删除。")
        except Exception as e:
            self.log_output.append(f"[ERROR] 无法删除日志文件: {str(e)}")

    def export_file_placeholder(self):
        self.log_output.append("[提示] 点击了“生成新文件”按钮（功能待实现）")

    def upload_to_server_placeholder(self):
        self.log_output.append("[提示] 点击了“提交服务器”按钮（功能待实现）")


def launch_gui():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
