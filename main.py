import os
from dotenv import load_dotenv
#uvicorn main:app --reload
from fastapi import FastAPI, HTTPException, Depends, Query, Path
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import enum
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

load_dotenv()  # This loads the variables from .env

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class RoleEnum(str, enum.Enum):
    student = "student"
    admin = "admin"

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
    studentId: str
    name: str
    email: str
    registration_number: str
    semester: str
    branch: str
    specialization: str
    starting_year: str
    passout_year: str

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

class Syllabus(Base):
    __tablename__ = "syllabus"
    id = Column(Integer, primary_key=True, autoincrement=True)
    subject = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False)
    semester = Column(Integer, nullable=False)
    branch = Column(String(100), nullable=False)
    credits = Column(Integer, nullable=False)
    faculty = Column(String(100), nullable=False)
    upload_date = Column(String(20), nullable=False)
    pdf_url = Column(String(255), nullable=True)
    description = Column(String(1000), nullable=True)

class SyllabusBase(BaseModel):
    subject: str
    code: str
    semester: int
    branch: str
    credits: int
    faculty: str
    upload_date: str
    pdf_url: str | None = None
    description: str | None = None

class SyllabusCreate(SyllabusBase):
    pass

class SyllabusUpdate(SyllabusBase):
    pass

class SyllabusOut(SyllabusBase):
    id: int
    class Config:
        orm_mode = True

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(
        User.email == request.email,
        User.password == request.password,
        User.role == request.role
    ).first()
    if not user:
        return LoginResponse(success=False, message="Invalid credentials or role.")
    return LoginResponse(
        success=True,
        user=UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role,
        )
    )

@app.post("/students")
def create_student(student: StudentCreate, db: Session = Depends(get_db)):
    db_student = db.query(Student).filter((Student.studentId == student.studentId) | (Student.email == student.email)).first()
    if db_student:
        raise HTTPException(status_code=400, detail="Student with this ID or email already exists.")
    new_student = Student(
        studentId=student.studentId,
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
            password="cutm123",
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

@app.get("/timetables")
def get_timetables(branch: str = Query(...), semester: int = Query(...), db: Session = Depends(get_db)):
    timetables = db.query(Timetable).filter(Timetable.branch == branch, Timetable.semester == semester).all()
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
def update_student(student_id: int, student: StudentUpdate, db: Session = Depends(get_db)):
    db_student = db.query(Student).filter(Student.studentId == student_id).first()
    if not db_student:
        raise HTTPException(status_code=404, detail="Student not found")
    for key, value in student.dict().items():
        setattr(db_student, key, value)
    db.commit()
    return {"success": True, "message": "Student updated successfully."}

@app.delete("/students/{student_id}")
def delete_student(student_id: int, db: Session = Depends(get_db)):
    db_student = db.query(Student).filter(Student.studentId == student_id).first()
    if not db_student:
        raise HTTPException(status_code=404, detail="Student not found")
    db.delete(db_student)
    db.commit()
    return {"success": True, "message": "Student deleted successfully."}

@app.get("/syllabus", response_model=list[SyllabusOut])
def get_syllabus(db: Session = Depends(get_db)):
    syllabus = db.query(Syllabus).all()
    result = []
    for s in syllabus:
        result.append({
            "id": s.id,
            "subject": s.subject,
            "code": s.code,
            "semester": s.semester,
            "branch": s.branch,
            "credits": s.credits,
            "faculty": s.faculty,
            "upload_date": s.upload_date.isoformat() if hasattr(s.upload_date, 'isoformat') else s.upload_date,
            "pdf_url": s.pdf_url,
            "description": s.description,
        })
    return result

@app.post("/syllabus", response_model=SyllabusOut)
def create_syllabus(entry: SyllabusCreate, db: Session = Depends(get_db)):
    new_entry = Syllabus(**entry.dict())
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)
    return new_entry

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

# To create tables (run once):
# Base.metadata.create_all(bind=engine) 