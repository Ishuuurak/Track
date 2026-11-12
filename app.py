"""Waffle Track - stage 1: simulated POS + order database + JSON API.
Run:  pip install flask   then   python app.py   then open http://localhost:5000
"""
import sqlite3, datetime
from flask import Flask, request, jsonify, render_template_string

DB = "waffle.db"
app = Flask(__name__)

def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def init():
    with db() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS orders(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item TEXT, qty INTEGER, status TEXT DEFAULT 'posted',
            created_at TEXT, completed_at TEXT)""")
        con.execute("""CREATE TABLE IF NOT EXISTS camera_events(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event TEXT, station TEXT, ts TEXT)""")

now = lambda: datetime.datetime.now().isoformat(timespec="seconds")

POS_PAGE = """<!doctype html><title>Waffle POS</title>
<h1>Waffle POS (simulated)</h1>
{% for w in menu %}<button onclick="order('{{w}}')" style="font-size:22px;margin:6px">{{w}}</button>{% endfor %}
<h2>Open orders</h2><ul id=list></ul>
<script>
async function order(item){await fetch('/api/orders',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({item,qty:1})});load()}
async function done(id){await fetch('/api/orders/'+id+'/complete',{method:'POST'});load()}
async function load(){let r=await (await fetch('/api/orders?status=posted')).json();
 document.getElementById('list').innerHTML=r.map(o=>`<li>#${o.id} ${o.item} <button onclick="done(${o.id})">Done</button></li>`).join('')}
load();setInterval(load,3000)
</script>"""

MENU = ["Classic", "Nutella", "Strawberry", "Bubble"]

@app.get("/")
def pos():
    return render_template_string(POS_PAGE, menu=MENU)

@app.post("/api/orders")
def new_order():
    d = request.get_json()
    with db() as con:
        cur = con.execute("INSERT INTO orders(item,qty,created_at) VALUES(?,?,?)",
                          (d["item"], int(d.get("qty", 1)), now()))
    return jsonify(id=cur.lastrowid), 201

@app.get("/api/orders")
def list_orders():
    status = request.args.get("status")
    q, args = "SELECT * FROM orders", ()
    if status:
        q, args = q + " WHERE status=?", (status,)
    with db() as con:
        return jsonify([dict(r) for r in con.execute(q + " ORDER BY id DESC", args)])

@app.post("/api/orders/<int:oid>/complete")
def complete(oid):
    with db() as con:
        con.execute("UPDATE orders SET status='completed', completed_at=? WHERE id=?", (now(), oid))
    return jsonify(ok=True)

@app.post("/api/camera")
def camera_event():
    """The camera script posts here, e.g. {"event":"waffle_out","station":"iron1"}"""
    d = request.get_json()
    with db() as con:
        con.execute("INSERT INTO camera_events(event,station,ts) VALUES(?,?,?)",
                    (d["event"], d.get("station", "main"), now()))
    return jsonify(ok=True)

@app.get("/api/summary")
def summary():
    """Today's numbers: orders posted vs waffles the camera saw. A gap = possible leak."""
    today = datetime.date.today().isoformat()
    with db() as con:
        posted = con.execute("SELECT COALESCE(SUM(qty),0) FROM orders WHERE created_at>=?", (today,)).fetchone()[0]
        done = con.execute("SELECT COALESCE(SUM(qty),0) FROM orders WHERE status='completed' AND created_at>=?", (today,)).fetchone()[0]
        seen = con.execute("SELECT COUNT(*) FROM camera_events WHERE event='waffle_out' AND ts>=?", (today,)).fetchone()[0]
    return jsonify(orders_posted=posted, orders_completed=done,
                   waffles_seen_by_camera=seen, mismatch=seen - done)

if __name__ == "__main__":
    init()
    app.run(host="0.0.0.0", port=5000)
