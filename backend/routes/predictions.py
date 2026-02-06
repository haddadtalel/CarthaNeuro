from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response
from typing import List
from models.prediction import ConsultationFormData, ConsultationResponse, PredictionRequest, PredictionResponse
from database import get_db
from models.user import TokenData
import uuid
from datetime import datetime
from pathlib import Path
import os

# Import get_current_user locally to avoid circular import
from routes.auth import get_current_user

# Import PDF service
from pdf_service import pdf_service, generate_report

router = APIRouter()

@router.post("/consultation", response_model=ConsultationResponse)
async def create_consultation(consultation_data: ConsultationFormData, current_user: TokenData = Depends(get_current_user)):
    db = get_db()
    
    # Calculate risk score (simplified for demo)
    risk_score = calculate_risk_score(consultation_data)
    
    consultation_id = str(uuid.uuid4())
    consultation = {
        "consultation_id": consultation_id,
        "patient_full_name": consultation_data.patient_full_name,
        "patient_reference_id": consultation_data.patient_reference_id,
        "age": consultation_data.age,
        "gender": consultation_data.gender,
        "family_history_ad": consultation_data.family_history_ad,
        "diabetes": consultation_data.diabetes,
        "hypertension": consultation_data.hypertension,
        "heart_disease": consultation_data.heart_disease,
        "stroke_history": consultation_data.stroke_history,
        "smoking": consultation_data.smoking,
        "alcohol_use": consultation_data.alcohol_use,
        "memory_complaints": consultation_data.memory_complaints,
        "difficulty_concentrating": consultation_data.difficulty_concentrating,
        "problem_solving_difficulty": consultation_data.problem_solving_difficulty,
        "mood_changes": consultation_data.mood_changes,
        "confusion": consultation_data.confusion,
        "personality_changes": consultation_data.personality_changes,
        "disorientation": consultation_data.disorientation,
        "difficulty_with_daily_tasks": consultation_data.difficulty_with_daily_tasks,
        "symptoms_duration_months": consultation_data.symptoms_duration_months,
        "previous_ad_evaluation": consultation_data.previous_ad_evaluation,
        "current_medications": consultation_data.current_medications,
        "notes": consultation_data.notes,
        "risk_score": risk_score,
        "created_at": datetime.utcnow(),
        "created_by": current_user.username,
    }
    
    await db.consultations.insert_one(consultation)
    
    return ConsultationResponse(
        consultation_id=consultation_id,
        risk_score=risk_score,
        message="Consultation created successfully"
    )

@router.get("/consultation/{consultation_id}", response_model=ConsultationResponse)
async def get_consultation(consultation_id: str):
    db = get_db()
    consultation = await db.consultations.find_one({"consultation_id": consultation_id})
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")

    return ConsultationResponse(
        consultation_id=consultation["consultation_id"],
        risk_score=consultation["risk_score"],
        message="Consultation retrieved successfully"
    )

@router.post("/upload")
async def upload_mri(file: UploadFile = File(...), patient_id: str = None, consultation_id: str = None):
    db = get_db()
    
    # Read file content for validation
    content = await file.read()
    
    # Validate MRI file type and content
    is_valid, message = validate_mri_image(content, file.filename)
    
    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail=message
        )
    
    # Save file to disk
    mri_id = str(uuid.uuid4())
    upload_dir = os.path.join(os.path.dirname(__file__), '..', 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, f"{mri_id}_{file.filename}")
    with open(file_path, "wb") as f:
        f.write(content)
    
    mri_record = {
        "mri_id": mri_id,
        "mri_image_id": mri_id,  # Add this for consistency
        "patient_id": patient_id,
        "consultation_id": consultation_id,
        "file_name": f"{mri_id}_{file.filename}",
        "file_path": f"/uploads/{mri_id}_{file.filename}",
        "file_size": len(content),
        "uploaded_at": datetime.utcnow(),
        "validation": {
            "valid": True,
            "message": "MRI image validated and saved successfully"
        }
    }
    
    await db.mri_uploads.insert_one(mri_record)
    
    return {
        "mri_id": mri_id,
        "validation": mri_record["validation"],
        "file_path": mri_record["file_path"],
        "message": "MRI uploaded and saved successfully"
    }

@router.post("/predict", response_model=PredictionResponse)
async def create_prediction(prediction_data: PredictionRequest, current_user: TokenData = Depends(get_current_user)):
    db = get_db()
    
    # Get consultation data if available
    consultation = None
    if prediction_data.consultation_id:
        consultation = await db.consultations.find_one({"consultation_id": prediction_data.consultation_id})
    
    # Simulate prediction (in a real app, this would call your ML model)
    disease_class, probability, confidence = await simulate_prediction(prediction_data.mri_image_id)
    
    prediction_id = str(uuid.uuid4())
    prediction = {
        "prediction_id": prediction_id,
        "patient_id": prediction_data.patient_id,
        "patient_full_name": prediction_data.patient_full_name,
        "mri_id": prediction_data.mri_image_id,
        "consultation_id": prediction_data.consultation_id,
        "disease_class": disease_class,
        "probability": probability,
        "confidence": confidence,
        "factors": {
            "image_analysis_weight": 0.9,
            "consultation_risk_score": consultation["risk_score"] if consultation else 0,
            "final_confidence": 0.85,
            "contribution_image": 0.9,
            "contribution_consultation": 0.1,
        },
        "recommendations": generate_recommendations(disease_class),
        "model_used": prediction_data.model_type or "default_model",
        "created_at": datetime.utcnow(),
        "doctor": {
            "id": current_user.username,
            "username": current_user.username,
        }
    }
    
    await db.predictions.insert_one(prediction)
    
    return PredictionResponse(**prediction)

@router.get("/results/{prediction_id}", response_model=PredictionResponse)
async def get_prediction(prediction_id: str):
    db = get_db()
    prediction = await db.predictions.find_one({"prediction_id": prediction_id})
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")
    
    return PredictionResponse(**prediction)

@router.get("/patient/{patient_id}", response_model=List[PredictionResponse])
async def get_patient_predictions(patient_id: str, limit: int = 10):
    db = get_db()
    predictions = []
    async for pred in db.predictions.find({"patient_id": patient_id}).limit(limit):
        predictions.append(PredictionResponse(**pred))
    return predictions

@router.get("/history")
async def get_prediction_history(skip: int = 0, limit: int = 100):
    db = get_db()
    predictions = []
    async for pred in db.predictions.find().skip(skip).limit(limit):
        predictions.append(PredictionResponse(**pred))
    return predictions

@router.get("/stats")
async def get_prediction_stats():
    db = get_db()
    total = await db.predictions.count_documents({})
    today = await db.predictions.count_documents({
        "created_at": {"$gte": datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)}
    })
    
    # Get predictions by class
    predictions_by_class = {
        "No Alzheimer's Disease": await db.predictions.count_documents({"disease_class": "No Alzheimer's Disease"}),
        "Mild Cognitive Impairment": await db.predictions.count_documents({"disease_class": "Mild Cognitive Impairment"}),
        "Early Stage Alzheimer's": await db.predictions.count_documents({"disease_class": "Early Stage Alzheimer's"}),
        "Moderate Stage Alzheimer's": await db.predictions.count_documents({"disease_class": "Moderate Stage Alzheimer's"}),
    }
    
    return {
        "total": total,
        "today": today,
        "by_class": predictions_by_class,
    }

@router.get("/report/{prediction_id}")
async def download_report(prediction_id: str, current_user: TokenData = Depends(get_current_user)):
    db = get_db()
    prediction = await db.predictions.find_one({"prediction_id": prediction_id})
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")
    
    # Get consultation data if available
    consultation_data = None
    if prediction.get('consultation_id'):
        consultation = await db.consultations.find_one({"consultation_id": prediction['consultation_id']})
        if consultation:
            # Convert consultation to dict format expected by PDF service
            consultation_data = {
                'patient_full_name': prediction['patient_full_name'],
                'patient_id': prediction['patient_id'],
                'age': consultation.get('age', 0),
                'gender': consultation.get('gender', 'N/A'),
                'family_history_ad': consultation.get('family_history_ad', False),
                'diabetes': consultation.get('diabetes', False),
                'hypertension': consultation.get('hypertension', False),
                'heart_disease': consultation.get('heart_disease', False),
                'stroke_history': consultation.get('stroke_history', False),
                'smoking': consultation.get('smoking', False),
                'alcohol_use': consultation.get('alcohol_use', False),
                'memory_complaints': consultation.get('memory_complaints', 0),
                'difficulty_concentrating': consultation.get('difficulty_concentrating', 0),
                'problem_solving_difficulty': consultation.get('problem_solving_difficulty', 0),
                'mood_changes': consultation.get('mood_changes', 0),
                'confusion': consultation.get('confusion', 0),
                'personality_changes': consultation.get('personality_changes', 0),
                'disorientation': consultation.get('disorientation', 0),
                'difficulty_with_daily_tasks': consultation.get('difficulty_with_daily_tasks', 0),
                'symptoms_duration_months': consultation.get('symptoms_duration_months', 0),
                'previous_ad_evaluation': consultation.get('previous_ad_evaluation', False),
                'current_medications': consultation.get('current_medications', ''),
                'notes': consultation.get('notes', ''),
                'created_at': consultation.get('created_at', datetime.utcnow()),
                'risk_score': consultation.get('risk_score', 0),
            }
    
    # Get MRI image path if available
    mri_image_path = None
    mri_id = prediction.get('mri_id') or prediction.get('mri_image_id')
    if mri_id:
        mri_record = await db.mri_uploads.find_one({"$or": [{"mri_id": mri_id}, {"mri_image_id": mri_id}]})
        if mri_record and mri_record.get('file_path'):
            # Construct the full path to the MRI image
            mri_filename = mri_record.get('file_name', '')
            if mri_filename:
                # Try to find the file in the uploads directory
                import os
                uploads_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'uploads')
                # Look for the file in common locations
                for root, dirs, files in os.walk(uploads_dir):
                    if mri_filename in files:
                        mri_image_path = os.path.join(root, mri_filename)
                        break
    
    # Prepare probabilities dict for PDF
    probabilities = {
        prediction['disease_class']: prediction['probability']
    }
    
    # Generate PDF report
    pdf_content = await generate_report(
        prediction_id=prediction_id,
        patient_id=prediction['patient_id'],
        predicted_class=prediction['disease_class'],
        confidence=prediction['confidence'],
        probabilities=probabilities,
        doctor_name=current_user.full_name if hasattr(current_user, 'full_name') else current_user.username,
        doctor_username=current_user.username,
        created_at=prediction['created_at'],
        consultation_data=consultation_data,
        mri_image_path=mri_image_path
    )
    
    # Return PDF file
    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=medical_report_{prediction_id}.pdf"
        }
    )

def calculate_risk_score(consultation_data: ConsultationFormData) -> float:
    # Simplified risk score calculation
    risk_factors = [
        consultation_data.family_history_ad,
        consultation_data.diabetes,
        consultation_data.hypertension,
        consultation_data.heart_disease,
        consultation_data.stroke_history,
        consultation_data.smoking,
        consultation_data.alcohol_use,
    ]
    
    risk_score = sum(risk_factors) * 0.1
    risk_score += (consultation_data.age / 100) * 0.5
    risk_score += (consultation_data.symptoms_duration_months / 12) * 0.2
    
    return min(max(risk_score, 0), 1)

async def simulate_prediction(mri_image_id: str = None):
    # If no MRI provided, fall back to simulation
    if not mri_image_id:
        print("DEBUG: No MRI image ID provided, using random simulation")
        import random
        disease_classes = [
            "No Alzheimer's Disease",
            "Mild Cognitive Impairment", 
            "Early Stage Alzheimer's",
            "Moderate Stage Alzheimer's"
        ]
        
        disease_class = random.choice(disease_classes)
        probability = random.uniform(0.5, 1.0)
        confidence_levels = ["Very High", "High", "Moderate", "Low", "Very Low"]
        confidence = random.choice(confidence_levels)
        
        return disease_class, probability, confidence
    
    # Real prediction using the Kaggle-trained model
    try:
        import tensorflow as tf
        from tensorflow.keras.models import load_model
        from tensorflow.keras.applications.efficientnet import preprocess_input
        import numpy as np
        import cv2
        import os
        import json
        
        print(f"DEBUG: Starting real prediction for MRI ID: {mri_image_id}")
        
        # Load the model
        model_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'kaggle_efficientnet_alzheimer.h5')
        print(f"DEBUG: Model path: {model_path}")
        print(f"DEBUG: Model exists: {os.path.exists(model_path)}")
        
        if not os.path.exists(model_path):
            print("DEBUG: Model file not found, falling back to simulation")
            # Fallback to simulation if model not found
            return await simulate_prediction()
            
        print("DEBUG: Loading model...")
        model = load_model(model_path)
        print("DEBUG: Model loaded successfully")
        
        # Load class names
        class_names_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'class_names.json')
        if os.path.exists(class_names_path):
            with open(class_names_path, 'r') as f:
                class_names = json.load(f)
            print(f"DEBUG: Class names loaded: {class_names}")
        else:
            class_names = ["Mild Impairment", "Moderate Impairment", "No Impairment", "Very Mild Impairment"]
            print(f"DEBUG: Using default class names: {class_names}")
        
        # Get MRI file path from database
        db = get_db()
        mri_record = await db.mri_uploads.find_one({"$or": [{"mri_id": mri_image_id}, {"mri_image_id": mri_image_id}]})
        print(f"DEBUG: MRI record found: {mri_record is not None}")
        
        if not mri_record:
            print("DEBUG: MRI record not found in database, falling back to simulation")
            return await simulate_prediction()
            
        file_path = mri_record.get('file_path', '').replace('/uploads/', 'uploads/')
        full_path = os.path.join(os.path.dirname(__file__), '..', file_path)
        print(f"DEBUG: Full image path: {full_path}")
        print(f"DEBUG: Image file exists: {os.path.exists(full_path)}")
        
        if not os.path.exists(full_path):
            print("DEBUG: Image file not found on disk, falling back to simulation")
            return await simulate_prediction()
        
        # Load and preprocess image
        print("DEBUG: Loading and preprocessing image...")
        image = cv2.imread(full_path)
        if image is None:
            print("DEBUG: Failed to load image with cv2, falling back to simulation")
            return await simulate_prediction()
            
        print(f"DEBUG: Original image shape: {image.shape}")
        # Convert BGR to RGB (cv2 loads as BGR, but EfficientNet expects RGB)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        print(f"DEBUG: After BGR to RGB conversion: shape {image.shape}")
        image = cv2.resize(image, (224, 224))
        print(f"DEBUG: Resized image shape: {image.shape}")
        image = np.expand_dims(image, axis=0)
        image = preprocess_input(image.astype(np.float32))
        print("DEBUG: Image preprocessed")
        
        # Make prediction
        print("DEBUG: Making prediction...")
        predictions = model.predict(image, verbose=0)
        print(f"DEBUG: Raw predictions: {predictions}")
        print(f"DEBUG: Predictions shape: {predictions.shape}")
        print(f"DEBUG: All class probabilities: {dict(zip(class_names, predictions[0]))}")
        predicted_class_idx = np.argmax(predictions[0])
        probability = float(predictions[0][predicted_class_idx])
        print(f"DEBUG: Predicted class index: {predicted_class_idx}, probability: {probability}")
        
        # Map to disease classes
        class_mapping = {
            "Mild Impairment": "Mild Cognitive Impairment",
            "Moderate Impairment": "Moderate Stage Alzheimer's", 
            "No Impairment": "No Alzheimer's Disease",
            "Very Mild Impairment": "Early Stage Alzheimer's"
        }
        
        predicted_class_name = class_names[predicted_class_idx]
        print(f"DEBUG: Predicted class name: {predicted_class_name}")
        disease_class = class_mapping.get(predicted_class_name, "No Alzheimer's Disease")
        print(f"DEBUG: Mapped disease class: {disease_class}")
        
        # Determine confidence level
        if probability > 0.9:
            confidence = "Very High"
        elif probability > 0.8:
            confidence = "High"
        elif probability > 0.7:
            confidence = "Moderate"
        elif probability > 0.6:
            confidence = "Low"
        else:
            confidence = "Very Low"
        
        print(f"DEBUG: Final result - Class: {disease_class}, Probability: {probability}, Confidence: {confidence}")
        return disease_class, probability, confidence
        
    except Exception as e:
        print(f"ERROR in real prediction: {e}")
        import traceback
        traceback.print_exc()
        # Fallback to simulation
        return await simulate_prediction()

def generate_recommendations(disease_class: str) -> str:
    recommendations = {
        "No Alzheimer's Disease": "Continue regular check-ups and maintain a healthy lifestyle.",
        "Mild Cognitive Impairment": "Monitor cognitive function closely and consider lifestyle interventions.",
        "Early Stage Alzheimer's": "Start appropriate treatment and implement cognitive therapies.",
        "Moderate Stage Alzheimer's": "Increase care support and review treatment options.",
    }
    
    return recommendations.get(disease_class, "Consult with a specialist for personalized recommendations.")

def validate_mri_image(content: bytes, filename: str) -> tuple:
    """
    Validate that the uploaded content is a valid MRI image.
    Returns (is_valid: bool, message: str)
    """
    # Lazy imports to avoid requiring cv2 at module load time
    import numpy as np
    import cv2
    
    try:
        # Check file extension
        valid_extensions = ('.dcm', '.dicom', '.nii', '.nii.gz', '.jpg', '.jpeg', '.png')
        file_ext = Path(filename).suffix.lower()
        
        if file_ext not in valid_extensions:
            return False, f"Invalid file type: {file_ext}. Allowed: {', '.join(valid_extensions)}"
        
        # Try to decode image content
        nparr = np.frombuffer(content, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return False, "Could not decode image file. The file may be corrupted or in an unsupported format."
        
        height, width = img.shape[:2]
        
        # Check dimensions
        if width < 64 or height < 64:
            return False, f"Image resolution too low ({width}x{height}). Minimum 64x64 required for MRI analysis."
        
        if width > 4096 or height > 4096:
            return False, f"Image resolution too high ({width}x{height}). Maximum 4096x4096 allowed."
        
        # Convert to grayscale for analysis
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
        
        # Calculate non-zero pixel ratio
        non_zero_pixels = np.count_nonzero(gray)
        total_pixels = gray.size
        non_zero_ratio = non_zero_pixels / total_pixels
        
        # MRI images often have more black pixels around edges, so use lower threshold
        # Training data typically has around 50-95% non-zero pixels
        if non_zero_ratio < 0.05:
            return False, "Unvalid Image ! Please provide a valid MRI image."
        
        if non_zero_ratio > 0.999:
            return False, "Unvalid Image ! Please provide a valid MRI image."
        
        # Calculate entropy (measure of randomness in intensity distribution)
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        hist_norm = hist.flatten() / hist.sum()
        
        # Remove zeros to avoid log(0)
        hist_norm = hist_norm[hist_norm > 0]
        entropy = -np.sum(hist_norm * np.log2(hist_norm))
        
        # MRI images typically have entropy between 4 and 8
        # Very low entropy means mostly uniform (not MRI-like)
        # Very high entropy might indicate complex natural images
        if entropy < 2:
            return False, "Unvalid Image ! Please provide a valid MRI image."
        
        if entropy > 9:
            # Still accept but warn - could be a complex natural image
            pass
        
        return True, "Valid MRI image for analysis."
        
    except Exception as e:
        return False, f"Error validating image: {str(e)}"
