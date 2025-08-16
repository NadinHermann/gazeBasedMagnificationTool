# Gaze-Based Magnification Tool

A Python application that provides a real-time, gaze-driven screen magnifier. The tool uses a webcam-based gaze estimator to magnify the area of the screen where you are looking.

## Features

- **Real-time gaze tracking:** Uses webcam input and a machine learning model to estimate your gaze location.
- **Smooth magnifier movement:** Smoothing, dead-zone, and velocity limiting are implemented for stable and comfortable magnifier tracking.
- **Transparent, always-on-top overlay:** The magnifier window is frameless and semi-transparent, always visible above other windows.
- **System tray integration:** Includes a tray icon for easy hiding, unhiding, and quitting of the magnifier.
- **Blink handling:** Ignores gaze input during detected blinks.

## Installation

1. **Clone this repository:**
   ```sh
   git clone https://github.com/NadinHermann/gazeBasedMagnificationTool.git
   cd gazeBasedMagnificationTool
2. **Install dependencies**
   ```sh
   pip install -r requiremnts.txt
   
## Usage
* 
   ```sh
     python main.py
* The application opens a transparent magnifier window that follows your gaze.
* Use the system tray icon to hide, show, or exit the magnifier.

## Project Structure
```.
├── main.py            # Application entry point
├── magnifier.py       # Magnifier overlay logic
├── eyetrax.py         # Gaze estimation logic (not shown here)
├── gaze_model.pkl     # Trained gaze estimation model
├── img/
│   └── icon.png       # System tray icon
├── requirements.txt   # Python dependencies
```
## Notes
* Webcam required: The tool needs access to your webcam for gaze estimation.
* Primary monitor: Magnification is implemented for the primary monitor.