from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from routes import auth, users, predictions, models, datasets, admin
from database import init_db, get_db
import os
from datetime import datetime

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    
    # Import and load local models into database
    db = get_db()
    models_dir = "/home/fawzi/Desktop/CNNN/backend/models"
    if os.path.exists(models_dir):
        model_files = [f for f in os.listdir(models_dir) if f.endswith('.pth') or f.endswith('.h5')]
        loaded_count = 0
        for model_file in model_files:
            # Extract model ID from filename (UUID format)
            model_id = model_file.replace('.pth', '').replace('.h5', '')
            
            # Check if model already exists in database
            existing = await db.models.find_one({"_id": model_id})
            if not existing:
                # Create model record in database
                model_record = {
                    "_id": model_id,
                    "name": f"Imported Model ({model_id[:8]})",
                    "model_type": "efficientnet" if model_file.endswith('.pth') else "tensorflow",
                    "status": "completed",
                    "config": {},
                    "is_production": False,
                    "created_at": datetime.utcnow(),
                    "trained_by": "system",
                    "training_progress": 100,
                    "model_path": os.path.join(models_dir, model_file)
                }
                await db.models.insert_one(model_record)
                loaded_count += 1
                print(f"Loaded model into database: {model_file}")
            else:
                print(f"Model already in database: {model_file}")
        
        if model_files:
            print(f"Loaded {loaded_count} new local models (total: {len(model_files)})")
        else:
            print("No local model files found.")
    else:
        print(f"Models directory not found: {models_dir}")
    
    # Log production model
    production_model = await db.models.find_one({"is_production": True})
    if production_model:
        print(f"Production model set: {production_model.get('name', 'Unknown')}")
    else:
        print("No production model set.")
    
    yield
    # Shutdown
    pass

app = FastAPI(title="Alzheimer's Prediction API", lifespan=lifespan)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(predictions.router, prefix="/api/predictions", tags=["predictions"])
app.include_router(models.router, prefix="/api/models", tags=["models"])
app.include_router(datasets.router, prefix="/api/datasets", tags=["datasets"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])

@app.get("/")
async def root():
    return {
        "message": "Alzheimer's Prediction API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "auth": "/api/auth",
            "users": "/api/users",
            "predictions": "/api/predictions",
            "models": "/api/models",
            "datasets": "/api/datasets",
            "admin": "/api/admin"
        }
    }

@app.get("/api")
async def api_root():
    return {"message": "Alzheimer's Prediction API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
