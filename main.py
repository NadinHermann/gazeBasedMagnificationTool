import sys
import time
import os

import cv2
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import QApplication
from eyetrax import GazeEstimator, run_9_point_calibration

from magnifier import Magnifier

import warnings

warnings.filterwarnings("ignore", category=UserWarning)

def resource_path(filename):
    """Return path to resource, works for dev and when bundled by PyInstaller."""
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(__file__)
    return os.path.join(base, filename)

if __name__ == '__main__':
    print('Start program...')
    app = QApplication(sys.argv)
    # keep the application running when the window is closed so the tray icon remains
    app.setQuitOnLastWindowClosed(False)

    # Create estimator and calibrate
    estimator = GazeEstimator()
    run_9_point_calibration(estimator)

    # Save model

    estimator.save_model(resource_path("gaze_model.pkl"))

    # Load model
    estimator = GazeEstimator()
    estimator.load_model(resource_path("gaze_model.pkl"))

    cap = cv2.VideoCapture(0)
    magnifier = Magnifier()
    magnifier.show()

    magnifier.exit_signal.connect(app.quit)

    blink_start = None
    scaled_for_blink = False
    eyes_open_since = None
    BLINK_THRESHOLD_SECONDS = 2
    GRACE_PERIOD = 0.75  # Eyes must stay open for 0.75s to reset the timer


    def update_gaze():
        global blink_start, scaled_for_blink, eyes_open_since

        ret, frame = cap.read()
        if not ret:
            return

        features, blink = estimator.extract_features(frame)
        now = time.monotonic()

        # 1. Eyes are OPEN and detected
        if features is not None and not blink:
            x, y = estimator.predict([features])[0]
            magnifier.set_coordinates(x, y)

            # If this is the first frame eyes are open, mark the starting time
            if eyes_open_since is None:
                eyes_open_since = now

            # Check if eyes have been open *long enough* to count as a real opening (grace period)
            # print(f"Eyes open. Time since first open: {now - eyes_open_since:.2f} seconds.")
            if blink_start is not None and (now - eyes_open_since >= GRACE_PERIOD):
                # print("Eyes open continuously for grace period, resetting blink timer.")
                blink_start = None
                scaled_for_blink = False

        # 2. Eyes are CLOSED or tracking flickered / lost
        else:
            eyes_open_since = None

            # Start or continue the blink timer
            if blink_start is None:
                blink_start = now
                # print("Blink timer started at:", blink_start)
            else:
                elapsed = now - blink_start
                # print(f"Blink timer running. Elapsed time: {elapsed:.2f} seconds.")
                if elapsed >= BLINK_THRESHOLD_SECONDS and not scaled_for_blink:
                    print("Long blink detected, processing magnification change.")
                    mods = QApplication.queryKeyboardModifiers()
                    shift_down = bool(mods & Qt.ShiftModifier)
                    print(shift_down)
                    if shift_down:
                        print("Long blink detected with Shift, halving magnification.")
                        magnifier.decrease_magnification()
                    else:
                        print("Long blink detected, doubling magnification.")
                        magnifier.double_magnification()

                    scaled_for_blink = True

    # Timer für Gaze-Update
    gaze_timer = QTimer()
    gaze_timer.timeout.connect(update_gaze)
    gaze_timer.start(30)  # 30 ms

    sys.exit(app.exec_())
