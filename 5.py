from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock
from PIL import ImageGrab
from kivy.uix.image import Image
from io import BytesIO
import io
import sqlite3
import os
import time
import threading

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
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_scan_time ON metadata (scan_time)')
        conn.commit()
        conn.close()

    def start_scanning(self, instance):
        self.stop_button.disabled = False
        self.start_button.disabled = True
        self.stopped = False  # Stopp-Bedingung zurücksetzen
        self.scanning_thread = threading.Thread(target=self.scan_and_save_metadata_thread)
        self.scanning_thread.daemon = True
        self.scanning_thread.start()

    def stop_scanning(self, instance):
        self.stop_button.disabled = True
        self.start_button.disabled = False
        self.stopped = True  # Stopp-Bedingung setzen
        if self.scanning_thread and self.scanning_thread.is_alive():
            self.scanning_thread.join()

    def scan_and_save_metadata_thread(self):
        while not self.stopped:  # Überprüfung der Stopp-Bedingung
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            scan_time = time.strftime("%Y-%m-%d %H:%M:%S")
            
            screenshot = ImageGrab.grab()
            buffer = io.BytesIO()
            screenshot.save(buffer, format='PNG')
            screenshot_binary = buffer.getvalue()

            cursor.execute("INSERT INTO metadata (scan_time, screenshot) VALUES (?, ?)", (scan_time, screenshot_binary))
            conn.commit()
            conn.close()
            print("Scanning and saving metadata at", scan_time)
            Clock.schedule_once(self.update_progress_label, 0)

            # Sleep for 5 seconds before the next scan
            time.sleep(5)

    def update_progress_label(self, *args):
        self.progress_label.text = f'Scan Progress: 100%'

    def show_latest_screenshot(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT screenshot FROM metadata ORDER BY id DESC LIMIT 1")
        latest_screenshot = cursor.fetchone()
        conn.close()

        if latest_screenshot:
            latest_screenshot_data = latest_screenshot[0]
            image_stream = BytesIO(latest_screenshot_data)
            img = Image(texture=image_stream.getvalue())
            self.layout.add_widget(img)

if __name__ == '__main__':
    ScreenScannerApp().run()
