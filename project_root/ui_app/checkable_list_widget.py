# ui_app/checkable_list_widget.py

from PyQt6.QtWidgets import QListWidget, QListWidgetItem
from PyQt6.QtCore import Qt

class CheckableListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 禁用原生的行选中高亮
        self.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        # 打开拖拽时的自动滚动
        self.setAutoScroll(True)
        # 当前正在“刷”向的状态：Qt.Checked / Qt.Unchecked / None
        self._painting_state = None

    def mousePressEvent(self, event):
        item = self.itemAt(event.pos())
        if isinstance(item, QListWidgetItem):
            # 先读取之前的状态，再切换到相反状态
            prev = item.checkState()
            new_state = Qt.CheckState.Unchecked if prev == Qt.CheckState.Checked else Qt.CheckState.Checked
            item.setCheckState(new_state)
            # 记录下来，后续拖拽时都按这个状态来
            self._painting_state = new_state
            # 阻止基类再次切换
            event.accept()
            return
        # 非勾选区域仍交由基类处理（例如滚动等）
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._painting_state is not None:
            # 拖动时，如果在某个 item 上，就把它设为同样的勾选状态
            item = self.itemAt(event.pos())
            if isinstance(item, QListWidgetItem):
                item.setCheckState(self._painting_state)

            # 自动滚动：当鼠标接近顶部/底部时，滚动列表
            margin = 20
            y = event.pos().y()
            vsb = self.verticalScrollBar()
            if y < margin:
                vsb.setValue(vsb.value() - 3)
            elif y > self.viewport().height() - margin:
                vsb.setValue(vsb.value() + 3)

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        # 停止“刷”状态
        self._painting_state = None
        # 不调用基类，避免在释放时再次切换
        event.accept()
