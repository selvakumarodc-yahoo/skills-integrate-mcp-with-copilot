"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr
import hashlib
import hmac
import os
import secrets
from pathlib import Path
from typing import Optional

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

SESSION_COOKIE_NAME = "session_token"

# In-memory activity database
activities = {
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

# In-memory student and session stores
students = {
    "michael@mergington.edu": {
        "name": "Michael",
        "grade": "11",
        "password_hash": "",
        "salt": ""
    }
}

sessions = {}

# Create a sample account with a secure password hash
def create_initial_sample_student():
    if students["michael@mergington.edu"]["password_hash"]:
        return
    salt = os.urandom(16)
    pwd_hash = hashlib.pbkdf2_hmac(
        "sha256",
        "password123".encode("utf-8"),
        salt,
        100000
    )
    students["michael@mergington.edu"]["salt"] = salt.hex()
    students["michael@mergington.edu"]["password_hash"] = pwd_hash.hex()

create_initial_sample_student()


class StudentRegistration(BaseModel):
    email: EmailStr
    password: str
    name: str
    grade: str


class StudentLogin(BaseModel):
    email: EmailStr
    password: str


class StudentProfile(BaseModel):
    email: EmailStr
    name: str
    grade: str


class ActivityAction(BaseModel):
    email: Optional[EmailStr] = None


def hash_password(password: str, salt: Optional[bytes] = None):
    salt = salt or os.urandom(16)
    pwd_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        100000
    )
    return salt.hex(), pwd_hash.hex()


def verify_password(password: str, salt_hex: str, hash_hex: str):
    salt = bytes.fromhex(salt_hex)
    pwd_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        100000
    )
    return hmac.compare_digest(pwd_hash.hex(), hash_hex)


def get_authenticated_student(request: Request) -> Optional[dict]:
    session_token = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_token:
        return None

    email = sessions.get(session_token)
    if not email:
        return None

    student = students.get(email)
    if not student:
        return None

    return {"email": email, "name": student["name"], "grade": student["grade"]}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.post("/auth/register")
def register_student(registration: StudentRegistration, response: Response):
    email = registration.email.lower()
    if email in students:
        raise HTTPException(status_code=400, detail="Email already registered")

    if len(registration.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    salt, pwd_hash = hash_password(registration.password)
    students[email] = {
        "name": registration.name,
        "grade": registration.grade,
        "password_hash": pwd_hash,
        "salt": salt
    }

    session_token = secrets.token_urlsafe(32)
    sessions[session_token] = email
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_token,
        httponly=True,
        samesite="lax"
    )

    return {
        "message": "Registration successful",
        "student": {"email": email, "name": registration.name, "grade": registration.grade}
    }


@app.post("/auth/login")
def login_student(login: StudentLogin, response: Response):
    email = login.email.lower()
    student = students.get(email)

    if not student or not verify_password(login.password, student["salt"], student["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    session_token = secrets.token_urlsafe(32)
    sessions[session_token] = email
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_token,
        httponly=True,
        samesite="lax"
    )

    return {
        "message": "Login successful",
        "student": {"email": email, "name": student["name"], "grade": student["grade"]}
    }


@app.post("/auth/logout")
def logout_student(request: Request, response: Response):
    session_token = request.cookies.get(SESSION_COOKIE_NAME)
    if session_token in sessions:
        sessions.pop(session_token)

    response.delete_cookie(SESSION_COOKIE_NAME)
    return {"message": "Logged out"}


@app.get("/auth/me")
def get_current_student(request: Request):
    student = get_authenticated_student(request)
    if not student:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return student


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, request: Request, email: Optional[str] = None):
    student = get_authenticated_student(request)
    if student:
        email = student["email"]

    if not email:
        raise HTTPException(status_code=401, detail="Authentication required to sign up")

    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    activity = activities[activity_name]
    if email in activity["participants"]:
        raise HTTPException(status_code=400, detail="Student is already signed up")

    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, request: Request, action: ActivityAction):
    student = get_authenticated_student(request)
    email = action.email
    if student:
        email = student["email"]

    if not email:
        raise HTTPException(status_code=401, detail="Authentication required to unregister")

    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    activity = activities[activity_name]
    if email not in activity["participants"]:
        raise HTTPException(status_code=400, detail="Student is not signed up for this activity")

    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
