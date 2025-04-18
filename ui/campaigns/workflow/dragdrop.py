import sys
import json
from PyQt6.QtWidgets import (
    QApplication, QGraphicsScene, QGraphicsView, QGraphicsItem, QGraphicsEllipseItem,QLabel, 
    QGraphicsTextItem, QGraphicsLineItem, QMenu, QFileDialog, QInputDialog, QGraphicsRectItem,
    QVBoxLayout, QHBoxLayout, QMainWindow, QPushButton, QWidget, QListWidget, QListWidgetItem
)
from PyQt6.QtGui import QPen, QColor, QPainter, QBrush
from PyQt6.QtCore import Qt, QPointF, QMimeData
from PyQt6.QtGui import QDrag


# ActionLibrary for the drag-and-drop feature
class ActionLibrary(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(200)
        self.setDragEnabled(True)
        self.add_actions()

    def add_actions(self):
        actions = [
            "Like_Post", "Comment_Post",
            "Send_Connection_Request", "Send_Follow_up_Message",
            "Condition_Node"
        ]
        for action in actions:
            item = QListWidgetItem(action)
            self.addItem(item)

    def startDrag(self, supportedActions):
        item = self.currentItem()
        mimeData = QMimeData()
        mimeData.setText(item.text())

        drag = QDrag(self)
        drag.setMimeData(mimeData)
        drag.exec(Qt.DropAction.MoveAction)


# NodeItem to represent individual nodes
class NodeItem(QGraphicsRectItem):
    def __init__(self, text, node_type="Action"):
        super().__init__(-50, -25, 100, 50)
        self.setBrush(QBrush(Qt.GlobalColor.lightGray))
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
                      QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
                      QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.text = QGraphicsTextItem(text, self)
        self.text.setDefaultTextColor(Qt.GlobalColor.black)
        self.text.setPos(-40, -15)
        self.node_type = node_type
        self.connections = []
        self.properties = {"name": text, "type": node_type}

    def contextMenuEvent(self, event):
        menu = QMenu()
        edit_action = QAction("Edit Properties")
        menu.addAction(edit_action)
        action = menu.exec(event.screenPos())

        if action == edit_action:
            name, ok = QInputDialog.getText(None, "Edit Node Name", "Name:", text=self.properties['name'])
            if ok:
                self.properties['name'] = name
                self.text.setPlainText(name)


# ConnectionLine to represent connections between nodes
class ConnectionLine(QGraphicsLineItem):
    def __init__(self, source_node, dest_node):
        super().__init__()
        self.source_node = source_node
        self.dest_node = dest_node
        self.setPen(QPen(Qt.GlobalColor.black, 2))
        self.update_position()

    def update_position(self):
        src_pos = self.source_node.sceneBoundingRect().center()
        dst_pos = self.dest_node.sceneBoundingRect().center()
        self.setLine(src_pos.x(), src_pos.y(), dst_pos.x(), dst_pos.y())


# WorkflowEditor where all nodes are placed, connected, and validated
class WorkflowEditor(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.setRenderHints(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setWindowTitle("Visual Workflow Editor")
        self.resize(800, 600)
        self.start_node = None
        self.setAcceptDrops(True)

    def mouseDoubleClickEvent(self, event):
        pos = self.mapToScene(event.pos())
        text, ok = QInputDialog.getText(self, "New Node", "Enter name:type (e.g., CheckUser:Condition)")
        if ok:
            if ':' in text:
                name, node_type = text.split(':')
            else:
                name, node_type = text, 'Action'
            node = NodeItem(name, node_type)
            node.setPos(pos)
            self.scene.addItem(node)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            item = self.itemAt(event.pos())
            if isinstance(item, NodeItem):
                self.start_node = item
            else:
                self.start_node = None
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton and self.start_node:
            item = self.itemAt(event.pos())
            if isinstance(item, NodeItem) and item != self.start_node:
                line = ConnectionLine(self.start_node, item)
                self.scene.addItem(line)
                self.start_node.connections.append(line)
                item.connections.append(line)
            self.start_node = None
        super().mouseReleaseEvent(event)

    def save_workflow(self, path):
        nodes = []
        lines = []
        for item in self.scene.items():
            if isinstance(item, NodeItem):
                nodes.append({
                    "id": id(item),
                    "name": item.properties['name'],
                    "type": item.node_type,
                    "x": item.pos().x(),
                    "y": item.pos().y()
                })
            elif isinstance(item, ConnectionLine):
                lines.append({
                    "from": id(item.source_node),
                    "to": id(item.dest_node)
                })
        data = {"nodes": nodes, "connections": lines}
        with open(path, 'w') as f:
            json.dump(data, f, indent=4)

    def load_workflow(self, path):
        with open(path, 'r') as f:
            data = json.load(f)
        self.scene.clear()
        id_map = {}
        for node_data in data["nodes"]:
            node = NodeItem(node_data["name"], node_data["type"])
            node.setPos(QPointF(node_data["x"], node_data["y"]))
            self.scene.addItem(node)
            id_map[node_data["id"]] = node
        for line in data["connections"]:
            if line["from"] in id_map and line["to"] in id_map:
                conn = ConnectionLine(id_map[line["from"]], id_map[line["to"]])
                self.scene.addItem(conn)

    def validate_workflow(self):
        errors = []
        for item in self.scene.items():
            if isinstance(item, NodeItem) and item.node_type == "Condition":
                count = sum(1 for line in item.connections if isinstance(line, ConnectionLine) and line.source_node == item)
                if count < 2:
                    errors.append(f"Condition node '{item.properties['name']}' has less than 2 branches.")
        return errors


# MainWindow to integrate the ActionLibrary and WorkflowEditor
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Visual Workflow Builder")
        self.setGeometry(100, 100, 1000, 600)
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout()

        self.action_library = ActionLibrary()
        self.canvas = WorkflowEditor()

        save_btn = QPushButton("🔄 Save Workflow")
        save_btn.clicked.connect(self.save_workflow)

        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("Action Library"))
        left_layout.addWidget(self.action_library)
        left_layout.addWidget(save_btn)

        main_layout.addLayout(left_layout)
        main_layout.addWidget(self.canvas)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def save_workflow(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Workflow", "workflow.json", "JSON Files (*.json)")
        if path:
            self.canvas.save_workflow(path)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
