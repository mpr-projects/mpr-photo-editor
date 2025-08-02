import sys

from PySide6.QtGui import (
    QResizeEvent, QShowEvent, QPainter, QPixmap,
    QMouseEvent, QKeySequence, QColor, QGuiApplication
)

from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel,
    QHBoxLayout, QVBoxLayout, QFrame, QSplitter,
    QFileDialog, QMenuBar
)

from PySide6.QtCore import Qt

from PySide6.QtWidgets import QGraphicsScene, QGraphicsView, QGraphicsRectItem
from PySide6.QtCore import QTimer

import mpr_photo_editor.nodes as nodes
import mpr_photo_editor.node_panels as node_panels
import mpr_photo_editor.helper as helper
from mpr_photo_editor.model import Model
from mpr_photo_editor.controller import Controller
from mpr_photo_editor.backend import invert_image, get_libraw_version

DEFAULT_WIDTH = 800
DEFAULT_HEIGHT = 600
DEFAULT_SIDEBAR_WIDTH = 250
DEFAULT_NODEBAR_HEIGHT = 200

image_data = [128] * (100 * 100)  # Dummy grayscale image

class DraggableImage(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Set a default pixmap and store aspect ratio
        pixmap = QPixmap(150, 100)  # Example default rectangle
        pixmap.fill("gray")
        self.setPixmap(pixmap)
        self.aspect_ratio = pixmap.width() / pixmap.height()
        self.setScaledContents(True)
        self.setFixedSize(pixmap.size())
        self.dragging = False
        self.offset = None
        self.setStyleSheet("border: 1px solid black;")
        self.resizing = False
        self.resize_margin = 10
        self.setMouseTracking(True)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            if self._in_resize_area(event.pos()):
                self.resizing = True
            else:
                self.dragging = True
                self.offset = event.pos()

    def cursorUpdate(self, pos):
        if self._in_resize_area(pos) or self.resizing:
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def mouseMoveEvent(self, event: QMouseEvent):
        self.cursorUpdate(event.pos())
        if event.buttons() == Qt.MouseButton.LeftButton:
            if self.resizing:
                width = max(20, event.pos().x())
                height = max(20, int(width / self.aspect_ratio))
                self.setFixedSize(width, height)
            elif self.dragging and self.offset is not None:
                new_pos = self.mapToParent(event.pos() - self.offset)
                self.move(new_pos)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.dragging = False
        self.resizing = False
        self.offset = None

    def enterEvent(self, event):
        self.setStyleSheet("border: 1px solid blue;")

    def leaveEvent(self, event):
        self.setStyleSheet("border: 1px solid black;")
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def _in_resize_area(self, pos):
        return (
            self.width() - self.resize_margin <= pos.x() <= self.width() and
            self.height() - self.resize_margin <= pos.y() <= self.height()
        )

class ImageCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 400)
        self.setStyleSheet("background-color: white;")
        self.setMouseTracking(True)

    def add_image(self):
        img = DraggableImage(self)
        img.move(10, 10)
        img.show()

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

        # Create the Model and Controller
        self.model = Model()
        self.controller = Controller(self.model)

        self.init_ui()

    def init_ui_(self):
        main_layout = QHBoxLayout(self)

        scene = QGraphicsScene()
        scene.setObjectName('The scene')
        scene.setSceneRect(-50, -50, 1300, 1300)

        rect = QGraphicsRectItem(10, 10, 700, 600)
        rect.setBrush(QColor("blue"))
        rect.setPen(Qt.PenStyle.NoPen)
        scene.addItem(rect)

        # pen = QPen(Qt.GlobalColor.yellow)
        # brush = QBrush(Qt.GlobalColor.red)
        # scene.addRect(10, 10, 700, 600, pen, brush)

        def zoom_to_content():
            print("View size:", view.viewport().size())
            print("Scene rect:", scene.sceneRect())
            print("Scene items bounding rect:", scene.itemsBoundingRect())
            view.fitInView(scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)
            view.centerOn(scene.itemsBoundingRect().center())

        QTimer.singleShot(0, zoom_to_content)
        
        view = QGraphicsView(scene)
        view.setStyleSheet("border: 2px solid red;")
        view.resetTransform()
        view.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)

        main_layout.addWidget(view)
        QTimer.singleShot(0, lambda: view.fitInView(scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio))
        # view.fitInView(scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        # view.centerOn(500, 500)

        print("Scene has items:", scene.items())
        self.scene = scene
        # self.view = view

    def init_ui(self):
        # The main layout is now vertical to accommodate the menu bar at the top.
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Menu Bar ---
        menu_bar = QMenuBar()

        # File Menu
        file_menu = menu_bar.addMenu("&File")
        file_menu.addAction("New... (placeholder)")

        # Edit Menu
        edit_menu = menu_bar.addMenu("&Edit")
        undo_action = self.controller.undo_stack.createUndoAction(self, "&Undo")
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)

        redo_action = self.controller.undo_stack.createRedoAction(self, "&Redo")
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)

        edit_menu.addAction(undo_action)
        edit_menu.addAction(redo_action)

        main_layout.addWidget(menu_bar)

        # fix width/height of right and bottom bars while allowing user to change them
        vertical_splitter = FixedBottomSplitter(Qt.Orientation.Vertical)
        horizontal_splitter = FixedRightSplitter(Qt.Orientation.Horizontal)

        # Top left Panel
        left_panel = QFrame()
        left_panel.setFrameShape(QFrame.Shape.StyledPanel)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        self.image_container = ImageCanvas(left_panel)
        left_layout.addWidget(self.image_container, stretch=1)

        # Top right Panel
        self.right_panel = right_panel = QFrame()
        right_panel.setFrameShape(QFrame.Shape.StyledPanel)
        right_layout = QVBoxLayout(right_panel)

        self.right_label = QLabel("Right Panel (for node settings)")
        right_layout.addWidget(self.right_label)

        load_button = QPushButton("Load Image")
        load_button.clicked.connect(self.load_image)
        right_layout.addWidget(load_button)

        invert_button = QPushButton("Invert Image")
        invert_button.clicked.connect(self.process_callback)
        right_layout.addWidget(invert_button)

        version_button = QPushButton("Get LibRaw Version")
        version_button.clicked.connect(self.show_libraw_version)
        right_layout.addWidget(version_button)

        self.version_label = QLabel("LibRaw version will be shown here.")
        right_layout.addWidget(self.version_label)

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

        self.node_scene = node_scene = nodes.NodeScene(self.controller, self.model)
        node_scene.node_selected.connect(self.update_right_panel)

        node_view = nodes.NodeView(node_scene)
        node_view.setStyleSheet("border: none;")
        bottom_layout.addWidget(node_view)

        screen_geometry = QGuiApplication.primaryScreen().availableGeometry()
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()
        node_scene.setSceneRect(-screen_width*5, -screen_height*5, screen_width*10, screen_height*10)

        node_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        node_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # node = nodes.NodeImageLoader()
        # node_scene.addItem(node)

        # QTimer.singleShot(0, lambda: node_view.centerOn(0, 0))
        # QTimer.singleShot(0, lambda: node.setPos(-node_view.viewport().width() / 2 + helper.dp(20),
        #                                         -node.height / 2))

        # helper.BackgroundRectHelper.initialize(node_scene)
        # helper.BackgroundRectHelper.add_scene_background_rect()

        vertical_splitter.addWidget(horizontal_splitter)
        vertical_splitter.addWidget(bottom_panel)

        # Set default sizes for top and bottom areas
        vertical_splitter.setSizes([DEFAULT_HEIGHT - DEFAULT_NODEBAR_HEIGHT, DEFAULT_NODEBAR_HEIGHT])

        main_layout.addWidget(vertical_splitter)

    def load_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open RAW Image",
            "",
            "RAW Images (*.cr2 *.nef *.arw *.dng *.rw2 *.orf *.raf *.srw *.pef);;All Files (*)"
        )
        if file_path:
            self.image_container.add_image()

    def update_right_panel(self, node):
        print("update_right_panel called with:", node)

        layout = self.right_panel.layout()
        if not layout:
            # This should not happen if init_ui is correct, but it's a safe guard.
            return

        # Clear old panel widgets more robustly.
        # This is the idiomatic way to clear a layout in Qt.
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        if node and node.node_id:
            # Pass the node_id, model, and controller to create a data-driven panel
            panel = node_panels.get_node_panel(node.node_id, self.model, self.controller)
            layout.addWidget(panel)

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
    helper._DPIHelper.initialize(app)

    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
