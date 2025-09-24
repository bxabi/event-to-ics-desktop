import sys
import os
import threading
import tempfile

from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QTextEdit, QPushButton, QVBoxLayout,
    QHBoxLayout, QFileDialog, QMessageBox, QProgressBar, QMenu, QSizePolicy
)
from PySide6.QtGui import QIcon, QDragEnterEvent, QDropEvent, QAction, QPixmap, QKeySequence, QImage, QPainter
from PySide6.QtCore import Qt, Signal, QObject, QEvent

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


class ImageLabel(QLabel):
    fileDropped = Signal(str)
    fileClicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pixmap = QPixmap()
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

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

    def setPixmap(self, pixmap):
        self._pixmap = pixmap
        self.update()  # Trigger a repaint

    def paintEvent(self, event):
        super().paintEvent(event)

        if not self._pixmap.isNull():
            # Scale pixmap to fit the label, keeping aspect ratio
            scaled_pixmap = self._pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio,
                                                Qt.TransformationMode.SmoothTransformation)
            painter = QPainter(self)
            # Center the scaled pixmap within the label
            x = (self.width() - scaled_pixmap.width()) / 2
            y = (self.height() - scaled_pixmap.height()) / 2
            painter.drawPixmap(int(x), int(y), scaled_pixmap)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Text to ICS")
        self.setWindowIcon(QIcon("icon.png"))
        self.file_path = ""
        self.temp_file_path = ""
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

        self.event_field.installEventFilter(self)
        self.reminder_field.installEventFilter(self)

        self.image_preview = ImageLabel()
        self.image_preview.setText("Drop an image here or Click to open file.")
        self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview.fileDropped.connect(self.on_file_dropped)
        self.image_preview.fileClicked.connect(self.choose_file)
        self.image_preview.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
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

        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()

        if mime_data.hasImage():
            paste_action.triggered.connect(lambda: self.handle_pasted_image(clipboard.image()))
        elif mime_data.hasText():
            paste_action.triggered.connect(self.event_field.paste)
        else:
            paste_action.setEnabled(False)

        menu.addAction(paste_action)
        menu.exec(self.event_field.mapToGlobal(pos))

    def cleanup_temp_file(self):
        if self.temp_file_path and os.path.exists(self.temp_file_path):
            os.remove(self.temp_file_path)
            self.temp_file_path = ""

    def closeEvent(self, event):
        self.cleanup_temp_file()
        super().closeEvent(event)

    def eventFilter(self, source, event):
        if (event.type() == QEvent.KeyPress and event.matches(QKeySequence.StandardKey.Paste)):
            if source is self.event_field or source is self.reminder_field:
                clipboard = QApplication.clipboard()
                if clipboard.mimeData().hasImage():
                    image = clipboard.image()
                    if not image.isNull():
                        self.handle_pasted_image(image)
                        return True  # Event handled
        return super().eventFilter(source, event)

    def handle_pasted_image(self, image: QImage):
        self.cleanup_temp_file()
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
            self.temp_file_path = temp_file.name
        if image.save(self.temp_file_path):
            self.file_path = self.temp_file_path
            self.set_image_preview()
        else:
            QMessageBox.warning(self, "Paste Error", "Could not save pasted image.")
            self.cleanup_temp_file()

    def choose_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Choose Image", os.path.expanduser("~") + "/Desktop",
            "Image files (*.jpg *.png *.jpeg *.JPG *.PNG *.JPEG)"
        )
        if file_path:
            self.cleanup_temp_file()
            self.file_path = file_path
            self.set_image_preview()

    def on_file_dropped(self, file_path):
        self.cleanup_temp_file()
        self.file_path = file_path
        self.set_image_preview()

    def set_image_preview(self):
        pixmap = QPixmap(self.file_path)
        if not pixmap.isNull():
            self.image_preview.setPixmap(pixmap)
        else:
            self.image_preview.setText("Drop an image here or Click to open file.")

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
