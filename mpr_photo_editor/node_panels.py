import os
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QFileDialog

from mpr_photo_editor.model import Model
from mpr_photo_editor.controller import Controller


def get_node_panel(node_id: str, model: Model, controller: Controller):
    """
    Factory function to create the appropriate settings panel for a given node.
    The panel is built based on data from the model, not the UI item.
    """
    node_data = model.nodes.get(node_id)
    if not node_data:
        return QLabel("Node not found in model.")

    node_type = node_data.get("type")

    if node_type == "ImageLoader":
        return _image_loader_panel(node_id, node_data, controller)
    elif node_type == "BlackLevels":
        return _black_levels_panel(node_id, node_data, controller)

    return QLabel(f"No panel available for node type: {node_type}")


def _image_loader_panel(node_id: str, node_data: dict, controller: Controller):
    """Creates the settings panel for the ImageLoader node."""
    panel = QWidget()
    layout = QVBoxLayout(panel)
    layout.addWidget(QLabel("Image Loader Settings"))

    # Get initial filepath from the model data
    filepath = node_data.get("settings", {}).get("filepath", "No file selected")
    if filepath != "No file selected":
        filepath = os.path.basename(filepath)

    file_label = QLabel(f"File: {filepath}")
    layout.addWidget(file_label)

    select_button = QPushButton("Change File")

    # When the button is clicked, open a dialog and call the controller
    def on_select_file():
        new_filepath, _ = QFileDialog.getOpenFileName(
            None, "Select Image File", "",
            "Raw Images (*.cr2 *.nef *.arw *.dng *.rw2 *.orf *.raf *.srw *.pef);;All Files (*)")
        if new_filepath:
            controller.update_node_setting(node_id, "filepath", new_filepath)

    select_button.clicked.connect(on_select_file)
    layout.addWidget(select_button)

    # Define a handler that updates the label when the model changes
    def on_setting_changed(changed_node_id, key, value):
        if changed_node_id == node_id and key == "filepath":
            new_filepath = "No file selected"
            if value:
                new_filepath = os.path.basename(str(value))
            file_label.setText(f"File: {new_filepath}")

    # Connect the model's signal to our handler
    model = controller.model
    model.node_setting_changed.connect(on_setting_changed)

    # IMPORTANT: Disconnect the handler when the panel widget is destroyed
    # to prevent memory leaks and calls to a non-existent widget.
    panel.destroyed.connect(lambda: model.node_setting_changed.disconnect(on_setting_changed))

    return panel


def _black_levels_panel(node_id: str, node_data: dict, controller: Controller):
    """Creates the settings panel for the BlackLevels node."""
    panel = QWidget()
    layout = QVBoxLayout(panel)
    layout.addWidget(QLabel("Black Levels Settings"))
    # TODO: Add sliders and input fields for black level settings here.
    # They would call controller.update_node_setting(...) on change.
    return panel