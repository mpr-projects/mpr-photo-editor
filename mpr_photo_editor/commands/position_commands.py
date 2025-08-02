from typing import Optional
from PySide6.QtCore import QPointF

from mpr_photo_editor.model import Model
from mpr_photo_editor.commands.command_base import Command


class MoveNodeCommand(Command):
    """A command to move a node to a new position."""

    def __init__(self, model: Model, node_id: str, end_pos: QPointF, start_pos: QPointF, parent: Optional[Command] = None):
        super().__init__(model, "Move Node", parent)
        self.node_id = node_id
        self.end_pos = end_pos
        self.start_pos = start_pos

    def redo(self):
        """Moves the node to the end position."""
        self.model.update_node_position(self.node_id, self.end_pos)

    def undo(self):
        """Moves the node back to the start position."""
        self.model.update_node_position(self.node_id, self.start_pos)