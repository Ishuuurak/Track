# Track

Waffle shop monitoring prototype: simulated POS + camera-based waffle counting, so orders posted can be compared with waffles actually made.

## Stage 1: POS and database
    pip install -r requirements.txt
    python app.py
Then open http://localhost:5000

## Stage 2: camera counter (Osmo Pocket 3)
Plug the Pocket 3 in over USB-C and set it to Webcam mode. With app.py running, in a second terminal:

    python camera.py --calibrate

Drag a box over the spot where finished waffles are placed, press ENTER. Each new waffle in that box is counted and posted to the server. Check totals at http://localhost:5000/api/summary

Keys: q quits, r redraws the box. If the wrong camera opens, try --camera 1 or 2.

## Next
Stage 3: live dashboard and mismatch alerts.
