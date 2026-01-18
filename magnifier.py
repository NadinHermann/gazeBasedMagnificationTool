import sys
import os
import cv2
import mss
import numpy as np
import pyautogui
import time
from PyQt5.QtCore import pyqtSignal, Qt, QTimer
from PyQt5.QtGui import QIcon, QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QMenu, QAction, QSystemTrayIcon

def resource_path(relative_path: str) -> str:
    """Return absolute path to resource, works for dev and PyInstaller onefile.
    Use like: resource_path('img/icon.png')
    """
    if getattr(sys, 'frozen', False):
        base = getattr(sys, '_MEIPASS', os.path.abspath('.'))
    else:
        base = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base, relative_path)

class Magnifier(QWidget):
    exit_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.last_window_pos = None
        self.window_width = 800
        self.window_height = 600
        self.scale_factor = 2.0
        self.max_scale = 12.0
        self.min_scale = 2.0

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

        # Dwell feature state
        self.dwell_enabled = False
        self.dwell_center = None  # (x, y) - dynamically tracks current gaze position
        self.dwell_radius = 100  # pixels - smaller radius for detecting stillness
        self.dwell_hold_time = 0.5  # seconds required to dwell
        self.dwell_start_time = None
        self.dwell_active = False

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_magnifier)
        self.timer.start(30)

    def create_tray_icon(self):
        self.create_context_menu()
        self.tray_icon = QSystemTrayIcon(self)
        print("get icon path:", resource_path("img/icon.png"))
        self.tray_icon.setIcon(QIcon(resource_path("img/icon.png")))
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.show()

    def toggle_visibility(self):
        if self.isVisible():
            self.hide()
            self.hide_action.setText("Unhide")
        else:
            self.show()
            self.hide_action.setText("Hide")

    def create_context_menu(self):
        self.tray_menu = QMenu(self)

        self.exit_action = QAction("Exit", self)
        self.exit_action.triggered.connect(QApplication.quit)
        self.tray_menu.addAction(self.exit_action)

        self.hide_action = QAction("Hide", self)
        self.hide_action.triggered.connect(self.toggle_visibility)
        self.tray_menu.addAction(self.hide_action)

        self.increase_magnification_action = QAction("Double Magnification", self)
        self.increase_magnification_action.triggered.connect(self.double_magnification)
        self.tray_menu.addAction(self.increase_magnification_action)
        # tooltip helps users find the tray icon
        try:
            self.tray_icon.setToolTip('Magnifier')
        except Exception:
            pass

        self.decrease_magnification_action = QAction("Decrease Magnification", self)
        self.decrease_magnification_action.triggered.connect(self.decrease_magnification)
        self.tray_menu.addAction(self.decrease_magnification_action)

        # Dwell option: when enabled, the window stays hidden until the user dwells
        # (stays still) on any point. The action is checkable.
        self.dwell_action = QAction("Enable Dwell", self)
        self.dwell_action.setCheckable(True)
        self.dwell_action.triggered.connect(self.toggle_dwell)
        self.tray_menu.addAction(self.dwell_action)
        # Diagnostic / robustness: ensure system tray is available and briefly show a message
        if not QSystemTrayIcon.isSystemTrayAvailable():
            print('Warning: system tray not available on this system')
        else:
            try:
                # show a brief message to provoke the tray icon to appear on some Windows setups
                self.tray_icon.showMessage('Magnifier', 'Application started', QSystemTrayIcon.Information, 1000)
            except Exception:
                pass


    def toggle_dwell(self, checked: bool):
        """Enable or disable dwell mode. When enabled, the magnifier only shows when
        the user dwells (stays still) on any point for the configured time."""
        if checked:
            self.dwell_enabled = True
            self.dwell_center = None  # Will be set dynamically in update_magnifier
            self.dwell_start_time = None
            self.dwell_active = False
            try:
                self.hide()
                self.hide_action.setText("Unhide")
            except Exception:
                pass
            self.dwell_action.setText("Disable Dwell")
        else:
            # turning dwell off: show window again and reset dwell state
            self.dwell_enabled = False
            self.dwell_center = None
            self.dwell_start_time = None
            self.dwell_active = False
            self.show()
            self.dwell_action.setText("Enable Dwell")
            self.hide_action.setText("Hide")

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

        # Dwell logic: when enabled, the magnifier should remain hidden until the user
        # dwells (stays still) at any point for the configured time.
        if self.dwell_enabled:
            # If no dwell center is set yet, initialize it to current position
            if self.dwell_center is None:
                # Start tracking at current gaze position
                self.dwell_center = (mx, my)
                self.dwell_start_time = time.time()
                print(f"Initial dwell center set to: {self.dwell_center}")
            else:
                dx = mx - self.dwell_center[0]
                dy = my - self.dwell_center[1]
                dist = (dx * dx + dy * dy) ** 0.5

                if dist <= self.dwell_radius:
                    # gaze is staying still within the radius
                  if (time.time() - self.dwell_start_time) >= self.dwell_hold_time:
                    # dwell satisfied -> show the window if not already visible
                    if not self.dwell_active:
                        self.dwell_active = True
                        # Update magnifier contents and position before showing
                        target_x = int(mx - self.window_width // 2)
                        target_y = int(my - self.window_height // 2)
                        try:
                            src = self.grab_region(mx, my)
                            magnified = cv2.resize(src, (self.window_width, self.window_height), interpolation=cv2.INTER_LINEAR)
                            h, w, _ = magnified.shape
                            qImg = QImage(magnified.data, w, h, 3 * w, QImage.Format_BGR888)
                            self.label.setPixmap(QPixmap.fromImage(qImg))
                            self.move(target_x, target_y)
                            self.last_window_pos = (target_x, target_y)
                        except Exception as e:
                            print(f"Error updating magnifier: {e}")
                        # Now show the window
                        self.show()
                        self.raise_()
                        self.activateWindow()
                else:
                    # gaze moved too far: reset dwell center to new position
                    self.dwell_center = (mx, my)
                    self.dwell_start_time = time.time()
                    if self.dwell_active:
                        self.hide()
                        self.dwell_active = False

            # If dwell is enabled but not yet active, do not update magnifier contents
            if not self.dwell_active:
                return

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

    def double_magnification(self):
        self.scale_factor = min(self.max_scale, self.scale_factor * 2.0)

    def decrease_magnification(self):
        self.scale_factor = max(self.min_scale, self.scale_factor / 2.0)

