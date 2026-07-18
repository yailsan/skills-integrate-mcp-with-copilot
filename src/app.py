"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from pathlib import Path
import sqlite3
import json

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent, "static")), name="static")

# SQLite DB file
DB_PATH = current_dir / "data.db"


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables and seed activities if DB is empty."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS activities (
            name TEXT PRIMARY KEY,
            description TEXT NOT NULL,
            schedule TEXT NOT NULL,
            max_participants INTEGER NOT NULL,
            participants_json TEXT NOT NULL
        )
        """
    )

    # Check if any activities exist
    cur.execute("SELECT COUNT(1) as cnt FROM activities")
    row = cur.fetchone()
    if row[0] == 0:
        seed_activities = {
            "Chess Club": {
                "description": "Learn strategies and compete in chess tournaments",
                "schedule": "Fridays, 3:30 PM - 5:00 PM",
                "max_participants": 12,
                "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
            },
            "Programming Class": {
                "description": "Learn programming fundamentals and build software projects",
                "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
                "max_participants": 20,
                "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
            },
            "Gym Class": {
                "description": "Physical education and sports activities",
                "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
                "max_participants": 30,
                "participants": ["john@mergington.edu", "olivia@mergington.edu"]
            },
            "Soccer Team": {
                "description": "Join the school soccer team and compete in matches",
                "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
                "max_participants": 22,
                "participants": ["liam@mergington.edu", "noah@mergington.edu"]
            },
            "Basketball Team": {
                "description": "Practice and play basketball with the school team",
                "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
                "max_participants": 15,
                "participants": ["ava@mergington.edu", "mia@mergington.edu"]
            },
            "Art Club": {
                "description": "Explore your creativity through painting and drawing",
                "schedule": "Thursdays, 3:30 PM - 5:00 PM",
                "max_participants": 15,
                "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
            },
            "Drama Club": {
                "description": "Act, direct, and produce plays and performances",
                "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
                "max_participants": 20,
                "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
            },
            "Math Club": {
                "description": "Solve challenging problems and participate in math competitions",
                "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
                "max_participants": 10,
                "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
            },
            "Debate Team": {
                "description": "Develop public speaking and argumentation skills",
                "schedule": "Fridays, 4:00 PM - 5:30 PM",
                "max_participants": 12,
                "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
            }
        }

        for name, details in seed_activities.items():
            cur.execute(
                "INSERT INTO activities (name, description, schedule, max_participants, participants_json) VALUES (?, ?, ?, ?, ?)",
                (name, details["description"], details["schedule"], details["max_participants"], json.dumps(details["participants"]))
            )
        conn.commit()

    conn.close()


def fetch_all_activities_from_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM activities")
    rows = cur.fetchall()
    result = {}
    for r in rows:
        participants = json.loads(r["participants_json"]) if r["participants_json"] else []
        result[r["name"]] = {
            "description": r["description"],
            "schedule": r["schedule"],
            "max_participants": r["max_participants"],
            "participants": participants,
        }
    conn.close()
    return result


@app.on_event("startup")
def startup():
    # Ensure DB exists and is seeded
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    init_db()


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return fetch_all_activities_from_db()


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity (stored in SQLite)."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM activities WHERE name = ?", (activity_name,))
    row = cur.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Activity not found")

    participants = json.loads(row["participants_json"]) if row["participants_json"] else []

    if email in participants:
        conn.close()
        raise HTTPException(status_code=400, detail="Student is already signed up")

    if len(participants) >= row["max_participants"]:
        conn.close()
        raise HTTPException(status_code=400, detail="Activity is full")

    participants.append(email)
    cur.execute("UPDATE activities SET participants_json = ? WHERE name = ?", (json.dumps(participants), activity_name))
    conn.commit()
    conn.close()
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str):
    """Unregister a student from an activity (stored in SQLite)."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM activities WHERE name = ?", (activity_name,))
    row = cur.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Activity not found")

    participants = json.loads(row["participants_json"]) if row["participants_json"] else []

    if email not in participants:
        conn.close()
        raise HTTPException(status_code=400, detail="Student is not signed up for this activity")

    participants.remove(email)
    cur.execute("UPDATE activities SET participants_json = ? WHERE name = ?", (json.dumps(participants), activity_name))
    conn.commit()
    conn.close()
    return {"message": f"Unregistered {email} from {activity_name}"}
