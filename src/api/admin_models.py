"""
Admin API endpoints for model management and MongoDB cloud integration
"""
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import time
import asyncio

from src.services.enhanced_model_service import get_enhanced_model_service
from src.auth.auth_middleware import get_user_id_from_token, get_admin_user, get_current_user
from src.auth.auth_service import UserResponse
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# Create router
admin_router = APIRouter()

# Request/Response Models
class PushModelRequest(BaseModel):
    """Request model for pushing model to MongoDB cloud"""
    model_name: str = Field(..., description="Name of the model to push")
    user_id: str = Field(..., description="Original model owner user ID")
    push_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional push metadata")
    confirm: bool = Field(default=False, description="Confirm the push operation")

class PushModelResponse(BaseModel):
    """Response model for model push operation"""
    success: bool
    message: str
    model_name: str
    model_id: Optional[str] = None
    push_date: Optional[str] = None
    files_included: Optional[int] = None
    total_size_bytes: Optional[int] = None
    error: Optional[str] = None
    timestamp: float

class AutoSavedModelsResponse(BaseModel):
    """Response model for auto-saved models list"""
    success: bool
    models: List[Dict[str, Any]]
    total: int
    timestamp: float

class ModelCleanupResponse(BaseModel):
    """Response model for cleanup operation"""
    success: bool
    message: str
    cleaned_count: int
    timestamp: float

# Admin endpoints
@admin_router.get("/models/auto-saved", response_model=AutoSavedModelsResponse)
async def get_auto_saved_models(
    current_user: UserResponse = Depends(get_admin_user)
):
    """
    Get list of all auto-saved models (admin only)
    """
    try:
        # Check if user is admin (already done by get_admin_user dependency)
        
        enhanced_service = get_enhanced_model_service()
        auto_saved_models = enhanced_service.get_auto_saved_models()
        
        return AutoSavedModelsResponse(
            success=True,
            models=auto_saved_models,
            total=len(auto_saved_models),
            timestamp=time.time()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get auto-saved models: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve auto-saved models: {str(e)}")

@admin_router.post("/models/push-to-cloud", response_model=PushModelResponse)
async def push_model_to_cloud(
    request: PushModelRequest,
    background_tasks: BackgroundTasks,
    current_user: UserResponse = Depends(get_admin_user)
):
    """
    Push an auto-saved model to MongoDB cloud storage (admin only)
    """
    try:
        # Get current user ID from the authenticated user
        current_user_id = current_user.user_id
        
        # Require confirmation for push operation
        if not request.confirm:
            raise HTTPException(
                status_code=400, 
                detail="Push operation requires confirmation. Set confirm=true to proceed."
            )
        
        enhanced_service = get_enhanced_model_service()
        
        # Push model to MongoDB cloud
        push_result = await enhanced_service.push_model_to_mongodb_cloud(
            model_name=request.model_name,
            user_id=request.user_id,
            admin_user_id=current_user_id,
            push_metadata=request.push_metadata
        )
        
        if push_result["success"]:
            return PushModelResponse(
                success=True,
                message=push_result["message"],
                model_name=request.model_name,
                model_id=push_result.get("model_id"),
                push_date=push_result.get("push_date"),
                files_included=push_result.get("files_included"),
                total_size_bytes=push_result.get("total_size_bytes"),
                timestamp=time.time()
            )
        else:
            return PushModelResponse(
                success=False,
                message="Failed to push model to cloud",
                model_name=request.model_name,
                error=push_result.get("error"),
                timestamp=time.time()
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to push model {request.model_name} to cloud: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to push model to cloud: {str(e)}")

@admin_router.delete("/models/cleanup-auto-saved", response_model=ModelCleanupResponse)
async def cleanup_auto_saved_models(
    current_user: UserResponse = Depends(get_admin_user)
):
    """
    Clean up all auto-saved models (admin only - typically called before server shutdown)
    """
    try:
        # Admin check already done by get_admin_user dependency
        
        enhanced_service = get_enhanced_model_service()
        cleaned_count = await enhanced_service.cleanup_auto_saved_models()
        
        return ModelCleanupResponse(
            success=True,
            message=f"Successfully cleaned up {cleaned_count} auto-saved models",
            cleaned_count=cleaned_count,
            timestamp=time.time()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cleanup auto-saved models: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to cleanup models: {str(e)}")

@admin_router.get("/models/summary")
async def get_models_summary(
    current_user: UserResponse = Depends(get_admin_user)
):
    """
    Get summary of all models (auto-saved, regular saved, MongoDB) - admin only
    """
    try:
        # Admin check already done by get_admin_user dependency
        
        enhanced_service = get_enhanced_model_service()
        
        # Get auto-saved models
        auto_saved_models = enhanced_service.get_auto_saved_models()
        
        # Get regular saved models (from models directory)
        import os
        from pathlib import Path
        
        regular_models = []
        models_dir = Path("models") / "keras_models"
        if models_dir.exists():
            for model_dir in models_dir.iterdir():
                if model_dir.is_dir():
                    regular_models.append({
                        "model_name": model_dir.name,
                        "path": str(model_dir),
                        "type": "regular_save"
                    })
        
        summary = {
            "auto_saved_models": {
                "count": len(auto_saved_models),
                "models": auto_saved_models
            },
            "regular_saved_models": {
                "count": len(regular_models),
                "models": regular_models
            },
            "total_models": len(auto_saved_models) + len(regular_models)
        }
        
        return {
            "success": True,
            "summary": summary,
            "timestamp": time.time()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get models summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get models summary: {str(e)}")

@admin_router.get("/health")
async def admin_health_check(
    current_user: UserResponse = Depends(get_admin_user)
):
    """
    Admin health check endpoint
    """
    try:
        # Admin check already done by get_admin_user dependency
        
        enhanced_service = get_enhanced_model_service()
        auto_saved_count = len(enhanced_service.get_auto_saved_models())
        
        return {
            "success": True,
            "status": "healthy",
            "auto_saved_models_count": auto_saved_count,
            "service_status": "operational",
            "timestamp": time.time()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Admin health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")