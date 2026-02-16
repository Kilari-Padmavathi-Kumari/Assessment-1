from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
from datetime import datetime

app = FastAPI()

# -------------------------
# Database Connection
# -------------------------
def connect():
    return psycopg2.connect(
        host="localhost",
        database="test_db",
        user="postgres",
        password="localhost"
    )

# -------------------------
# Models
# -------------------------
class Student(BaseModel):
    name: str
    email: str


class Course(BaseModel):
    title: str
    description: str


class Enrollment(BaseModel):
    student_id: int
    course_id: int


# -------------------------
# 1️⃣ Create Student
# -------------------------
@app.post("/students")
def create_student(student: Student):

    conn = connect()
    cur = conn.cursor()   # used to execute sql query

    try:
        cur.execute(
    "INSERT INTO students (name, email) VALUES (%s, %s) RETURNING id;",
    (student.name, student.email)
)

        new_id = cur.fetchone()[0]
        conn.commit()
    except Exception as e:
     print("Error:", e)
     raise HTTPException(status_code=400, detail=str(e))


    finally:
        cur.close()
        conn.close()

    return {"id": new_id, "name": student.name, "email": student.email}


# -------------------------
# 2️⃣ Create Course
# -------------------------
@app.post("/courses")
def create_course(course: Course):

    conn = connect()
    cur = conn.cursor()

    cur.execute(
    "INSERT INTO courses (title, description) VALUES (%s, %s) RETURNING id;",
    (course.title, course.description)
)


    new_id = cur.fetchone()[0]
    conn.commit()

    cur.close()
    conn.close()

    return {"id": new_id, "title": course.title}


# -------------------------
# 3️⃣ Enroll Student
# -------------------------
@app.post("/enrollments")
def enroll_student(data: Enrollment):

    conn = connect()
    cur = conn.cursor()

    # Check student exists
    cur.execute("SELECT id FROM students WHERE id=%s;", (data.student_id,))
    if not cur.fetchone():
        raise HTTPException(status_code=404, detail="Student not found")

    # Check course exists
    cur.execute("SELECT id FROM courses WHERE id=%s;", (data.course_id,))
    if not cur.fetchone():
        raise HTTPException(status_code=404, detail="Course not found")

    # Insert enrollment
    try:
        cur.execute(
            "INSERT INTO enrollments (student_id, course_id, enrolled_at) VALUES (%s, %s, %s);",
            (data.student_id, data.course_id, datetime.now())
        )
        conn.commit()
    except:
        raise HTTPException(status_code=400, detail="Already enrolled")

    finally:
        cur.close()
        conn.close()

    return {"message": "Enrolled successfully"}


# -------------------------
# 4️⃣ Get Student with Courses
# -------------------------
@app.get("/students/{student_id}")
def get_student(student_id: int):

    conn = connect()
    cur = conn.cursor()

    # Get student
    cur.execute("SELECT id, name, email FROM students WHERE id=%s;", (student_id,))
    student = cur.fetchone()

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Get courses
    cur.execute("""
        SELECT c.id, c.title
        FROM enrollments e
        JOIN courses c ON e.course_id = c.id
        WHERE e.student_id=%s;
    """, (student_id,))

    course_data = cur.fetchall()

    courses = []
    for c in course_data:
        courses.append({
            "id": c[0],
            "title": c[1]
        })

    cur.close()
    conn.close()

    return {
        "id": student[0],
        "name": student[1],
        "email": student[2],
        "courses": courses
    }
