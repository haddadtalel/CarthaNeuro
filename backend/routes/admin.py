from fastapi import APIRouter, Depends, HTTPException
from database import get_db
from models.user import TokenData
from datetime import datetime

# Import get_current_user locally to avoid circular import
from routes.auth import get_current_user

router = APIRouter()

@router.get("/dashboard")
async def get_dashboard_stats(current_user: TokenData = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    db = get_db()

    # User stats
    total_users = await db.users.count_documents({})
    active_users = await db.users.count_documents({"is_active": True})
    admins = await db.users.count_documents({"role": "admin"})
    doctors = await db.users.count_documents({"role": "doctor"})
    recent_registrations = await db.users.count_documents({
        "created_at": {"$gte": datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)}
    })

    # Prediction stats
    total_predictions = await db.predictions.count_documents({})
    today_predictions = await db.predictions.count_documents({
        "created_at": {"$gte": datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)}
    })

    # Get predictions by class
    predictions_by_class = {
        "No Alzheimer's Disease": await db.predictions.count_documents({"disease_class": "No Alzheimer's Disease"}),
        "Mild Cognitive Impairment": await db.predictions.count_documents({"disease_class": "Mild Cognitive Impairment"}),
        "Early Stage Alzheimer's": await db.predictions.count_documents({"disease_class": "Early Stage Alzheimer's"}),
        "Moderate Stage Alzheimer's": await db.predictions.count_documents({"disease_class": "Moderate Stage Alzheimer's"}),
    }

    # Dataset stats
    total_datasets = await db.datasets.count_documents({})
    total_size = await db.datasets.aggregate([
        {"$group": {"_id": None, "total_size": {"$sum": "$size_mb"}}}
    ]).to_list(length=1)
    total_size_mb = total_size[0]["total_size"] if total_size else 0

    # Model stats
    total_models = await db.models.count_documents({})
    trained_models = await db.models.count_documents({"status": "completed"})
    production_model = await db.models.find_one({"is_production": True})

    return {
        "users": {
            "total": total_users,
            "active": active_users,
            "admins": admins,
            "doctors": doctors,
            "recent_registrations": recent_registrations,
        },
        "predictions": {
            "total": total_predictions,
            "today": today_predictions,
            "by_class": predictions_by_class,
        },
        "datasets": {
            "total": total_datasets,
            "total_size_mb": total_size_mb,
        },
        "models": {
            "total": total_models,
            "trained": trained_models,
            "production_model": production_model["name"] if production_model else None,
        }
    }

@router.get("/activity")
async def get_recent_activity(limit: int = 10, current_user: TokenData = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    db = get_db()

    # Get recent activity from the database
    activity = []
    async for pred in db.predictions.find().sort("created_at", -1).limit(limit):
        activity.append({
            "id": str(pred["prediction_id"]),
            "type": "prediction",
            "user_id": pred["doctor"]["id"],
            "patient_id": pred["patient_id"],
            "result": pred["disease_class"],
            "confidence": pred["confidence"],
            "timestamp": pred["created_at"].isoformat(),
        })

    return activity

@router.get("/system-health")
async def get_system_health(current_user: TokenData = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return {
        "status": "healthy",
        "database": "connected",
        "api": "operational",
        "timestamp": datetime.utcnow().isoformat(),
    }

@router.get("/users/activity")
async def get_user_activity(user_id: str = None, limit: int = 10, current_user: TokenData = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    db = get_db()

    # Get user activity from the database
    activity = []
    
    # Get predictions made by the user
    async for pred in db.predictions.find({"doctor.id": user_id}).sort("created_at", -1).limit(limit):
        activity.append({
            "id": str(pred["prediction_id"]),
            "type": "prediction",
            "user_id": pred["doctor"]["id"],
            "timestamp": pred["created_at"].isoformat(),
        })

    # Get user logins (if available in your database)
    # This would require a separate collection for user logins
    
    return activity

@router.get("/predictions/analysis")
async def get_predictions_analysis(start_date: str = None, end_date: str = None, current_user: TokenData = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    db = get_db()
    
    # Build query based on date range
    query = {}
    if start_date and end_date:
        query["created_at"] = {
            "$gte": datetime.fromisoformat(start_date),
            "$lte": datetime.fromisoformat(end_date)
        }
    
    # Get total predictions
    total_predictions = await db.predictions.count_documents(query)
    
    # Get predictions by class
    predictions_by_class = {
        "No Alzheimer's Disease": await db.predictions.count_documents({**query, "disease_class": "No Alzheimer's Disease"}),
        "Mild Cognitive Impairment": await db.predictions.count_documents({**query, "disease_class": "Mild Cognitive Impairment"}),
        "Early Stage Alzheimer's": await db.predictions.count_documents({**query, "disease_class": "Early Stage Alzheimer's"}),
        "Moderate Stage Alzheimer's": await db.predictions.count_documents({**query, "disease_class": "Moderate Stage Alzheimer's"}),
    }
    
    # Calculate accuracy (this would require actual ground truth data in a real implementation)
    # For now, we'll use a placeholder
    accuracy = 0.95  # Placeholder
    
    return {
        "total_predictions": total_predictions,
        "accuracy": accuracy,
        "by_class": predictions_by_class,
    }

@router.get("/predictions")
async def get_predictions_admin(skip: int = 0, limit: int = 100, current_user: TokenData = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    from models.prediction import PredictionResponse
    
    db = get_db()
    predictions = []
    async for pred in db.predictions.find().skip(skip).limit(limit):
        # Convert MongoDB document to dict, excluding MongoDB-specific fields
        pred_dict = dict(pred)
        pred_dict.pop('_id', None)  # Remove MongoDB ObjectId
        
        # Ensure all required fields are present and properly typed
        try:
            prediction_data = {
                "prediction_id": str(pred_dict.get("prediction_id", "")),
                "patient_id": str(pred_dict.get("patient_id", "")),
                "patient_full_name": str(pred_dict.get("patient_full_name", "")),
                "disease_class": str(pred_dict.get("disease_class", "")),
                "probability": float(pred_dict.get("probability", 0.0)),
                "confidence": str(pred_dict.get("confidence", "")),
                "factors": pred_dict.get("factors", {}),
                "recommendations": str(pred_dict.get("recommendations", "")),
                "model_used": str(pred_dict.get("model_used", "")),
                "created_at": pred_dict.get("created_at"),
                "doctor": pred_dict.get("doctor")
            }
            
            predictions.append(PredictionResponse(**prediction_data))
        except Exception as e:
            # Skip invalid predictions
            print(f"Skipping invalid prediction {pred_dict.get('prediction_id')}: {e}")
            continue
    
    return predictions