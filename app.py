import os
import sqlite3
from flask import Flask, g, jsonify, render_template, request

app = Flask(__name__)
DATABASE = os.path.join(app.root_path, "venues.db")


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(error):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    with sqlite3.connect(DATABASE) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS venues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                location TEXT NOT NULL,
                capacity INTEGER NOT NULL,
                rate_per_day INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                venue_id INTEGER NOT NULL,
                client_name TEXT NOT NULL,
                client_phone TEXT NOT NULL,
                event_date TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (venue_id) REFERENCES venues (id) ON DELETE CASCADE,
                UNIQUE (venue_id, event_date)
            );
            """
        )

        existing = conn.execute("SELECT COUNT(*) FROM venues").fetchone()[0]
        if existing == 0:
            conn.executemany(
                "INSERT INTO venues (name, location, capacity, rate_per_day) VALUES (?, ?, ?, ?)",
                [
                    ("Mekatilili Hall","Mvita", 120, 18000),
                    ("Ampitheatre","Mvita", 250, 32000),
                    ("Mazrui","Mvita", 35, 8500),
                    ("Jitume Hub","Mvita", 180, 24000),
                ],
            )
        conn.commit()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/venues", methods=["GET"])
def list_venues():
    rows = get_db().execute("SELECT * FROM venues ORDER BY name ASC").fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/api/bookings", methods=["GET"])
def list_bookings():
    rows = get_db().execute(
        """
        SELECT b.id, b.venue_id, v.name AS venue_name, v.location,
               b.client_name, b.client_phone, b.event_date
        FROM bookings b
        JOIN venues v ON v.id = b.venue_id
        ORDER BY b.event_date ASC, b.id DESC
        """
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/api/bookings", methods=["POST"])
def create_booking():
    data = request.get_json(silent=True) or {}
    venue_id = data.get("venue_id")
    client_name = (data.get("client_name") or "").strip()
    client_phone = (data.get("client_phone") or "").strip()
    event_date = (data.get("event_date") or "").strip()

    if not venue_id or not client_name or not client_phone or not event_date:
        return jsonify({"error": "All booking fields are required."}), 400

    db = get_db()
    venue = db.execute("SELECT id FROM venues WHERE id = ?", (venue_id,)).fetchone()
    if not venue:
        return jsonify({"error": "Selected venue does not exist."}), 404

    try:
        cur = db.execute(
            """
            INSERT INTO bookings (venue_id, client_name, client_phone, event_date)
            VALUES (?, ?, ?, ?)
            """,
            (venue_id, client_name, client_phone, event_date),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": "That venue is already booked on this date."}), 409

    booking = db.execute(
        """
        SELECT b.id, b.venue_id, v.name AS venue_name, v.location,
               b.client_name, b.client_phone, b.event_date
        FROM bookings b
        JOIN venues v ON v.id = b.venue_id
        WHERE b.id = ?
        """,
        (cur.lastrowid,),
    ).fetchone()

    return jsonify(dict(booking)), 201


@app.route("/api/bookings/<int:booking_id>", methods=["DELETE"])
def cancel_booking(booking_id):
    db = get_db()
    cur = db.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
    db.commit()
    if cur.rowcount == 0:
        return jsonify({"error": "Booking not found."}), 404
    return jsonify({"deleted": True, "id": booking_id})


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
