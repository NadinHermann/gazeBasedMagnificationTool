import cv2
import mss
import numpy as np
import pyautogui
from PyQt5.QtCore import pyqtSignal, Qt, QTimer
from PyQt5.QtGui import QIcon, QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QMenu, QAction, QSystemTrayIcon

class Magnifier(QWidget):
    exit_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.last_window_pos = None
        self.window_width = 800
        self.window_height = 600
        self.scale_factor = 2.0

        # Window settings
        self.setWindowFlags(
            self.windowFlags()
            | Qt.Tool
            | Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowOpacity(0.9)
        self.setWindowTitle("Magnifier")

        self.label = QLabel(self)
        self.label.setFixedSize(self.window_width, self.window_height)

        self.create_tray_icon()

        # Smoothed gaze data
        self.gaze_x = None
        self.gaze_y = None
        self.gaze_history = []
        self.gaze_history_size = 12  # more smoothing

        # Jitter control
        self.dead_zone = 20  # px, ignore small movements
        self.max_speed = 50  # px/frame, clamp movement
        self.window_move_dead_zone = 100

        self.sct = mss.mss()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_magnifier)
        self.timer.start(30)

    def create_tray_icon(self):
        self.create_context_menu()
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("img/icon.png"))
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.show()

    def create_context_menu(self):
        self.tray_menu = QMenu(self)

        self.exit_action = QAction("Exit", self)
        self.exit_action.triggered.connect(QApplication.quit)
        self.tray_menu.addAction(self.exit_action)

        self.hide_action = QAction("Hide (Esc)", self)
        self.hide_action.triggered.connect(self.hide)
        self.tray_menu.addAction(self.hide_action)

        self.unhide_hide_action = QAction("Unhide", self)
        self.unhide_hide_action.triggered.connect(self.show)

    def set_coordinates(self, x, y):
        if self.gaze_x is not None and self.gaze_y is not None:
            # Dead zone: ignore tiny movements
            if abs(x - self.gaze_x) < self.dead_zone and abs(y - self.gaze_y) < self.dead_zone:
                return

        self.gaze_history.append((int(x), int(y)))
        if len(self.gaze_history) > self.gaze_history_size:
            self.gaze_history.pop(0)

        # Weighted smoothing: newer points have more weight
        total_weight = sum(range(1, len(self.gaze_history) + 1))
        xs = [pt[0] * (i + 1) for i, pt in enumerate(self.gaze_history)]
        ys = [pt[1] * (i + 1) for i, pt in enumerate(self.gaze_history)]
        smoothed_x = int(sum(xs) / total_weight)
        smoothed_y = int(sum(ys) / total_weight)

        # Velocity limit: move max_speed px per frame
        if self.gaze_x is not None and self.gaze_y is not None:
            dx = smoothed_x - self.gaze_x
            dy = smoothed_y - self.gaze_y
            dist = max(abs(dx), abs(dy))
            if dist > self.max_speed:
                scale = self.max_speed / dist
                smoothed_x = self.gaze_x + int(dx * scale)
                smoothed_y = self.gaze_y + int(dy * scale)

        self.gaze_x, self.gaze_y = smoothed_x, smoothed_y

    def _primary_monitor_bounds(self):
        mon = self.sct.monitors[1]
        return mon["left"], mon["top"], mon["width"], mon["height"]

    def _region_around_point(self, x, y):
        mon_left, mon_top, mon_w, mon_h = self._primary_monitor_bounds()
        src_w = int(self.window_width / self.scale_factor)
        src_h = int(self.window_height / self.scale_factor)

        left = x - src_w // 2
        top = y - src_h // 2

        left = max(mon_left, min(left, mon_left + mon_w - src_w))
        top = max(mon_top, min(top, mon_top + mon_h - src_h))

        return {"left": left, "top": top, "width": src_w, "height": src_h}

    def grab_region(self, x, y):
        region = self._region_around_point(x, y)
        shot = self.sct.grab(region)
        return np.array(shot)[:, :, :3]

    def update_magnifier(self):
        if self.gaze_x is not None and self.gaze_y is not None:
            mx, my = self.gaze_x, self.gaze_y
        else:
            mx, my = pyautogui.position()

        target_x = int(mx - self.window_width // 2)
        target_y = int(my - self.window_height // 2)
        if self.last_window_pos:
            if self.last_window_pos[0] is None or self.last_window_pos[1] is None:
                self.move(target_x, target_y)
                self.last_window_pos = (target_x, target_y)
            else:
                dx = abs(target_x - self.last_window_pos[0])
                dy = abs(target_y - self.last_window_pos[1])
                if dx > self.window_move_dead_zone or dy > self.window_move_dead_zone:
                    # Capture before moving window
                    self.setWindowOpacity(0)
                    src = self.grab_region(mx, my)
                    self.setWindowOpacity(0.9)
                    magnified = cv2.resize(src, (self.window_width, self.window_height), interpolation=cv2.INTER_LINEAR)

                    h, w, _ = magnified.shape
                    qImg = QImage(magnified.data, w, h, 3 * w, QImage.Format_BGR888)
                    self.label.setPixmap(QPixmap.fromImage(qImg))
                    self.move(target_x, target_y)
                    self.last_window_pos = (target_x, target_y)
        else:
            self.last_window_pos = (target_x, target_y)
