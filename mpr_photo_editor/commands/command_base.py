from typing import Optional
from PySide6.QtGui import QUndoCommand

from mpr_photo_editor.model import Model


class Command(QUndoCommand):
    """Abstract base class for all commands in the application."""

    def __init__(self, model: Model, text: str, parent: Optional[QUndoCommand] = None):
        super().__init__(text, parent)
        self.model = model
