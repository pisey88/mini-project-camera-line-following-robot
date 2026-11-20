from flask import Flask, Response
import cv2
import numpy as np
import serial
import time

app = Flask(__name__)

PORT = "/dev/ttyUSB0"
BAUD = 115200
ser = None

try:
    ser = serial.Serial(PORT, BAUD, timeout=1)
    time.sleep(2)
    print(f"[+] Serial connection established on {PORT}")
except Exception as e:
    print(f"[-] Serial connection failed: {e}")
    ser = None

last_sent_decision = ""

TURN_SPEED = 50
SEARCH_SPEED = 50
SEARCH_FORWARD_SPEED = 50
SEARCH_STEP_TIME = 0.4
SEARCH_WIDEN_BY = 0.4
SEARCH_MAX_STEP_TIME = 1.0
SEARCH_FORWARD_TIME = 0.5
SEARCH_DELAY = 0.3

search_cycle = 0
search_phase = 0
search_start_time = None
lost_since = None


def reset_search():
    global search_cycle, search_phase, search_start_time, lost_since
    search_cycle = 0
    search_phase = 0
    search_start_time = None
    lost_since = None


def get_search_decision():
    """Sweep right, left, back to center, move forward a bit, then search again
    (a little wider each cycle) until the black line is found
    (reset_search() is called when it is)."""
    global search_cycle, search_phase, search_start_time, lost_since

    now = time.time()

    if lost_since is None:
        lost_since = now
    if now - lost_since < SEARCH_DELAY:
        return "NO LINE"

    if search_start_time is None:
        search_start_time = now

    T = min(SEARCH_STEP_TIME + search_cycle * SEARCH_WIDEN_BY,
            SEARCH_MAX_STEP_TIME)

    durations = [T, 2 * T, T, SEARCH_FORWARD_TIME]

    if now - search_start_time >= durations[search_phase]:
        search_phase += 1
        search_start_time = now
        if search_phase > 3:
            search_phase = 0
            search_cycle += 1

    return ["SEARCH RIGHT", "SEARCH LEFT", "SEARCH RIGHT", "SEARCH FORWARD"][search_phase]


def send_command(decision):
    global last_sent_decision

    if decision == "FORWARD":
        cmd = b"FORWARD,50\n"
    elif decision == "LEFT":
        cmd = f"LEFT,{TURN_SPEED}\n".encode()
    elif decision == "RIGHT":
        cmd = f"RIGHT,{TURN_SPEED}\n".encode()
    elif decision == "SEARCH RIGHT":
        cmd = f"RIGHT,{SEARCH_SPEED}\n".encode()
    elif decision == "SEARCH LEFT":
        cmd = f"LEFT,{SEARCH_SPEED}\n".encode()
    elif decision == "SEARCH FORWARD":
        cmd = f"FORWARD,{SEARCH_FORWARD_SPEED}\n".encode()
    else:
        cmd = b"STOP,0\n"

    if decision != last_sent_decision:
        if ser and ser.is_open:
            ser.write(cmd)
            ser.flush()
            print(f"[SERIAL] Sent: {cmd.decode().strip()}")
        last_sent_decision = decision

cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

def get_mask(roi):
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    lower = (0, 0, 0)
    upper = (180, 255, 80) 

    mask = cv2.inRange(hsv, lower, upper)
    return mask

def generate_frames():
    while True:
        ret, frame = cap.read()
        if not ret:
            for _ in range(20):
                time.sleep(0.1)
                ret, frame = cap.read()
                if ret:
                    break
        if not ret:
            print("[-] Failed to capture frame from camera")
            send_command("NO LINE")
            break

        h, w = frame.shape[:2]
        top = int(0.6 * h)
        roi = frame[top:h, :]

        mask = get_mask(roi)
        M = cv2.moments(mask)

        decision = "NO LINE"

        if M["m00"] > 0:
            cx = int(M["m10"] / M["m00"])
            cv2.circle(roi, (cx, 50), 8, (0, 0, 255), -1)
            reset_search()

            if cx < w // 3:
                decision = "LEFT"
            elif cx > (2 * w) // 3:
                decision = "RIGHT"
            else:
                decision = "FORWARD"
        else:

            decision = get_search_decision()
        send_command(decision)

        cv2.rectangle(frame, (0, top), (w, h), (0, 255, 0), 2)
        cv2.line(frame, (w // 3, top), (w // 3, h), (0, 0, 255), 2)
        cv2.line(frame, (2 * w // 3, top), (2 * w // 3, h), (255, 0, 0), 2)
        cv2.putText(frame, decision, (10, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/')
def video():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    print("[+] Starting Line Follower Web Server on Raspberry Pi...")
    print("[+] Open your browser and go to: http://<YOUR_PI_IP>:5000")
    try:
        app.run(host='0.0.0.0', port=5000, threaded=True)
    finally:
        if ser and ser.is_open:
            ser.write(b"STOP,0\n")
            ser.close()
        cap.release()