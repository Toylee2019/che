# ui_utils.py

def apply_dark_theme(widget):
    widget.setStyleSheet("""
        QWidget {
            background-color: #1c1c1c;
            color: #f0f0f0;
            font-size: 14px;
        }
        QLineEdit, QTextEdit, QComboBox, QListWidget {
            background-color: #2a2a2a;
            border: 1px solid #444;
            border-radius: 5px;
            padding: 4px;
        }
        QListWidget::item {
            /* 默认列表项背景 */
            background-color: #2a2a2a;
            /* 取消默认焦点边框 */
            outline: none;
        }
        QListWidget::item:hover {
            /* 鼠标悬停时的背景色 */
            background-color: #3a3a3a;
        }
        QListWidget::item:selected {
            /* 选中时的背景色 */
            background-color: #505050;
            color: #ffffff;
        }
        QPushButton {
            background-color: #3c3c3c;
            color: #ffffff;
            border: 1px solid #555;
            border-radius: 4px;
            padding: 6px 10px;
        }
        QPushButton:hover {
            background-color: #505050;
        }
    """)

def apply_light_theme(widget):
    widget.setStyleSheet("""
        QWidget {
            background-color: #f5f5f5;
            color: #202020;
            font-size: 14px;
        }
        QLineEdit, QTextEdit, QComboBox, QListWidget {
            background-color: #ffffff;
            border: 1px solid #ccc;
            border-radius: 5px;
            padding: 4px;
        }
        QListWidget::item {
            /* 默认列表项背景 */
            background-color: #ffffff;
            outline: none;
        }
        QListWidget::item:hover {
            /* 鼠标悬停时的背景色 */
            background-color: #eaeaea;
        }
        QListWidget::item:selected {
            /* 选中时的背景色 */
            background-color: #c0c0f0;
            color: #202020;
        }
        QPushButton {
            background-color: #e0e0e0;
            color: #202020;
            border: 1px solid #bbb;
            border-radius: 4px;
            padding: 6px 10px;
        }
        QPushButton:hover {
            background-color: #d0d0d0;
        }
    """)
