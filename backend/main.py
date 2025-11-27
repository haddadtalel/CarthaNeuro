from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import tensorflow as tf
from tensorflow.keras.applications.efficientnet import preprocess_input
import numpy as np
from PIL import Image
import io
import json
import os
from datetime import datetime

app = FastAPI(title="Alzheimer Detection API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load model and class names
def load_model_safely():
    """Load model with compatibility handling"""
    try:
        # Try loading the .keras format first
        model = tf.keras.models.load_model('alzheimer_model.keras', compile=False)
        print("✅ Model loaded successfully from .keras format!")
    except Exception as e:
        print(f"❌ Error loading .keras model: {e}")
        try:
            # Fall back to .h5 format
            model = tf.keras.models.load_model('alzheimer_model.h5', compile=False)
            print("✅ Model loaded successfully from .h5 format!")
        except Exception as e2:
            print(f"❌ Error loading .h5 model: {e2}")
            raise e2
    
    # Recompile the model with the original settings
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )
    return model

try:
    model = load_model_safely()
    with open('class_names.json', 'r') as f:
        CLASS_NAMES = json.load(f)
    print(f"✅ Available classes: {CLASS_NAMES}")
    print("✅ Model and class names loaded successfully!")
except Exception as e:
    print(f"❌ Error loading model: {e}")
    raise e

def preprocess_image(image: Image.Image) -> np.ndarray:
    """
    Preprocess image for model prediction
    """
    # Resize image to match model input size
    image = image.resize((224, 224))
    # Convert to array
    image_array = np.array(image)
    # Ensure 3 channels (convert RGBA to RGB if needed)
    if image_array.shape[-1] == 4:
        image_array = image_array[:, :, :3]
    elif len(image_array.shape) == 2:  # Grayscale
        image_array = np.stack([image_array] * 3, axis=-1)
    # Add batch dimension and preprocess
    image_array = np.expand_dims(image_array, axis=0)
    image_array = preprocess_input(image_array.astype(np.float32))
    return image_array

@app.get("/")
async def root():
    return {
        "message": "Alzheimer Detection API", 
        "status": "active",
        "model_loaded": True,
        "available_classes": CLASS_NAMES
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "model": "EfficientNetB0",
        "input_size": "224x224",
        "classes": len(CLASS_NAMES)
    }

@app.get("/class-names")
async def get_class_names():
    return {"class_names": CLASS_NAMES}

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    """
    Predict Alzheimer stage from MRI image
    """
    # Validate file type
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        # Read image file
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert('RGB')
        
        # Preprocess image
        processed_image = preprocess_image(image)
        
        # Make prediction
        predictions = model.predict(processed_image, verbose=0)
        predicted_class_idx = np.argmax(predictions[0])
        confidence = float(predictions[0][predicted_class_idx])
        
        # Get class name
        predicted_class = CLASS_NAMES[predicted_class_idx]
        
        # Get all probabilities
        all_probabilities = {
            CLASS_NAMES[i]: float(prob) for i, prob in enumerate(predictions[0])
        }
        
        return JSONResponse({
            "predicted_class": predicted_class,
            "confidence": confidence,
            "all_probabilities": all_probabilities,
            "predicted_class_index": int(predicted_class_idx),
            "timestamp": datetime.now().isoformat(),
            "file_name": file.filename
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

@app.post("/predict-batch")
async def predict_batch(files: list[UploadFile] = File(...)):
    """
    Predict multiple images at once
    """
    results = []
    
    for file in files:
        if not file.content_type.startswith('image/'):
            results.append({
                "filename": file.filename,
                "error": "File must be an image"
            })
            continue
            
        try:
            contents = await file.read()
            image = Image.open(io.BytesIO(contents)).convert('RGB')
            processed_image = preprocess_image(image)
            
            predictions = model.predict(processed_image, verbose=0)
            predicted_class_idx = np.argmax(predictions[0])
            confidence = float(predictions[0][predicted_class_idx])
            predicted_class = CLASS_NAMES[predicted_class_idx]
            
            results.append({
                "filename": file.filename,
                "predicted_class": predicted_class,
                "confidence": confidence,
                "predicted_class_index": int(predicted_class_idx),
                "all_probabilities": {
                    CLASS_NAMES[i]: float(prob) for i, prob in enumerate(predictions[0])
                }
            })
            
        except Exception as e:
            results.append({
                "filename": file.filename,
                "error": str(e)
            })
    
    return {"results": results}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)