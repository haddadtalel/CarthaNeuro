"""
Data preprocessing utilities for CarthaNeuro
Handles image preprocessing, augmentation, and 3D volume creation
"""

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from typing import List, Tuple, Optional, Union, Dict, Any
import cv2
from pathlib import Path
import albumentations as A
from albumentations.pytorch import ToTensorV2
import SimpleITK as sitk
import nibabel as nib

from src.utils.logger import setup_logger
from src.config.settings import settings

logger = setup_logger(__name__)

class ImagePreprocessor:
    """Handles image preprocessing and augmentation"""
    
    def __init__(self, image_size: int = 224, normalize: bool = True):
        self.image_size = image_size
        self.normalize = normalize
        
        # Define augmentation pipeline for training
        self.train_transform = A.Compose([
            A.Resize(height=image_size, width=image_size, interpolation=cv2.INTER_CUBIC),
            A.HorizontalFlip(p=0.5),
            A.RandomRotate90(p=0.5),
            A.OneOf([
                A.GaussianBlur(blur_limit=3, p=1.0),
                A.MotionBlur(blur_limit=3, p=1.0),
            ], p=0.2),
            A.OneOf([
                A.RandomBrightnessContrast(brightness_limit=0.2, contrast_limit=0.2, p=1.0),
                A.HueSaturationValue(hue_shift_limit=20, sat_shift_limit=30, val_shift_limit=20, p=1.0),
            ], p=0.3),
            A.Normalize(mean=[0.485], std=[0.229]) if normalize else A.NoOp(),
            ToTensorV2()
        ])
        
        # Define augmentation pipeline for validation/inference
        self.val_transform = A.Compose([
            A.Resize(height=image_size, width=image_size, interpolation=cv2.INTER_CUBIC),
            A.Normalize(mean=[0.485], std=[0.229]) if normalize else A.NoOp(),
            ToTensorV2()
        ])
        
    def preprocess_image(
        self, 
        image: Union[np.ndarray, Image.Image, str], 
        is_training: bool = False
    ) -> torch.Tensor:
        """
        Preprocess a single image
        
        Args:
            image: Input image (numpy array, PIL Image, or file path)
            is_training: Whether to apply training augmentations
            
        Returns:
            Preprocessed tensor image
        """
        try:
            # Convert to numpy array
            if isinstance(image, str):
                image = self._load_image_from_path(image)
            elif isinstance(image, Image.Image):
                image = np.array(image)
                
            # Ensure grayscale for medical images
            if len(image.shape) == 3:
                image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
                
            # Convert to uint8 if necessary
            if image.dtype != np.uint8:
                if image.max() <= 1.0:
                    image = (image * 255).astype(np.uint8)
                else:
                    image = image.astype(np.uint8)
                    
            # Apply transforms
            transform = self.train_transform if is_training else self.val_transform
            transformed = transform(image=image)
            
            return transformed['image'].unsqueeze(0)  # Add batch dimension
            
        except Exception as e:
            logger.error(f"Image preprocessing failed: {str(e)}")
            # Return dummy tensor as fallback
            return torch.randn(1, 1, self.image_size, self.image_size)
            
    def _load_image_from_path(self, image_path: str) -> np.ndarray:
        """Load image from file path"""
        image_path = Path(image_path)
        
        if image_path.suffix.lower() in ['.nii', '.nii.gz']:
            # Load NIfTI format
            return self._load_nifti_image(str(image_path))
        elif image_path.suffix.lower() in ['.dcm', '.dicom']:
            # Load DICOM format
            return self._load_dicom_image(str(image_path))
        else:
            # Load standard image format
            return np.array(Image.open(image_path))
            
    def _load_nifti_image(self, file_path: str) -> np.ndarray:
        """Load NIfTI image file"""
        try:
            nifti_img = nib.load(file_path)
            image_data = nifti_img.get_fdata()
            
            # Normalize to 0-255 range
            if image_data.max() > 0:
                image_data = (image_data / image_data.max() * 255).astype(np.uint8)
            else:
                image_data = np.zeros_like(image_data, dtype=np.uint8)
                
            # Take middle slice if 3D
            if len(image_data.shape) == 3:
                slice_idx = image_data.shape[2] // 2
                image_data = image_data[:, :, slice_idx]
                
            return image_data
            
        except Exception as e:
            logger.warning(f"Failed to load NIfTI file {file_path}: {str(e)}")
            return np.zeros((256, 256), dtype=np.uint8)
            
    def _load_dicom_image(self, file_path: str) -> np.ndarray:
        """Load DICOM image file"""
        try:
            image_reader = sitk.ImageFileReader()
            image_reader.SetFileName(file_path)
            image_reader.LoadImageInformation()
            
            image = image_reader.Execute()
            image_array = sitk.GetArrayFromImage(image)[0]
            
            # Normalize to 0-255 range
            if image_array.max() > 0:
                image_array = (image_array / image_array.max() * 255).astype(np.uint8)
            else:
                image_array = np.zeros_like(image_array, dtype=np.uint8)
                
            return image_array
            
        except Exception as e:
            logger.warning(f"Failed to load DICOM file {file_path}: {str(e)}")
            return np.zeros((256, 256), dtype=np.uint8)

class VolumeCreator:
    """Creates 3D volumes from 2D image slices"""
    
    def __init__(self, num_slices: int = 32):
        self.num_slices = num_slices
        
    def create_volume_from_slices(
        self, 
        slices: List[Union[np.ndarray, torch.Tensor]], 
        target_size: Tuple[int, int] = (224, 224)
    ) -> torch.Tensor:
        """
        Create 3D volume from 2D slices
        
        Args:
            slices: List of 2D image slices
            target_size: Target size for each slice (height, width)
            
        Returns:
            3D tensor volume (1, depth, height, width)
        """
        try:
            if not slices:
                logger.warning("No slices provided for volume creation")
                return torch.zeros(1, self.num_slices, *target_size)
                
            # Ensure all slices are numpy arrays
            processed_slices = []
            for slice_img in slices:
                if isinstance(slice_img, torch.Tensor):
                    slice_img = slice_img.numpy()
                    
                if len(slice_img.shape) == 3:  # RGB to grayscale
                    slice_img = cv2.cvtColor(slice_img.astype(np.uint8), cv2.COLOR_RGB2GRAY)
                elif len(slice_img.shape) == 2:
                    slice_img = slice_img.astype(np.uint8)
                    
                # Resize to target size
                slice_img = cv2.resize(slice_img, target_size, interpolation=cv2.INTER_CUBIC)
                processed_slices.append(slice_img)
                
            # Stack slices
            volume_array = np.stack(processed_slices, axis=0)
            
            # Pad or truncate to desired number of slices
            if volume_array.shape[0] < self.num_slices:
                # Pad with zeros
                pad_width = ((0, self.num_slices - volume_array.shape[0]), (0, 0), (0, 0))
                volume_array = np.pad(volume_array, pad_width, mode='constant')
            elif volume_array.shape[0] > self.num_slices:
                # Truncate
                start_idx = (volume_array.shape[0] - self.num_slices) // 2
                volume_array = volume_array[start_idx:start_idx + self.num_slices]
                
            # Convert to tensor and add batch/channel dimensions
            volume_tensor = torch.from_numpy(volume_array).float().unsqueeze(0).unsqueeze(0)
            
            return volume_tensor
            
        except Exception as e:
            logger.error(f"Volume creation failed: {str(e)}")
            return torch.zeros(1, 1, self.num_slices, *target_size)
            
    def create_volume_from_single_image(
        self, 
        image: Union[np.ndarray, torch.Tensor], 
        target_size: Tuple[int, int] = (224, 224)
    ) -> torch.Tensor:
        """
        Create 3D volume from single 2D image by duplicating slices
        
        Args:
            image: Single 2D image
            target_size: Target size for each slice (height, width)
            
        Returns:
            3D tensor volume (1, depth, height, width)
        """
        try:
            # Ensure image is 2D numpy array
            if isinstance(image, torch.Tensor):
                image = image.numpy()
                
            if len(image.shape) == 3:
                image = cv2.cvtColor(image.astype(np.uint8), cv2.COLOR_RGB2GRAY)
            elif len(image.shape) == 2:
                image = image.astype(np.uint8)
                
            # Resize to target size
            image = cv2.resize(image, target_size, interpolation=cv2.INTER_CUBIC)
            
            # Create slices by adding slight variations
            slices = []
            for i in range(self.num_slices):
                # Add slight noise and brightness variations
                slice_img = image.copy().astype(np.float32)
                
                # Add small random noise
                noise = np.random.normal(0, 5, slice_img.shape)
                slice_img += noise
                
                # Clip to valid range
                slice_img = np.clip(slice_img, 0, 255).astype(np.uint8)
                slices.append(slice_img)
                
            return self.create_volume_from_slices(slices, target_size)
            
        except Exception as e:
            logger.error(f"Single image volume creation failed: {str(e)}")
            return torch.zeros(1, 1, self.num_slices, *target_size)

class BrainTumorDataset:
    """Dataset class for brain tumor classification"""
    
    def __init__(
        self, 
        data_dir: Union[str, Path], 
        class_names: List[str],
        split: str = "train",
        transform: Optional[A.Compose] = None,
        target_size: Tuple[int, int] = (224, 224)
    ):
        self.data_dir = Path(data_dir)
        self.class_names = class_names
        self.split = split
        self.target_size = target_size
        
        # Load dataset
        self.samples = self._load_dataset()
        
        # Initialize transforms
        self.preprocessor = ImagePreprocessor(image_size=target_size[0])
        self.volume_creator = VolumeCreator(num_slices=settings.num_slices)
        
    def _load_dataset(self) -> List[Tuple[str, int]]:
        """Load dataset from directory structure"""
        samples = []
        
        dataset_path = self.data_dir / "Tumor" / "Brain Tumor labeled dataset"
        
        if not dataset_path.exists():
            logger.warning(f"Dataset directory not found: {dataset_path}")
            return samples
            
        for class_idx, class_name in enumerate(self.class_names):
            class_path = dataset_path / class_name
            
            if not class_path.exists():
                logger.warning(f"Class directory not found: {class_path}")
                continue
                
            # Get image files
            image_files = list(class_path.glob("*.jpg")) + list(class_path.glob("*.png"))
            
            # Split data
            if self.split == "train":
                images = image_files[:int(0.7 * len(image_files))]
            elif self.split == "val":
                images = image_files[int(0.7 * len(image_files)):int(0.9 * len(image_files))]
            elif self.split == "test":
                images = image_files[int(0.9 * len(image_files)):]
            else:
                images = image_files
                
            for img_path in images:
                samples.append((str(img_path), class_idx))
                
        logger.info(f"Loaded {len(samples)} samples for {self.split} split")
        return samples
        
    def __len__(self) -> int:
        return len(self.samples)
        
    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        """Get a sample from the dataset"""
        try:
            img_path, label = self.samples[idx]
            
            # Load and preprocess image
            image = self.preprocessor._load_image_from_path(img_path)
            volume = self.volume_creator.create_volume_from_single_image(
                image, 
                self.target_size
            )
            
            return volume, label
            
        except Exception as e:
            logger.error(f"Failed to load sample {idx}: {str(e)}")
            # Return dummy data
            return torch.zeros(1, 1, settings.num_slices, *self.target_size), 0

def create_data_loaders(
    batch_size: int = 8,
    num_workers: int = 4,
    validation_split: float = 0.2
) -> Tuple[torch.utils.data.DataLoader, torch.utils.data.DataLoader, torch.utils.data.DataLoader]:
    """
    Create training, validation, and test data loaders
    
    Args:
        batch_size: Batch size for data loaders
        num_workers: Number of worker processes
        validation_split: Validation split ratio
        
    Returns:
        Tuple of (train_loader, val_loader, test_loader)
    """
    try:
        # Create datasets
        train_dataset = BrainTumorDataset(
            data_dir=settings.data_dir,
            class_names=settings.class_names,
            split="train"
        )
        
        val_dataset = BrainTumorDataset(
            data_dir=settings.data_dir,
            class_names=settings.class_names,
            split="val"
        )
        
        test_dataset = BrainTumorDataset(
            data_dir=settings.data_dir,
            class_names=settings.class_names,
            split="test"
        )
        
        # Create data loaders
        train_loader = torch.utils.data.DataLoader(
            train_dataset,
            batch_size=batch_size,
            shuffle=True,
            num_workers=num_workers,
            pin_memory=True
        )
        
        val_loader = torch.utils.data.DataLoader(
            val_dataset,
            batch_size=batch_size,
            shuffle=False,
            num_workers=num_workers,
            pin_memory=True
        )
        
        test_loader = torch.utils.data.DataLoader(
            test_dataset,
            batch_size=batch_size,
            shuffle=False,
            num_workers=num_workers,
            pin_memory=True
        )
        
        logger.info(f"Created data loaders - Train: {len(train_dataset)}, Val: {len(val_dataset)}, Test: {len(test_dataset)}")
        
        return train_loader, val_loader, test_loader
        
    except Exception as e:
        logger.error(f"Failed to create data loaders: {str(e)}")
        raise