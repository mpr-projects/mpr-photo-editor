import os
from typing import Optional
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QFileDialog, QApplication, QSizePolicy
from PySide6.QtGui import QPixmap, QPainter, QImage
from PySide6.QtCore import Qt, Signal

from mpr_photo_editor.model import Model
from mpr_photo_editor.controller import Controller
from mpr_photo_editor import backend


class CollapsibleBox(QWidget):
    """A collapsible box widget to hide/show content."""

    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self._title = title
        self.title_button = QPushButton()
        self.title_button.setCheckable(True)
        self.title_button.setStyleSheet(
            "text-align: left; font-weight: bold; border: none; padding: 5px;"
        )

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(15, 0, 0, 0)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(self.title_button)
        main_layout.addWidget(self.content_widget)

        self.title_button.toggled.connect(self.on_toggled)
        self.on_toggled(self.title_button.isChecked())

    def addWidget(self, widget):
        self.content_layout.addWidget(widget)

    def on_toggled(self, checked):
        arrow = "▼" if checked else "►"
        self.title_button.setText(f"{arrow} {self._title}")
        self.content_widget.setVisible(checked)

    def set_collapsed(self, collapsed):
        self.title_button.setChecked(not collapsed)

    def is_collapsed(self) -> bool:
        return not self.title_button.isChecked()

class AspectRatioLabel(QLabel):
    """
    A QLabel that maintains its aspect ratio. It tells the layout system
    its preferred height for any given width.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pixmap = QPixmap()

    def setPixmap(self, pixmap: QPixmap | QImage):
        """Sets the pixmap and informs the layout system that the size hint has changed."""
        # Ensure we are working with a QPixmap for internal storage and comparison
        if isinstance(pixmap, QImage):
            pixmap_to_set = QPixmap.fromImage(pixmap)
        else:
            pixmap_to_set = pixmap

        if self._pixmap != pixmap_to_set:
            self._pixmap = pixmap_to_set
            self.updateGeometry()  # Crucial: tells the layout to re-query size hints
            self.update()  # Trigger a repaint

    def pixmap(self) -> QPixmap:
        return self._pixmap

    def hasHeightForWidth(self) -> bool:
        """This label has a preferred height for a given width."""
        return not self._pixmap.isNull()

    def heightForWidth(self, width: int) -> int:
        """Returns the preferred height for a given width to maintain the aspect ratio."""
        if self._pixmap.isNull() or self._pixmap.width() == 0:
            return -1
        return (self._pixmap.height() * width) // self._pixmap.width()

    def paintEvent(self, event):
        """Paints the pixmap scaled to the widget's size, maintaining aspect ratio."""
        super().paintEvent(event) # Draw background, etc.
        if not self._pixmap.isNull():
            painter = QPainter(self)
            scaled_pixmap = self._pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            # Center the pixmap
            x = (self.width() - scaled_pixmap.width()) / 2
            y = (self.height() - scaled_pixmap.height()) / 2
            painter.drawPixmap(int(x), int(y), scaled_pixmap)


class DefaultPanel(QWidget):
    """The default panel shown when no node is selected."""
    load_image_clicked = Signal()
    get_version_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        wip_label = QLabel(
            "This program is a work in progress. "
            "Both functionality and GUI are constantly being improved."
        )
        wip_label.setWordWrap(True)
        wip_label.setStyleSheet("font-style: italic; color: #888;")
        layout.addWidget(wip_label)

        layout.addSpacing(10)

        right_label = QLabel("Right Panel (for node settings)")
        layout.addWidget(right_label)

        load_button = QPushButton("Load Image")
        load_button.clicked.connect(self.load_image_clicked)
        layout.addWidget(load_button)

        version_button = QPushButton("Get LibRaw Version")
        version_button.clicked.connect(self.get_version_clicked)
        layout.addWidget(version_button)

        self.version_label = QLabel("LibRaw version will be shown here.")
        layout.addWidget(self.version_label)

    def set_version_text(self, text: str):
        self.version_label.setText(text)

def get_node_panel(node_id: str, model: Model, controller: Controller, parent=None):
    """
    Factory function to create the appropriate settings panel for a given node.
    The panel is built based on data from the model, not the UI item.
    """
    node_data = model.nodes.get(node_id)
    if not node_data:
        return QLabel("Node not found in model.", parent=parent)

    node_type = node_data.get("type")

    if node_type == "ImageLoader":
        return _ImageLoaderPanel(node_id, node_data, controller, parent=parent)
    elif node_type == "BlackLevels":
        return _black_levels_panel(node_id, node_data, controller, parent=parent)

    return QLabel(f"No panel available for node type: {node_type}", parent=parent)


class _ImageLoaderPanel(QWidget):
    """The settings panel widget for the ImageLoader node."""

    def __init__(self, node_id: str, node_data: dict, controller: Controller, parent=None):
        super().__init__(parent)
        self.node_id = node_id
        self.controller = controller
        self.model = controller.model
        self.original_pixmap: Optional[QPixmap] = None

        self._init_ui(node_data)
        self._connect_signals()

        # --- Initial State ---
        self.settings_box.set_collapsed(False)
        initial_raw_image_id = node_data.get("settings", {}).get("raw_image_id")
        self.update_panel_info(initial_raw_image_id)

    def _init_ui(self, node_data: dict):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # --- Settings Box ---
        self.settings_box = CollapsibleBox("Image Loader Settings")
        filepath = node_data.get("settings", {}).get("filepath")
        file_label_text = f"File: {os.path.basename(filepath)}" if filepath else "File: No file selected"
        self.file_label = QLabel(file_label_text)
        self.file_label.setWordWrap(True)
        self.settings_box.addWidget(self.file_label)

        self.select_button = QPushButton("Change File")
        self.settings_box.addWidget(self.select_button)
        main_layout.addWidget(self.settings_box)

        # --- Thumbnail Box ---
        self.thumbnail_box = CollapsibleBox("Thumbnail")
        self.thumbnail_label = AspectRatioLabel()
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail_box.addWidget(self.thumbnail_label)
        main_layout.addWidget(self.thumbnail_box)

        # --- Metadata Box ---
        self.metadata_box = CollapsibleBox("Metadata")
        self.metadata_label = QLabel("No metadata available.")
        self.metadata_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.metadata_box.addWidget(self.metadata_label)
        main_layout.addWidget(self.metadata_box)

        # --- Full Metadata Box ---
        self.full_metadata_box = CollapsibleBox("All Metadata")
        self.full_metadata_label = QLabel("No metadata available.")
        self.full_metadata_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.full_metadata_label.setWordWrap(True)
        self.full_metadata_box.addWidget(self.full_metadata_label)
        self.full_metadata_box.set_collapsed(True)  # Collapsed by default
        main_layout.addWidget(self.full_metadata_box)

        main_layout.addStretch()  # Push everything to the top

    def _connect_signals(self):
        self.select_button.clicked.connect(self._on_select_file)
        self.model.node_setting_changed.connect(self._on_setting_changed)
        self.destroyed.connect(lambda: self.model.node_setting_changed.disconnect(self._on_setting_changed))

    def _on_select_file(self):
        new_filepath, _ = QFileDialog.getOpenFileName(
            None, "Select Image File", "",
            "Raw Images (*.cr2 *.nef *.arw *.dng *.rw2 *.orf *.raf *.srw *.pef);;All Files (*)")
        if new_filepath:
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            try:
                self.controller.update_node_setting(self.node_id, "filepath", new_filepath)
            finally:
                QApplication.restoreOverrideCursor()

    def _on_setting_changed(self, changed_node_id, key, value):
        if changed_node_id == self.node_id:
            if key == "filepath":
                new_filepath = "No file selected"
                if value:
                     new_filepath = os.path.basename(str(value))
                self.file_label.setText(f"File: {new_filepath}")
            elif key == "raw_image_id":
                self.update_panel_info(value)

    def update_panel_info(self, raw_image_id: Optional[int]):
        if raw_image_id is not None:
            self.thumbnail_box.set_collapsed(False)
            self.metadata_box.set_collapsed(False)
            self.full_metadata_box.setVisible(True)

            # --- Update Thumbnail ---
            thumb_data = self.model.thumbnail_cache.get(raw_image_id)
            if thumb_data is None:
                try:
                    thumb_data = backend.get_thumbnail(raw_image_id)
                    self.model.thumbnail_cache[raw_image_id] = thumb_data
                except Exception as e:
                    print(f"Error getting thumbnail: {e}")
                    thumb_data = None

            if thumb_data:
                self.thumbnail_label.setText("")  
                self.original_pixmap = QPixmap()
                self.original_pixmap.loadFromData(thumb_data)
                self.thumbnail_label.setPixmap(self.original_pixmap)
            else:
                self.original_pixmap = None
                self.thumbnail_label.setText("Thumbnail Error")
                self.thumbnail_label.setPixmap(QPixmap()) # Clear pixmap

            # --- Update Metadata ---
            try:
                meta = backend.get_metadata(raw_image_id)
                # Key metadata
                meta_text = (
                    f"<b>Make:</b> {meta.get('make', 'N/A')}<br>"
                    f"<b>Model:</b> {meta.get('model', 'N/A')}<br>"
                    f"<b>ISO:</b> {meta.get('iso', 'N/A')}<br>"
                    f"<b>Shutter:</b> {meta.get('shutter', 'N/A')}s<br>"
                    f"<b>Aperture:</b> f/{meta.get('aperture', 'N/A')}"
                )
                self.metadata_label.setText(meta_text)

                # Full metadata
                full_meta_text = "<br>".join(
                    f"<b>{key}:</b> {value}" for key, value in sorted(meta.items())
                )
                self.full_metadata_label.setText(full_meta_text)

            except Exception as e:
                print(f"Error getting metadata: {e}")
                self.metadata_label.setText("Metadata Error")
                self.full_metadata_label.setText("Metadata Error")
        else:
            # No image loaded
            self.original_pixmap = None
            self.thumbnail_box.set_collapsed(True)
            self.metadata_box.set_collapsed(True)
            self.full_metadata_box.setVisible(False)
            self.thumbnail_label.setText("No thumbnail available.")
            self.thumbnail_label.setPixmap(QPixmap()) # Clear pixmap
            self.metadata_label.setText("No metadata available.")
            self.full_metadata_label.setText("No metadata available.")


def _black_levels_panel(node_id: str, node_data: dict, controller: Controller, parent=None):
    """Creates the settings panel for the BlackLevels node."""
    panel = QWidget(parent)
    layout = QVBoxLayout(panel)
    layout.addWidget(QLabel("Black Levels Settings"))
    # TODO: Add sliders and input fields for black level settings here.
    # They would call controller.update_node_setting(...) on change.
    return panel