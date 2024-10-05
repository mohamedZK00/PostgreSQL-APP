import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pickle
from pydantic import BaseModel
import psycopg2

app = FastAPI()

# Load model
working_dir = os.path.dirname(os.path.realpath(__file__))
model_path = os.path.join(working_dir, 'MLPRegressor_grade')

with open(model_path, 'rb') as f:
    model = pickle.load(f)

# لتشغيل ال API علي انترنت بدون حدوث اي مشاكل
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,  # يسمح بالوصول الي اي مصدر 
    allow_methods=["*"],
    allow_headers=["*"],
)

class GradeInput(BaseModel):
    grade_1: int
    grade_2: int
    grade_3: int

# Connect to PostgreSQL Database
def get_db_connection():
    try:
        # استخدم DATABASE_URL مباشرة
        database_url = os.environ.get("DATABASE_URl")
        conn = psycopg2.connect(database_url)
        return conn
    except psycopg2.Error as e:
        print(e)
        return None

# Create the table if not exists
def db_create():
    try:
        conn = get_db_connection()
        if conn is None:
            return {"error": "Connection to PostgreSQL failed_1"}

        cursor = conn.cursor()
        cursor.execute(''' 
            CREATE TABLE IF NOT EXISTS students_grades (
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
    except psycopg2.Error as e:
        print(e)
        return {"error": "Failed to create table in PostgreSQL"}

db_create()

@app.post('/predict')
def prediction(input_data: GradeInput):
    try:
        conn = get_db_connection()
        if conn is None:
            return {"error": "Connection to PostgreSQL failed_2"}

        cursor = conn.cursor()
        
        # Prepare data for prediction
        data = [[input_data.grade_1, input_data.grade_2, input_data.grade_3]]
        predictions = model.predict(data)
        
        # Insert data into the PostgreSQL table
        cursor.execute("INSERT INTO students_grades (grade_month_1, grade_month_2, grade_month_3, predictions) VALUES (%s, %s, %s, %s)",
                       (input_data.grade_1, input_data.grade_2, input_data.grade_3, round(predictions[0], 2)))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        print('Predicted Grade:', round(predictions[0], 2))
        return {"message": "Student added successfully", 'predicted_grade': round(predictions[0], 2)}
    
    except psycopg2.Error as e:
        print(e)
        return {"error": "Failed to add predictions to PostgreSQL"}
