import uuid
from PySide6.QtCore import QObject, Signal, QPointF

from mpr_photo_editor import backend


class Model(QObject):
    """
    The central data model for the application (The "M" in MVC).

    It holds the entire state of the node graph and emits signals when it changes.
    It knows nothing about the UI (View) or the application logic (Controller),
    but it inherits from QObject so it can use Qt's signal/slot mechanism to
    notify observers when its state changes.
    """

    # Signals for node changes
    node_added = Signal(str)  # node_id
    node_removed = Signal(str)  # node_id
    node_setting_changed = Signal(str, str, object)  # node_id, key, value
    node_position_changed = Signal(str, QPointF)  # node_id, position

    # Signals for connection changes
    connection_added = Signal(dict)  # connection_data
    connection_removed = Signal(dict)  # connection_data

    def __init__(self, parent=None):
        super().__init__(parent)

        # The version of the model structure. Useful for handling project file
        # format changes in the future.
        self.version = "0.1.0"

        # The "source of truth" for the graph structure and settings.
        # This is what gets serialized when saving the project.
        # { node_id: { "type": "...", "position": (x, y), "settings": {...} } }
        self.nodes = {}

        # [ {"from_node": ..., "from_socket": ..., "to_node": ..., "to_socket": ...} ]
        self.connections = []

        # A cache for large, non-serializable data from the backend (e.g., image handles).
        # This is never saved to the project file. It is rebuilt on load or can be
        # persisted locally in a separate cache file for faster startup.
        # { node_id: backend_object_handle }
        self.runtime_cache = {}

        # A cache for thumbnails to avoid re-fetching from the backend,
        # as some backend operations may be one-shot.
        self.thumbnail_cache = {}

    def to_dict(self):
        """
        Convert graph information to dictionary for easy saving.
        """
        return dict(
            version = self.version,
            nodes = self.nodes,
            connections = self.connections
        )

    def clear(self):
        """Clears the entire model, releasing any associated backend resources."""
        # Release backend resources for all image loader nodes
        for node_data in self.nodes.values():
            if node_data.get("type") == "ImageLoader":
                raw_image_id = node_data.get("settings", {}).get("raw_image_id")
                if raw_image_id is not None:
                    backend.release_raw_image(raw_image_id)

        # Emit signals to remove all UI elements before clearing the data.
        # Iterate over copies as the lists will be modified by remove signals.
        for conn_data in list(self.connections):
            self.connection_removed.emit(conn_data)

        for node_id in list(self.nodes.keys()):
            self.node_removed.emit(node_id)

        # Clear the internal data structures
        self.nodes = {}
        self.connections = []
        self.runtime_cache = {}
        self.thumbnail_cache = {}

    def from_dict(self, data: dict):
        """Populates the model from a dictionary, rebuilding the graph."""
        self.clear()  # Start with a clean slate, releasing old resources.

        self.version = data.get('version', self.version)
        nodes_data = data.get('nodes', {})

        # Re-acquire backend resources for image loaders before adding to model
        for node_id, node_data in nodes_data.items():
            if node_data.get("type") == "ImageLoader" and node_data.get("settings", {}).get("filepath"):
                filepath = node_data["settings"]["filepath"]
                try:
                    node_data["settings"]["raw_image_id"] = backend.load_raw_image(filepath)
                except Exception as e:
                    print(f"Failed to reload image '{filepath}' for node {node_id}: {e}")
                    node_data["settings"]["raw_image_id"] = None

        self.nodes = nodes_data
        self.connections = data.get('connections', [])

        # Now that data is loaded, emit signals to build the UI
        for node_id in self.nodes.keys():
            self.node_added.emit(node_id)

        for connection_data in self.connections:
            self.connection_added.emit(connection_data)

    def _add_node_with_data(self, node_id: str, node_data: dict):
        """
        Private method to add a node with a specific ID and data.
        Used for undo/redo and loading projects.
        """
        if node_id in self.nodes:
            raise ValueError(f"Node with ID {node_id} already exists.")

        self.nodes[node_id] = node_data
        self.node_added.emit(node_id)

    def add_node(self, node_type: str, position: QPointF) -> str:
        """Adds a new node to the model and returns its unique ID."""
        node_id = f"node_{uuid.uuid4().hex[:8]}"
        while node_id in self.nodes:
            # This is extremely unlikely, but we should handle it just in case.
            node_id = f"node_{uuid.uuid4().hex[:8]}"

        node_data = {
            "type": node_type,
            "position": (position.x(), position.y()),
            "settings": {}
        }

        self._add_node_with_data(node_id, node_data)

        return node_id

    def remove_node(self, node_id: str):
        """Removes a node and its connections from the model."""
        if node_id in self.nodes:
            # First, remove all connections associated with this node
            connections_to_remove = [
                c for c in self.connections
                if c["from_node"] == node_id or c["to_node"] == node_id
            ]
            for conn in connections_to_remove:
                self.remove_connection(conn)

            # Free backend resources if this is an image loader node
            node_data = self.nodes[node_id]
            if node_data.get("type") == "ImageLoader":
                raw_image_id = node_data.get("settings", {}).get("raw_image_id")
                if raw_image_id is not None:
                    backend.release_raw_image(raw_image_id)
                    if raw_image_id in self.thumbnail_cache:
                        del self.thumbnail_cache[raw_image_id]

            # Remove the node itself from the model
            del self.nodes[node_id]

            self.node_removed.emit(node_id)
        else:
            raise ValueError(f"Attempted to remove non-existent node: {node_id}. "
                             "This indicates a logic error in the application.")

    def update_node_setting(self, node_id: str, key: str, value):
        """Updates a specific setting for a given node."""
        if node_id in self.nodes:
            self.nodes[node_id]["settings"][key] = value
            self.node_setting_changed.emit(node_id, key, value)
        else:
            raise ValueError(f"Attempted to update settings for non-existent node: {node_id}. "
                             "This indicates a logic error in the application.")

    def update_node_position(self, node_id: str, position: QPointF):
        """Updates the position of a given node."""
        if node_id in self.nodes:
            self.nodes[node_id]["position"] = (position.x(), position.y())
            self.node_position_changed.emit(node_id, position)
        else:
            raise ValueError(f"Attempted to update position for non-existent node: {node_id}. "
                             "This indicates a logic error in the application.")

    def add_connection(self, from_node: str, from_socket: str, to_node: str, to_socket: str):
        """Adds a connection between two nodes."""
        if from_node not in self.nodes or to_node not in self.nodes:
            raise ValueError(f"Attempted to create a connection with a non-existent node. "
                             f"From: {from_node}, To: {to_node}. "
                             "This indicates a logic error in the application.")

        connection_data = {
            "from_node": from_node, "from_socket": from_socket,
            "to_node": to_node, "to_socket": to_socket,
        }
        if connection_data not in self.connections:
            self.connections.append(connection_data)
            self.connection_added.emit(connection_data)
        else:
            raise ValueError("Attempted to add connection_data that already exists.")

    def remove_connection(self, connection_data: dict):
        """Removes a specific connection."""
        if connection_data in self.connections:
            self.connections.remove(connection_data)
            self.connection_removed.emit(connection_data)
        else:
            raise ValueError("Attempted to remove connection data that doesn't exist.")