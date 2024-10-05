import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
import pickle
from pydantic import BaseModel
import psycopg2

load_dotenv()  # تحميل المتغيرات من .env

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
        database_url = os.environ.get("DATABASE_URL")
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

@app.get("/", response_class=HTMLResponse)
def read_root():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
        <title>Student Grade Prediction</title>
    </head>
    <body>
        <div class="container mt-5">
            <h1 class="text-center">Student Grade Prediction</h1>
            <form id="gradeForm">
                <div class="form-group">
                    <label for="grade1">Grade Month 1:</label>
                    <input type="number" class="form-control" id="grade1" required>
                </div>
                <div class="form-group">
                    <label for="grade2">Grade Month 2:</label>
                    <input type="number" class="form-control" id="grade2" required>
                </div>
                <div class="form-group">
                    <label for="grade3">Grade Month 3:</label>
                    <input type="number" class="form-control" id="grade3" required>
                </div>
                <button type="submit" class="btn btn-primary">Predict</button>
            </form>
            <div id="result" class="mt-3"></div>
        </div>

        <script src="https://code.jquery.com/jquery-3.5.1.min.js"></script>
        <script>
            $(document).ready(function() {
                $('#gradeForm').on('submit', function(event) {
                    event.preventDefault();
                    const grade1 = $('#grade1').val();
                    const grade2 = $('#grade2').val();
                    const grade3 = $('#grade3').val();

                    $.ajax({
                        url: '/predict',
                        method: 'POST',
                        contentType: 'application/json',
                        data: JSON.stringify({
                            grade_1: parseInt(grade1),
                            grade_2: parseInt(grade2),
                            grade_3: parseInt(grade3)
                        }),
                        success: function(response) {
                            const predictedGrade = response.predicted_grade;
                            $('#result').html(`<div class="alert alert-success">Predicted Grade: ${predictedGrade}</div>`);
                        },
                        error: function(xhr) {
                            $('#result').html(`<div class="alert alert-danger">Error: ${xhr.responseJSON.error}</div>`);
                        }
                    });
                });
            });
        </script>
    </body>
    </html>
    """

@app.post('/predict')
def prediction(input_data: GradeInput):
    try:
        conn = get_db_connection()
        if conn is None:
            return {"error": "Connection to PostgreSQL failed during prediction"}

        cursor = conn.cursor()
        data = [[input_data.grade_1, input_data.grade_2, input_data.grade_3]]
        predictions = model.predict(data)

        cursor.execute(
            "INSERT INTO students_grade_2 (grade_month_1, grade_month_2, grade_month_3, predictions) VALUES (%s, %s, %s, %s)",
            (input_data.grade_1, input_data.grade_2, input_data.grade_3, float(round(predictions[0], 2)))
        )
        conn.commit()

        cursor.close()
        conn.close()

        print('Predicted Grade:', round(predictions[0], 2))
        return {"message": "Student added successfully", 'predicted_grade': round(predictions[0], 2)}

    except psycopg2.Error as e:
        print(f"Prediction error: {e}")
        return {"error": "Failed to add predictions to PostgreSQL"}
