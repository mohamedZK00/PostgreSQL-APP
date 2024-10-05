import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pickle
from pydantic import BaseModel

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

@app.post('/predict')
def prediction(input_data: GradeInput):
    try:
        # Prepare data for prediction
        data = [[input_data.grade_1, input_data.grade_2, input_data.grade_3]]
        predictions = model.predict(data)

        # Return predicted grade
        print('Predicted Grade:', round(predictions[0], 2))
        return {"message": "Prediction successful", 'predicted_grade': round(predictions[0], 2)}

    except Exception as e:
        print(f"Prediction error: {e}")
        return {"error": "Failed to make prediction"}
