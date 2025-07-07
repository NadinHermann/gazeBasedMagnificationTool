# This is a sample Python script.

# Press Umschalt+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
from eyetrax import GazeEstimator, run_9_point_calibration
import cv2


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Strg+F8 to toggle the breakpoint.


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print_hi('PyCharm')

    # Create estimator and calibrate
    estimator = GazeEstimator()
    run_9_point_calibration(estimator)

    # Save model
    estimator.save_model("gaze_model.pkl")

    # Load model
    estimator = GazeEstimator()
    estimator.load_model("gaze_model.pkl")

    cap = cv2.VideoCapture(0)

    while True:
        # Extract features from frame
        ret, frame = cap.read()
        features, blink = estimator.extract_features(frame)

        # Predict screen coordinates
        if features is not None and not blink:
            x, y = estimator.predict([features])[0]
            print(f"Gaze: ({x:.0f}, {y:.0f})")
        else:
            print("Blink")

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
