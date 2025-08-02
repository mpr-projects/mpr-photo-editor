from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from mpr_photo_editor.nodes import NodeImageLoader, NodeBlackLevels

def get_node_panel(node):
    if isinstance(node, NodeImageLoader):
        return _image_loader_panel(node)
    elif isinstance(node, NodeBlackLevels):
        return _black_levels_panel(node)
    return QLabel("No panel available for this node.")

def _image_loader_panel(node):
    panel = QWidget()
    layout = QVBoxLayout(panel)
    layout.addWidget(QLabel("Image Loader Panel"))
    layout.addWidget(QLabel("File: " + node.file_label.toPlainText()))
    return panel

def _black_levels_panel(node):
    panel = QWidget()
    layout = QVBoxLayout(panel)
    layout.addWidget(QLabel("Black Levels Panel"))
    return panel