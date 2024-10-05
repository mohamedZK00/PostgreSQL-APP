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

# Middleware for CORS
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

# Connect to PostgreSQL Database
def get_db_connection():
    try:
        # استخدم DATABASE_URL من متغيرات البيئة
        database_url = os.environ.get("DATABASE_URl")  # تأكد من أن هذا المتغير موجود في بيئة Railway
        if not database_url:
            raise ValueError("DATABASE_URL is not set in the environment.")
        
        conn = psycopg2.connect(database_url)
        return conn
    except psycopg2.Error as e:
        print(f"Database connection error: {e}")
        return None

# Create the table if it does not exist
def db_create():
    try:
        conn = get_db_connection()
        if conn is None:
            return {"error": "Connection to PostgreSQL failed during table creation"}

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
    except psycopg2.Error as e:
        print(f"Table creation error: {e}")
        return {"error": "Failed to create table in PostgreSQL"}

# Create table when the app starts
db_create()

@app.post('/predict')
def prediction(input_data: GradeInput):
    try:
        conn = get_db_connection()
        if conn is None:
            return {"error": "Connection to PostgreSQL failed during prediction"}

        cursor = conn.cursor()

        # Prepare data for prediction
        data = [[input_data.grade_1, input_data.grade_2, input_data.grade_3]]
        predictions = model.predict(data)

        # Insert data into the PostgreSQL table
        cursor.execute(
            "INSERT INTO students_grade_2 (grade_month_1, grade_month_2, grade_month_3, predictions) VALUES (%s, %s, %s, %s)",
            (input_data.grade_1, input_data.grade_2, input_data.grade_3, round(predictions[0], 2))
        )
        conn.commit()

        cursor.close()
        conn.close()

        print('Predicted Grade:', round(predictions[0], 2))
        return {"message": "Student added successfully", 'predicted_grade': round(predictions[0], 2)}

    except psycopg2.Error as e:
        print(f"Prediction error: {e}")
        return {"error": "Failed to add predictions to PostgreSQL"}
        
