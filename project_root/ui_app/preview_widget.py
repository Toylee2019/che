# ui_app/preview_widget.py

from PyQt6.QtWidgets import QTextBrowser

class PreviewWidget(QTextBrowser):
    """
    实时预览区，占位组件。可通过 .setHtml(...) 动态展示排版后的 HTML/文本内容。
    """
    def __init__(self):
        super().__init__()
        self.setPlaceholderText("这里会实时预览当前选中题目的排版效果")
