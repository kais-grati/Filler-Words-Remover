import sys
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QWidget, QPushButton, QGridLayout, QFileDialog, QVBoxLayout, QLabel
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import Qt, QUrl, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import  QMovie
from classes import *
import ressource_rc



class MyApp(QtWidgets.QMainWindow):
    def __init__(self):
        super(MyApp, self).__init__()
        uic.loadUi('gui.ui', self)
        self.is_playing = False
        self.cached_text = {}
        self.selected_index = None
        self.grid_buttons = []
        self.skip_intervals = []
        self.stop_at = None
        self.filepath = None
        self.default_model = "large"
        self.default_device = "cpu"

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_skip)

        self.player = QMediaPlayer(None, QMediaPlayer.StreamPlayback)
        self.player.positionChanged.connect(self.update_slider)
        self.player.durationChanged.connect(self.update_duration)
        self.player.stateChanged.connect(self.handle_state_changed)
        
        self.position_slider.sliderMoved.connect(self.set_position)
        self.play_track_button.clicked.connect(self.pauseplayAudio)
        self.remove_word_button.clicked.connect(self.remove_word)
        self.import_button.clicked.connect(self.import_file)
        self.play_word_button.clicked.connect(self.play_word)
        self.min_entry.valueChanged.connect(self.manual_update)
        self.sec_entry.valueChanged.connect(self.manual_update)
        self.ms_entry.valueChanged.connect(self.manual_update)
        self.export_button.clicked.connect(self.export_video)
        self.start_entry.valueChanged.connect(self.modify_timings)
        self.end_entry.valueChanged.connect(self.modify_timings)

        self.set_model_high.triggered.connect(lambda: self.set_model("large"))
        self.set_model_medium.triggered.connect(lambda: self.set_model("medium"))
        self.set_model_low.triggered.connect(lambda: self.set_model("small"))

        self.set_device_cpu.triggered.connect(lambda: self.set_device("cpu"))
        self.set_device_gpu.triggered.connect(lambda: self.set_device("cuda"))

        self.position_slider.setEnabled(False)
        self.play_track_button.setEnabled(False)
        self.remove_word_button.setEnabled(False)
        self.play_word_button.setEnabled(False)
        self.min_entry.setEnabled(False)
        self.sec_entry.setEnabled(False)
        self.ms_entry. setEnabled(False)
        self.export_button.setEnabled(False)
        self.start_entry.setEnabled(False)
        self.end_entry.setEnabled(False)

        self.animation_wrapper_layout = QVBoxLayout(self.animation_wrapper)
        self.animation_wrapper_layout.setAlignment(Qt.AlignTop)

        self.status_bar.showMessage('Clearing cache...', 2000)
        # self.show_loading_widget()
        # self.loading_widget.set_status_text("Clearing cache")
        self.clear_cache()
        

    def start_thread(self, file_path):
        self.thread = TextExtractor(file_path, self.default_device, self.default_model)
        self.thread.update_signal.connect(self.update_text)
        self.thread.start()

    def update_text(self, results):
        self.loading_widget.deleteLater()
        self.status_bar.clearMessage()
        self.status_bar.showMessage("Transcription completed!")
        text = results[0]
        self.cached_text = results[1]

        grid_layout = QGridLayout()
        row = 0
        col = 0
        max_columns = 10  # Adjust this value to change the number of columns in the grid

        for index, word in enumerate(text):
            button = CustomButton(word)
            button.clicked.connect(lambda checked, idx=index: self.word_pressed(idx))
            self.grid_buttons.append(button)
            grid_layout.addWidget(button, row, col)   
            
            # Update the row and column indices
            col += 1
            if col >= max_columns:
                col = 0
                row += 1

        # Set the layout to the wrapper widget
        self.body.setLayout(grid_layout)

        url = QUrl.fromLocalFile('cache.wav')
        content = QMediaContent(url)
        self.player.setMedia(content)

    def word_pressed(self, index):
        self.selected_index = index
        print(index)
        self.display_timings()

    def display_timings(self):
        index = self.selected_index

        if index != None:
            for segment in self.cached_text['segments']:
                if index < len(segment['words']):
                    start = segment['words'][index]["start"]
                    end = segment['words'][index]["end"]
                    self.start_entry.setValue(start)
                    self.end_entry.setValue(end)
                    break
                else:
                    index -= len(segment['words'])

    def modify_timings(self):
        start = self.start_entry.value()
        end = self.end_entry.value()
        index = self.selected_index

        if index != None:
            for idx, segment in enumerate(self.cached_text['segments']):
                if index < len(segment['words']):
                    self.cached_text['segments'][idx]['words'][index]["start"] = start
                    self.cached_text['segments'][idx]['words'][index]["end"] = end
                    break
                else:
                    index -= len(segment['words'])

    def remove_word(self):
        index = self.selected_index
        if self.selected_index == None:
            return
        
        button = self.grid_buttons[index]
        button.deleteLater()
        
        for segment in self.cached_text['segments']:
            if index < len(segment['words']):
                start = int(segment['words'][index]["start"] * 1000) 
                end = int(segment['words'][index]["end"] * 1000)
                self.skip_intervals.append((start, end))
                segment['words'].pop(index)
                break
            else:
                index -= len(segment['words'])
        
        self.selected_index = None


    def play_word(self):
        index = self.selected_index
        for segment in self.cached_text['segments']:
            if index < len(segment['words']):
                print(segment['words'][index]["word"])
                start = int(segment['words'][index]["start"] * 1000) 
                end = int(segment['words'][index]["end"] * 1000)
                self.player.setPosition(start)
                self.stop_at = end
                self.player.play()
                self.timer.start(10)
                break
            else:
                index -= len(segment['words'])

    def set_position(self, position):
        self.player.setPosition(position)

    def check_skip(self):
        position = self.player.position()
        if self.stop_at:
            if position >= self.stop_at:
                self.player.pause()
                self.timer.stop()
                self.stop_at = None
        else:
            for start, end in self.skip_intervals:
                if start <= position < end:
                    self.player.setPosition(end)
                    break

    def pauseplayAudio(self):
        
        if self.is_playing == True:
            self.player.pause()
            self.timer.stop()
        else:
            self.player.play()
            self.timer.start(10)
        
        self.is_playing = not self.is_playing

    def manual_update(self):
        min = self.min_entry.value()
        sec = self.sec_entry.value()
        ms = self.ms_entry.value()
        position = min * 60000 + sec * 1000 + ms
        self.player.setPosition(position)
        self.update_slider(position)

    def update_slider(self, position):
        self.position_slider.setValue(position)
        milliseconds = position % 1000
        seconds = (position // 1000) % 60
        minutes = (position // 60000) % 60
        
        self.min_entry.setValue(minutes)
        self.sec_entry.setValue(seconds)
        self.ms_entry.setValue(milliseconds)
        # self.position_label.setText(f"{minutes:02}:{seconds:02}.{milliseconds:03}")

    def update_duration(self, duration):
        self.position_slider.setRange(0, duration)

    def handle_state_changed(self, new_state):
        if new_state == QMediaPlayer.StoppedState:
            self.is_playing = False

    def export_video(self):
        self.status_bar.showMessage("Exporting...")
        intervals = [(start / 1000, end / 1000) for start, end in self.skip_intervals]
        self.export_thread = Exporter(self.filepath, intervals, self.cached_text)
        self.export_thread.update_signal.connect(self.finished_exporting)
        self.export_thread.start()

    def finished_exporting(self, data):
        self.status_bar.showMessage("Done exporting, output file is final.mp4")

    def import_file(self):

        options = QFileDialog.Options()
        file_filter = 'Video Files (*.mp4 *.avi *.mov *.mkv)'
        file_name, _ = QFileDialog.getOpenFileName(self, 'Open Video File', '', file_filter, options=options)
        self.filepath = file_name
        
        if file_name:

            self.show_loading()
            self.loading_widget.set_status_text('Transcribing video...')
            self.player.stop()
            self.start_thread(file_name)
            self.status_bar.showMessage("Transcribing video, this can take a while...")

            self.position_slider.setEnabled(True)
            self.play_track_button.setEnabled(True)
            self.remove_word_button.setEnabled(True)
            self.play_word_button.setEnabled(True)
            self.min_entry.setEnabled(True)
            self.sec_entry.setEnabled(True)
            self.ms_entry.setEnabled(True)
            self.export_button.setEnabled(True)
            self.start_entry.setEnabled(True)
            self.end_entry.setEnabled(True)
        else:
            return
    
    def clear_cache(self):
        self.clear_cache_thread = ClearCacheThread()
        self.clear_cache_thread.finished.connect(self.on_cache_cleared)
        self.clear_cache_thread.start()
        self.show_loading()
        self.loading_widget.set_status_text('Clearing cache...')

    def on_cache_cleared(self):
        self.status_bar.showMessage("Cache cleared successfully!", 5000)
        self.loading_widget.deleteLater()

    def set_model(self, model):
        self.default_model = model
        print(self.default_model, self.default_device)

    def set_device(self, device):
        self.default_device = device

    def show_loading(self):
        self.loading_widget = LoadingWidget(self.animation_wrapper)
        
        # Clear existing content in the body_widget
        for i in reversed(range(self.animation_wrapper_layout.count())):
            widget = self.animation_wrapper_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        # Add the loading widget to the body_layout
        self.animation_wrapper_layout.addWidget(self.loading_widget)

def main():

    app = QtWidgets.QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
