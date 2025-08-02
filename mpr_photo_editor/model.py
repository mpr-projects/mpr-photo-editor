import uuid
from PySide6.QtCore import QObject, Signal, QPointF


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

            # Remove the node itself
            del self.nodes[node_id]
            if node_id in self.runtime_cache:
                # TODO: Tell the backend to free the associated resource
                del self.runtime_cache[node_id]

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