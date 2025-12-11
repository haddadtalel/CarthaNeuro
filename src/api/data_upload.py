"""
Data upload routes for CarthaNeuro Backend
Handles training data upload and management
"""

from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, BackgroundTasks, Query, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import time
import io
import shutil
import os
from pathlib import Path
import zipfile
import uuid
from concurrent.futures import ThreadPoolExecutor

from src.utils.logger import setup_logger
from src.config.settings import settings
from src.database.mongodb_service import get_db_operations, DatasetDocument, FileMetadataDocument
from src.auth.auth_middleware import get_user_id_from_token
from bson import ObjectId

logger = setup_logger(__name__)

# Global model manager reference
_model_manager = None

def set_model_manager(manager):
    """Set the global model manager instance"""
    global _model_manager
    _model_manager = manager

def get_model_manager():
    """Dependency injection for model manager"""
    global _model_manager
    if _model_manager is None:
        raise HTTPException(status_code=503, detail="Model manager not initialized")
    return _model_manager

# Create router
data_router = APIRouter()

# Request/Response Models
class UploadResponse(BaseModel):
    """Response model for file upload"""
    success: bool
    message: str
    uploaded_files: List[str]
    total_files: int
    errors: List[str]
    upload_id: str
    timestamp: float

class ValidationResult(BaseModel):
    """Model for validation results"""
    valid_files: List[str]
    invalid_files: List[str]
    file_counts: Dict[str, int]
    total_size: int

class DatasetInfo(BaseModel):
    """Model for dataset information"""
    name: str
    path: str
    total_samples: int
    class_distribution: Dict[str, int]
    last_updated: str
    status: str

@data_router.post("/upload", response_model=UploadResponse)
async def upload_training_data(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(..., description="Training image files"),
    class_label: str = Form(..., description="Class label for the uploaded files"),
    dataset_name: str = Form("custom_dataset", description="Name of the dataset"),
    zip_file: Optional[UploadFile] = File(None, description="Optional zip file containing images"),
    user_id: str = Depends(get_user_id_from_token),
    model_manager: 'ModelManager' = Depends(get_model_manager)
):
    """
    Upload training data files for model training
    
    Args:
        files: List of image files to upload
        class_label: Class label (glioma, meningioma, notumor, pituitary)
        dataset_name: Name for the dataset
        zip_file: Optional zip file containing multiple images
    """
    start_time = time.time()
    upload_id = str(uuid.uuid4())
    
    try:
        logger.info(f"Starting data upload with ID: {upload_id}")
        
        # Validate class label
        valid_classes = settings.class_names
        if class_label not in valid_classes:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid class label. Must be one of: {valid_classes}"
            )
        
        # Create upload directory
        upload_dir = settings.data_dir / "uploads" / upload_id
        class_dir = upload_dir / class_label
        class_dir.mkdir(parents=True, exist_ok=True)
        
        uploaded_files = []
        errors = []
        
        # Handle zip file upload
        if zip_file:
            logger.info("Processing zip file upload")
            zip_result = await _process_zip_upload(zip_file, class_dir, class_label)
            uploaded_files.extend(zip_result.get("files", []))
            errors.extend(zip_result.get("errors", []))
        
        # Handle individual file uploads
        if files:
            logger.info(f"Processing {len(files)} individual files")
            for file in files:
                try:
                    # Validate file type
                    if not file.filename.lower().endswith(('.jpg', '.jpeg', '.png', '.dcm', '.nii')):
                        errors.append(f"Invalid file type: {file.filename}")
                        continue
                    
                    # Generate unique filename
                    file_extension = Path(file.filename).suffix
                    unique_filename = f"{uuid.uuid4().hex}{file_extension}"
                    file_path = class_dir / unique_filename
                    
                    # Save file
                    content = await file.read()
                    with open(file_path, "wb") as buffer:
                        buffer.write(content)
                    
                    uploaded_files.append(unique_filename)
                    logger.debug(f"Uploaded: {file.filename} -> {unique_filename}")
                    
                except Exception as e:
                    error_msg = f"Failed to upload {file.filename}: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)
        
        # Process uploaded files in background
        background_tasks.add_task(_process_uploaded_data, upload_dir, class_label, upload_id)
        
        # Save dataset and file metadata to MongoDB
        try:
            db_operations = get_db_operations()
            
            # Calculate file statistics
            total_size = len(uploaded_files) * 1024  # Approximate size per file
            class_distribution = {class_label: len(uploaded_files)}
            
            # Create dataset document
            dataset_doc = DatasetDocument(
                user_id=ObjectId(user_id),  # Use authenticated user ID
                dataset_name=dataset_name,
                file_count=len(uploaded_files),
                total_size_bytes=total_size,
                class_distribution=class_distribution,
                upload_id=upload_id,
                metadata={"class_label": class_label},
                status="uploaded"
            )
            
            # Save dataset to MongoDB
            dataset_id = await db_operations.create_dataset(dataset_doc)
            logger.info(f"Dataset metadata saved to MongoDB with ID: {dataset_id}")
            
            # Save individual file metadata
            for filename in uploaded_files:
                file_doc = FileMetadataDocument(
                    user_id=ObjectId(user_id),  # Use authenticated user ID
                    upload_id=upload_id,
                    original_filename=filename,
                    file_path=str(class_dir / filename),
                    file_size_bytes=1024,  # Approximate
                    file_type="image",
                    class_label=class_label,
                    metadata={"dataset_id": dataset_id}
                )
                await db_operations.create_file_metadata(file_doc)
                
        except Exception as e:
            logger.error(f"Failed to save metadata to MongoDB: {str(e)}")
            # Don't fail the entire upload if MongoDB save fails
        
        processing_time = time.time() - start_time
        
        return UploadResponse(
            success=True,
            message=f"Successfully uploaded {len(uploaded_files)} files",
            uploaded_files=uploaded_files,
            total_files=len(uploaded_files) + len(errors),
            errors=errors,
            upload_id=upload_id,
            timestamp=time.time()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        return UploadResponse(
            success=False,
            message=f"Upload failed: {str(e)}",
            uploaded_files=[],
            total_files=0,
            errors=[str(e)],
            upload_id=upload_id,
            timestamp=time.time()
        )

@data_router.get("/validate", response_model=ValidationResult)
async def validate_uploaded_data(
    upload_id: str = Query(..., description="Upload ID to validate"),
    model_manager: 'ModelManager' = Depends(get_model_manager)
):
    """
    Validate uploaded training data
    
    Args:
        upload_id: Upload ID from the upload process
    """
    try:
        upload_dir = settings.data_dir / "uploads" / upload_id
        
        if not upload_dir.exists():
            raise HTTPException(status_code=404, detail="Upload not found")
        
        valid_files = []
        invalid_files = []
        file_counts = {}
        total_size = 0
        
        # Scan all class directories
        for class_dir in upload_dir.iterdir():
            if class_dir.is_dir():
                class_name = class_dir.name
                class_files = []
                class_size = 0
                
                # Check image files
                for file_path in class_dir.glob("*"):
                    if file_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.dcm', '.nii']:
                        try:
                            # Try to open and validate the file
                            with open(file_path, 'rb') as f:
                                # Read first few bytes to validate
                                header = f.read(100)
                                if len(header) > 0:
                                    class_files.append(file_path.name)
                                    class_size += file_path.stat().st_size
                                    total_size += file_path.stat().st_size
                                else:
                                    invalid_files.append(f"{class_name}/{file_path.name}")
                        except Exception as e:
                            invalid_files.append(f"{class_name}/{file_path.name}: {str(e)}")
                
                file_counts[class_name] = len(class_files)
                valid_files.extend([f"{class_name}/{f}" for f in class_files])
        
        return ValidationResult(
            valid_files=valid_files,
            invalid_files=invalid_files,
            file_counts=file_counts,
            total_size=total_size
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Validation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")

@data_router.post("/merge", response_model=Dict[str, Any])
async def merge_uploaded_data(
    upload_id: str = Query(..., description="Upload ID to merge"),
    dataset_name: str = Query(..., description="Name for the merged dataset"),
    model_manager: 'ModelManager' = Depends(get_model_manager)
):
    """
    Merge uploaded data into main training dataset
    
    Args:
        upload_id: Upload ID to merge
        dataset_name: Name for the merged dataset
    """
    try:
        upload_dir = settings.data_dir / "uploads" / upload_id
        main_dataset_dir = settings.data_dir / "Tumor" 
        
        if not upload_dir.exists():
            raise HTTPException(status_code=404, detail="Upload not found")
        
        if not main_dataset_dir.exists():
            raise HTTPException(status_code=404, detail="Main dataset not found")
        
        merged_files = []
        
        # Copy files from upload to main dataset
        for class_dir in upload_dir.iterdir():
            if class_dir.is_dir() and class_dir.name in settings.class_names:
                target_class_dir = main_dataset_dir / class_dir.name
                target_class_dir.mkdir(parents=True, exist_ok=True)
                
                # Copy files
                for file_path in class_dir.glob("*"):
                    if file_path.is_file():
                        target_path = target_class_dir / file_path.name
                        shutil.copy2(file_path, target_path)
                        merged_files.append(f"{class_dir.name}/{file_path.name}")
        
        # Clean up upload directory
        shutil.rmtree(upload_dir)
        
        logger.info(f"Merged {len(merged_files)} files from upload {upload_id}")
        
        return {
            "success": True,
            "message": f"Successfully merged {len(merged_files)} files",
            "merged_files": merged_files,
            "dataset_name": dataset_name,
            "timestamp": time.time()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Merge failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Merge failed: {str(e)}")

@data_router.get("/datasets", response_model=List[DatasetInfo])
async def list_datasets(
    model_manager: 'ModelManager' = Depends(get_model_manager)
):
    """List all available datasets"""
    try:
        datasets = []
        
        logger.info(f"Listing datasets from data_dir: {settings.data_dir}")
        
        # Check main dataset
        main_dataset_dir = settings.data_dir / "Tumor"
        if main_dataset_dir.exists():
            dataset_info = await _get_dataset_info(main_dataset_dir, "main_dataset")
            if dataset_info.total_samples > 0:
                datasets.append(dataset_info)
        
        # Check for custom datasets (uploads)
        custom_datasets_dir = settings.data_dir / "uploads"
        if custom_datasets_dir.exists():
            for dataset_dir in custom_datasets_dir.iterdir():
                if dataset_dir.is_dir():
                    dataset_info = await _get_dataset_info(dataset_dir, dataset_dir.name)
                    # Include all uploaded datasets
                    datasets.append(dataset_info)
        
        logger.info(f"Returning {len(datasets)} datasets")
        return datasets
        
    except Exception as e:
        logger.error(f"Failed to list datasets: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list datasets: {str(e)}")

@data_router.delete("/cleanup")
async def cleanup_temp_uploads(
    model_manager: 'ModelManager' = Depends(get_model_manager)
):
    """Clean up temporary upload directories"""
    try:
        uploads_dir = settings.data_dir / "uploads"
        cleaned_count = 0
        
        if uploads_dir.exists():
            for upload_dir in uploads_dir.iterdir():
                if upload_dir.is_dir():
                    # Remove directories older than 24 hours
                    if time.time() - upload_dir.stat().st_mtime > 86400:
                        shutil.rmtree(upload_dir)
                        cleaned_count += 1
        
        return {
            "success": True,
            "message": f"Cleaned up {cleaned_count} temporary upload directories",
            "cleaned_count": cleaned_count,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Cleanup failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")

# Helper functions

async def _process_zip_upload(zip_file: UploadFile, target_dir: Path, class_label: str) -> Dict[str, Any]:
    """Process zip file upload"""
    files = []
    errors = []
    
    try:
        # Save zip file temporarily
        zip_path = target_dir.parent / f"{uuid.uuid4().hex}.zip"
        content = await zip_file.read()
        
        with open(zip_path, "wb") as buffer:
            buffer.write(content)
        
        # Extract zip file
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(target_dir)
        
        # Find image files in extracted content
        for file_path in target_dir.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.dcm', '.nii']:
                # Move to class directory if it's in a subfolder
                if file_path.parent != target_dir:
                    new_path = target_dir / file_path.name
                    shutil.move(str(file_path), str(new_path))
                    files.append(new_path.name)
        
        # Clean up zip file
        os.remove(zip_path)
        
        # Remove empty directories
        for dir_path in target_dir.iterdir():
            if dir_path.is_dir() and not any(dir_path.iterdir()):
                dir_path.rmdir()
        
    except Exception as e:
        errors.append(f"Zip processing failed: {str(e)}")
    
    return {"files": files, "errors": errors}

async def _process_uploaded_data(upload_dir: Path, class_label: str, upload_id: str):
    """Background task to process uploaded data"""
    try:
        logger.info(f"Processing uploaded data for {upload_id}")
        
        # Here you could add additional processing like:
        # - Image validation and preprocessing
        # - Metadata extraction
        # - Quality checks
        # - Automatic dataset splitting
        
        # For now, just log the completion
        logger.info(f"Data processing completed for upload {upload_id}")
        
    except Exception as e:
        logger.error(f"Data processing failed for upload {upload_id}: {str(e)}")

async def _get_dataset_info(dataset_dir: Path, name: str) -> DatasetInfo:
    """Get information about a dataset"""
    class_distribution = {}
    total_samples = 0
    
    for class_name in settings.class_names:
        class_dir = dataset_dir / class_name
        if class_dir.exists():
            # Check for various image extensions (case-insensitive on Windows)
            image_files = list(class_dir.glob("*.jpg")) + list(class_dir.glob("*.jpeg")) + \
                         list(class_dir.glob("*.png")) + list(class_dir.glob("*.JPG")) + \
                         list(class_dir.glob("*.PNG")) + list(class_dir.glob("*.dcm")) + \
                         list(class_dir.glob("*.nii"))
            count = len(image_files)
            class_distribution[class_name] = count
            total_samples += count
    
    return DatasetInfo(
        name=name,
        path=str(dataset_dir),
        total_samples=total_samples,
        class_distribution=class_distribution,
        last_updated=time.strftime("%Y-%m-%d %H:%M:%S"),
        status="ready" if total_samples > 0 else "empty"
    )

# Fix circular import issue
from src.models.model_manager import ModelManager