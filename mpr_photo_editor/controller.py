from PySide6.QtCore import QObject, QPointF
from PySide6.QtGui import QUndoStack

from mpr_photo_editor.model import Model
import mpr_photo_editor.commands.position_commands as position_commands
import mpr_photo_editor.commands.node_commands as node_commands
import mpr_photo_editor.commands.setting_commands as setting_commands
import mpr_photo_editor.commands.conn_commands as conn_commands


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
        command = setting_commands.ChangeSettingCommand(self.model, node_id, key, value)
        self.undo_stack.push(command)

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