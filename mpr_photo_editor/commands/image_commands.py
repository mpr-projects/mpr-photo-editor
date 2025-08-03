from typing import Optional

from mpr_photo_editor.model import Model
from mpr_photo_editor.commands.command_base import Command
from mpr_photo_editor import backend


class LoadImageCommand(Command):
    """
    A command to load a raw image file for a node.

    This command manages the lifecycle of the image in the Rust backend,
    ensuring that resources are loaded and released correctly during
    redo and undo operations.
    """

    def __init__(self, model: Model, node_id: str, new_filepath: str, new_raw_image_id: int, parent: Optional[Command] = None):
        super().__init__(model, "Load Image", parent)
        self.node_id = node_id
        self.new_filepath = new_filepath

        # This is the ID from the controller's initial, validated load.
        # It will be used for the first redo, then consumed (set to None).
        self._initial_raw_image_id = new_raw_image_id

        # This will hold the active ID for the new image during the command's life.
        self.new_raw_image_id: Optional[int] = None

        # Store the state before the command is executed for undo
        node_settings = self.model.nodes[self.node_id]["settings"]
        self.old_filepath: Optional[str] = node_settings.get("filepath")
        self.old_raw_image_id: Optional[int] = node_settings.get("raw_image_id")

    def redo(self):
        """Releases the old image and updates the model with the new one."""
        if self.old_raw_image_id is not None:
            backend.release_raw_image(self.old_raw_image_id)
            if self.old_raw_image_id in self.model.thumbnail_cache:
                del self.model.thumbnail_cache[self.old_raw_image_id]

        # If this is the first run, use the pre-loaded ID from the controller.
        if self._initial_raw_image_id is not None:
            self.new_raw_image_id = self._initial_raw_image_id
            self._initial_raw_image_id = None  # Consume the initial ID
        else:
            # On subsequent redos (after an undo), we must reload the image
            # because its handle was released by the undo() method.
            try:
                self.new_raw_image_id = backend.load_raw_image(self.new_filepath)
            except Exception as e:
                print(f"Error re-loading image '{self.new_filepath}' during redo: {e}")
                self.new_raw_image_id = None
                # The command is now in a failed state.

        self.model.update_node_setting(self.node_id, "filepath", self.new_filepath)
        self.model.update_node_setting(self.node_id, "raw_image_id", self.new_raw_image_id)

    def undo(self):
        """Releases the new image, reloads the old one, and restores the model."""
        if self.new_raw_image_id is not None:
            backend.release_raw_image(self.new_raw_image_id)
            if self.new_raw_image_id in self.model.thumbnail_cache:
                del self.model.thumbnail_cache[self.new_raw_image_id]
            self.new_raw_image_id = None  # The ID is now invalid

        # If there was an old file, we must reload it to get a new, valid handle.
        if self.old_filepath:
            try:
                self.old_raw_image_id = backend.load_raw_image(self.old_filepath)
            except Exception as e:
                print(f"Failed to reload old image '{self.old_filepath}' during undo: {e}")
                self.old_filepath = None
                self.old_raw_image_id = None
        else:
            self.old_raw_image_id = None

        self.model.update_node_setting(self.node_id, "filepath", self.old_filepath)
        self.model.update_node_setting(self.node_id, "raw_image_id", self.old_raw_image_id)
