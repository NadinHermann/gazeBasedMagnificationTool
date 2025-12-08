import sys
import time

import cv2
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication
from eyetrax import GazeEstimator, run_9_point_calibration

from magnifier import Magnifier

if __name__ == '__main__':
    print('Start program...')
    app = QApplication(sys.argv)

    # Create estimator and calibrate
    estimator = GazeEstimator()
    run_9_point_calibration(estimator)

    # Save model
    estimator.save_model("gaze_model.pkl")

    # Load model
    estimator = GazeEstimator()
    estimator.load_model("gaze_model.pkl")

    cap = cv2.VideoCapture(0)
    magnifier = Magnifier()
    magnifier.show()

    magnifier.exit_signal.connect(app.quit)

    # Blink tracking configuration
    blink_start = None
    scaled_for_blink = False
    BLINK_THRESHOLD_SECONDS = 1

    def update_gaze():
        print("Updating gaze...")
        global blink_start, scaled_for_blink
        ret, frame = cap.read()
        if not ret:
            return
        features, blink = estimator.extract_features(frame)

        # Gaze detected and not blinking
        if features is not None and not blink:
            x, y = estimator.predict([features])[0]
            magnifier.set_coordinates(x, y)
            print(f"Gaze: ({x:.0f}, {y:.0f})")
            blink_start = None
            scaled_for_blink = False
        else:
            now = time.time()
            print(now)
            if blink_start is None:
                blink_start = now
            else:
                print("Blink ongoing...", now - blink_start)
                if now - blink_start > BLINK_THRESHOLD_SECONDS and scaled_for_blink is False:
                    print("Long blink detected, doubling magnification.")
                    magnifier.double_scale()
                    scaled_for_blink = True


    # Timer für Gaze-Update
    gaze_timer = QTimer()
    gaze_timer.timeout.connect(update_gaze)
    gaze_timer.start(30)  # 30 ms

    sys.exit(app.exec_())
