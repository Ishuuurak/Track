# Track

Waffle shop monitoring prototype: simulated POS + camera-based waffle counting, so orders posted can be compared with waffles actually made.

## Stage 1 (this commit)
Simulated POS, order database and JSON API.

    pip install -r requirements.txt
    python app.py

Then open http://localhost:5000

## Next
Stage 2: camera script (Osmo Pocket 2 as USB webcam) counting waffles and posting events to /api/camera.
Stage 3: live dashboard and mismatch alerts.
