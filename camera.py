"""Waffle Track - stage 2: camera counter.

Reads the Osmo Pocket 3 (set to Webcam mode over USB-C), watches a marked region of the
frame where finished waffles are placed (the "pass" area), and posts a
"waffle_out" event to the Flask app each time a new waffle appears there.

Run:   python camera.py                 (live camera)
       python camera.py --camera 1      (try another camera index if 0 is your laptop webcam)
       python camera.py --calibrate     (draw the pass area, then it is saved to zone.json)

Keys while running:  q = quit,  r = re-draw the pass area
"""
import argparse, json, os, time
import cv2
import requests

SERVER = "http://localhost:5000/api/camera"
ZONE_FILE = "zone.json"
MIN_AREA = 6000          # smallest blob (pixels) that counts as a waffle; tune for your setup
SETTLE_FRAMES = 15       # blob must be stable this many frames before it counts
COOLDOWN_SEC = 2.0       # ignore new counts for this long after one

def pick_zone(frame):
    r = cv2.selectROI("Draw the pass area, press ENTER", frame, showCrosshair=False)
    cv2.destroyWindow("Draw the pass area, press ENTER")
    zone = [int(v) for v in r]
    json.dump(zone, open(ZONE_FILE, "w"))
    return zone

def post_event(event, station):
    try:
        requests.post(SERVER, json={"event": event, "station": station}, timeout=3)
    except requests.RequestException as e:
        print("could not reach server:", e)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--camera", type=int, default=0)
    ap.add_argument("--station", default="main")
    ap.add_argument("--calibrate", action="store_true")
    args = ap.parse_args()

    cap = cv2.VideoCapture(args.camera, cv2.CAP_DSHOW)   # CAP_DSHOW works best on Windows
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    ok, frame = cap.read()
    if not ok:
        raise SystemExit("No camera frame. Is the Pocket 3 in Webcam mode and plugged in?")

    if args.calibrate or not os.path.exists(ZONE_FILE):
        zone = pick_zone(frame)
    else:
        zone = json.load(open(ZONE_FILE))

    bg = cv2.createBackgroundSubtractorMOG2(history=300, varThreshold=40, detectShadows=False)
    count, stable, occupied, last_count_time = 0, 0, False, 0.0

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        x, y, w, h = zone
        roi = frame[y:y + h, x:x + w]
        mask = bg.apply(roi)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
        area = cv2.countNonZero(mask)
        present = area > MIN_AREA

        stable = stable + 1 if present else 0
        if stable >= SETTLE_FRAMES and not occupied and time.time() - last_count_time > COOLDOWN_SEC:
            occupied = True
            count += 1
            last_count_time = time.time()
            post_event("waffle_out", args.station)
            print(f"waffle #{count} counted")
        if not present:
            occupied = False

        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0) if present else (0, 0, 255), 2)
        cv2.putText(frame, f"waffles counted: {count}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.imshow("Waffle Track camera", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        if key == ord("r"):
            zone = pick_zone(frame)

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
