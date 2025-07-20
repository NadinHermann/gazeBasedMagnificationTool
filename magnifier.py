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
        self.scale_factor = 2.0  # Default scale factor

        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint) # Frameless window, stays on top
        self.setAttribute(Qt.WA_TranslucentBackground) # Uncomment for transparent background
        self.setWindowOpacity(0.8)  # Set window opacity to 80%
        self.setWindowTitle("Magnifier")
        self.setWindowIcon(QIcon('img/icon.png')) # check why not working

        self.label = QLabel(self)
        self.label.setFixedSize(400, 300) # check if size is okay??

      #  most likely move to main, so i can give coordinates to the magnifier ?
       # Set how often we update the magnifier
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_magnifier)
        # self.update_magnifier()  # Initial call to display the magnifier immediately
        self.timer.start(30) # in milliseconds

        # tray menu
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

    def update_magnifier(self):
        # Get the mouse position
        mx, my = pyautogui.position()

        # Capture the screen (check if region makes sense)
        screen = pyautogui.screenshot()

        # Convert the screenshot to a NumPy array
        frame = np.array(screen)

        # Calculate the region to magnify
        # Size / scale_factor = X
        # X / 2
        # Width of magnification: 400 / 2 = 200
        # Height of magnification: 300 / 2 = 150
        magnify_x1, magnify_y1 = max(0, mx - 100), max(0, my - 75)
        magnify_x2, magnify_y2 = min(frame.shape[1], mx + 100), min(frame.shape[0], my + 75)

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
        self.move(mx + 10, my + 10)

