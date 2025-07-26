from PyQt5.QtCore import pyqtSignal, Qt, QTimer
from PyQt5.QtGui import QIcon, QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QMenu, QAction, QSystemTrayIcon
import pyautogui
import cv2
import numpy as np

class Magnifier(QWidget):
    exit_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.window_width = 800
        self.window_height = 600
        self.scale_factor = 2.0  # Vergrößerungsfaktor
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint) # Frameless window, stays on top
        self.setAttribute(Qt.WA_TranslucentBackground) # Uncomment for transparent background
        self.setWindowOpacity(0.8)  # Set window opacity to 80%
        self.setWindowTitle("Magnifier")
        self.setWindowIcon(QIcon('img/icon.png')) # check why not working

        self.label = QLabel(self)
        self.label.setFixedSize(self.window_width, self.window_height)

        # Neue Attribute für Gaze-Koordinaten
        self.gaze_x = None
        self.gaze_y = None

        # Für Glättung: Liste der letzten N Gaze-Koordinaten
        self.gaze_history = []
        self.gaze_history_size = 5  # Je größer, desto glatter, aber träger

        # Set how often we update the magnifier
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_magnifier)
        self.timer.start(30) # in milliseconds

        self.create_tray_icon()

    def create_tray_icon(self):
        self.create_context_menu()
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("img/icon.png"))  # Set your icon path here (needs to be a valid icon file)
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.show()

    def create_context_menu(self):
        self.tray_menu = QMenu(self)

        # Add actions to the context menu
        self.exit_action = QAction("Exit", self)
        self.exit_action.triggered.connect(QApplication.quit)
        self.tray_menu.addAction(self.exit_action)

        self.hide_action = QAction("Hide (Esc)", self)
        self.hide_action.triggered.connect(self.hide)
        self.tray_menu.addAction(self.hide_action)

        self.unhide_hide_action = QAction("Unhide", self)
        self.unhide_hide_action.triggered.connect(self.show)

    def set_coordinates(self, x, y):
        # Neue Koordinate zur Historie hinzufügen
        self.gaze_history.append((int(x), int(y)))
        if len(self.gaze_history) > self.gaze_history_size:
            self.gaze_history.pop(0)
        # Mittelwert berechnen
        xs = [pt[0] for pt in self.gaze_history]
        ys = [pt[1] for pt in self.gaze_history]
        self.gaze_x = int(sum(xs) / len(xs))
        self.gaze_y = int(sum(ys) / len(ys))

    def update_magnifier(self):
        # Verwende Gaze-Koordinaten, falls vorhanden, sonst Mausposition
        if self.gaze_x is not None and self.gaze_y is not None:
            mx, my = self.gaze_x, self.gaze_y
        else:
            mx, my = pyautogui.position()

        # Capture the screen (check if region makes sense)
        screen = pyautogui.screenshot()

        # Convert the screenshot to a NumPy array
        frame = np.array(screen)

        # Calculate the region to magnify
        half_width = int(self.window_width / (2 * self.scale_factor))
        half_height = int(self.window_height / (2 * self.scale_factor))
        magnify_x1, magnify_y1 = max(0, mx - half_width), max(0, my - half_height)
        magnify_x2, magnify_y2 = min(frame.shape[1], mx + half_width), min(frame.shape[0], my + half_height)

        # Magnify the region
        magnified_frame = frame[magnify_y1:magnify_y2, magnify_x1:magnify_x2]
        magnified_frame = cv2.resize(magnified_frame, (0, 0), fx=self.scale_factor, fy=self.scale_factor)

        # Convert the magnified frame to QImage and display it in the label
        height, width, channel = magnified_frame.shape
        bytesPerLine = 3 * width
        qImg = QImage(magnified_frame.data, width, height, bytesPerLine, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qImg)
        self.label.setPixmap(pixmap)

        # Move the window to follow the mouse cursor
        self.move(mx + 1, my + 1)
