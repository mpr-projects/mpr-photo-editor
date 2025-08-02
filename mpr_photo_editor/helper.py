from PySide6.QtCore import Qt
from PySide6.QtGui import QScreen
from PySide6.QtWidgets import QGraphicsRectItem
from PySide6.QtGui import QColor


class _DPIHelper:
    _scale = 1.0

    @classmethod
    def initialize(cls, app):
        screen: QScreen = app.primaryScreen()
        dpi = screen.logicalDotsPerInch()
        cls._scale = dpi / 96.0  # 96 is the baseline DPI

    @classmethod
    def dp(cls, value: float) -> float:
        """Convert a value in logical pixels to scaled device pixels."""
        return value * cls._scale

    @classmethod
    def scale(cls) -> float:
        return cls._scale


# Public API
def dp(value: float) -> float:
    return _DPIHelper.dp(value)

def scale() -> float:
    return _DPIHelper.scale()



# help debugging
class BackgroundRectHelper:
    _SCENE = None

    @classmethod
    def initialize(cls, scene):
        cls._SCENE = scene

    @classmethod
    def add_scene_background_rect(cls):
        if cls._SCENE is None:
            return
        
        # Remove old one if it exists
        existing = getattr(cls._SCENE, "_background_rect", None)

        if existing:
            cls._SCENE.removeItem(existing)

        # Add new filled rect to match sceneRect
        rect_item = QGraphicsRectItem(cls._SCENE.sceneRect())
        rect_item.setBrush(QColor("lightgray"))
        rect_item.setPen(Qt.PenStyle.NoPen)
        rect_item.setZValue(-10000)  # Ensure it's below everything
        cls._SCENE.addItem(rect_item)

        # Save for future replacement
        cls._SCENE._background_rect = rect_item