"""Waffle Track - stage 2b: marker-based waffle counter (Osmo Pocket 3).

Every waffle box carries the SAME printed marker (print marker_sheet.png as stickers).
The camera counts one waffle each time a marker newly appears in view, and posts
"waffle_out" to the order app. Hands, plates and cups are ignored.

Run:   python camera_marker.py --camera 2
Keys:  q = quit
Options: --backend MSMF|DSHOW|ANY   --station main   --gone-sec 1.5
"""
import argparse, time
import cv2
import requests

SERVER = "http://localhost:5000/api/camera"
MARKER_ID = 7            # the id printed on every sticker
SEEN_FRAMES = 6          # marker must be seen this many frames in a row to count
COOLDOWN_SEC = 1.0       # minimum gap between two counts

def open_camera(index, forced_backend):
    for name, backend in (("MSMF", cv2.CAP_MSMF), ("DSHOW", cv2.CAP_DSHOW), ("ANY", cv2.CAP_ANY)):
        if forced_backend and forced_backend.upper() != name:
            continue
        cap = cv2.VideoCapture(index, backend)
        if not cap.isOpened():
            cap.release()
            continue
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        for _ in range(40):
            ok, f = cap.read()
            if ok and f is not None and f.mean() > 5:
                print(f"Using camera {index} with backend {name}")
                return cap
            time.sleep(0.05)
        cap.release()
    raise SystemExit("No picture from this camera. Try another --camera number.")

def post_event(station):
    try:
        requests.post(SERVER, json={"event": "waffle_out", "station": station}, timeout=3)
    except requests.RequestException as e:
        print("could not reach server:", e)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--camera", type=int, default=2)
    ap.add_argument("--backend", default="")
    ap.add_argument("--station", default="main")
    ap.add_argument("--gone-sec", type=float, default=1.5,
                    help="marker must be out of view this long before the next one counts")
    args = ap.parse_args()

    cap = open_camera(args.camera, args.backend)
    aruco = cv2.aruco
    detector = aruco.ArucoDetector(aruco.getPredefinedDictionary(aruco.DICT_4X4_50),
                                   aruco.DetectorParameters())
    count, streak, armed, last_seen, last_count = 0, 0, True, 0.0, 0.0

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        corners, ids, _ = detector.detectMarkers(frame)
        visible = ids is not None and MARKER_ID in ids.flatten().tolist()
        now = time.time()

        if visible:
            last_seen = now
            streak += 1
            aruco.drawDetectedMarkers(frame, corners, ids)
            if armed and streak >= SEEN_FRAMES and now - last_count > COOLDOWN_SEC:
                count += 1
                armed = False
                last_count = now
                post_event(args.station)
                print(f"waffle #{count} counted")
        else:
            streak = 0
            if now - last_seen > args.gone_sec:
                armed = True

        cv2.putText(frame, f"waffles counted: {count}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(frame, "marker seen" if visible else "no marker", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                    (0, 255, 0) if visible else (0, 0, 255), 2)
        cv2.imshow("Waffle Track marker counter", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
