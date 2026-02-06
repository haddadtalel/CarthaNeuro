from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import List, Dict, Optional
from models.dataset import Dataset, DatasetCreate
from database import get_db
from models.user import TokenData
import uuid
from datetime import datetime
import os
import zipfile
import tarfile
import io
import shutil

# Import get_current_user locally to avoid circular import
from routes.auth import get_current_user

router = APIRouter()

# Configure upload directory
UPLOAD_DIR = "/home/fawzi/Desktop/CNNN/backend/uploads/datasets"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Supported image extensions
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.nii', '.nii.gz', '.dcm'}

def get_file_format(filename: str) -> str:
    """Detect file format from filename extension"""
    lower_name = filename.lower()
    if lower_name.endswith('.zip'):
        return 'zip'
    elif lower_name.endswith('.tar.gz') or lower_name.endswith('.tgz'):
        return 'tar.gz'
    return ''

def count_images_in_directory(path: str) -> int:
    """Count all image files in a directory recursively"""
    image_count = 0
    for root, dirs, files in os.walk(path):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in IMAGE_EXTENSIONS:
                image_count += 1
    return image_count

def analyze_dataset_structure(extract_path: str) -> Dict:
    """
    Analyze the extracted dataset structure.
    Returns dict with total_images, classes, and class_distribution.
    Supports:
    - Train/Test structure: train/ and test/ folders with class subfolders
    - Single-level: images in class folders
    - Nested structure: class folders may contain subdirectories
    - Flat structure: all images in root
    """
    total_images = 0
    classes = []
    class_distribution: Dict[str, int] = {}
    has_train_test_split = False
    train_count = 0
    test_count = 0
    
    if not os.path.exists(extract_path):
        return {
            "total_images": 0,
            "classes": [],
            "class_distribution": {},
            "has_train_test_split": False,
            "train_count": 0,
            "test_count": 0
        }
    
    # Get all items in the extract path
    items = os.listdir(extract_path)
    
    # Separate files and directories
    files_in_root = []
    directories_in_root = []
    
    for item in items:
        item_path = os.path.join(extract_path, item)
        if os.path.isdir(item_path):
            directories_in_root.append(item)
        else:
            files_in_root.append(item)
    
    # Check for train/test folder structure FIRST
    train_path = os.path.join(extract_path, "train")
    test_path = os.path.join(extract_path, "test")
    
    if "train" in directories_in_root and "test" in directories_in_root:
        # Found train/test structure!
        has_train_test_split = True
        
        # Analyze train folder
        train_classes = []
        train_distribution = {}
        if os.path.exists(train_path):
            for class_dir in os.listdir(train_path):
                class_path = os.path.join(train_path, class_dir)
                if os.path.isdir(class_path):
                    train_classes.append(class_dir)
                    class_count = count_images_in_directory(class_path)
                    if class_count > 0:
                        train_distribution[class_dir] = class_count
                        train_count += class_count
        
        # Analyze test folder
        test_classes = []
        test_distribution = {}
        if os.path.exists(test_path):
            for class_dir in os.listdir(test_path):
                class_path = os.path.join(test_path, class_dir)
                if os.path.isdir(class_path):
                    if class_dir not in train_classes:
                        # Add class if not in train (should be same classes)
                        train_classes.append(class_dir)
                    test_classes.append(class_dir)
                    class_count = count_images_in_directory(class_path)
                    if class_count > 0:
                        test_distribution[class_dir] = class_count
                        test_count += class_count
        
        # Combine distributions
        classes = train_classes
        class_distribution = train_distribution.copy()
        for cls, count in test_distribution.items():
            if cls in class_distribution:
                class_distribution[cls] += count
            else:
                class_distribution[cls] = count
        
        total_images = train_count + test_count
        
        return {
            "total_images": total_images,
            "classes": classes,
            "class_distribution": class_distribution,
            "has_train_test_split": True,
            "train_count": train_count,
            "test_count": test_count,
            "train_distribution": train_distribution,
            "test_distribution": test_distribution
        }
    
    # Strategy 1: Directories exist - likely class folders (non train/test)
    if directories_in_root:
        for dir_name in directories_in_root:
            dir_path = os.path.join(extract_path, dir_name)
            if os.path.isdir(dir_path):
                # Count images in this directory
                image_count = count_images_in_directory(dir_path)
                if image_count > 0:
                    classes.append(dir_name)
                    class_distribution[dir_name] = image_count
                    total_images += image_count
        
        # If no classes found with images, check for nested structure
        if not classes and files_in_root:
            # Check if files are directly in root
            for file in files_in_root:
                ext = os.path.splitext(file)[1].lower()
                if ext in IMAGE_EXTENSIONS:
                    total_images += 1
            if total_images > 0:
                classes = ["default"]
                class_distribution = {"default": total_images}
    
    # Strategy 2: No directories - all files in root (flat structure)
    else:
        for file in files_in_root:
            ext = os.path.splitext(file)[1].lower()
            if ext in IMAGE_EXTENSIONS:
                total_images += 1
        if total_images > 0:
            classes = ["default"]
            class_distribution = {"default": total_images}
    
    return {
        "total_images": total_images,
        "classes": classes,
        "class_distribution": class_distribution,
        "has_train_test_split": False,
        "train_count": 0,
        "test_count": 0
    }

def extract_archive(file_content: bytes, file_format: str, extract_path: str) -> None:
    """Extract archive file to the specified path"""
    if file_format == 'zip':
        with zipfile.ZipFile(io.BytesIO(file_content), 'r') as zip_ref:
            zip_ref.extractall(extract_path)
    elif file_format == 'tar.gz':
        with tarfile.open(fileobj=io.BytesIO(file_content), mode='r:gz') as tar:
            tar.extractall(extract_path)
    
    # Handle nested single folder: if archive extracted to a single folder, move contents up
    items = os.listdir(extract_path)
    if len(items) == 1:
        single_item = items[0]
        single_path = os.path.join(extract_path, single_item)
        if os.path.isdir(single_path):
            # Move all contents from the single folder to the parent
            for item in os.listdir(single_path):
                src = os.path.join(single_path, item)
                dst = os.path.join(extract_path, item)
                shutil.move(src, dst)
            # Remove the now-empty single folder
            os.rmdir(single_path)

@router.get("/", response_model=List[Dataset])
async def get_datasets(skip: int = 0, limit: int = 100):
    db = get_db()
    datasets = []
    async for dataset in db.datasets.find().skip(skip).limit(limit):
        # Convert MongoDB _id to id and ensure all required fields are present
        dataset_dict = dict(dataset)
        dataset_dict["id"] = str(dataset_dict.pop("_id"))
        # Ensure created_at is present
        if "created_at" not in dataset_dict:
            dataset_dict["created_at"] = datetime.utcnow()
        # Ensure new fields have defaults
        if "total_images" not in dataset_dict:
            dataset_dict["total_images"] = 0
        if "classes" not in dataset_dict:
            dataset_dict["classes"] = []
        if "class_distribution" not in dataset_dict:
            dataset_dict["class_distribution"] = {}
        if "file_format" not in dataset_dict:
            dataset_dict["file_format"] = ""
        # Add frontend compatibility fields
        dataset_dict["image_count"] = dataset_dict.get("total_images", 0)
        dataset_dict["status"] = "ready" if dataset_dict.get("is_active", True) else "inactive"
        dataset_dict["image_extensions"] = []
        datasets.append(Dataset(**dataset_dict))
    return datasets

@router.post("/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    name: str = Form(None),
    description: str = Form(""),
    current_user: TokenData = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can upload datasets")

    db = get_db()

    # Detect file format
    file_format = get_file_format(file.filename)
    if not file_format:
        raise HTTPException(status_code=400, detail="Only ZIP and TAR.GZ files are supported")

    # Read file content
    file_content = await file.read()
    file_size = len(file_content)
    file_size_mb = file_size / (1024 * 1024)

    # Generate dataset ID and create directories
    dataset_id = str(uuid.uuid4())
    extract_path = os.path.join(UPLOAD_DIR, dataset_id)
    os.makedirs(extract_path, exist_ok=True)

    try:
        # Extract archive
        extract_archive(file_content, file_format, extract_path)

        # Analyze dataset structure
        analysis = analyze_dataset_structure(extract_path)

        dataset_record = {
            "_id": dataset_id,
            "name": name or file.filename,
            "description": description or "",
            "path": extract_path,
            "file_count": 1,
            "size_bytes": file_size,
            "size_mb": round(file_size_mb, 2),
            "uploaded_by": current_user.username,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "total_images": analysis["total_images"],
            "classes": analysis["classes"],
            "class_distribution": analysis["class_distribution"],
            "file_format": file_format,
            # Train/Test split fields (NEW)
            "has_train_test_split": analysis.get("has_train_test_split", False),
            "train_count": analysis.get("train_count", 0),
            "test_count": analysis.get("test_count", 0),
            "train_distribution": analysis.get("train_distribution", {}),
            "test_distribution": analysis.get("test_distribution", {}),
            # Alias for frontend compatibility
            "image_count": analysis["total_images"],
        }

        await db.datasets.insert_one(dataset_record)

        return {
            "message": "Dataset uploaded and analyzed successfully",
            "dataset_id": dataset_id,
            "analysis": analysis
        }
    except Exception as e:
        # Clean up on error
        if os.path.exists(extract_path):
            shutil.rmtree(extract_path)
        raise HTTPException(status_code=500, detail=f"Error processing dataset: {str(e)}")

@router.get("/{dataset_id}", response_model=Dataset)
async def get_dataset_details(dataset_id: str):
    db = get_db()
    dataset = await db.datasets.find_one({"_id": dataset_id})
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    # Convert MongoDB _id to id and ensure all required fields are present
    dataset_dict = dict(dataset)
    dataset_dict["id"] = str(dataset_dict.pop("_id"))
    # Ensure created_at is present
    if "created_at" not in dataset_dict:
        dataset_dict["created_at"] = datetime.utcnow()
    # Ensure new fields have defaults
    if "total_images" not in dataset_dict:
        dataset_dict["total_images"] = 0
    if "classes" not in dataset_dict:
        dataset_dict["classes"] = []
    if "class_distribution" not in dataset_dict:
        dataset_dict["class_distribution"] = {}
    if "file_format" not in dataset_dict:
        dataset_dict["file_format"] = ""
    # Add frontend compatibility fields
    dataset_dict["image_count"] = dataset_dict.get("total_images", 0)
    dataset_dict["status"] = "ready" if dataset_dict.get("is_active", True) else "inactive"
    dataset_dict["image_extensions"] = []
    return Dataset(**dataset_dict)

@router.delete("/{dataset_id}")
async def delete_dataset(dataset_id: str, current_user: TokenData = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can upload datasets")

    db = get_db()
    dataset = await db.datasets.find_one({"_id": dataset_id})
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Delete the extracted files
    dataset_path = dataset.get("path", "")
    if dataset_path and os.path.exists(dataset_path):
        shutil.rmtree(dataset_path)

    await db.datasets.delete_one({"_id": dataset_id})

    return {"message": "Dataset deleted successfully"}

@router.get("/{dataset_id}/preview")
async def get_dataset_preview(dataset_id: str):
    db = get_db()
    dataset = await db.datasets.find_one({"_id": dataset_id})
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Get preview data from the stored analysis
    preview_data = {
        "dataset_id": dataset_id,
        "name": dataset["name"],
        "file_count": dataset.get("file_count", 1),
        "total_images": dataset.get("total_images", 0),
        "classes": dataset.get("classes", []),
        "class_distribution": dataset.get("class_distribution", {}),
        "sample_files": [
            {"filename": f"sample1.nii", "size": dataset["size_bytes"] // 2},
            {"filename": f"sample2.nii", "size": dataset["size_bytes"] // 4},
        ]
    }

    return preview_data

@router.post("/{dataset_id}/reanalyze")
async def reanalyze_dataset(dataset_id: str, current_user: TokenData = Depends(get_current_user)):
    """Re-analyze an existing dataset"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can reanalyze datasets")

    db = get_db()
    dataset = await db.datasets.find_one({"_id": dataset_id})
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    dataset_path = dataset.get("path", "")
    if not dataset_path or not os.path.exists(dataset_path):
        raise HTTPException(status_code=404, detail="Dataset files not found")

    # Re-analyze the dataset
    analysis = analyze_dataset_structure(dataset_path)

    # Update the database
    await db.datasets.update_one(
        {"_id": dataset_id},
        {
            "$set": {
                "total_images": analysis["total_images"],
                "classes": analysis["classes"],
                "class_distribution": analysis["class_distribution"],
                "image_count": analysis["total_images"],
            }
        }
    )

    return {
        "message": "Dataset reanalyzed successfully",
        "analysis": analysis
    }

@router.post("/fix-missing-fields")
async def fix_missing_fields(current_user: TokenData = Depends(get_current_user)):
    """Fix missing image_count field for all existing datasets"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can perform this action")

    db = get_db()
    updated = 0

    async for dataset in db.datasets.find({}):
        dataset_id = dataset.get("_id")
        total_images = dataset.get("total_images", 0)
        image_count = dataset.get("image_count")

        # Only update if image_count is missing or different from total_images
        if image_count != total_images:
            await db.datasets.update_one(
                {"_id": dataset_id},
                {"$set": {"image_count": total_images}}
            )
            updated += 1

    return {
        "message": f"Updated {updated} datasets with missing image_count field"
    }

