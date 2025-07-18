# from eyetrax import GazeEstimator, run_9_point_calibration
from PyQt5.QtWidgets import QApplication
import sys

from magnifier import Magnifier

if __name__ == '__main__':
    print('Start program...')

    app = QApplication(sys.argv)
    magnifier = Magnifier()
    magnifier.show()

    magnifier.exit_signal.connect(app.quit)

    sys.exit(app.exec_())


    # # Create estimator and calibrate
    # estimator = GazeEstimator()
    # run_9_point_calibration(estimator)
    #
    # # Save model
    # estimator.save_model("gaze_model.pkl")
    #
    # # Load model
    # estimator = GazeEstimator()
    # estimator.load_model("gaze_model.pkl")
    #
    # cap = cv2.VideoCapture(0)
    #
    # while True:
    #     # Extract features from frame
    #     ret, frame = cap.read()
    #     features, blink = estimator.extract_features(frame)
    #
    #     # Predict screen coordinates
    #     if features is not None and not blink:
    #         x, y = estimator.predict([features])[0]
    #         print(f"Gaze: ({x:.0f}, {y:.0f})")
    #     else:
    #         print("Blink")
