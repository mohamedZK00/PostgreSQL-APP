import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import pickle
from pydantic import BaseModel
import psycopg2

# تحميل المتغيرات البيئية
load_dotenv()

app = FastAPI()

# تحميل النموذج
working_dir = os.path.dirname(os.path.realpath(__file__))
model_path = os.path.join(working_dir, 'MLPRegressor_grade')

with open(model_path, 'rb') as f:
    model = pickle.load(f)

# إعداد CORS
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
    try:
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL is not set in the environment.")
        
        conn = psycopg2.connect(database_url)
        return conn
    except psycopg2.Error as e:
        print(f"Database connection error: {e}")
        return None

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
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css">
        <title>Student Grade Prediction</title>
        <style>
            body, html {
                height: 100%;
                margin: 0;
                font-family: Arial, sans-serif;
                background-image: url('https://img.freepik.com/free-photo/schoolgirl-with-notebook-her-hands-sunset-background-school-goes-school_169016-57817.jpg?w=1380&t=st=1728160456~exp=1728161056~hmac=626fc8cfc661e660633d4e06d5a25ded225d31ca86b428630a453b4112062a14');
                background-size: cover;
                background-position: center;
                background-repeat: no-repeat;
                background-attachment: fixed;
            }
            .card {
                border-radius: 15px;
                background-color: rgba(255, 255, 255, 0.8);
                padding: 20px;
                margin-top: 100px;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            }
            h1 {
                color: #333;
            }
            .btn-primary {
                background-color: #ff5722;
                border: none;
            }
            .rocket {
                font-size: 50px;
                color: #ffcc00;
                animation: rocket-animation 1s infinite;
            }
            @keyframes rocket-animation {
                0% { transform: translateY(0); }
                100% { transform: translateY(-10px); }
            }
            #result {
                transition: all 0.3s ease;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="card p-4">
                <h1 class="text-center mb-4"><i class="fas fa-graduation-cap"></i> Student Grade Prediction</h1>
                <form id="gradeForm">
                    <div class="form-group">
                        <label for="grade1">Grade_month 1</label>
                        <input type="number" class="form-control" id="grade1" required>
                    </div>
                    <div class="form-group">
                        <label for="grade2">Grade_month 2</label>
                        <input type="number" class="form-control" id="grade2" required>
                    </div>
                    <div class="form-group">
                        <label for="grade3">Grade_month 3</label>
                        <input type="number" class="form-control" id="grade3" required>
                    </div>
                    <button type="submit" class="btn btn-primary btn-block">Predict <i class="fas fa-paper-plane"></i></button>
                </form>
                <div id="result" class="mt-4"></div>
            </div>
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
                        url: 'http://localhost:8000/predict',
                        method: 'POST',
                        contentType: 'application/json',
                        data: JSON.stringify({
                            grade_1: parseInt(grade1),
                            grade_2: parseInt(grade2),
                            grade_3: parseInt(grade3)
                        }),
                        success: function(response) {
                            const predictedGrade = response.predicted_grade;
                            let message = '';
                            let icons = '';

                            if (predictedGrade >= 90) {
                                message = '🎉 Excellent Job! Keep it up!';
                                icons = '<div class="rocket">🚀 🚀 🚀</div>';
                            } else if (predictedGrade >= 75) {
                                message = '😊 Good Job! You are doing well!';
                                icons = '<div class="rocket">🎈 🎈 🎈</div>';
                            } else if (predictedGrade >= 60) {
                                message = '👍 Not bad! A little more effort!';
                                icons = '<div class="rocket">🌟 🌟 🌟</div>';
                            } else {
                                message = '😞 Don’t worry! You can improve!';
                                icons = '<div class="rocket">💔 💔 💔</div>';
                            }

                            $('#result').html(`
                                <div class="alert alert-success fade show">
                                    ${message} <br>
                                    ${icons} <br>
                                    Predicted value: ${predictedGrade}
                                </div>
                            `);
                        },
                        error: function(xhr) {
                            $('#result').html(`<div class="alert alert-danger fade show">Error occurred: ${xhr.responseJSON.error}</div>`);
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

        return {"message": "Student added successfully", 'predicted_grade': round(predictions[0], 2)}

    except psycopg2.Error as e:
        print(f"Prediction error: {e}")
        return {"error": "Failed to predict"}
