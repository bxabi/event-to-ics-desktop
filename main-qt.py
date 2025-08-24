import sys
import os
import threading

from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QTextEdit, QPushButton, QVBoxLayout,
    QHBoxLayout, QFileDialog, QMessageBox, QProgressBar, QMenu
)
from PySide6.QtGui import QIcon, QDragEnterEvent, QDropEvent, QAction, QPixmap
from PySide6.QtCore import Qt, Signal, QObject

from ai import ask_gpt
from ui_independent import add_to_calendar


class Worker(QObject):
    finished = Signal(str, bool)

    def __init__(self, text, reminder, file_path):
        super().__init__()
        self.text = text
        self.reminder = reminder
        self.file_path = file_path

    def run(self):
        try:
            result = ask_gpt(self.text, self.reminder, self.file_path)
            self.finished.emit(result, True)
        except Exception as e:
            self.finished.emit(str(e), False)

class DropLabel(QLabel):
    fileDropped = Signal(str)
    fileClicked = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                file_path = urls[0].toLocalFile()
                self.fileDropped.emit(file_path)
        else:
            super().dropEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.fileClicked.emit()
        super().mousePressEvent(event)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Text to ICS")
        self.setWindowIcon(QIcon("icon.png"))
        self.file_path = ""
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.event_label = QLabel("Event Description:")
        layout.addWidget(self.event_label)
        self.event_field = QTextEdit()
        self.event_field.setAcceptDrops(False)
        layout.addWidget(self.event_field)

        self.reminder_label = QLabel("Reminder:")
        layout.addWidget(self.reminder_label)
        self.reminder_field = QTextEdit()
        self.reminder_field.setAcceptDrops(False)
        self.reminder_field.setFixedHeight(40)
        layout.addWidget(self.reminder_field)

        self.image_preview = DropLabel()
        self.image_preview.setText("Drop an image here or Click to open file.")
        self.image_preview.setFixedHeight(100)
        self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview.fileDropped.connect(self.on_file_dropped)
        self.image_preview.fileClicked.connect(self.choose_file)
        layout.addWidget(self.image_preview)

        self.ics_label = QLabel("ICS:")
        self.ics_field = QTextEdit()
        self.ics_field.setVisible(False)
        self.ics_label.setVisible(False)
        layout.addWidget(self.ics_label)
        layout.addWidget(self.ics_field)

        button_layout = QHBoxLayout()
        self.generate_button = QPushButton("Generate")
        self.generate_button.clicked.connect(self.generate_click)
        button_layout.addWidget(self.generate_button)

        self.show_ics = QPushButton("Show the ICS")
        self.show_ics.setEnabled(False)
        self.show_ics.clicked.connect(self.toggle_ics)
        button_layout.addWidget(self.show_ics)
        layout.addLayout(button_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.setLayout(layout)

        # Context menu for event_field
        self.event_field.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.event_field.customContextMenuRequested.connect(self.show_event_menu)

    def show_event_menu(self, pos):
        menu = QMenu(self)
        paste_action = QAction("Paste", self)
        paste_action.triggered.connect(lambda: self.event_field.paste())
        menu.addAction(paste_action)
        menu.exec(self.event_field.mapToGlobal(pos))

    def choose_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Choose Image", os.path.expanduser("~") + "/Desktop",
            "Image files (*.jpg *.png *.jpeg *.JPG *.PNG *.JPEG)"
        )
        if file_path:
            self.file_path = file_path
            self.set_image_preview()

    def on_file_dropped(self, file_path):
        self.file_path = file_path
        self.set_image_preview()

    def set_image_preview(self):
        pixmap = QPixmap(self.file_path)
        if not pixmap.isNull():
            self.image_preview.setPixmap(
                pixmap.scaled(
                    self.image_preview.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.file_path:
            self.set_image_preview()

    def generate_click(self):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.generate_button.setEnabled(False)
        self.show_ics.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate

        text = self.event_field.toPlainText()
        reminder = self.reminder_field.toPlainText()

        self.worker = Worker(text, reminder, self.file_path)
        self.worker.finished.connect(self.on_finished)
        self.thread = threading.Thread(target=self.worker.run)
        self.thread.start()

    def on_finished(self, result, success):
        self.progress_bar.setVisible(False)
        QApplication.restoreOverrideCursor()
        self.generate_button.setEnabled(True)
        self.show_ics.setEnabled(True)
        if success:
            self.ics_field.setPlainText(result)
            add_to_calendar(result)
        else:
            QMessageBox.critical(self, "Error", result)

    def toggle_ics(self):
        visible = not self.ics_field.isVisible()
        self.ics_field.setVisible(visible)
        self.ics_label.setVisible(visible)
        self.show_ics.setText("Hide the ICS" if visible else "Show the ICS")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
