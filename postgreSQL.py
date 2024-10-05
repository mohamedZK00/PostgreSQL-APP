import os
import pickle
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

# Load the model
working_dir = os.path.dirname(os.path.realpath(__file__))
model_path = os.path.join(working_dir, 'MLPRegressor_grade')

with open(model_path, 'rb') as f:
    model = pickle.load(f)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GradeInput(BaseModel):
    grade_1: int
    grade_2: int
    grade_3: int

def get_db_connection():
    """Establish a connection to the PostgreSQL database."""
    try:
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL is not set in the environment.")
        
        conn = psycopg2.connect(database_url)
        return conn
    except psycopg2.Error as e:
        print(f"Database connection error: {e}")
        raise HTTPException(status_code=500, detail="Database connection error")

def db_create():
    """Create the students_grade_2 table in the PostgreSQL database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students_grade_2 (
            id SERIAL PRIMARY KEY,
            grade_month_1 INTEGER NOT NULL,
            grade_month_2 INTEGER NOT NULL,
            grade_month_3 INTEGER NOT NULL,
            predictions FLOAT 
        )
    ''')
    conn.commit()
    cursor.close()
    conn.close()

db_create()

@app.get("/", response_class=HTMLResponse)
def read_root():
    """Return the main HTML file."""
    return FileResponse("16.html")

@app.post('/predict')
def prediction(input_data: GradeInput):
    """Predict the student's grade based on input data and store it in the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    data = [[input_data.grade_1, input_data.grade_2, input_data.grade_3]]
    predictions = model.predict(data)

    try:
        cursor.execute(
            "INSERT INTO students_grade_2 (grade_month_1, grade_month_2, grade_month_3, predictions) VALUES (%s, %s, %s, %s)",
            (input_data.grade_1, input_data.grade_2, input_data.grade_3, float(round(predictions[0], 2)))
        )
        conn.commit()
        return {"message": "Student added successfully", 'predicted_grade': float(round(predictions[0], 2))}
    except psycopg2.Error as e:
        print(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail="Prediction failed")
    finally:
        cursor.close()
        conn.close()
