from __future__ import annotations
import os
from typing import cast, Optional

from PySide6.QtWidgets import QApplication, QGraphicsItem, QGraphicsEllipseItem, QGraphicsRectItem, QGraphicsSceneMouseEvent, QGraphicsTextItem, QGraphicsPathItem, QGraphicsScene, QGraphicsView, QFileDialog, QPushButton, QGraphicsProxyWidget, QMenu, QGraphicsSceneContextMenuEvent
from PySide6.QtGui import QPainterPath, QPen, QColor, QPainter, QBrush, QTransform, QCursor, QMouseEvent
from PySide6.QtCore import QRectF, QPointF, Qt, QEvent, Signal

from mpr_photo_editor.controller import Controller
from mpr_photo_editor.model import Model
from mpr_photo_editor.helper import dp
# from mpr_photo_editor.helper import BackgroundRectHelper


# Type categories
class SocketType:
    RAW = "Raw"
    CFA = "CFA"
    META = "Metadata"
    IMAGE = "Image"
    NUMBER = "Number"
    # Extend as needed

    COLORS = {
        RAW: QColor("#D32F2F"),        # red
        CFA: QColor("#1976D2"),        # blue
        META: QColor("#388E3C"),       # green
        IMAGE: QColor("#FBC02D"),      # yellow
        NUMBER: QColor("#7B1FA2"),     # purple
    }


# Refactored NodeSocket as a factory with subclasses for different connection types.
class NodeSocketFactory:
    def __new__(cls, x, y, is_input=True, socket_type=SocketType.IMAGE, parent=None, single_connection=True):
        if single_connection:
            return SingleConnectionNodeSocket(x, y, is_input, socket_type, parent)
        else:
            return MultiConnectionNodeSocket(x, y, is_input, socket_type, parent)


class NodeSocket:
    DIAMETER = 10

    def __init__(self, socket_type, is_input=True, parent=None):
        self.is_input = is_input
        self.socket_type = socket_type
        self.connections = []
        self.name = ""
    
    def update_connections(self):
        for connection in self.connections:
            connection.update_path()

    def add_connection(self, connection):
        if connection not in self.connections:
            self.connections.append(connection)

    def remove_connection(self, connection):
        if connection in self.connections:
            self.connections.remove(connection)

    def get_parent_node(self) -> NodeBase:
        """A type-hinted helper to get the parent item as a NodeBase."""
        # This method is called on subclasses that are QGraphicsItems.
        return cast(NodeBase, self.parentItem())  # type: ignore


class SingleConnectionNodeSocket(NodeSocket, QGraphicsEllipseItem):
    def __init__(self, x, y, is_input=True, socket_type=SocketType.IMAGE, parent=None):
        NodeSocket.__init__(self, socket_type, is_input=is_input, parent=parent)
        QGraphicsEllipseItem.__init__(
            self, -NodeSocket.DIAMETER/2, -NodeSocket.DIAMETER/2,
            NodeSocket.DIAMETER, NodeSocket.DIAMETER, parent)
        
        self.setPos(x, y)
        self.setBrush(SocketType.COLORS.get(socket_type, QColor("gray")))
    
    def add_connection(self, connection):
        if len(self.connections) > 0:
            self.connections[0].delete()
        self.connections.append(connection)


class MultiConnectionNodeSocket(NodeSocket, QGraphicsRectItem):
    def __init__(self, x, y, is_input=True, socket_type=SocketType.IMAGE, parent=None):
        side = NodeSocket.DIAMETER

        NodeSocket.__init__(self, socket_type, is_input=is_input, parent=parent)
        QGraphicsRectItem.__init__(self, -side/2, -side/2, side, side, parent)

        self.setPos(x, y)
        self.setBrush(SocketType.COLORS.get(socket_type, QColor("gray")))

    def paint(self, painter, option, widget=None):
        painter.setBrush(self.brush())
        painter.setPen(self.pen())
        painter.drawRoundedRect(self.rect(), 3, 3)


class NodeBase(QGraphicsItem):
    def __init__(self, name, height=dp(60), width=dp(120)):
        super().__init__()
        self.name = name
        self.width = width
        self.height = height
        self.node_id: Optional[str] = None
        self._drag_start_pos: Optional[QPointF] = None

        self.inputs = []
        self.outputs = []
        self.output_labels = []

        self.title_height = dp(35)
        self.title_offset = dp(13)
        self.vertical_item_offset = dp(-9)

        self.title = QGraphicsTextItem(name, self)
        self.title.setDefaultTextColor(QColor(Qt.GlobalColor.white))
        self.set_title(name)

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)

        self.bg_color = QColor(70, 70, 70)
        self.title_bg_color = QColor(50, 50, 50)
    
    def itemChange(self, change, value):
        # BackgroundRectHelper.add_scene_background_rect()
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            for socket in self.outputs:
                socket.update_connections()

            for socket in self.inputs:
                socket.update_connections()
        return super().itemChange(change, value)

    def set_title(self, title):
        self.title.setPlainText(title)
        
        title_width = self.title.boundingRect().width()
        title_height = self.title.boundingRect().height()

        self.title.setPos(
            (self.width - title_width) / 2, 
            (self.title_height - title_height) / 2
        )

    def get_scene(self) -> NodeScene:
        """A type-hinted helper to get the scene as a NodeScene."""
        return cast(NodeScene, self.scene())

    def on_setting_changed(self, node_id: str, key: str, value: object):
        """Virtual method to allow subclasses to react to setting changes"""
        pass

    def boundingRect(self):
        return QRectF(0, 0, self.width, self.height)

    def paint(self, painter, option, widget=None):
        painter.setPen(QPen(QColor(Qt.GlobalColor.black), 1))
        painter.setBrush(QBrush(self.bg_color))
        painter.drawRoundedRect(0, 0, self.width, self.height, 5, 5)

        painter.setBrush(QBrush(self.title_bg_color))
        painter.drawRoundedRect(0, 0, self.width, self.title_height, 5, 5)

        # Draw border highlight if selected
        if self.isSelected():
            border_color = QColor("#E0C708")
            pen = QPen(border_color, 3)
            pen.setStyle(Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            # Draw the selected border so it fully covers the outer black border
            painter.drawRoundedRect(0, 0, self.width, self.height, 5, 5)

    def add_input(self, socket_type, label_text, y_offset=None, single_connection=True):
        label = QGraphicsTextItem(label_text, self)
        label.setDefaultTextColor(QColor(Qt.GlobalColor.white))

        # explicitly assuming that each label only covers one single line
        y = y_offset or self.title_height + self.title_offset
        y += len(self.inputs) * (self.vertical_item_offset + label.boundingRect().height())

        label.setPos(
            NodeSocket.DIAMETER / 2,
            y - label.boundingRect().height() / 2
        )
        self.output_labels.append(label)

        socket = NodeSocketFactory(0, y, is_input=True, socket_type=socket_type, parent=self, single_connection=single_connection)
        socket.name = f"{label_text}_in"
        self.inputs.append(socket)

    def add_output(self, socket_type, label_text, y_offset=None):
        label = QGraphicsTextItem(label_text, self)
        label.setDefaultTextColor(QColor(Qt.GlobalColor.white))

        # explicitly assuming that each label only covers one single line
        y = y_offset or self.title_height + self.title_offset
        y += len(self.outputs) * (self.vertical_item_offset + label.boundingRect().height())

        label.setPos(
            self.width - label.boundingRect().width() - NodeSocket.DIAMETER / 2,
            y - label.boundingRect().height() / 2
        )
        self.output_labels.append(label)

        socket = NodeSocketFactory(self.width, y, is_input=False, socket_type=socket_type, parent=self, single_connection=False)
        socket.name = f"{label_text}_out"
        self.outputs.append(socket)

    def add_input_output(self, socket_type, label_text, y_offset=None, single_connection=True):
        label = QGraphicsTextItem(label_text, self)
        label.setDefaultTextColor(QColor(Qt.GlobalColor.white))

        # explicitly assuming that each label only covers one single line
        y = y_offset or self.title_height + self.title_offset
        y += len(self.outputs) * (self.vertical_item_offset + label.boundingRect().height())
        
        label.setPos(
            (self.width - label.boundingRect().width()) / 2,
            y - label.boundingRect().height() / 2
        )
        self.output_labels.append(label)

        socket = NodeSocketFactory(0, y, is_input=True, socket_type=socket_type, parent=self, single_connection=single_connection)
        socket.name = f"{label_text}_in"
        self.inputs.append(socket)

        socket = NodeSocketFactory(self.width, y, is_input=False, socket_type=socket_type, parent=self, single_connection=False)
        socket.name = f"{label_text}_out"
        self.outputs.append(socket)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if self.get_scene().socket_active:
            event.ignore()
            return

        # Use the central selection service
        self.get_scene().select_node_item(self)

        # Store starting position for a potential move command
        self._drag_start_pos = self.pos()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().mouseReleaseEvent(event)
        if self._drag_start_pos is not None:
            current_pos = self.pos()
            # Only create a command if the position has actually changed.
            if current_pos != self._drag_start_pos:
                if self.node_id:
                    self.get_scene().controller.move_node(
                        node_id=self.node_id,
                        end_pos=current_pos,
                        start_pos=self._drag_start_pos
                    )
            self._drag_start_pos = None
        
    def contextMenuEvent(self, event):
        menu = QMenu()
        delete_action = menu.addAction("Delete Node")
        action = menu.exec(event.screenPos())
        if action == delete_action and self.node_id:
            self.get_scene().controller.remove_node(self.node_id)

    def delete_node(self):
        for socket in self.inputs + self.outputs:
            for connection in socket.connections[:]:
                connection.delete()

        if self.scene():
            self.scene().removeItem(self)


class NodeImageLoader(NodeBase):
    """Loads raw data, thumbnail and metadata from a raw image file."""

    def __init__(self):
        super().__init__("Load Image", height=dp(120), width=dp(175))
        y = self.title_height + self.title_offset

        # button to select file
        self.select_button = QPushButton("Select File")
        self.select_button_proxy = QGraphicsProxyWidget(self)
        y -= self.select_button_proxy.boundingRect().height() / 2

        self.select_button.setStyleSheet(
            """
            QPushButton {
                background-color: transparent;
                border: none;
                color: white;
            }
            QPushButton:hover {
                text-decoration: underline;
            }
            """
        )
        self.select_button_proxy.setWidget(self.select_button)
        self.select_button_proxy.setPos(
            (self.width - self.select_button_proxy.boundingRect().width()) / 2, y
        )
        y += self.select_button_proxy.boundingRect().height()
        self.select_button.clicked.connect(self.select_file)

        # label showing filename
        self.file_label = QGraphicsTextItem("No file selected", self)
        self.file_label.setDefaultTextColor(QColor(Qt.GlobalColor.white))
        self.file_label.setPos(
            (self.width - self.file_label.boundingRect().width()) / 2, y
        )
        y += self.select_button_proxy.boundingRect().height() * 1.5 + self.title_offset

        # add outputs
        self.add_output(SocketType.RAW, "RAW", y_offset=y)
        self.add_output(SocketType.CFA, "CFA", y_offset=y)
        self.add_output(SocketType.META, "Metadata", y_offset=y)

        # adjust height
        self.height = self.output_labels[-1].y() + self.output_labels[-1].boundingRect().height()

    def select_file(self):
        # Use the central selection service to ensure this node is selected
        self.get_scene().select_node_item(self)

        file_path, _ = QFileDialog.getOpenFileName(
            None, "Select Image File", "",
            "Raw Images (*.cr2 *.nef *.arw *.dng *.rw2 *.orf *.raf *.srw *.pef);;All Files (*)")

        if file_path and self.node_id:
            self.get_scene().controller.update_node_setting(self.node_id, "filepath", file_path)

    def on_setting_changed(self, node_id: str, key: str, value: object):
        if self.node_id == node_id and key == "filepath":
            if value:
                file_name = os.path.basename(str(value))
            else:
                file_name = "No file selected"
            self.file_label.setPlainText(file_name)


class NodeBlackLevels(NodeBase):
    """Sets the black levels of the image and normalizes the values to range [0, 1]"""

    def __init__(self):
        super().__init__("Black Levels")

        self.add_input_output(SocketType.RAW, "RAW")
        self.add_input_output(SocketType.CFA, "CFA")
        self.add_input_output(SocketType.META, "Metadata")

        # adjust height
        self.height = self.output_labels[-1].y() + self.output_labels[-1].boundingRect().height()


class NodeConnection(QGraphicsPathItem):
    def __init__(self, start_socket, end_socket):
        super().__init__()
        self.start_socket = start_socket
        self.end_socket = end_socket
        blended_color = self.blend_color(self.start_socket.brush().color(), QColor("gray"), 0.5)
        self.conn_data: Optional[dict] = None
        self.setPen(QPen(blended_color, 2))
        self.update_path()
        self.setZValue(-1)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)

    def delete(self):
        self.start_socket.remove_connection(self)
        self.end_socket.remove_connection(self)
        if self.scene():
            self.scene().removeItem(self)

    def on_added_to_scene(self):
        if self.scene() is not None:
            self.start_socket.installSceneEventFilter(self)
            self.end_socket.installSceneEventFilter(self)

    def update_path(self):
        p1 = self.start_socket.scenePos()
        p2 = self.end_socket.scenePos()
        path = QPainterPath(p1)
        ctr1 = QPointF(p1.x() + 50, p1.y())
        ctr2 = QPointF(p2.x() - 50, p2.y())
        path.cubicTo(ctr1, ctr2, p2)
        self.setPath(path)

    def blend_color(self, color1, color2, ratio):
        r = color1.red() * (1 - ratio) + color2.red() * ratio
        g = color1.green() * (1 - ratio) + color2.green() * ratio
        b = color1.blue() * (1 - ratio) + color2.blue() * ratio
        return QColor(int(r), int(g), int(b))

    def paint(self, painter, option, widget=None):
        color = self.pen().color()
        if self.isSelected():
            color = color.lighter(150)  # brighten the color when selected

        pen = QPen(color, 2)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(self.path())


class NodeScene(QGraphicsScene):
    node_selected = Signal(object)

    def __init__(self, controller: Controller, model: Model, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.model = model

        self.temp_connection: Optional[QGraphicsPathItem] = None
        self.start_socket: Optional[NodeSocket] = None
        self.socket_active = False

        # Store a map from model ID to the QGraphicsItem. This will be used
        # to create and delete UI nodes when the model changes.
        self.node_items: dict[str, NodeBase] = {}

        # A map from connection data to the QGraphicsPathItem for easy removal.
        self.connection_items: dict[frozenset, NodeConnection] = {}

        # Connect to model signals to make the UI data-driven
        self.model.node_added.connect(self.on_node_added)
        self.model.node_removed.connect(self.on_node_removed)
        self.model.connection_added.connect(self.on_connection_added)
        self.model.connection_removed.connect(self.on_connection_removed)
        self.model.node_position_changed.connect(self.on_node_position_changed)

    def select_node_item(self, node_to_select: Optional[NodeBase]):
        """
        Central method to handle node selection.

        Clears the current selection, selects the given node (if any),
        and emits the node_selected signal to update the UI.
        """
        current_selection = self.selectedItems()

        # Prevent redundant work if the selection state is already correct.
        if not node_to_select and not current_selection:
            return  # Nothing to do, already deselected
        if node_to_select and len(current_selection) == 1 and current_selection[0] == node_to_select:
            return  # Nothing to do, node already selected

        self.clearSelection()
        if node_to_select:
            node_to_select.setSelected(True)

        # Emit the signal with the new selection (or None if deselected)
        self.node_selected.emit(node_to_select)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        item = self.itemAt(event.scenePos(), QTransform())
        if isinstance(item, NodeSocket):
            self.start_socket = item
            self.temp_connection = QGraphicsPathItem()
            self.temp_connection.setPen(QPen(QColor(Qt.GlobalColor.darkYellow), 2, Qt.PenStyle.DashLine))
            self.temp_connection.setZValue(-1)  # Ensure it's drawn under the sockets
            self.addItem(self.temp_connection)
            self.socket_active = True
            return  # Consume the event and do not process further

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        if self.temp_connection and self.start_socket:
            p1 = self.start_socket.scenePos()  # type: ignore
            p2 = event.scenePos()
            path = QPainterPath(p1)
            ctr1 = QPointF(p1.x() + 50, p1.y())
            ctr2 = QPointF(p2.x() - 50, p2.y())
            path.cubicTo(ctr1, ctr2, p2)
            self.temp_connection.setPath(path)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        if self.temp_connection and self.start_socket:
            self.socket_active = False

            end_item: Optional[NodeSocket] = next(
                (i for i in self.items(event.scenePos())
                 if isinstance(i, NodeSocket)
                 and i is not self.start_socket
                 and i.socket_type == self.start_socket.socket_type
                 and i.is_input != self.start_socket.is_input),
                 None
            )
            if isinstance(end_item, NodeSocket) and end_item != self.start_socket:
                if (
                    self.start_socket.socket_type == end_item.socket_type and
                    self.start_socket.is_input != end_item.is_input and
                    self.start_socket.parentItem() != end_item.parentItem()  # type: ignore
                ):
                    # Determine which socket is the output (from) and which is the input (to)
                    from_socket = self.start_socket if not self.start_socket.is_input else end_item
                    to_socket = end_item if end_item.is_input else self.start_socket

                    from_node = from_socket.get_parent_node()
                    to_node = to_socket.get_parent_node()

                    if from_node.node_id and to_node.node_id:
                        self.controller.add_connection(
                            from_node=from_node.node_id, from_socket=from_socket.name,
                            to_node=to_node.node_id, to_socket=to_socket.name
                        )
            self.removeItem(self.temp_connection)
            self.temp_connection = None
            self.start_socket = None
        super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event: QGraphicsSceneContextMenuEvent):
        item = self.itemAt(event.scenePos(), QTransform())
        print('item:', item)
        
        # check if we should pass the context menu event to a Node
        for item in self.items(event.scenePos()):
            print('item:', item)
            while item:
                if isinstance(item, NodeBase):
                    item.contextMenuEvent(event)
                    return
                item = item.parentItem()
        
        menu = QMenu()

        # title
        title_action = menu.addAction("Add Node")
        title_action.setEnabled(False)
        font = title_action.font()
        font.setBold(True)
        title_action.setFont(font)

        menu.addSeparator()

        # node options
        add_loader_action = menu.addAction("Load Image Node")
        add_black_action = menu.addAction("Black Levels Node")

        add_loader_action.triggered.connect(lambda: self.controller.add_node("ImageLoader", event.scenePos()))
        add_black_action.triggered.connect(lambda: self.controller.add_node("BlackLevels", event.scenePos()))
        menu.exec(event.screenPos())

    def on_connection_added(self, conn_data: dict):
        """Slot to handle when a connection is added to the model."""
        from_node_id = conn_data["from_node"]
        from_socket_name = conn_data["from_socket"]
        to_node_id = conn_data["to_node"]
        to_socket_name = conn_data["to_socket"]

        if from_node_id in self.node_items and to_node_id in self.node_items:
            from_node = self.node_items[from_node_id]
            to_node = self.node_items[to_node_id]

            start_socket = next((s for s in from_node.outputs if s.name == from_socket_name), None)
            end_socket = next((s for s in to_node.inputs if s.name == to_socket_name), None)

            if start_socket and end_socket:
                connection = NodeConnection(start_socket, end_socket)
                self.addItem(connection)
                connection.on_added_to_scene()
                start_socket.add_connection(connection)
                end_socket.add_connection(connection)

                # Store for later removal
                key = frozenset(conn_data.items())
                connection.conn_data = conn_data
                self.connection_items[key] = connection

    def on_node_position_changed(self, node_id: str, position: QPointF):
        """Slot to handle when a node's position changes in the model."""
        if node_id in self.node_items:
            node_item = self.node_items[node_id]
            node_item.setPos(position)

    def on_connection_removed(self, conn_data: dict):
        """Slot to handle when a connection is removed from the model."""
        key = frozenset(conn_data.items())
        if key in self.connection_items:
            connection = self.connection_items.pop(key)
            connection.delete()

    def on_node_added(self, node_id: str):
        """Slot to handle when a node is added to the model."""
        node_data = self.model.nodes[node_id]
        node_type = node_data["type"]
        position = QPointF(*node_data["position"])

        # This will be replaced by the node registry later.
        node_class = {"ImageLoader": NodeImageLoader, "BlackLevels": NodeBlackLevels}.get(node_type)

        if node_class:
            node_item = node_class()
            node_item.node_id = node_id
            node_item.setPos(position)
            self.addItem(node_item)
            self.node_items[node_id] = node_item
            self.model.node_setting_changed.connect(node_item.on_setting_changed)
            
            for key, value in node_data.get("settings", {}).items():
                node_item.on_setting_changed(node_id, key, value)

            # Automatically select the new node and update the side panel
            self.clearSelection()
            node_item.setSelected(True)
            self.node_selected.emit(node_item)

    def on_node_removed(self, node_id: str):
        """Slot to handle when a node is removed from the model."""
        if node_id in self.node_items:
            node_item = self.node_items.pop(node_id)

            # Check if the item to be removed is currently selected.
            is_selected = node_item.isSelected()

            self.model.node_setting_changed.disconnect(node_item.on_setting_changed)
            node_item.delete_node()  # Use the node's own cleanup method

            # If the deleted node was selected, clear the side panel.
            if is_selected:
                self.node_selected.emit(None)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_X:
            for item in self.selectedItems():
                if isinstance(item, NodeConnection):
                    if item.conn_data:
                        self.controller.remove_connection(item.conn_data)
        else:
            super().keyPressEvent(event)


class NodeView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)

        self.viewport().setAutoFillBackground(False)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setRenderHints(self.renderHints() | QPainter.RenderHint.Antialiasing)
        self._zoom = 1.0
        self._zoom_range = (0.5, 2.0)
        self._zoom_in_factor = 1.15
        self._zoom_out_factor = 1 / self._zoom_in_factor
        self._is_panning = False
        self._pan_start = QPointF()
        self.setDragMode(QGraphicsView.DragMode.NoDrag)

    def get_scene(self) -> NodeScene:
        """A type-hinted helper to get the scene as a NodeScene."""
        return cast(NodeScene, self.scene())

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            zoom_factor = self._zoom_in_factor
        else:
            zoom_factor = self._zoom_out_factor

        self.zoom(zoom_factor)

    def zoom(self, zoom_factor):
        new_zoom = self._zoom * zoom_factor
        min_zoom, max_zoom = self._zoom_range

        if not (min_zoom <= new_zoom <= max_zoom):
            return

        self._zoom = new_zoom

        self.setTransformationAnchor(self.ViewportAnchor.AnchorUnderMouse)     
        self.setResizeAnchor(self.ViewportAnchor.AnchorUnderMouse)

        self.scale(zoom_factor, zoom_factor)

        self.setTransformationAnchor(self.ViewportAnchor.NoAnchor)
        self.setResizeAnchor(self.ViewportAnchor.NoAnchor)

    def mousePressEvent(self, event: QMouseEvent):
        is_middle_click = event.button() == Qt.MouseButton.MiddleButton
        is_left_background_click = (
            event.button() == Qt.MouseButton.LeftButton and
            not self.scene().items(self.mapToScene(event.position().toPoint()))
        )

        if is_middle_click or is_left_background_click:
            self._is_panning = True
            self._pan_start = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._is_panning:
            pan_end = event.position()
            delta = pan_end - self._pan_start
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - int(delta.x()))
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - int(delta.y()))
            self._pan_start = pan_end
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self._is_panning:
            # Check if it was a click without a significant drag
            moved_distance = (event.position() - self._pan_start).manhattanLength()
            is_left_click = event.button() == Qt.MouseButton.LeftButton

            if is_left_click and moved_distance < QApplication.startDragDistance():
                self.get_scene().select_node_item(None)

            self._is_panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
            return

        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_A and event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            # Only trigger the context menu if the mouse is over this view.
            if self.underMouse():
                cursor_pos = QCursor.pos()  # Global screen position
                scene_pos = self.mapToScene(self.mapFromGlobal(cursor_pos))  # Convert to scene coords

                context_event = QGraphicsSceneContextMenuEvent(QEvent.Type.GraphicsSceneContextMenu)
                context_event.setScenePos(scene_pos)
                context_event.setScreenPos(cursor_pos)
                context_event.setModifiers(Qt.KeyboardModifier.NoModifier)

                self.scene().contextMenuEvent(context_event)
                event.accept()
            else:
                super().keyPressEvent(event)

        elif event.key() == Qt.Key.Key_Plus:
            self.zoom(self._zoom_in_factor)
            event.accept()

        elif event.key() == Qt.Key.Key_Minus:
            self.zoom(self._zoom_out_factor)
            event.accept()

        else:
            super().keyPressEvent(event)