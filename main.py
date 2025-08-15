import cv2
from eyetrax import GazeEstimator, run_9_point_calibration
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
import sys

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

    def update_gaze():
        print("Updating gaze...")
        ret, frame = cap.read()
        if not ret:
            return
        features, blink = estimator.extract_features(frame)

        if features is not None and not blink:
            x, y = estimator.predict([features])[0]
            magnifier.set_coordinates(x, y)
            print(f"Gaze: ({x:.0f}, {y:.0f})")
        else:
            print("Blink")

    # Timer für Gaze-Update
    gaze_timer = QTimer()
    gaze_timer.timeout.connect(update_gaze)
    gaze_timer.start(30)  # 30 ms

    sys.exit(app.exec_())
