import os
import pickle
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.responses import FileResponse
from pydantic import BaseModel
import psycopg2
from dotenv import load_dotenv

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
    """تأسيس اتصال بقاعدة بيانات PostgreSQL."""
    try:
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL غير مضبوطة في البيئة.")
        
        conn = psycopg2.connect(database_url)
        return conn
    except psycopg2.Error as e:
        print(f"خطأ في الاتصال بقاعدة البيانات: {e}")
        raise HTTPException(status_code=500, detail="خطأ في الاتصال بقاعدة البيانات")

def db_create():
    """إنشاء جدول students_grade_2 في قاعدة بيانات PostgreSQL."""
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
    """إرجاع ملف HTML الرئيسي."""
    return FileResponse("index.html")

@app.post('/predict')
def prediction(input_data: GradeInput):
    """يتوقع درجة الطالب بناءً على بيانات الإدخال ويخزنها في قاعدة البيانات."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    data = [[input_data.grade_1, input_data.grade_2, input_data.grade_3]]
    predictions = model.predict(data)

    try:
        cursor.execute(
            "INSERT INTO students_grade_2 (grade_month_1, grade_month_2, grade_month_3, predictions) VALUES (%s, %s, %s, %s)",
            (input_data.grade_1, input_data.grade_2, input_data.grade_3, float(predictions[0]))
        )
        conn.commit()
        return {"message": "تم إضافة الطالب بنجاح", 'predicted_grade': float(predictions[0])}
    except psycopg2.Error as e:
        print(f"خطأ في التوقع: {e}")
        raise HTTPException(status_code=500, detail="فشل في التوقع")
    finally:
        cursor.close()
        conn.close()
