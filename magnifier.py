from PyQt5.QtCore import pyqtSignal, Qt, QTimer
from PyQt5.QtGui import QIcon, QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QMenu, QAction, QSystemTrayIcon
import mss
import pyautogui
import cv2
import platform
import numpy as np

class Magnifier(QWidget):
    exit_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.window_width = 800
        self.window_height = 600
        self.scale_factor = 2.0
        self.setWindowFlags(
            self.windowFlags()
            | Qt.Tool
            | Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowOpacity(0.8)  # Set window opacity to 80%
        self.setWindowTitle("Magnifier")

        self.label = QLabel(self)
        self.label.setFixedSize(self.window_width, self.window_height)

        self.gaze_x = None
        self.gaze_y = None

        # List for moving average of gaze coordinates
        self.gaze_history = []
        self.gaze_history_size = 3  # Bigger size for smoother movement, but slower response

        # MSS screen capturer
        self.sct = mss.mss()

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
        # Add the new gaze coordinates to the history
        self.gaze_history.append((int(x), int(y)))
        if len(self.gaze_history) > self.gaze_history_size:
            self.gaze_history.pop(0)
        # Calculate the average gaze coordinates
        xs = [pt[0] for pt in self.gaze_history]
        ys = [pt[1] for pt in self.gaze_history]
        self.gaze_x = int(sum(xs) / len(xs))
        self.gaze_y = int(sum(ys) / len(ys))

    def grab_screen(self):
        # Grab from primary monitor
        monitor = self.sct.monitors[1]
        shot = self.sct.grab(monitor)

        # Convert to NumPy array in RGB
        img = np.array(shot)
        img = img[:, :, :3]  # Remove alpha channel if present
        return img

    def update_magnifier(self):
        # Use the gaze coordinates if available, otherwise use the mouse position
        if self.gaze_x is not None and self.gaze_y is not None:
            mx, my = self.gaze_x, self.gaze_y
        else:
            mx, my = pyautogui.position()

        # Capture the screen (check if region makes sense)
        # self.hide()
        # self.setWindowOpacity(0.0)
        # screen = pyautogui.screenshot()
        # self.setWindowOpacity(0.8)
        # self.show()

        # Convert the screenshot to a NumPy array
        # frame = np.array(screen)

        # frame = self.grab_screen()

        frame = self.grab_screen_excluding_self()

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
        # self.move(mx + 1, my + 1)
        self.move(mx - self.window_width // 2, my - self.window_height // 2)

    def exclude_from_capture(self):
        os_name = platform.system()
        print(os_name)
        if platform.system() == "Windows":
            old_pos = self.pos()
            self.move(-2000, -2000)  # far off-screen
            QApplication.processEvents()
            img = self.grab_screen()
            self.move(old_pos)
            QApplication.processEvents()
            return img
        else:
            return self.grab_screen()
        # if os_name == "Windows":
        #     import ctypes
        #     hwnd = int(self.winId())
        #     GWL_EXSTYLE = -20
        #     WS_EX_LAYERED = 0x00080000
        #     WS_EX_TRANSPARENT = 0x00000020
        #     user32 = ctypes.windll.user32
        #     GetWindowLong = user32.GetWindowLongW
        #     SetWindowLong = user32.SetWindowLongW
        #     style = GetWindowLong(hwnd, GWL_EXSTYLE)
        #     style |= WS_EX_LAYERED | WS_EX_TRANSPARENT
        #     SetWindowLong(hwnd, GWL_EXSTYLE, style)

        # elif os_name == "Darwin":  # macOS
        #     from AppKit import NSApp
        #     from Quartz import kCGWindowSharingNone
        #     window = NSApp.windows()[-1]
        #     window.setSharingType_(kCGWindowSharingNone)
        #
        # elif os_name == "Linux":  # X11 only
        #     from PyQt5.QtX11Extras import QX11Info
        #     import Xlib.display
        #     display = Xlib.display.Display()
        #     window = display.create_resource_object('window', int(self.winId()))
        #     NET_WM_WINDOW_TYPE = display.intern_atom('_NET_WM_WINDOW_TYPE')
        #     NET_WM_WINDOW_TYPE_DOCK = display.intern_atom('_NET_WM_WINDOW_TYPE_DOCK')
        #     window.change_property(NET_WM_WINDOW_TYPE, Xlib.Xatom.ATOM, 32, [NET_WM_WINDOW_TYPE_DOCK])
        #     display.sync()
