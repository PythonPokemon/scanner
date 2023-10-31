from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.core.window import Window
from PIL import ImageGrab
import io
import sqlite3
import os
import time

class ScreenScannerApp(App):
    def build(self):
        self.layout = BoxLayout(orientation='vertical')
        self.start_button = Button(text='Start Scanning')
        self.stop_button = Button(text='Stop Scanning', disabled=True)
        self.start_button.bind(on_press=self.start_scanning)
        self.stop_button.bind(on_press=self.stop_scanning)
        self.layout.add_widget(self.start_button)
        self.layout.add_widget(self.stop_button)

        # Neu hinzugefügt: Fortschrittsanzeige
        self.progress_label = Label(text='Scan Progress: 0%')
        self.layout.add_widget(self.progress_label)

        self.db_path = os.path.join(os.path.dirname(__file__), "scanned_data.db")
        self.create_database()
        return self.layout

    def create_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_time TEXT,
                screenshot BLOB
            )
        ''')

        # Hinzufügen eines Index für die Spalte scan_time
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_scan_time ON metadata (scan_time)')

        conn.commit()
        conn.close()

    def start_scanning(self, instance):
        self.stop_button.disabled = False
        self.start_button.disabled = True
        self.scanning_event = Clock.schedule_interval(self.scan_and_save_metadata, 5)

    def stop_scanning(self, instance):
        self.stop_button.disabled = True
        self.start_button.disabled = False
        self.scanning_event.cancel()

    def scan_and_save_metadata(self, dt):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        scan_time = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Screenshots des aktuellen Bildschirms
        screenshot = ImageGrab.grab()
        buffer = io.BytesIO()
        screenshot.save(buffer, format='PNG')
        screenshot_binary = buffer.getvalue()

        cursor.execute("INSERT INTO metadata (scan_time, screenshot) VALUES (?, ?)", (scan_time, screenshot_binary))
        conn.commit()
        conn.close()
        print("Scanning and saving metadata at", scan_time)
        self.progress_label.text = f'Scan Progress: {int(dt*100)}%'

if __name__ == '__main__':
    ScreenScannerApp().run()
