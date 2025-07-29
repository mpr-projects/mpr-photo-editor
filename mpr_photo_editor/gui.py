import sys
from PySide6.QtGui import QResizeEvent, QShowEvent
from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel,
    QHBoxLayout, QVBoxLayout, QFrame, QSplitter
)
from PySide6.QtCore import Qt
from mpr_photo_editor.backend import invert_image, get_libraw_version

DEFAULT_WIDTH = 800
DEFAULT_HEIGHT = 600
DEFAULT_SIDEBAR_WIDTH = 250
DEFAULT_NODEBAR_HEIGHT = 200

image_data = [128] * (100 * 100)  # Dummy grayscale image

# Replace the splitter setup in init_ui with a subclass that locks the right panel
class FixedRightSplitter(QSplitter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.right_width = DEFAULT_SIDEBAR_WIDTH
        self.splitterMoved.connect(self.on_splitter_moved)

    def on_splitter_moved(self, pos, index):
        self.right_width = self.sizes()[1]

    def _resize(self):
        total = self.width()
        right = min(self.right_width, total - 10)
        self.setSizes([total - right, right])

    def resizeEvent(self, event):
        self._resize()
        super().resizeEvent(event)

    def showEvent(self, event):
        self._resize()
        super().showEvent(event)

class FixedBottomSplitter(QSplitter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bottom_height = DEFAULT_NODEBAR_HEIGHT
        self.splitterMoved.connect(self.on_splitter_moved)

    def on_splitter_moved(self, pos, index):
        self.bottom_height = self.sizes()[1]

    def _resize(self):
        total = self.height()
        bottom = min(self.bottom_height, total - 10)
        self.setSizes([total - bottom, bottom])

    def resizeEvent(self, event: QResizeEvent) -> None:
        self._resize()
        return super().resizeEvent(event)
    
    def showEvent(self, event: QShowEvent) -> None:
        self._resize()
        return super().showEvent(event)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Photo Editor - by mpr")
        self.setMinimumSize(DEFAULT_WIDTH, DEFAULT_HEIGHT)
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)

        # fix width/height of right and bottom bars while allowing user to change them
        vertical_splitter = FixedBottomSplitter(Qt.Orientation.Vertical)
        horizontal_splitter = FixedRightSplitter(Qt.Orientation.Horizontal)

        # Top left Panel
        left_panel = QFrame()
        left_panel.setFrameShape(QFrame.Shape.StyledPanel)
        left_layout = QVBoxLayout(left_panel)

        self.left_label = QLabel("Left Panel")
        left_layout.addWidget(self.left_label)

        invert_button = QPushButton("Invert Image")
        invert_button.clicked.connect(self.process_callback)
        left_layout.addWidget(invert_button)

        version_button = QPushButton("Get LibRaw Version")
        version_button.clicked.connect(self.show_libraw_version)
        left_layout.addWidget(version_button)

        self.version_label = QLabel("LibRaw version will be shown here.")
        left_layout.addWidget(self.version_label)

        # Top right Panel
        right_panel = QFrame()
        right_panel.setFrameShape(QFrame.Shape.StyledPanel)
        right_layout = QVBoxLayout(right_panel)

        self.right_label = QLabel("Right Panel (for node settings)")
        right_layout.addWidget(self.right_label)

        horizontal_splitter.addWidget(left_panel)
        horizontal_splitter.addWidget(right_panel)

        # Set default sizes for top left and right panels
        right_width = DEFAULT_SIDEBAR_WIDTH
        left_width = DEFAULT_WIDTH - right_width
        horizontal_splitter.setSizes([left_width, right_width])

        # Bottom Panel
        bottom_panel = QFrame()
        bottom_panel.setFrameShape(QFrame.Shape.StyledPanel)
        bottom_layout = QVBoxLayout(bottom_panel)
        self.bottom_label = QLabel("Bottom Panel (for nodes)")
        bottom_layout.addWidget(self.bottom_label)

        vertical_splitter.addWidget(horizontal_splitter)
        vertical_splitter.addWidget(bottom_panel)

        # Set default sizes for top and bottom areas
        vertical_splitter.setSizes([DEFAULT_HEIGHT - DEFAULT_NODEBAR_HEIGHT, DEFAULT_NODEBAR_HEIGHT])

        main_layout.addWidget(vertical_splitter)

    def process_callback(self):
        global image_data
        result = invert_image(image_data, 100, 100)
        print("Image processed. First 10 pixels:", result[:10])

    def show_libraw_version(self):
        """Gets the LibRaw version and displays it in the label."""
        version = get_libraw_version()
        self.version_label.setText(f"LibRaw Version: {version}")

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
