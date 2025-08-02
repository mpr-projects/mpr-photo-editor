from typing import Optional

from mpr_photo_editor.model import Model
from mpr_photo_editor.commands.command_base import Command


class ChangeSettingCommand(Command):
    """A command to change a setting on a node."""

    def __init__(self, model: Model, node_id: str, key: str, new_value, parent: Optional[Command] = None):
        super().__init__(model, f"Change {key}", parent)
        self.node_id = node_id
        self.key = key
        self.new_value = new_value
        # Store the old value for undo
        self.old_value = model.nodes[node_id]["settings"].get(key)

    def redo(self):
        """Applies the new setting value to the model."""
        self.model.update_node_setting(self.node_id, self.key, self.new_value)

    def undo(self):
        """Restores the old setting value in the model."""
        self.model.update_node_setting(self.node_id, self.key, self.old_value)

