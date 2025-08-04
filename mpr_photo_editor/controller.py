import json
from typing import Optional

from PySide6.QtCore import QObject, QPointF
from PySide6.QtGui import QUndoStack

from mpr_photo_editor.model import Model
import mpr_photo_editor.commands.position_commands as position_commands
import mpr_photo_editor.commands.node_commands as node_commands
import mpr_photo_editor.commands.setting_commands as setting_commands
import mpr_photo_editor.commands.conn_commands as conn_commands
from mpr_photo_editor.commands import image_commands
from mpr_photo_editor import backend


class Controller(QObject):
    """
    The Controller for the application (The "C" in MVC).

    It translates user actions from the View into Commands that modify the Model.
    It also manages the undo/redo stack.
    """

    def __init__(self, model: Model, parent=None):
        super().__init__(parent)
        self.model = model
        self.undo_stack = QUndoStack(self)

    def add_node(self, node_type: str, position: QPointF):
        """Creates and executes a command to add a node."""
        command = node_commands.AddNodeCommand(self.model, node_type, position)
        self.undo_stack.push(command)

    def remove_node(self, node_id: str):
        """Creates and executes a command to remove a node."""
        command = node_commands.RemoveNodeCommand(self.model, node_id)
        self.undo_stack.push(command)

    def update_node_setting(self, node_id: str, key: str, value):
        """Creates and executes a command to change a node's setting."""
        node_data = self.model.nodes.get(node_id)
        if not node_data:
            # This should ideally not happen if the UI and model are in sync.
            print(f"Error: Controller could not find node {node_id} in model.")
            return

        node_type = node_data.get("type")
        if node_type == "ImageLoader" and key == "filepath":
            # This is a special case for the ImageLoader node. We must validate that the image can be loaded *before* creating a command. If it fails, no action is taken.
            try:
                new_raw_image_id = backend.load_raw_image(value)
                # If loading succeeds, create the specialized command.
                load_command = image_commands.LoadImageCommand(self.model, node_id, value, new_raw_image_id)
                self.undo_stack.push(load_command)
            except Exception as e:
                # TODO: Show this error to the user in a dialog.
                print(f"Failed to load image '{value}': {e}. The action was cancelled.")
        else:
            # For all other settings, use the generic command.
            setting_command = setting_commands.ChangeSettingCommand(self.model, node_id, key, value)
            self.undo_stack.push(setting_command)

    def add_connection(self, from_node: str, from_socket: str, to_node: str, to_socket: str):
        """Creates and executes a command to add a connection."""
        command = conn_commands.AddConnectionCommand(self.model, from_node, from_socket, to_node, to_socket)
        self.undo_stack.push(command)

    def remove_connection(self, conn_data: dict):
        """Creates and executes a command to remove a connection."""
        command = conn_commands.RemoveConnectionCommand(self.model, conn_data)
        self.undo_stack.push(command)

    def move_node(self, node_id: str, end_pos: QPointF, start_pos: QPointF):
        """Creates and executes a command to move a node."""
        command = position_commands.MoveNodeCommand(self.model, node_id, end_pos, start_pos)
        self.undo_stack.push(command)

    def save_project(self, filepath: str, selected_node_id: Optional[str], binary: bool = False):
        """Asks the model for its data, adds UI state, and saves it to a file."""
        print(f"Controller: Saving project to {filepath}")
        data = self.model.to_dict()
        data['ui_state'] = {'selected_node_id': selected_node_id}
        with open(filepath, 'wb' if binary else 'w') as f:
            json.dump(data, f, indent=None if binary else 4)

    def load_project(self, filepath: str, binary: bool = False) -> Optional[dict]:
        """Loads an .mpr file, rebuilds the model, and returns UI state."""
        with open(filepath, 'rb' if binary else 'r') as f:
            data = json.load(f)

        ui_state = data.get('ui_state')
        self.model.from_dict(data)
        return ui_state
