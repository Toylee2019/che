from PyQt6.QtWidgets import QTextEdit

class PreviewWidget(QTextEdit):
    """
    用于显示实时更新的预览内容的组件
    """
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)  # 设置为只读
        self.setPlaceholderText("实时预览内容...")  # 初始占位文本

    def update_preview(self, preview_text):
        """
        更新预览内容，接收并显示新的预览文本。
        """
        self.append(preview_text)  # 将新的预览内容追加到文本框中
