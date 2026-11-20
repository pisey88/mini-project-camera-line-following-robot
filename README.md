# Mini Project: Camera-Based Line Following Robot

## Group Members
- LY Sokpisey
- LINH Kimsourmana

## Project Overview
This project implements an autonomous camera-based line-following robot using a Raspberry Pi, OpenCV, Flask, and a serial-connected motion controller. The camera captures the track in real time, isolates the black line in the lower Region of Interest (ROI) using HSV thresholding (`lower = (0, 0, 0)`, `upper = (180, 255, 80)`), computes the horizontal centroid (`cx`) via `cv2.moments`, and sends movement commands (`FORWARD,50\n`, `LEFT,50\n`, `RIGHT,50\n`, or `STOP,0\n`) over serial only when the decision changes. If the line is lost, the robot waits briefly (`SEARCH_DELAY`) and runs a widening search pattern (`SEARCH RIGHT`, `SEARCH LEFT`, `SEARCH RIGHT`, `SEARCH FORWARD`) until the line is found again.

## Demonstration Video
Watch the unedited start-to-finish robot demonstration videos here:
- [Demonstration Video 1 (MP4)](https://drive.google.com/file/d/1ia8iZjY-YdGFJ6g-EKz8HE9tTLAyi_kr/view?usp=sharing)
- [Demonstration Video 2 (MP4)](https://drive.google.com/file/d/1uckXffUNP1Z74-iUeYXsBv7_Gyxaih9X/view?usp=sharing)

## Hardware Used
- **Compute Board:** Raspberry Pi (headless setup accessed over SSH / local network)
- **Camera:** USB / V4L2 camera (`cv2.VideoCapture(0, cv2.CAP_V4L2)`, `640x480`, `CAP_PROP_BUFFERSIZE = 1`)
- **Motor / Motion Controller:** Serial-controlled robot controller connected on `/dev/ttyUSB0` (`115200` baud)
- **Motors & Driver:** Robot motors and motor driver (`ENA`, `ENB`, and `IN1`–`IN4` control pins; add exact driver/motor models if needed)
- **Chassis & Battery Pack:** Mobile robot chassis powered by a 12V 2500mAh Lithium-Ion battery pack (Model `YSN-1202500`, 12.6V charging limit, center-positive DC barrel connector; use appropriate voltage regulation for 5V/logic electronics)

## How to Run the Program
1. Ensure the Raspberry Pi, camera, serial controller (`/dev/ttyUSB0`), and viewing device are connected and on the same network (if viewing the web feed).
2. Install the required Python libraries:
   ```bash
   pip install flask opencv-python numpy pyserial
   ```
## Run the script on the Raspberry Pi (ensure app = Flask(__name__) and if __name__ == "__main__": are set in your file):

```Bash
python3 line_follower.py
```

Place the robot at the start of the track and let it run autonomously. Press Ctrl+C in the terminal to stop cleanly (STOP,0\n) and release the camera and serial port.
