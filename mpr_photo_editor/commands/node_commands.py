from typing import Optional
from PySide6.QtCore import QPointF

from mpr_photo_editor.model import Model
from mpr_photo_editor.commands.command_base import Command


class AddNodeCommand(Command):
    """A command to add a new node to the model."""

    def __init__(self, model: Model, node_type: str, position: QPointF, parent: Optional[Command] = None):
        super().__init__(model, f"Add {node_type} Node", parent)
        self.node_type = node_type
        self.position = position
        self.node_id = None  # Will be set on the first redo

    def redo(self):
        """Adds the node to the model."""
        if self.node_id is None:
            # First time: create the node and get its ID
            self.node_id = self.model.add_node(self.node_type, self.position)
        else:
            # Subsequent redos: re-add the node with its original ID and data
            node_data = {
                "type": self.node_type,
                "position": (self.position.x(), self.position.y()),
                "settings": {}
            }
            self.model._add_node_with_data(self.node_id, node_data)

    def undo(self):
        """Removes the node from the model."""
        if self.node_id:
            self.model.remove_node(self.node_id)


class RemoveNodeCommand(Command):
    """A command to remove a node from the model."""

    def __init__(self, model: Model, node_id: str, parent: Optional[Command] = None):
        super().__init__(model, "Remove Node", parent)
        self.node_id = node_id
        # Store all data required to recreate the node
        self.node_data = model.nodes[self.node_id].copy()
        self.connections_data = [c.copy() for c in model.connections if c["from_node"] == node_id or c["to_node"] == node_id]

    def redo(self):
        """Removes the node from the model."""
        self.model.remove_node(self.node_id)

    def undo(self):
        """Re-adds the node and its connections to the model."""
        self.model._add_node_with_data(self.node_id, self.node_data)
        for conn_data in self.connections_data:
            self.model.add_connection(**conn_data)

