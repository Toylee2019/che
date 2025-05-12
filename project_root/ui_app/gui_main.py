import sys
import os
import logging
from collections import defaultdict
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QComboBox,
    QPushButton, QTextEdit, QListWidgetItem, QFileDialog,
    QVBoxLayout, QHBoxLayout, QTabWidget, QMessageBox,
    QProgressBar, QCheckBox, QFormLayout
)
from PyQt6.QtCore import Qt, QThread, QTimer
from ui_utils import apply_dark_theme, apply_light_theme

from config.requirements import EXPECT_COUNTS
from database.db_manager import (
    init_db, get_job_id, get_level_id,
    has_questions, count_questions, delete_questions_by_level,
    fetch_questions_by_level, fetch_jobs
)
from ui_app.worker import ParseWorker
from ui_app.worker_export import ExportWorker
from ui_app.preview_widget import PreviewWidget
from ui_app.checkable_list_widget import CheckableListWidget

# 确保 templates 目录存在
os.makedirs("templates", exist_ok=True)

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
        self.resize(1000, 600)
        self.dark_mode = True

        # 参数与日志上下文
        self.current_job_name = ""
        self.current_level_text = ""
        self.current_level_id = None

        # 进度条假计时器 & 色相计时器
        self.fake_timer = QTimer(self)
        self.fake_timer.setInterval(150)
        self.fake_timer.timeout.connect(self._on_fake_tick)
        self.hue_timer = QTimer(self)
        self.hue_timer.setInterval(50)
        self.hue_timer.timeout.connect(self._on_hue_tick)
        self.current_hue = 0

        # 主 Tab
        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_param_log_tab(), "参数与日志")
        self.tabs.addTab(self._build_export_tab(), "题库与文档生成")
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

    def update_preview(self, preview_text: str):
        """
        接收 ExportWorker.preview 信号，更新右侧预览区域。
        """
        self.preview2.append(preview_text)

    # ---------------- 参数与日志 Tab ----------------
    def _build_param_log_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 行1：工种名称 + 级别
        r1 = QHBoxLayout()
        r1.addWidget(QLabel("工种名称："))
        self.job_input = QLineEdit()
        r1.addWidget(self.job_input)
        r1.addWidget(QLabel("级别："))
        self.level_combo = QComboBox()
        self.level_combo.addItems(["初级工", "中级工", "高级工", "技师", "高级技师"])
        self.level_combo.setMinimumWidth(100)
        r1.addWidget(self.level_combo)
        layout.addLayout(r1)

        # 行2：按钮组
        r2 = QHBoxLayout()
        self.theme_btn = QPushButton("🌙")
        self.theme_btn.setFixedSize(50, 32)
        self.theme_btn.clicked.connect(self.toggle_theme)
        r2.addWidget(self.theme_btn)

        file_btn = QPushButton("选择文件")
        file_btn.setFixedHeight(32)
        file_btn.clicked.connect(self.select_file)
        r2.addWidget(file_btn)

        self.file_label = QLabel("未选择文件")
        r2.addWidget(self.file_label)
        r2.addStretch()

        parse_btn = QPushButton("开始解析")
        parse_btn.setFixedHeight(32)
        parse_btn.clicked.connect(self.start_parsing)
        r2.addWidget(parse_btn)

        clear_btn = QPushButton("清除日志")
        clear_btn.setFixedHeight(32)
        clear_btn.clicked.connect(self.clear_log_output)
        r2.addWidget(clear_btn)

        layout.addLayout(r2)

        # 行3：日志 + 进度 + 状态
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(1)

        self.percent_label = QLabel("0%")
        self.percent_label.setFixedWidth(40)
        self.status_label = QLabel("")
        self.status_label.setMinimumWidth(120)

        r3 = QHBoxLayout()
        r3.addStretch()
        r3.addWidget(QLabel("日志输出："))
        r3.addWidget(self.progress_bar, stretch=1)
        r3.addWidget(self.percent_label)
        r3.addWidget(self.status_label)
        layout.addLayout(r3)

        # 日志显示区
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)

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
        if not getattr(self, 'selected_file', None):
            self.log_output.append("[ERROR] 未选择文件")
            return

        self.tabs.setEnabled(False)
        init_db()

        job = self.job_input.text().strip()
        lvl = self.level_combo.currentText().strip()
        if not job:
            QMessageBox.warning(self, "缺少工种名称", "请先输入“工种名称”再继续")
            self.tabs.setEnabled(True)
            return

        jid = get_job_id(job)
        lid = get_level_id(jid, lvl)
        self.current_job_name = job
        self.current_level_text = lvl
        self.current_level_id = lid

        if has_questions(lid):
            old = count_questions(lid)
            reply = QMessageBox.question(
                self, "确认删除旧题库",
                f"{job} 工种已有 {lvl} 级别题库（共 {old} 题），删除后才能上传新题库，是否继续？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                self.log_output.append("[INFO] 用户取消上传新题库")
                self.tabs.setEnabled(True)
                return
            delete_questions_by_level(lid)
            new = count_questions(lid)
            self.log_output.append(
                f"[INFO] 已删除旧题库：共删除 {old - new} 题（原 {old} 题，现 {new} 题）"
            )

        self.hue_timer.start()
        self.fake_timer.stop()

        # 启动解析线程
        self.thread = QThread()
        self.worker = ParseWorker(self.selected_file, lid)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.update_progress)
        # 新增：接收逐条解析错误并输出到日志
        self.worker.warning.connect(lambda msg: self.log_output.append(msg))
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.error.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.error.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def update_progress(self, value: int, message: str):
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
        self.progress_bar.setStyleSheet(
            f"QProgressBar::chunk {{ background: hsl({self.current_hue},100%,50%); }}"
        )

    def on_finished(self, summary: dict):
        self.tabs.setEnabled(True)
        self.fake_timer.stop()
        self.hue_timer.stop()
        self.progress_bar.setValue(100)
        self.percent_label.setText("100%")
        self.status_label.setText("解析完成")
        self.log_output.append("[INFO] 解析完成 (100%)")

        # 汇总日志
        self.log_output.append("[INFO] 解析结果汇总：")
        type_map = {
            "single_choice":   "单项选择题",
            "multiple_choice": "多项选择题",
            "judgment":        "判断题",
            "short_answer":    "简答题",
            "calculation":     "计算题"
        }
        for key in type_map:
            info = summary.get(key, {})
            ok, err = info.get("count", 0), len(info.get("errors", []))
            self.log_output.append(f"{type_map[key]}：成功 {ok} 题，失败 {err} 题")

        # 判断题校验
        qs_all = fetch_questions_by_level(self.current_level_id)
        jd_qs = [q for q in qs_all if q["question_type"] == "判断"]
        groups = defaultdict(list)
        for q in jd_qs:
            groups[q["recognition_code"]].append(q)
        if groups:
            self.log_output.append("[ERROR] —— 判断题 校验错误 ——")
            for code, group in sorted(groups.items()):
                answers = [q["answer"] for q in group]
                if len(answers) == 2 and answers[0] == answers[1]:
                    self.log_output.append(
                        f"[ERROR] 解析错误：判断题{code} 两题答案都为'{answers[0]}'"
                    )

        # 刷新导出列表
        jobs = fetch_jobs()
        self.job_cb2.clear()
        self.job_cb2.addItems(jobs)
        self.job_cb2.setCurrentText(self.current_job_name)
        self.level_cb2.setCurrentText(self.current_level_text)
        self._reload2()

    def on_error(self, msg: str):
        self.tabs.setEnabled(True)
        self.fake_timer.stop()
        self.hue_timer.stop()
        self.log_output.append(f"[ERROR] {msg}")
        QMessageBox.critical(self, "错误", f"发生异常：{msg}")

    def clear_log_output(self):
        self.log_output.clear()
        log_path = "logs/parsing.log"
        if os.path.exists(log_path):
            logging.shutdown()
            os.remove(log_path)
            self.log_output.append("[INFO] 日志文件已删除。")

    # ---------------- 题库与文档生成 Tab ----------------
    def _build_export_tab(self):
        tab = QWidget()
        h = QHBoxLayout(tab)

        # 左侧筛选区
        left = QWidget()
        ll = QVBoxLayout(left)

        # 工种 | 级别
        top_row = QHBoxLayout()
        top_row.addWidget(QLabel("工种："))
        self.job_cb2 = QComboBox()
        self.job_cb2.setEditable(True)
        self.job_cb2.addItems(fetch_jobs())
        self.job_cb2.setMinimumWidth(150)
        top_row.addWidget(self.job_cb2)
        top_row.addWidget(QLabel("级别："))
        self.level_cb2 = QComboBox()
        self.level_cb2.addItems(["初级工", "中级工", "高级工", "技师", "高级技师"])
        self.level_cb2.setMinimumWidth(100)
        top_row.addWidget(self.level_cb2)
        ll.addLayout(top_row)

        # 题型复选框
        cb_row = QHBoxLayout()
        for name in ["单选", "多选", "判断", "简答", "计算"]:
            cb = QCheckBox(name)
            cb.setChecked(True)
            setattr(self, f"chk_{name}", cb)
            cb_row.addWidget(cb)
        ll.addLayout(cb_row)

        # 认定点搜索
        self.search_le2 = QLineEdit()
        self.search_le2.setPlaceholderText("按认定点搜索…")
        ll.addWidget(self.search_le2)

        # 可勾选列表
        self.q_list2 = CheckableListWidget()
        ll.addWidget(self.q_list2, 1)
        self.q_list2.itemChanged.connect(self._update_summary)

        # 全选/反选/清空
        btns = QHBoxLayout()
        btns.addWidget(QPushButton("全选", clicked=self._select_all2))
        btns.addWidget(QPushButton("反选", clicked=self._invert2))
        btns.addWidget(QPushButton("清空", clicked=self._clear2))
        ll.addLayout(btns)

        h.addWidget(left, 3)

        # 右侧：模板+统计+预览+导出
        right = QVBoxLayout()
        form = QFormLayout()

        self.tpl_cb = QComboBox()
        tmps = [f for f in os.listdir("templates")
                if f.endswith(".docx") and not f.startswith("~")]
        self.tpl_cb.addItems(tmps)
        form.addRow("模板：", self.tpl_cb)

        self.header_le2 = QLineEdit()
        form.addRow("页眉文本：", self.header_le2)

        self.summary_label = QLabel("单选0，多选0，判断0，简答0，计算0；已选 0 题")
        form.addRow("选题统计：", self.summary_label)

        ans_page = QHBoxLayout()
        self.cb_ans2 = QCheckBox("末尾加入答案与解析")
        self.cb_page2 = QCheckBox("卷面显示认定点")
        ans_page.addWidget(self.cb_ans2)
        ans_page.addWidget(self.cb_page2)
        ans_page.addStretch()
        ans_page.addWidget(QPushButton("生成文档", clicked=self._on_export2))
        ans_page.addWidget(QPushButton("打开输出目录", clicked=self._open2))
        form.addRow("", ans_page)

        right.addLayout(form)

        # 实时预览控件
        self.preview2 = PreviewWidget()
        right.addWidget(self.preview2, 1)

        h.addLayout(right, 5)

        # 绑定刷新信号
        widgets = [self.job_cb2, self.level_cb2, self.search_le2] + [
            getattr(self, f"chk_{n}") for n in ["单选", "多选", "判断", "简答", "计算"]
        ]
        for w in widgets:
            if isinstance(w, QCheckBox):
                w.stateChanged.connect(self._reload2)
            elif isinstance(w, QComboBox):
                w.currentTextChanged.connect(self._reload2)
            else:
                w.textChanged.connect(self._reload2)

        self._reload2()
        return tab

    # ---------------- 全选 / 反选 / 清空 ----------------
    def _select_all2(self):
        for i in range(self.q_list2.count()):
            self.q_list2.item(i).setCheckState(Qt.CheckState.Checked)

    def _invert2(self):
        for i in range(self.q_list2.count()):
            it = self.q_list2.item(i)
            it.setCheckState(
                Qt.CheckState.Unchecked
                if it.checkState() == Qt.CheckState.Checked
                else Qt.CheckState.Checked
            )

    def _clear2(self):
        for i in range(self.q_list2.count()):
            self.q_list2.item(i).setCheckState(Qt.CheckState.Unchecked)

    # ---------------- 导出 ----------------
    def _on_export2(self):
        codes = [
            self.q_list2.item(i).data(Qt.ItemDataRole.UserRole)
            for i in range(self.q_list2.count())
            if self.q_list2.item(i).checkState() == Qt.CheckState.Checked
        ]
        if not codes:
            QMessageBox.warning(self, "未选题目", "请先勾选至少一条题目再导出。")
            return

        opts = {
            "template":   self.tpl_cb.currentText(),
            "header":     self.header_le2.text(),
            "with_ans":   self.cb_ans2.isChecked(),
            "new_page":   self.cb_page2.isChecked(),
            "job_name":   self.job_cb2.currentText().strip(),
            "level_name": self.level_cb2.currentText().strip()
        }

        self.export_thread = QThread()
        self.export_worker = ExportWorker(codes, opts)
        self.export_worker.progress.connect(self._on_export_progress)
        self.export_worker.preview.connect(self.update_preview)
        self.export_worker.finished.connect(self.export_thread.quit)
        self.export_worker.finished.connect(self.export_worker.deleteLater)

        self.export_worker.moveToThread(self.export_thread)
        self.export_thread.started.connect(self.export_worker.run)
        self.export_thread.finished.connect(self.export_thread.deleteLater)
        self.export_thread.start()

    def _on_export_progress(self, pct: int, msg: str):
        self.progress_bar.setValue(pct)
        self.percent_label.setText(f"{pct}%")
        self.status_label.setText(msg)
        self.log_output.append(f"[EXPORT] {msg} ({pct}%)")
        if pct == 100:
            QMessageBox.information(self, "导出完成", "文档已生成")

    def _open2(self):
        out = "output"
        os.makedirs(out, exist_ok=True)
        os.startfile(out)

    # ---------------- 重新加载 & 统计 ----------------
    def _reload2(self):
        self.q_list2.clear()
        job = self.job_cb2.currentText().strip()
        lvl = self.level_cb2.currentText().strip()
        qs = fetch_questions_by_level(get_level_id(get_job_id(job), lvl))
        self.current_qs = qs
        self.filtered_qs = []

        for q in qs:
            key = q["question_type"]
            if not getattr(self, f"chk_{key}").isChecked():
                continue
            code = q["recognition_code"]
            if self.search_le2.text() and self.search_le2.text() not in code:
                continue
            self.filtered_qs.append(q)
            text = f"{code}  {q['content_text'][:50]}"
            item = QListWidgetItem(text)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)
            item.setData(Qt.ItemDataRole.UserRole, q["id"])
            self.q_list2.addItem(item)

        self._update_summary()

    def _update_summary(self):
        counts = {"单选":0, "多选":0, "判断":0, "简答":0, "计算":0}
        for q in self.filtered_qs:
            typ = q.get("question_type")
            if typ in counts:
                counts[typ] += 1
        sel = sum(
            1 for i in range(self.q_list2.count())
            if self.q_list2.item(i).checkState() == Qt.CheckState.Checked
        )
        disp_str = "，".join(f"{k}{v}" for k, v in counts.items())
        self.summary_label.setText(f"{disp_str}；已选 {sel} 题")


def launch_gui():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    launch_gui()
