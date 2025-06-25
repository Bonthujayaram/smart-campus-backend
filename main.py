import os
from dotenv import load_dotenv
#uvicorn main:app --reload
from fastapi import FastAPI, HTTPException, Depends, Query, Path, Response, Body, UploadFile, File, Form, WebSocket, WebSocketDisconnect, Request
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Enum, func, ForeignKey, Date, Boolean, UniqueConstraint, or_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
import enum
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import mysql.connector
from mysql.connector import Error
import json

load_dotenv()  # This loads the variables from .env

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",  # Vite default
        "http://localhost:5173",  # Vite alternative
        "http://localhost:3000",  # React default
        "http://127.0.0.1:8080",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "http://10.9.7.73:8080",
        "http://10.9.7.73:5173",
        "http://10.9.7.73:3000",
        "https://cutmcampusassitant.netlify.app",
        "https://smart-campus-backend-ty7w.onrender.com",
        "wss://smart-campus-backend-ty7w.onrender.com"
        # Removed wildcard "*" as it's not compatible with credentials
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]  # Added to ensure all response headers are accessible
)
# Mount static files directory
uploads_path = Path("uploads")
uploads_path.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

DATABASE_URL = os.getenv("DATABASE_URL")  # Get the URL from environment variable

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# After all model definitions and before any routes
# Create all tables
Base.metadata.create_all(bind=engine)

class RoleEnum(str, enum.Enum):
    student = "student"
    admin = "admin"
    faculty = "faculty"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    email = Column(String(255), unique=True, index=True)
    password = Column(String(255))
    role = Column(Enum(RoleEnum))
    

class LoginRequest(BaseModel):
    email: str
    password: str
    role: RoleEnum

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: RoleEnum
    studentId: int | None = None
    facultyId: int | None = None

class LoginResponse(BaseModel):
    success: bool
    user: UserResponse | None = None
    message: str | None = None

class Student(Base):
    __tablename__ = "student"
    studentId = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    registration_number = Column(String(50), nullable=False)
    semester = Column(Integer)
    branch = Column(String(50))
    specialization = Column(String(100))
    starting_year = Column(Integer)
    passout_year = Column(Integer)

class StudentCreate(BaseModel):
    name: str
    email: str
    registration_number: str
    semester: int
    branch: str
    specialization: str
    starting_year: int
    passout_year: int

class StudentUpdate(BaseModel):
    name: str
    email: str
    registration_number: str
    semester: int
    branch: str
    specialization: str
    starting_year: int
    passout_year: int

class Timetable(Base):
    __tablename__ = "timetable"
    id = Column(Integer, primary_key=True, autoincrement=True)
    day = Column(String(20), nullable=False)
    time = Column(String(20), nullable=False)
    subject = Column(String(100), nullable=False)
    faculty = Column(String(100), nullable=False)
    room = Column(String(50), nullable=False)
    type = Column(String(20), nullable=False)
    branch = Column(String(100), nullable=False)
    semester = Column(Integer, nullable=False)

class TimetableCreate(BaseModel):
    day: str
    time: str
    subject: str
    faculty: str
    room: str
    type: str
    branch: str
    semester: int

class Faculty(Base):
    __tablename__ = "faculty"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    faculty_code = Column(String(50), unique=True, nullable=False)
    department = Column(String(100), nullable=False)
    designation = Column(String(100), nullable=False)
    joining_date = Column(String(20), nullable=False)
    specialization = Column(String(200), nullable=True)
    contact_number = Column(String(20), nullable=True)
    is_active = Column(Integer, default=1)

class FacultyCreate(BaseModel):
    name: str
    email: str
    faculty_code: str
    department: str
    designation: str
    joining_date: str
    specialization: str | None = None
    contact_number: str | None = None
    is_active: int = 1

class FacultyUpdate(BaseModel):
    name: str
    email: str
    faculty_code: str
    department: str
    designation: str
    joining_date: str
    specialization: str | None = None
    contact_number: str | None = None
    is_active: int

class Syllabus(Base):
    __tablename__ = "syllabus"
    id = Column(Integer, primary_key=True, autoincrement=True)
    subject = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False)
    semester = Column(Integer, nullable=False)
    branch = Column(String(100), nullable=False)
    credits = Column(Integer, nullable=False)
    faculty_id = Column(Integer, ForeignKey("faculty.id"), nullable=True)
    faculty = relationship("Faculty", backref="syllabus")
    upload_date = Column(String(20), nullable=False)
    pdf_url = Column(String(255), nullable=True)
    description = Column(String(1000), nullable=True)
    specialization = Column(String(50), nullable=True)

class SyllabusBase(BaseModel):
    subject: str
    code: str
    semester: int
    branch: str
    credits: int
    faculty_id: int | None = None
    upload_date: str
    pdf_url: str | None = None
    description: str | None = None
    specialization: str | None = None

class SyllabusCreate(SyllabusBase):
    pass

class SyllabusUpdate(SyllabusBase):
    pass

class SyllabusOut(BaseModel):
    id: int
    subject: str
    code: str
    semester: int
    branch: str
    credits: int
    faculty_id: int | None = None
    faculty: str | None = None
    upload_date: str
    pdf_url: str | None = None
    description: str | None = None
    specialization: str | None = None

    class Config:
        orm_mode = True

class Assignment(Base):
    __tablename__ = "assignments"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    subject = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    semester = Column(Integer, nullable=False)
    branch = Column(String(100), nullable=False)
    specialization = Column(String(100), nullable=True)
    due_date = Column(String(20), nullable=False)
    faculty_id = Column(Integer, ForeignKey("faculty.id"), nullable=False)
    faculty = relationship("Faculty", backref="assignments")

class AssignmentCreate(BaseModel):
    title: str
    subject: str
    description: str
    semester: int
    branch: str
    specialization: str | None = None
    due_date: str
    faculty_id: int

class AssignmentUpdate(BaseModel):
    title: str
    subject: str
    description: str
    semester: int
    branch: str
    specialization: str | None = None
    due_date: str
    faculty_id: int | None = None

class Submission(Base):
    __tablename__ = "submissions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("student.studentId"), nullable=False)
    file_url = Column(String(255), nullable=True)
    text_answer = Column(String(1000), nullable=True)
    submitted_at = Column(String(20), nullable=False)
    status = Column(String(20), default="pending")
    
    # Add unique constraint to prevent multiple submissions
    __table_args__ = (UniqueConstraint('assignment_id', 'student_id', name='uix_1'),)

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    message = Column(String(1000), nullable=False)
    type = Column(String(50), nullable=False)
    target_audience = Column(String(100), nullable=False)
    priority = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False)
    created_at = Column(String(20), nullable=False)
    sent_at = Column(String(20), nullable=True)
    recipients_count = Column(Integer, default=0)

class ReadNotification(Base):
    __tablename__ = "read_notifications"
    id = Column(Integer, primary_key=True, autoincrement=True)
    notification_id = Column(Integer, ForeignKey("notifications.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    read_at = Column(String(20), nullable=False)
    
    # Add unique constraint to prevent duplicate read records
    __table_args__ = (UniqueConstraint('notification_id', 'user_id', name='uix_read_notification'),)

class Attendance(Base):
    __tablename__ = "attendance"
    attendance_id = Column(Integer, primary_key=True)
    studentId = Column(Integer, ForeignKey("student.studentId"))
    subject_code = Column(String)
    date = Column(String)  # Keep as string since that's how it's in the DB
    attendance = Column(String)  # 'P' or 'A'
    class_type = Column(String)  # Add class type field

class AttendanceCreate(BaseModel):
    student_id: int
    subject: str
    date: str
    status: str
    class_type: str  # Add class type to the model

class SubmissionStatusUpdate(BaseModel):
    status: str

class NotificationCreate(BaseModel):
    title: str
    message: str
    type: str
    target_audience: str
    priority: str
    status: str

class NotificationReadRequest(BaseModel):
    user_id: int

class QRScanRequest(BaseModel):
    qrData: str
    studentId: int | None = None  # Make studentId optional for backward compatibility

class QRScanResponse(BaseModel):
    newScans: list
    message: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    try:
        if request.role == RoleEnum.faculty:
            # For faculty, we use faculty_code instead of password
            faculty = db.query(Faculty).filter(
                Faculty.email == request.email,
                Faculty.faculty_code == request.password  # Using password field to receive faculty_code
            ).first()
            
            if not faculty:
                return LoginResponse(success=False, message="Invalid email or faculty code")
            
            return LoginResponse(
                success=True,
                user=UserResponse(
                    id=str(faculty.id),
                    name=faculty.name,
                    email=faculty.email,
                    role=RoleEnum.faculty,
                    facultyId=faculty.id
                )
            )
        else:
            # Handle existing student and admin login logic
            user = db.query(User).filter(
                User.email == request.email,
                User.password == request.password,
                User.role == request.role
            ).first()
            
            if not user:
                return LoginResponse(success=False, message="Invalid credentials")
            
            # Add studentId if the user is a student
            student = None
            if user.role == RoleEnum.student:
                student = db.query(Student).filter(Student.email == user.email).first()
            
            return LoginResponse(
                success=True,
                user=UserResponse(
                    id=str(user.id),
                    name=user.name,
                    email=user.email,
                    role=user.role,
                    studentId=student.studentId if student else None
                )
            )
    except Exception as e:
        return LoginResponse(success=False, message=str(e))

@app.post("/students")
def create_student(student: StudentCreate, db: Session = Depends(get_db)):
    db_student = db.query(Student).filter((Student.email == student.email)).first()
    if db_student:
        raise HTTPException(status_code=400, detail="Student with this email already exists.")
    new_student = Student(
        name=student.name,
        email=student.email,
        registration_number=student.registration_number,
        semester=student.semester,
        branch=student.branch,
        specialization=student.specialization,
        starting_year=student.starting_year,
        passout_year=student.passout_year
    )
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    # Also add to users table if not present
    db_user = db.query(User).filter(User.email == student.email).first()
    if not db_user:
        new_user = User(
            name=student.name,
            email=student.email,
            password=None,  # No hardcoded password, should be set by user later
            role=RoleEnum.student
        )
        db.add(new_user)
        db.commit()
    return {"success": True, "message": "Student added successfully."}

@app.get("/students")
def get_students(db: Session = Depends(get_db)):
    students = db.query(Student).all()
    result = []
    for s in students:
        result.append({
            "studentId": s.studentId,
            "name": s.name,
            "email": s.email,
            "registration_number": s.registration_number,
            "semester": s.semester,
            "branch": s.branch,
            "specialization": s.specialization,
            "starting_year": s.starting_year,
            "passout_year": s.passout_year,
        })
    return JSONResponse(content=result)

@app.get("/students/me")
def get_current_student(email: str = Query(...), db: Session = Depends(get_db)):
    student = db.query(Student).filter(func.lower(Student.email) == email.lower()).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return {
        "studentId": student.studentId,
        "name": student.name,
        "email": student.email,
        "branch": student.branch,
        "semester": student.semester,
    }

@app.get("/timetables")
def get_timetables(branch: str = Query(...), semester: int = Query(...), db: Session = Depends(get_db)):
    timetables = db.query(Timetable).filter(
        func.lower(Timetable.branch) == branch.lower().strip(),
        Timetable.semester == int(semester)
    ).all()
    return [
        {
            "id": t.id,
            "day": t.day,
            "time": t.time,
            "subject": t.subject,
            "faculty": t.faculty,
            "room": t.room,
            "type": t.type,
            "branch": t.branch,
            "semester": t.semester,
        }
        for t in timetables
    ]

@app.post("/timetables")
def add_timetable(entry: TimetableCreate, db: Session = Depends(get_db)):
    new_entry = Timetable(**entry.dict())
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)
    return {"success": True, "id": new_entry.id}

@app.post("/timetables/bulk")
def add_timetables_bulk(entries: List[TimetableCreate], db: Session = Depends(get_db)):
    valid_entries = []
    errors = []
    for idx, entry in enumerate(entries):
        try:
            # Validate required fields
            if not all([
                entry.day and entry.day.strip(),
                entry.time and entry.time.strip(),
                entry.subject and entry.subject.strip(),
                entry.faculty and entry.faculty.strip(),
                entry.room and entry.room.strip(),
                entry.type and entry.type.strip(),
                entry.branch and entry.branch.strip(),
                entry.semester is not None and str(entry.semester).strip()
            ]):
                raise ValueError("Missing required field(s)")
            valid_entries.append(Timetable(**entry.dict()))
        except Exception as e:
            errors.append({"row": idx + 1, "error": str(e), "data": entry.dict()})

    inserted = 0
    if valid_entries:
        db.add_all(valid_entries)
        db.commit()
        inserted = len(valid_entries)

    return {
        "success": True,
        "inserted": inserted,
        "failed": len(errors),
        "errors": errors
    }

@app.put("/timetables/{id}")
def update_timetable(id: int, entry: TimetableCreate, db: Session = Depends(get_db)):
    timetable = db.query(Timetable).filter(Timetable.id == id).first()
    if not timetable:
        raise HTTPException(status_code=404, detail="Timetable entry not found")
    for key, value in entry.dict().items():
        setattr(timetable, key, value)
    db.commit()
    return {"success": True}

@app.delete("/timetables/{id}")
def delete_timetable(id: int, db: Session = Depends(get_db)):
    timetable = db.query(Timetable).filter(Timetable.id == id).first()
    if not timetable:
        raise HTTPException(status_code=404, detail="Timetable entry not found")
    db.delete(timetable)
    db.commit()
    return {"success": True}

@app.put("/students/{student_id}")
def update_student(student_id: int, student_data: dict, db: Session = Depends(get_db)):
    try:
        # Get the student
        student = db.query(Student).filter(Student.studentId == student_id).first()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")

        # Update only allowed fields
        allowed_fields = ["name", "email", "registration_number", "semester", "specialization"]
        for field in allowed_fields:
            if field in student_data:
                setattr(student, field, student_data[field])

        db.commit()
        return {"message": "Student updated successfully"}
    except Exception as e:
        db.rollback()
        print(f"Error updating student: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/students/{student_id}")
def delete_student(student_id: int, db: Session = Depends(get_db)):
    db_student = db.query(Student).filter(Student.studentId == student_id).first()
    if not db_student:
        raise HTTPException(status_code=404, detail="Student not found")
    db.delete(db_student)
    db.commit()
    return {"success": True, "message": "Student deleted successfully."}

@app.get("/syllabus", response_model=list[SyllabusOut])
def get_syllabus(
    branch: str | None = Query(None),
    semester: int | None = Query(None),
    specialization: str | None = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Syllabus)
    
    if branch:
        query = query.filter(Syllabus.branch == branch)
    if semester:
        query = query.filter(Syllabus.semester == int(semester))
    if specialization and specialization != 'all':
        query = query.filter(Syllabus.specialization == specialization)
    
    syllabus = query.all()
    result = []
    for s in syllabus:
        faculty_name = None
        if s.faculty_id:
            faculty = db.query(Faculty).filter(Faculty.id == s.faculty_id).first()
            faculty_name = faculty.name if faculty else None
        upload_date_str = (
            s.upload_date.isoformat() if hasattr(s.upload_date, 'isoformat') else str(s.upload_date)
        )
        result.append({
            "id": s.id,
            "subject": s.subject,
            "code": s.code,
            "semester": s.semester,
            "branch": s.branch,
            "credits": s.credits,
            "faculty_id": s.faculty_id,
            "faculty": faculty_name,
            "upload_date": upload_date_str,
            "pdf_url": s.pdf_url,
            "description": s.description,
            "specialization": s.specialization
        })
    return result

@app.post("/syllabus", response_model=SyllabusOut)
def create_syllabus(entry: SyllabusCreate, db: Session = Depends(get_db)):
    entry_dict = entry.dict()
    # Ensure upload_date is a string
    if hasattr(entry_dict["upload_date"], 'isoformat'):
        entry_dict["upload_date"] = entry_dict["upload_date"].isoformat()
    else:
        entry_dict["upload_date"] = str(entry_dict["upload_date"])
    new_entry = Syllabus(**entry_dict)
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)
    # Convert upload_date to string for the response
    result = new_entry.__dict__.copy()
    if hasattr(new_entry.upload_date, 'isoformat'):
        result["upload_date"] = new_entry.upload_date.isoformat()
    else:
        result["upload_date"] = str(new_entry.upload_date)
    return result

@app.put("/syllabus/{syllabus_id}", response_model=SyllabusOut)
def update_syllabus(syllabus_id: int, entry: SyllabusUpdate, db: Session = Depends(get_db)):
    syllabus = db.query(Syllabus).filter(Syllabus.id == syllabus_id).first()
    if not syllabus:
        raise HTTPException(status_code=404, detail="Syllabus entry not found")
    for key, value in entry.dict().items():
        setattr(syllabus, key, value)
    db.commit()
    db.refresh(syllabus)
    return syllabus

@app.delete("/syllabus/{syllabus_id}")
def delete_syllabus(syllabus_id: int, db: Session = Depends(get_db)):
    syllabus = db.query(Syllabus).filter(Syllabus.id == syllabus_id).first()
    if not syllabus:
        raise HTTPException(status_code=404, detail="Syllabus entry not found")
    db.delete(syllabus)
    db.commit()
    return {"success": True, "message": "Syllabus deleted successfully."}

@app.get("/syllabus/subjects-faculty")
def get_subjects_faculty(branch: str = Query(...), semester: int = Query(...), db: Session = Depends(get_db)):
    syllabus = db.query(Syllabus).filter(Syllabus.branch == branch, Syllabus.semester == semester).all()
    return [
        {"subject": s.subject, "faculty_id": s.faculty_id} for s in syllabus
    ]

@app.get("/assignments")
def get_assignments(db: Session = Depends(get_db)):
    assignments = db.query(Assignment).all()
    result = []
    for a in assignments:
        result.append({
            "id": a.id,
            "title": a.title,
            "subject": a.subject,
            "description": a.description,
            "semester": a.semester,
            "branch": a.branch,
            "due_date": a.due_date,
        })
    return result

@app.post("/assignments")
def create_assignment(assignment: AssignmentCreate, db: Session = Depends(get_db)):
    new_assignment = Assignment(**assignment.dict())
    db.add(new_assignment)
    db.commit()
    db.refresh(new_assignment)
    return {
        "id": new_assignment.id,
        "title": new_assignment.title,
        "subject": new_assignment.subject,
        "description": new_assignment.description,
        "semester": new_assignment.semester,
        "branch": new_assignment.branch,
        "due_date": new_assignment.due_date,
        "faculty_id": new_assignment.faculty_id
    }

@app.put("/assignments/{assignment_id}")
def update_assignment(assignment_id: int, assignment: AssignmentUpdate, db: Session = Depends(get_db)):
    db_assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not db_assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    for key, value in assignment.dict().items():
        setattr(db_assignment, key, value)
    db.commit()
    db.refresh(db_assignment)
    return {
        "id": db_assignment.id,
        "title": db_assignment.title,
        "subject": db_assignment.subject,
        "description": db_assignment.description,
        "semester": db_assignment.semester,
        "branch": db_assignment.branch,
        "due_date": db_assignment.due_date,
    }

@app.delete("/assignments/{assignment_id}")
def delete_assignment(assignment_id: int, db: Session = Depends(get_db)):
    db_assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not db_assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    db.delete(db_assignment)
    db.commit()
    return {"success": True, "message": "Assignment deleted successfully."}

@app.post("/students/bulk-delete")
def bulk_delete_students(ids: dict = Body(...), db: Session = Depends(get_db)):
    # ids should be a dict with key 'ids' and value as list of student IDs
    student_ids = ids.get("ids", [])
    if not isinstance(student_ids, list) or not all(isinstance(i, int) for i in student_ids):
        raise HTTPException(status_code=400, detail="Invalid input. 'ids' must be a list of integers.")
    deleted_count = db.query(Student).filter(Student.studentId.in_(student_ids)).delete(synchronize_session=False)
    db.commit()
    return {"success": True, "deleted": deleted_count, "message": f"Deleted {deleted_count} students."}

@app.get("/dashboard-stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    total_students = db.query(Student).count()
    total_faculty = db.query(Faculty).count()  # Changed to count from Faculty table
    active_assignments = db.query(Assignment).count()  # TODO: Filter by active if you have a status field
    pending_notifications = 0  # TODO: Implement notification model and logic
    attendance_today = 0  # TODO: Implement attendance model and logic
    upcoming_events = 0  # TODO: Implement events model and logic
    return {
        "totalStudents": total_students,
        "totalFaculty": total_faculty,
        "activeAssignments": active_assignments,
        "pendingNotifications": pending_notifications,
        "attendanceToday": attendance_today,
        "upcomingEvents": upcoming_events
    }

@app.get("/faculty")
def get_faculty(db: Session = Depends(get_db)):
    faculty = db.query(Faculty).all()
    return faculty

@app.get("/faculty/{faculty_id}")
def get_faculty_by_id(faculty_id: int, db: Session = Depends(get_db)):
    faculty = db.query(Faculty).filter(Faculty.id == faculty_id).first()
    if not faculty:
        raise HTTPException(status_code=404, detail="Faculty not found")
    return faculty

@app.post("/faculty")
def create_faculty(faculty: FacultyCreate, db: Session = Depends(get_db)):
    try:
        # Check if faculty with same email exists
        existing_faculty = db.query(Faculty).filter(Faculty.email == faculty.email).first()
        if existing_faculty:
            raise HTTPException(status_code=400, detail="Faculty with this email already exists")
        
        # Create new faculty
        db_faculty = Faculty(**faculty.dict())
        db.add(db_faculty)
        db.commit()
        db.refresh(db_faculty)
        return db_faculty
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/faculty/{faculty_id}")
def update_faculty(faculty_id: int, faculty: FacultyUpdate, db: Session = Depends(get_db)):
    try:
        # Check if faculty exists
        db_faculty = db.query(Faculty).filter(Faculty.id == faculty_id).first()
        if not db_faculty:
            raise HTTPException(status_code=404, detail="Faculty not found")
        
        # Check if email is being changed and if new email already exists
        if faculty.email != db_faculty.email:
            existing_faculty = db.query(Faculty).filter(Faculty.email == faculty.email).first()
            if existing_faculty:
                raise HTTPException(status_code=400, detail="Faculty with this email already exists")
        
        # Update faculty
        for key, value in faculty.dict().items():
            setattr(db_faculty, key, value)
        
        db.commit()
        db.refresh(db_faculty)
        return db_faculty
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/faculty/{faculty_id}")
def delete_faculty(faculty_id: int, db: Session = Depends(get_db)):
    try:
        faculty = db.query(Faculty).filter(Faculty.id == faculty_id).first()
        if not faculty:
            raise HTTPException(status_code=404, detail="Faculty not found")
        
        db.delete(faculty)
        db.commit()
        return {"message": "Faculty deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/faculty/stats")
def get_faculty_stats(db: Session = Depends(get_db)):
    try:
        total_faculty = db.query(func.count(Faculty.id)).scalar()
        active_faculty = db.query(func.count(Faculty.id)).filter(Faculty.is_active == 1).scalar()
        departments = db.query(Faculty.department, func.count(Faculty.id)).group_by(Faculty.department).all()
        department_stats = [{"department": dept, "count": count} for dept, count in departments]
        
        return {
            "total_faculty": total_faculty,
            "active_faculty": active_faculty,
            "department_stats": department_stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/students/{student_id}/assignments")
def get_student_assignments(student_id: int, db: Session = Depends(get_db)):
    try:
        # Get student details first
        student = db.query(Student).filter(Student.studentId == student_id).first()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")

        # Get assignments for student's branch
        query = db.query(Assignment).filter(
            Assignment.branch == student.branch
        )

        # If student has specialization, filter by it using syllabus table
        if student.specialization:
            # Get subjects for the student's specialization
            specialized_subjects = db.query(Syllabus.subject).filter(
                Syllabus.branch == student.branch,
                Syllabus.specialization == student.specialization
            ).all()
            specialized_subjects = [s[0] for s in specialized_subjects]
            
            # If there are specialized subjects, filter assignments by them
            if specialized_subjects:
                query = query.filter(Assignment.subject.in_(specialized_subjects))

        assignments = query.all()
        result = []
        for a in assignments:
            # Check if student has submitted this assignment
            submission = db.query(Submission).filter(
                Submission.assignment_id == a.id,
                Submission.student_id == student_id
            ).first()
            
            status = submission.status if submission else None
            result.append({
                "id": a.id,
                "title": a.title,
                "subject": a.subject,
                "description": a.description,
                "semester": a.semester,
                "branch": a.branch,
                "due_date": a.due_date,
                "status": status,
            })
        return result
    except Exception as e:
        print(f"Error getting student assignments: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/assignments/{assignment_id}/submit")
def submit_assignment(
    assignment_id: int,
    student_id: int = Form(...),
    text_answer: str = Form(None),
    file: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    # Check if student has already submitted this assignment
    existing_submission = db.query(Submission).filter(
        Submission.assignment_id == assignment_id,
        Submission.student_id == student_id
    ).first()
    
    if existing_submission and existing_submission.status != 'rejected':
        raise HTTPException(
            status_code=400,
            detail="You cannot resubmit this assignment unless it has been rejected"
        )

    file_url = None
    if file:
        # Ensure the uploads directory exists
        os.makedirs("uploads", exist_ok=True)
        file_location = f"uploads/{assignment_id}_{student_id}_{file.filename}"
        with open(file_location, "wb") as f:
            f.write(file.file.read())
        file_url = file_location

    if existing_submission:
        # Update existing submission
        existing_submission.file_url = file_url if file else existing_submission.file_url
        existing_submission.text_answer = text_answer if text_answer else existing_submission.text_answer
        existing_submission.submitted_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        existing_submission.status = "pending"
        db.commit()
    else:
        # Create new submission
        submission = Submission(
            assignment_id=assignment_id,
            student_id=student_id,
            file_url=file_url,
            text_answer=text_answer,
            submitted_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            status="pending"
        )
        db.add(submission)
        db.commit()

    return {"success": True, "message": "Assignment submitted successfully!"}

@app.get("/")
def read_root():
    return {"message": "API is running"}

@app.put("/submissions/{submission_id}/status")
def update_submission_status(submission_id: int, status_update: SubmissionStatusUpdate, db: Session = Depends(get_db)):
    try:
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")
        
        if status_update.status not in ["approved", "rejected", "pending"]:
            raise HTTPException(status_code=422, detail="Status must be either 'approved', 'rejected', or 'pending'")
        
        # If status is being set to approved and there's a file, delete it
        if status_update.status == "approved" and submission.file_url:
            try:
                file_path = os.path.join(os.getcwd(), submission.file_url)
                if os.path.exists(file_path):
                    os.remove(file_path)  # Delete the file
                    # Update the file_url to None since file is deleted
                    submission.file_url = None
            except Exception as e:
                print(f"Error deleting file: {e}")
                # Continue with status update even if file deletion fails
        
        submission.status = status_update.status
        db.commit()
        return {
            "message": "Status updated successfully",
            "status": status_update.status,
            "file_deleted": submission.file_url is None
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/assignments")
def get_admin_assignments(db: Session = Depends(get_db)):
    assignments = db.query(Assignment).all()
    result = []
    for a in assignments:
        submission_count = db.query(func.count(Submission.id)).filter(Submission.assignment_id == a.id).scalar()
        status = "submitted" if submission_count > 0 else "pending"
        result.append({
            "id": a.id,
            "title": a.title,
            "subject": a.subject,
            "description": a.description,
            "semester": a.semester,
            "branch": a.branch,
            "due_date": a.due_date,
            "status": status,
        })
    return result

@app.get("/assignments/{assignment_id}/submissions")
def get_assignment_submissions(assignment_id: int, db: Session = Depends(get_db)):
    try:
        submissions = db.query(
            Submission,
            Student.name.label('student_name'),
            Student.registration_number.label('student_registration')
        )\
        .join(Student, Student.studentId == Submission.student_id)\
        .filter(Submission.assignment_id == assignment_id)\
        .all()
        
        return [{
            **submission[0].__dict__,
            'student_name': submission[1],
            'student_registration': submission[2]
        } for submission in submissions]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/submissions")
def get_all_submissions(db: Session = Depends(get_db)):
    submissions = db.query(Submission).all()
    result = []
    for s in submissions:
        result.append({
            "id": s.id,
            "assignment_id": s.assignment_id,
            "student_id": s.student_id,
            "file_url": s.file_url,
            "text_answer": s.text_answer,
            "submitted_at": s.submitted_at,
        })
    return result

@app.post("/attendance/mark")
def mark_attendance(
    attendance: dict = Body(...),
    db: Session = Depends(get_db)
):
    try:
        # Verify student exists
        student = db.query(Student).filter(Student.studentId == attendance["student_id"]).first()
        if not student:
            raise HTTPException(status_code=404, detail=f"Student with ID {attendance['student_id']} not found")

        # Verify subject exists in syllabus for student's branch and semester
        subject_exists = db.query(Syllabus).filter(
            Syllabus.subject == attendance["subject"],
            Syllabus.branch == student.branch,
            Syllabus.semester == student.semester
        ).first()
        
        if not subject_exists:
            raise HTTPException(
                status_code=400, 
                detail=f"Subject {attendance['subject']} is not valid for {student.branch} branch semester {student.semester}"
            )

        # Check if attendance already exists
        existing_attendance = db.query(Attendance).filter(
            Attendance.studentId == attendance["student_id"],
            Attendance.subject_code == attendance["subject"],
            Attendance.date == attendance["date"]
        ).first()

        if existing_attendance:
            # Update existing attendance
            existing_attendance.attendance = attendance["status"]
        else:
            # Create new attendance record
            new_attendance = Attendance(
                studentId=attendance["student_id"],
                subject_code=attendance["subject"],
                date=attendance["date"],
                attendance=attendance["status"]
            )
            db.add(new_attendance)
        
        db.commit()
        return {"message": "Attendance marked successfully"}
    except Exception as e:
        db.rollback()
        print(f"Error marking attendance: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dashboard/stats")
def get_stats():
    return [
        {"label": "Attendance", "value": "85%", "color": "bg-green-100 text-green-800"},
        {"label": "Pending Assignments", "value": "3", "color": "bg-yellow-100 text-yellow-800"},
        {"label": "Upcoming Events", "value": "2", "color": "bg-blue-100 text-blue-800"},
        {"label": "Notifications", "value": "5", "color": "bg-red-100 text-red-800"},
    ]

@app.get("/dashboard/actions")
def get_actions():
    return [
        {"title": "View Timetable", "description": "Check your daily schedule", "icon": "Calendar", "link": "/timetable", "color": "bg-blue-500"},
        # ... more actions ...
    ]

@app.get("/dashboard/notifications")
def get_notifications():
    return [
        {"title": "Mid-term Exam Schedule Released", "time": "2 hours ago", "type": "exam"},
        # ... more notifications ...
    ]

@app.get("/faculty/{faculty_id}/assignments")
def get_faculty_assignments(faculty_id: int, db: Session = Depends(get_db)):
    try:
        assignments = db.query(Assignment).filter(Assignment.faculty_id == faculty_id).all()
        return assignments
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/faculty/{faculty_id}/dashboard-stats")
def get_faculty_dashboard_stats(faculty_id: int, db: Session = Depends(get_db)):
    try:
        # Teaching Statistics
        total_subjects = db.query(func.count(Syllabus.id))\
            .filter(Syllabus.faculty_id == faculty_id)\
            .scalar() or 0
            
        # Get unique branches and semesters this faculty teaches
        teaching_branches = db.query(func.count(func.distinct(Syllabus.branch)))\
            .filter(Syllabus.faculty_id == faculty_id)\
            .scalar() or 0
            
        # Assignment Statistics
        total_assignments = db.query(func.count(Assignment.id))\
            .filter(Assignment.faculty_id == faculty_id)\
            .scalar() or 0
            
        pending_evaluations = db.query(func.count(Submission.id))\
            .join(Assignment, Assignment.id == Submission.assignment_id)\
            .filter(Assignment.faculty_id == faculty_id)\
            .filter(Submission.status == 'pending')\
            .scalar() or 0
            
        # Recent Submissions (last 7 days)
        seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        recent_submissions = db.query(func.count(Submission.id))\
            .join(Assignment, Assignment.id == Submission.assignment_id)\
            .filter(Assignment.faculty_id == faculty_id)\
            .filter(Submission.submitted_at >= seven_days_ago)\
            .scalar() or 0
            
        # Attendance Statistics
        today = datetime.now().strftime("%Y-%m-%d")
        total_attendance_today = db.query(func.count(Attendance.attendance_id))\
            .filter(Attendance.date == today)\
            .scalar() or 0
            
        # Get today's scheduled classes
        today_day = datetime.now().strftime("%A")  # Get day name (Monday, Tuesday, etc.)
        classes_today = db.query(func.count(Timetable.id))\
            .join(Faculty, Faculty.name == Timetable.faculty)\
            .filter(Faculty.id == faculty_id)\
            .filter(Timetable.day == today_day)\
            .scalar() or 0
            
        # Student Engagement
        active_students = db.query(func.count(func.distinct(Submission.student_id)))\
            .join(Assignment, Assignment.id == Submission.assignment_id)\
            .filter(Assignment.faculty_id == faculty_id)\
            .scalar() or 0
            
        return {
            "totalSubjects": total_subjects,
            "teachingBranches": teaching_branches,
            "totalAssignments": total_assignments,
            "pendingEvaluations": pending_evaluations,
            "recentSubmissions": recent_submissions,
            "totalAttendanceToday": total_attendance_today,
            "classesToday": classes_today,
            "activeStudents": active_students
        }
    except Exception as e:
        print(f"Error in faculty dashboard stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/faculty/{faculty_id}/timetable")
def get_faculty_timetable(faculty_id: int, db: Session = Depends(get_db)):
    try:
        faculty = db.query(Faculty).filter(Faculty.id == faculty_id).first()
        if not faculty:
            raise HTTPException(status_code=404, detail="Faculty not found")
        
        timetable = db.query(Timetable)\
            .filter(Timetable.faculty == faculty.name)\
            .all()
        
        return timetable
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/faculty/{faculty_id}/subjects")
def get_faculty_subjects(faculty_id: int, db: Session = Depends(get_db)):
    try:
        # Get subjects from syllabus where faculty_id matches
        subjects = db.query(Syllabus.subject)\
            .filter(Syllabus.faculty_id == faculty_id)\
            .filter(Syllabus.subject.isnot(None))\
            .filter(Syllabus.subject != '')\
            .distinct()\
            .all()
        return [subject[0] for subject in subjects if subject[0] and subject[0].strip()]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/specializations/{branch}")
def get_specializations(branch: str, db: Session = Depends(get_db)):
    try:
        # Get distinct specializations for the given branch from students table
        specializations = db.query(Student.specialization)\
            .filter(Student.branch == branch)\
            .filter(Student.specialization.isnot(None))\
            .filter(Student.specialization != '')\
            .distinct()\
            .all()
        return [spec[0] for spec in specializations if spec[0] and spec[0].strip()]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/students/specializations")
def get_student_specializations(
    branch: str = Query(...),
    semester: int = Query(...),
    db: Session = Depends(get_db)
):
    try:
        # Get distinct specializations for the given branch and semester
        specializations = db.query(Student.specialization)\
            .filter(Student.branch == branch)\
            .filter(Student.semester == semester)\
            .filter(Student.specialization.isnot(None))\
            .filter(Student.specialization != '')\
            .distinct()\
            .all()
        
        # Convert from list of tuples to list of strings and remove None/empty values
        result = [spec[0] for spec in specializations if spec[0] and spec[0].strip()]
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/students/filtered")
def get_filtered_students(
    branch: str,
    semester: int,
    specialization: str = None,
    db: Session = Depends(get_db)
):
    try:
        query = db.query(Student).filter(
            Student.branch == branch,
            Student.semester == semester
        )
        
        if specialization:
            query = query.filter(Student.specialization == specialization)
            
        students = query.all()
        return [
            {
                "studentId": student.studentId,
                "name": student.name,
                "registration_number": student.registration_number,
                "branch": student.branch,
                "semester": student.semester,
                "specialization": student.specialization
            }
            for student in students
        ]
    except Exception as e:
        print(f"Error fetching students: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/attendance/by-date-subject")
def get_attendance_by_date_subject(
    date: str = Query(...),
    subject: str = Query(...),
    db: Session = Depends(get_db)
):
    try:
        attendance_records = db.query(Attendance).filter(
            Attendance.date == date,
            Attendance.subject_code == subject
        ).all()
        
        return [
            {
                "attendance_id": record.attendance_id,
                "studentId": record.studentId,  # Changed from student_id to studentId
                "subject": record.subject_code,
                "date": record.date,
                "attendance": record.attendance
            }
            for record in attendance_records
        ]
    except Exception as e:
        print(f"Error fetching attendance: {str(e)}")  # Add logging
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/attendance/{attendance_id}")
def update_attendance(
    attendance_id: int,
    attendance: AttendanceCreate,
    db: Session = Depends(get_db)
):
    try:
        db_attendance = db.query(Attendance).filter(Attendance.attendance_id == attendance_id).first()
        if not db_attendance:
            raise HTTPException(status_code=404, detail="Attendance record not found")
        
        # Update the attendance record
        db_attendance.student_id = attendance.student_id
        db_attendance.subject_code = attendance.subject
        db_attendance.date = attendance.date
        db_attendance.attendance = attendance.status
        
        db.commit()
        return {"message": "Attendance updated successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/faculty/{faculty_id}/timetable-classes")
def get_faculty_timetable_classes(faculty_id: int, db: Session = Depends(get_db)):
    try:
        # Get faculty name first
        faculty = db.query(Faculty).filter(Faculty.id == faculty_id).first()
        if not faculty:
            raise HTTPException(status_code=404, detail="Faculty not found")

        # Get timetable entries for this faculty
        timetable_entries = db.query(Timetable).filter(
            Timetable.faculty == faculty.name
        ).all()

        return [
            {
                "id": entry.id,
                "day": entry.day,
                "time": entry.time,
                "subject": entry.subject,
                "room": entry.room,
                "type": entry.type,
                "branch": entry.branch,
                "semester": entry.semester
            }
            for entry in timetable_entries
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/attendance/check")
def check_attendance(
    date: str,
    subject: str,
    type: str = Query(...),  # Add type parameter
    db: Session = Depends(get_db)
):
    try:
        print(f"Checking attendance for date: {date}, subject: {subject}, type: {type}")
        
        # Validate date format
        try:
            datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
            
        # Get all attendance records for this date, subject, and class type
        attendance_records = db.query(Attendance).filter(
            Attendance.date == date,
            Attendance.subject_code == subject,
            Attendance.class_type == type  # Add class type filter
        ).all()
        
        print(f"Found {len(attendance_records)} attendance records")
        
        if attendance_records:
            return {
                "exists": True,
                "message": f"Attendance already taken for this {type} class",
                "count": len(attendance_records)
            }
        return {
            "exists": False,
            "message": "No attendance found"
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error checking attendance: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while checking attendance: {str(e)}"
        )

@app.get("/assignments/filtered")
def get_filtered_assignments(
    branch: str = Query(None),
    semester: int = Query(None),
    subject: str = Query(None),
    specialization: str = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Assignment)
    
    if branch:
        query = query.filter(Assignment.branch == branch)
    if semester:
        query = query.filter(Assignment.semester == semester)
    if subject:
        query = query.filter(Assignment.subject == subject)
    if specialization:
        query = query.filter(Assignment.specialization == specialization)
    
    assignments = query.all()
    result = []
    for a in assignments:
        result.append({
            "id": a.id,
            "title": a.title,
            "subject": a.subject,
            "description": a.description,
            "semester": a.semester,
            "branch": a.branch,
            "due_date": a.due_date,
            "faculty_id": a.faculty_id,
            "specialization": a.specialization
        })
    return result

@app.get("/students/{student_id}")
def get_student(student_id: int, db: Session = Depends(get_db)):
    try:
        student = db.query(Student).filter(Student.studentId == student_id).first()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        return {
            "studentId": student.studentId,
            "name": student.name,
            "email": student.email,
            "branch": student.branch,
            "semester": student.semester,
            "specialization": student.specialization,
            "registration_number": student.registration_number
        }
    except Exception as e:
        print(f"Error getting student details: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/attendance/student-summary")
def get_student_attendance_summary(
    branch: str = Query(...),
    semester: int = Query(...),
    specialization: str = Query(None),
    db: Session = Depends(get_db)
):
    try:
        print(f"Getting attendance summary for branch={branch}, semester={semester}, specialization={specialization}")
        
        # First get all students matching the criteria
        student_query = db.query(Student).filter(
            Student.branch == branch,
            Student.semester == semester
        )
        
        # Only filter by specialization if it's provided and not 'all'
        if specialization and specialization.lower() != 'all':
            student_query = student_query.filter(Student.specialization == specialization)
            
        students = student_query.all()
        print(f"Found {len(students)} students matching criteria")

        # Get all attendance records for these students in one query
        student_ids = [student.studentId for student in students]
        
        # Get subjects for this branch and semester from syllabus
        valid_subjects = db.query(Syllabus.subject).filter(
            Syllabus.branch == branch,
            Syllabus.semester == semester
        ).all()
        valid_subjects = [s[0] for s in valid_subjects]
        print(f"Valid subjects for {branch} semester {semester}: {valid_subjects}")

        # Get attendance records filtered by student IDs and valid subjects
        attendance_records = db.query(Attendance).filter(
            Attendance.studentId.in_(student_ids),
            Attendance.subject_code.in_(valid_subjects)
        ).all()
        print(f"Found {len(attendance_records)} attendance records")

        # Get unique subjects from attendance records
        subjects = list(set(record.subject_code for record in attendance_records))
        print(f"Found subjects: {subjects}")

        # Group attendance records by student
        attendance_by_student = {}
        for record in attendance_records:
            if record.studentId not in attendance_by_student:
                attendance_by_student[record.studentId] = []
            attendance_by_student[record.studentId].append(record)

        # Calculate summaries for each student
        student_summaries = []
        for student in students:
            student_records = attendance_by_student.get(student.studentId, [])
            print(f"Processing student {student.studentId} with {len(student_records)} records")
            
            subject_attendance = {}
            for subject in subjects:
                subject_records = [r for r in student_records if r.subject_code == subject]
                total_classes = len(subject_records)
                if total_classes == 0:
                    subject_attendance[subject] = {
                        "present": 0,
                        "total": 0,
                        "percentage": 0
                    }
                else:
                    present_count = len([r for r in subject_records if r.attendance == 'P'])
                    subject_attendance[subject] = {
                        "present": present_count,
                        "total": total_classes,
                        "percentage": (present_count / total_classes) * 100
                    }

            # Calculate overall percentage only if there are classes
            total_present = sum(data["present"] for data in subject_attendance.values())
            total_classes = sum(data["total"] for data in subject_attendance.values())
            overall_percentage = (total_present / total_classes * 100) if total_classes > 0 else 0

            summary = {
                "studentId": student.studentId,
                "name": student.name,
                "branch": student.branch,
                "semester": student.semester,
                "specialization": student.specialization,
                "subjects": subject_attendance,
                "overallPercentage": overall_percentage,
                "totalClasses": total_classes,
                "totalPresent": total_present
            }
            print(f"Student {student.studentId} summary: {summary}")
            student_summaries.append(summary)

        return student_summaries
    except Exception as e:
        print(f"Error getting student attendance summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/branches")
def get_branches(db: Session = Depends(get_db)):
    """Get all unique branches from the student table"""
    branches = db.query(Student.branch).distinct().all()
    return [branch[0] for branch in branches if branch[0]]  # Filter out None values

@app.get("/students/{student_id}/assignments/{assignment_id}/status")
def get_assignment_status(student_id: int, assignment_id: int, db: Session = Depends(get_db)):
    try:
        # Check if student has submitted this assignment
        submission = db.query(Submission).filter(
            Submission.student_id == student_id,
            Submission.assignment_id == assignment_id
        ).first()
        
        if submission:
            return {"status": submission.status}
        return {"status": None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/faculty/{faculty_id}/graph-data")
def get_faculty_graph_data(faculty_id: int, db: Session = Depends(get_db)):
    try:
        # Get last 7 days
        days = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)][::-1]
        
        # Get daily submission counts
        submission_data = []
        for day in days:
            count = db.query(func.count(Submission.id))\
                .join(Assignment, Assignment.id == Submission.assignment_id)\
                .filter(Assignment.faculty_id == faculty_id)\
                .filter(func.date(Submission.submitted_at) == day)\
                .scalar() or 0
            submission_data.append({"date": day, "count": count})
            
        # Get daily attendance counts
        attendance_data = []
        for day in days:
            count = db.query(func.count(Attendance.attendance_id))\
                .filter(Attendance.date == day)\
                .scalar() or 0
            attendance_data.append({"date": day, "count": count})
            
        return {
            "submissions": submission_data,
            "attendance": attendance_data
        }
    except Exception as e:
        print(f"Error in faculty graph data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/graph-data")
def get_admin_graph_data(
    branch: str = Query(None),
    semester: int = Query(None),
    specialization: str = Query(None),
    db: Session = Depends(get_db)
):
    try:
        # Get all branches first
        all_branches = db.query(Student.branch).distinct().all()
        all_branches = [b[0] for b in all_branches]

        # Base query for students
        student_query = db.query(Student.branch, func.count(Student.studentId).label('count'))
        
        # Apply filters if provided
        if branch:
            student_query = student_query.filter(Student.branch == branch)
        if semester:
            student_query = student_query.filter(Student.semester == semester)
        if specialization and specialization != 'all':
            student_query = student_query.filter(Student.specialization == specialization)
            
        students_by_branch = student_query.group_by(Student.branch).all()
        students_by_branch = [{"branch": b, "count": c} for b, c in students_by_branch]

        # Faculty data
        faculty_by_dept = db.query(
            Faculty.department,
            func.count(Faculty.id).label('count')
        ).group_by(Faculty.department).all()
        faculty_by_dept = [{"department": d, "count": c} for d, c in faculty_by_dept]

        # Assignments data with filters
        assignment_query = db.query(
            Assignment.subject,
            func.count(Assignment.id).label('count')
        )
        if branch:
            assignment_query = assignment_query.filter(Assignment.branch == branch)
        if semester:
            assignment_query = assignment_query.filter(Assignment.semester == semester)
        if specialization and specialization != 'all':
            assignment_query = assignment_query.filter(Assignment.specialization == specialization)
            
        assignments_by_subject = assignment_query.group_by(Assignment.subject).all()
        assignments_by_subject = [{"subject": s, "count": c} for s, c in assignments_by_subject]

        # Initialize attendance data for all branches
        attendance_by_branch = {b: {"present": 0, "total": 0} for b in all_branches}

        # Get all students and their attendance
        student_filter = []
        if branch:
            student_filter.append(Student.branch == branch)
        if semester:
            student_filter.append(Student.semester == semester)
        if specialization and specialization != 'all':
            student_filter.append(Student.specialization == specialization)

        students = db.query(Student).filter(*student_filter).all()
        
        for student in students:
            attendance_records = db.query(Attendance).filter(
                Attendance.studentId == student.studentId
            ).all()
            
            if attendance_records:
                present_count = sum(1 for record in attendance_records if record.attendance == 'P')
                total_count = len(attendance_records)
                
                if student.branch in attendance_by_branch:
                    attendance_by_branch[student.branch]["present"] += present_count
                    attendance_by_branch[student.branch]["total"] += total_count

        # Calculate percentages
        attendance_data = []
        for branch, counts in attendance_by_branch.items():
            percentage = 0
            if counts["total"] > 0:
                percentage = (counts["present"] / counts["total"]) * 100
            attendance_data.append({
                "branch": branch,
                "percentage": round(percentage, 2)
            })

        return {
            "studentsByBranch": students_by_branch,
            "facultyByDepartment": faculty_by_dept,
            "assignmentsBySubject": assignments_by_subject,
            "attendanceByBranch": attendance_data
        }

    except Exception as e:
        print(f"Error in get_admin_graph_data: {str(e)}")  # Add logging
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/graph-data/assignments")
def get_admin_assignment_data(
    branch: str = Query(None),
    semester: int = Query(None),
    specialization: str = Query(None),
    db: Session = Depends(get_db)
):
    try:
        # Assignments data with filters
        assignment_query = db.query(
            Assignment.subject,
            func.count(Assignment.id).label('count')
        )
        if branch:
            assignment_query = assignment_query.filter(Assignment.branch == branch)
        if semester:
            assignment_query = assignment_query.filter(Assignment.semester == semester)
        if specialization and specialization != 'all':
            assignment_query = assignment_query.filter(Assignment.specialization == specialization)
            
        assignments_by_subject = assignment_query.group_by(Assignment.subject).all()
        assignments_by_subject = [{"subject": s, "count": c} for s, c in assignments_by_subject]

        return {
            "assignmentsBySubject": assignments_by_subject
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/graph-data/attendance")
def get_admin_attendance_data(
    branch: str = Query(None),
    semester: int = Query(None),
    specialization: str = Query(None),
    db: Session = Depends(get_db)
):
    try:
        # Attendance data with filters
        attendance_data = []
        if branch or semester or (specialization and specialization != 'all'):
            # Get filtered students
            student_filter = []
            if branch:
                student_filter.append(Student.branch == branch)
            if semester:
                student_filter.append(Student.semester == semester)
            if specialization and specialization != 'all':
                student_filter.append(Student.specialization == specialization)
                
            students = db.query(Student).filter(*student_filter).all()
            
            for student in students:
                # Get attendance for each student
                attendance_records = db.query(Attendance).filter(
                    Attendance.studentId == student.studentId
                ).all()
                
                if attendance_records:
                    present_count = sum(1 for record in attendance_records if record.attendance == 'P')
                    total_count = len(attendance_records)
                    percentage = (present_count / total_count * 100) if total_count > 0 else 0
                    
                    # Add to branch statistics
                    branch_entry = next(
                        (item for item in attendance_data if item["branch"] == student.branch),
                        None
                    )
                    if branch_entry:
                        branch_entry["total_percentage"] += percentage
                        branch_entry["student_count"] += 1
                    else:
                        attendance_data.append({
                            "branch": student.branch,
                            "total_percentage": percentage,
                            "student_count": 1
                        })

            # Calculate average percentage for each branch
            attendance_by_branch = [
                {
                    "branch": item["branch"],
                    "percentage": round(item["total_percentage"] / item["student_count"], 2) if item["student_count"] > 0 else 0
                }
                for item in attendance_data
            ]
        else:
            # If no filters, get overall attendance by branch
            attendance_by_branch = db.query(
                Student.branch,
                func.avg(
                    func.case(
                        (Attendance.attendance == 'P', 100),
                        else_=0
                    )
                ).label('percentage')
            ).join(
                Attendance,
                Student.studentId == Attendance.studentId,
                isouter=True
            ).group_by(Student.branch).all()
            
            attendance_by_branch = [
                {"branch": branch, "percentage": round(float(percentage), 2) if percentage is not None else 0}
                for branch, percentage in attendance_by_branch
            ]

        return {
            "attendanceByBranch": attendance_by_branch
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test-db")
def test_database(db: Session = Depends(get_db)):
    try:
        # Test student table
        student_count = db.query(func.count(Student.studentId)).scalar()
        
        # Test faculty table
        faculty_count = db.query(func.count(Faculty.id)).scalar()
        
        # Test assignment table
        assignment_count = db.query(func.count(Assignment.id)).scalar()
        
        # Test attendance table
        attendance_count = db.query(func.count(Attendance.attendance_id)).scalar()
        
        return {
            "status": "success",
            "tables": {
                "student": student_count,
                "faculty": faculty_count,
                "assignment": assignment_count,
                "attendance": attendance_count
            }
        }
    except Exception as e:
        print(f"Database test error: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

@app.get("/test/attendance-data")
def test_attendance_data(db: Session = Depends(get_db)):
    try:
        # Test 1: Check if we can get any students
        students = db.query(Student).limit(5).all()
        student_count = len(students)
        
        # Test 2: Check if we can get any attendance records
        attendance = db.query(Attendance).limit(5).all()
        attendance_count = len(attendance)
        
        # Test 3: Try a simple join
        joined_data = db.query(Student, Attendance).\
            join(Attendance, Student.studentId == Attendance.studentId).\
            limit(5).all()
        joined_count = len(joined_data)
        
        # Test 4: Get unique branches
        branches = db.query(Student.branch).distinct().all()
        branch_list = [str(b[0]) for b in branches]
        
        return {
            "status": "success",
            "diagnostics": {
                "student_sample_count": student_count,
                "attendance_sample_count": attendance_count,
                "joined_sample_count": joined_count,
                "branches_found": branch_list,
                "database_connected": True
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "diagnostics": {
                "database_connected": False
            }
        }

@app.get("/test/branch-data")
def test_branch_data(db: Session = Depends(get_db)):
    try:
        # Test 1: Get all unique branches
        branches = db.query(Student.branch).distinct().filter(Student.branch.isnot(None)).all()
        branch_list = [str(b[0]) for b in branches]

        # Test 2: Sample data for first branch (if exists)
        sample_data = {}
        if branch_list:
            test_branch = branch_list[0]
            
            # Get student count
            student_count = db.query(Student).\
                filter(Student.branch == test_branch).\
                count()

            # Get assignment count
            assignment_count = db.query(Assignment).\
                join(Student, Student.studentId == Assignment.studentId).\
                filter(Student.branch == test_branch).\
                count()

            # Get attendance data
            attendance_data = db.query(
                func.count(Attendance.attendance_id).label('total'),
                func.sum(case([(Attendance.attendance == 'P', 1)], else_=0)).label('present')
            ).\
            join(Student, Student.studentId == Attendance.studentId).\
            filter(Student.branch == test_branch).\
            first()

            sample_data = {
                "test_branch": test_branch,
                "student_count": student_count,
                "assignment_count": assignment_count,
                "total_attendance": attendance_data.total or 0,
                "present_attendance": attendance_data.present or 0
            }

        return {
            "status": "success",
            "diagnostics": {
                "all_branches": branch_list,
                "branch_count": len(branch_list),
                "sample_data": sample_data,
                "database_connected": True
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "diagnostics": {
                "database_connected": False
            }
        }

@app.get("/test/branch-counts")
def test_branch_counts(db: Session = Depends(get_db)):
    try:
        # Get all branches
        branches = db.query(Student.branch).distinct().filter(Student.branch.isnot(None)).all()
        branch_list = [str(b[0]) for b in branches]

        # Test data for each branch
        branch_data = {}
        for branch in branch_list:
            # Get assignment count
            assignment_count = db.query(Assignment).\
                join(Student, Student.studentId == Assignment.studentId).\
                filter(Student.branch == branch).\
                count()

            # Get attendance count
            attendance_count = db.query(Attendance).\
                join(Student, Student.studentId == Attendance.studentId).\
                filter(Student.branch == branch).\
                count()

            # Get student count
            student_count = db.query(Student).\
                filter(Student.branch == branch).\
                count()

            branch_data[branch] = {
                "students": student_count,
                "assignments": assignment_count,
                "attendance_records": attendance_count
            }

        return {
            "status": "success",
            "diagnostics": {
                "branches_found": branch_list,
                "branch_counts": branch_data,
                "database_connected": True
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "diagnostics": {
                "database_connected": False
            }
        }

@app.post("/notifications")
async def create_notification(notification: NotificationCreate, db: Session = Depends(get_db)):
    try:
        # Calculate recipients count based on target audience
        recipients_count = 0
        if notification.target_audience == 'all':
            # Count all users
            recipients_count = db.query(User).count()
        else:
            # Count users with matching specialization
            recipients_count = db.query(Student).filter(
                Student.specialization == notification.target_audience
            ).count()

        new_notification = Notification(
            title=notification.title,
            message=notification.message,
            type=notification.type,
            target_audience=notification.target_audience,
            priority=notification.priority,
            status=notification.status,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            sent_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S") if notification.status == "sent" else None,
            recipients_count=recipients_count
        )
        
        db.add(new_notification)
        db.commit()
        db.refresh(new_notification)
        
        return {"success": True, "message": "Notification created successfully", "notification": new_notification}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/notifications")
async def get_notifications(type: Optional[str] = None, user_id: Optional[int] = None, db: Session = Depends(get_db)):
    try:
        query = db.query(Notification)
        
        # If type is specified and not 'all', filter by type
        if type and type != "all":
            query = query.filter(Notification.type == type)
            
        # If user_id is provided, get user's role and specialization
        if user_id:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                # If user not found, return empty list
                return {"success": True, "notifications": []}
                
            # For students, only show notifications targeted to their specialization or 'all'
            if user.role == 'student':
                student = db.query(Student).filter(Student.email == user.email).first()
                if student:
                    query = query.filter(
                        or_(
                            Notification.target_audience == 'all',
                            Notification.target_audience == student.specialization
                        )
                    )
            # For faculty, show all notifications
            elif user.role == 'faculty':
                pass  # No additional filters needed
            # For admin, show all notifications
            elif user.role == 'admin':
                pass  # No additional filters needed
        
        notifications = query.order_by(Notification.created_at.desc()).all()
        return {"success": True, "notifications": notifications}
    except Exception as e:
        print(f"Error in get_notifications: {str(e)}")  # Add logging
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/notifications/{notification_id}")
async def delete_notification(notification_id: int, db: Session = Depends(get_db)):
    try:
        # First, delete all related read_notifications records
        db.query(ReadNotification).filter(
            ReadNotification.notification_id == notification_id
        ).delete()

        # Then delete the notification itself
        notification = db.query(Notification).filter(Notification.id == notification_id).first()
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        db.delete(notification)
        db.commit()
        return {"success": True, "message": "Notification deleted successfully"}
    except Exception as e:
        db.rollback()
        print(f"Error deleting notification: {str(e)}")  # Add logging
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/notifications/{notification_id}")
async def update_notification(notification_id: int, notification: NotificationCreate, db: Session = Depends(get_db)):
    try:
        db_notification = db.query(Notification).filter(Notification.id == notification_id).first()
        if not db_notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        # If target audience is changing, recalculate recipients count
        if notification.target_audience != db_notification.target_audience:
            if notification.target_audience == 'all':
                # Count all users
                recipients_count = db.query(User).count()
            else:
                # Count users with matching specialization
                recipients_count = db.query(Student).filter(
                    Student.specialization == notification.target_audience
                ).count()
            notification.recipients_count = recipients_count
        
        for key, value in notification.dict().items():
            setattr(db_notification, key, value)
        
        db.commit()
        return {"message": "Notification updated successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: int, request: NotificationReadRequest, db: Session = Depends(get_db)):
    try:
        # Check if notification exists
        notification = db.query(Notification).filter(Notification.id == notification_id).first()
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        # Check if already read
        existing_read = db.query(ReadNotification).filter(
            ReadNotification.notification_id == notification_id,
            ReadNotification.user_id == request.user_id
        ).first()
        
        if existing_read:
            return {"message": "Notification already marked as read"}
        
        # Create new read record
        read_notification = ReadNotification(
            notification_id=notification_id,
            user_id=request.user_id,
            read_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        db.add(read_notification)
        db.commit()
        
        return {"message": "Notification marked as read"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/notifications/read-status/{user_id}")
async def get_read_notifications(user_id: int, db: Session = Depends(get_db)):
    try:
        read_notifications = db.query(ReadNotification.notification_id).filter(
            ReadNotification.user_id == user_id
        ).all()
        read_ids = [n.notification_id for n in read_notifications]
        return {"read_notifications": read_ids}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        try:
            await websocket.accept()
            self.active_connections.append(websocket)
            print(f"New WebSocket connection. Total connections: {len(self.active_connections)}")
        except Exception as e:
            print(f"Error accepting WebSocket connection: {str(e)}")
            raise

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(f"WebSocket disconnected. Remaining connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        print(f"Broadcasting message to {len(self.active_connections)} connections:", message)
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error broadcasting to connection: {str(e)}")
                disconnected.append(connection)
        
        # Clean up disconnected connections
        for conn in disconnected:
            if conn in self.active_connections:
                self.active_connections.remove(conn)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    try:
        await manager.connect(websocket)
        print("WebSocket connected successfully")
        
        while True:
            try:
                data = await websocket.receive_text()
                print("Received WebSocket message:", data)
            except WebSocketDisconnect:
                manager.disconnect(websocket)
                break
            except Exception as e:
                print(f"Error in WebSocket communication: {str(e)}")
                manager.disconnect(websocket)
                break
    except Exception as e:
        print(f"WebSocket connection error: {str(e)}")
        if websocket in manager.active_connections:
            manager.disconnect(websocket)

# Add TemporaryAttendance model
class TemporaryAttendance(Base):
    __tablename__ = "temporary_attendance"
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("student.studentId"), nullable=False)
    subject = Column(String(255), nullable=False)
    date = Column(Date, nullable=False)
    scan_timestamp = Column(String(50), nullable=False)
    class_type = Column(String(50), nullable=False)  # Add class type field

# Update the QR scan endpoint to use SQLAlchemy
@app.post("/attendance/qr-scans")
async def process_qr_scan(request: Request, db: Session = Depends(get_db)):
    try:
        # Get the raw request body
        body = await request.json()
        print("Received QR scan request:", body)
        
        # Extract QR data and student ID
        qr_data_str = body.get("qrData")
        student_id = body.get("studentId")
        
        if not qr_data_str:
            raise HTTPException(status_code=400, detail="QR data not provided")
            
        # Parse QR data
        try:
            qr_data = json.loads(qr_data_str)
            print("Parsed QR data:", qr_data)
        except json.JSONDecodeError as e:
            print("Error parsing QR data:", str(e))
            raise HTTPException(status_code=400, detail="Invalid QR data format")

        # Validate required fields
        required_fields = ["subject", "branch", "semester", "date", "type", "timestamp"]
        missing_fields = [field for field in required_fields if field not in qr_data]
        if missing_fields:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required fields in QR data: {', '.join(missing_fields)}"
            )
            
        # Check for duplicate scan
        existing_scan = db.query(TemporaryAttendance).filter(
            TemporaryAttendance.student_id == student_id,
            TemporaryAttendance.subject == qr_data["subject"],
            TemporaryAttendance.date == qr_data["date"]
        ).first()
        
        if existing_scan:
            raise HTTPException(status_code=400, detail="Attendance already marked for this class")
            
        # Create new temporary attendance record
        new_scan = TemporaryAttendance(
            student_id=student_id,
            subject=qr_data["subject"],
            date=qr_data["date"],
            scan_timestamp=datetime.now().isoformat(),
            class_type=qr_data["type"]  # Add class type
        )
        db.add(new_scan)

        # Get student details
        student = db.query(Student).filter(Student.studentId == student_id).first()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")

        db.commit()
        
        # Broadcast the scan via WebSocket
        await manager.broadcast({
            "type": "qr_scan",
            "data": {
                "studentId": student_id,
                "subject": qr_data["subject"],
                "date": qr_data["date"],
                "name": student.name,
                "registration_number": student.registration_number,
                "class_type": qr_data["type"]  # Add class type
            }
        })

        return {
            "message": "Attendance recorded successfully",
            "newScans": [{
                "studentId": student_id,
                "name": student.name,
                "registration_number": student.registration_number
            }]
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        db.rollback()
        print("Error processing QR scan:", str(e))
        raise HTTPException(status_code=500, detail="Failed to process QR scan")

# Add endpoint to finalize attendance
@app.post("/attendance/finalize")
async def finalize_attendance(request: Request, db: Session = Depends(get_db)):
    try:
        # Get request data
        data = await request.json()
        subject = data.get("subject")
        date = data.get("date")
        class_type = data.get("type")  # Get class type from request
        attendance_data = data.get("attendanceData", [])

        if not subject or not date or not class_type:
            raise HTTPException(status_code=400, detail="Subject, date, and class type are required")

        # Get temporary attendance records
        temp_records = db.query(TemporaryAttendance).filter(
            TemporaryAttendance.subject == subject,
            TemporaryAttendance.date == date
        ).all()
        
        # Create a set of student IDs who scanned QR codes
        scanned_students = {temp.student_id for temp in temp_records}

        # Process all students from the form submission
        for record in attendance_data:
            student_id = record.get("studentId")
            # If student scanned QR code, they should be marked present regardless of checkbox
            status = "P" if student_id in scanned_students else record.get("status", "A")

            # Check if attendance record exists
            existing_record = db.query(Attendance).filter(
                Attendance.studentId == student_id,
                Attendance.subject_code == subject,
                Attendance.date == date
            ).first()

            if existing_record:
                existing_record.attendance = status
                existing_record.class_type = class_type  # Update class type
            else:
                new_attendance = Attendance(
                    studentId=student_id,
                    subject_code=subject,
                    date=date,
                    attendance=status,
                    class_type=class_type  # Add class type
                )
                db.add(new_attendance)

        # Clear temporary attendance records
        db.query(TemporaryAttendance).filter(
            TemporaryAttendance.subject == subject,
            TemporaryAttendance.date == date
        ).delete()

        db.commit()
        return {"message": "Attendance finalized successfully"}

    except Exception as e:
        db.rollback()
        print("Error finalizing attendance:", str(e))
        raise HTTPException(status_code=500, detail=str(e))
