from typing import Optional

from mpr_photo_editor.model import Model
from mpr_photo_editor.commands.command_base import Command


class AddConnectionCommand(Command):
    """A command to add a new connection to the model."""

    def __init__(self, model: Model, from_node: str, from_socket: str, to_node: str, to_socket: str, parent: Optional[Command] = None):
        super().__init__(model, "Add Connection", parent)
        self.conn_data = {
            "from_node": from_node, "from_socket": from_socket,
            "to_node": to_node, "to_socket": to_socket
        }

    def redo(self):
        """Adds the connection to the model."""
        self.model.add_connection(**self.conn_data)

    def undo(self):
        """Removes the connection from the model."""
        self.model.remove_connection(self.conn_data)


class RemoveConnectionCommand(Command):
    """A command to remove a connection from the model."""

    def __init__(self, model: Model, conn_data: dict, parent: Optional[Command] = None):
        super().__init__(model, "Remove Connection", parent)
        self.conn_data = conn_data

    def redo(self):
        """Removes the connection from the model."""
        self.model.remove_connection(self.conn_data)

    def undo(self):
        """Re-adds the connection to the model."""
        self.model.add_connection(**self.conn_data)
