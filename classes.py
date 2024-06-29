import os
import re
import time
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QWidget, QPushButton, QGridLayout, QFileDialog, QVBoxLayout, QLabel
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import Qt, QUrl, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import  QMovie
import ressource_rc
import extractor

class CustomButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setStyleSheet(self.default_style())
        self.clicked.connect(self.handle_click)

    def default_style(self):
        return """
            QPushButton{
            border-radius: 10px;
            border: none;
            padding: 10px;
            background-color: none;
            color: white;
            font-size: 15px;
            }

            QPushButton:hover{
            color: #e83259
            }
        """

    def selected_style(self):
        return """
            QPushButton{
            border-radius: 10px;
            border: none;
            padding: 10px;
            background-color: none;
            color: white;
            font-size: 20px;
            color: #e83259
            }

            QPushButton:hover{
            color: #e83259
            }
        """

    def handle_click(self):
        for button in self.parent().findChildren(CustomButton):
            if button is not self:
                button.setChecked(False)
                button.setStyleSheet(button.default_style())
        self.setStyleSheet(self.selected_style())

class TextExtractor(QThread):
    update_signal = pyqtSignal(tuple)

    def __init__(self, file_path, device, model):
        super().__init__()
        self.file_path = file_path
        self.device = device
        self.model = model

    def run(self):
        result = extractor.run_whisper(self.file_path, self.device, self.model)
        self.update_signal.emit(result)

class Exporter(QThread):
    update_signal = pyqtSignal(str)

    def __init__(self, file_path, unwanted_words, result):
        super().__init__()
        self.file_path = file_path
        self.unwanted_words = unwanted_words
        self.result = result

    def run(self):
        extractor.exporter(self.unwanted_words, self.result, self.file_path)
        self.update_signal.emit('Done exporting!')


class LoadingWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        self.dots_label = QLabel(self)
        self.movie = QMovie("dots.gif")  
        self.dots_label.setMovie(self.movie)
        self.movie.start()

        self.status_label = QLabel(self)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: white; font-size: 20px")
        self.status_label.setText("Loading...")  


        layout.addWidget(self.dots_label)
        layout.addWidget(self.status_label)

        self.setLayout(layout)

    def set_status_text(self, text):
        self.status_label.setText(text)

class ClearCacheThread(QThread):
    finished = pyqtSignal()  

    def __init__(self, parent=None):
        super().__init__(parent)

    def run(self):
        time.sleep(3)
        current_directory = os.getcwd()

        # Remove cache.wav if it exists
        cache_file = os.path.join(current_directory, "cache.wav")
        if os.path.exists(cache_file):
            os.remove(cache_file)
            print(f"Removed {cache_file}")

        # Remove cutvid[number].mp4 files
        pattern = re.compile(r'^cutvid(\d+)\.mp4$')
        for filename in os.listdir(current_directory):
            if pattern.match(filename):
                file_path = os.path.join(current_directory, filename)
                os.remove(file_path)
                print(f"Removed {file_path}")

        self.finished.emit()