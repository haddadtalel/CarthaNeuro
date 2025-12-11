"""
3D CNN Classifier for Brain Tumor Classification
Implements 3D ResNet and 3D DenseNet architectures
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Any, Optional, Tuple
import time
from pathlib import Path

from src.utils.logger import setup_logger
from src.config.settings import settings

logger = setup_logger(__name__)

class Conv3dBlock(nn.Module):
    """3D Convolutional block with batch normalization and ReLU"""
    
    def __init__(self, in_channels: int, out_channels: int, kernel_size: int = 3, stride: int = 1):
        super().__init__()
        self.conv = nn.Conv3d(in_channels, out_channels, kernel_size, stride, kernel_size//2)
        self.bn = nn.BatchNorm3d(out_channels)
        self.relu = nn.ReLU(inplace=True)
        
    def forward(self, x):
        return self.relu(self.bn(self.conv(x)))

class ResNet3DBottleneck(nn.Module):
    """3D ResNet Bottleneck block"""
    
    def __init__(self, in_channels: int, planes: int, stride: int = 1):
        super().__init__()
        self.conv1 = nn.Conv3d(in_channels, planes, 1, bias=False)
        self.bn1 = nn.BatchNorm3d(planes)
        self.conv2 = nn.Conv3d(planes, planes, 3, stride, 1, bias=False)
        self.bn2 = nn.BatchNorm3d(planes)
        self.conv3 = nn.Conv3d(planes, planes * 4, 1, bias=False)
        self.bn3 = nn.BatchNorm3d(planes * 4)
        self.relu = nn.ReLU(inplace=True)
        
        self.shortcut = nn.Sequential()
        if stride != 1 or in_channels != planes * 4:
            self.shortcut = nn.Sequential(
                nn.Conv3d(in_channels, planes * 4, 1, stride, bias=False),
                nn.BatchNorm3d(planes * 4)
            )
            
    def forward(self, x):
        out = self.relu(self.bn1(self.conv1(x)))
        out = self.relu(self.bn2(self.conv2(out)))
        out = self.bn3(self.conv3(out))
        out += self.shortcut(x)
        out = self.relu(out)
        return out

class DenseNet3DBlock(nn.Module):
    """3D DenseNet block"""
    
    def __init__(self, in_channels: int, growth_rate: int, bn_size: int = 4):
        super().__init__()
        self.bn1 = nn.BatchNorm3d(in_channels)
        self.conv1 = nn.Conv3d(in_channels, bn_size * growth_rate, 1, bias=False)
        self.bn2 = nn.BatchNorm3d(bn_size * growth_rate)
        self.conv2 = nn.Conv3d(bn_size * growth_rate, growth_rate, 3, padding=1, bias=False)
        self.relu = nn.ReLU(inplace=True)
        
    def forward(self, x):
        out = self.relu(self.bn1(x))
        out = self.relu(self.bn2(self.conv1(out)))
        out = self.conv2(out)
        out = torch.cat([x, out], 1)
        return out

class Transition3DLayer(nn.Module):
    """3D DenseNet transition layer"""
    
    def __init__(self, in_channels: int, out_channels: int):
        super().__init__()
        self.bn = nn.BatchNorm3d(in_channels)
        self.conv = nn.Conv3d(in_channels, out_channels, 1, bias=False)
        self.pool = nn.AvgPool3d(2, stride=2)
        self.relu = nn.ReLU(inplace=True)
        
    def forward(self, x):
        out = self.relu(self.bn(x))
        out = self.conv(out)
        out = self.pool(out)
        return out

class Classifier3DCNN(nn.Module):
    """3D CNN Classifier for brain tumor classification"""
    
    def __init__(
        self, 
        num_classes: int = 4,
        model_type: str = "resnet",  # "resnet" or "densenet"
        device: str = "cuda",
        pretrained: bool = True
    ):
        super().__init__()
        
        self.num_classes = num_classes
        self.model_type = model_type
        self.device = device
        self.pretrained = pretrained
        
        # Input shape: (batch_size, channels, depth, height, width)
        # Typical: (batch_size, 1, 32, 224, 224) for brain MRI
        
        if model_type == "resnet":
            self._build_resnet()
        elif model_type == "densenet":
            self._build_densenet()
        else:
            raise ValueError(f"Unknown model type: {model_type}")
            
        # Classifier head
        self.classifier = nn.Sequential(
            nn.AdaptiveAvgPool3d((1, 1, 1)),
            nn.Flatten(),
            nn.Linear(self.feature_dim, 512),
            nn.ReLU(inplace=True),
            nn.Dropout(0.5),
            nn.Linear(512, num_classes)
        )
        
        # Initialize weights
        self._initialize_weights()
        
        logger.info(f"3D CNN {model_type} initialized with {num_classes} classes")
        
    def _build_resnet(self):
        """Build 3D ResNet architecture"""
        self.in_channels = 64
        
        # Initial convolution
        self.conv1 = nn.Conv3d(1, 64, kernel_size=7, stride=2, padding=3, bias=False)
        self.bn1 = nn.BatchNorm3d(64)
        self.relu = nn.ReLU(inplace=True)
        self.maxpool = nn.MaxPool3d(kernel_size=3, stride=2, padding=1)
        
        # ResNet blocks
        self.layer1 = self._make_resnet_layer(64, 3, stride=1)
        self.layer2 = self._make_resnet_layer(128, 4, stride=2)
        self.layer3 = self._make_resnet_layer(256, 6, stride=2)
        self.layer4 = self._make_resnet_layer(512, 3, stride=2)
        
        self.feature_dim = 512 * 4  # 2048
        
    def _make_resnet_layer(self, planes: int, blocks: int, stride: int) -> nn.Module:
        """Create ResNet layer with multiple bottleneck blocks"""
        layers = []
        layers.append(ResNet3DBottleneck(self.in_channels, planes, stride))
        self.in_channels = planes * 4
        
        for _ in range(1, blocks):
            layers.append(ResNet3DBottleneck(self.in_channels, planes))
            
        return nn.Sequential(*layers)
        
    def _build_densenet(self):
        """Build 3D DenseNet architecture"""
        # Initial convolution
        self.conv1 = nn.Conv3d(1, 64, 7, stride=2, padding=3, bias=False)
        self.bn1 = nn.BatchNorm3d(64)
        self.relu = nn.ReLU(inplace=True)
        self.maxpool = nn.MaxPool3d(3, stride=2, padding=1)
        
        # Dense blocks
        self.dense1 = self._make_dense_block(64, 6, growth_rate=32)
        num_features = 64 + 6 * 32
        self.trans1 = Transition3DLayer(num_features, num_features // 2)
        num_features = num_features // 2
        
        self.dense2 = self._make_dense_block(num_features, 12, growth_rate=32)
        num_features += 12 * 32
        self.trans2 = Transition3DLayer(num_features, num_features // 2)
        num_features = num_features // 2
        
        self.dense3 = self._make_dense_block(num_features, 24, growth_rate=32)
        num_features += 24 * 32
        self.trans3 = Transition3DLayer(num_features, num_features // 2)
        num_features = num_features // 2
        
        self.dense4 = self._make_dense_block(num_features, 16, growth_rate=32)
        num_features += 16 * 32
        
        self.feature_dim = num_features
        
    def _make_dense_block(self, in_channels: int, num_layers: int, growth_rate: int) -> nn.Module:
        """Create DenseNet block"""
        layers = []
        channels = in_channels
        
        for _ in range(num_layers):
            layers.append(DenseNet3DBlock(channels, growth_rate))
            channels += growth_rate
            
        return nn.Sequential(*layers)
        
    def _initialize_weights(self):
        """Initialize model weights"""
        for m in self.modules():
            if isinstance(m, nn.Conv3d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
            elif isinstance(m, nn.BatchNorm3d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, 0, 0.01)
                nn.init.constant_(m.bias, 0)
                
    def forward(self, x):
        """Forward pass"""
        if x.dim() == 4:  # Add channel dimension if missing
            x = x.unsqueeze(1)
            
        # Ensure both model and input are on the same device
        x = x.to(self.device)
        self.to(self.device)  # Ensure model is on the correct device
        
        if self.model_type == "resnet":
            # ResNet forward pass
            x = self.conv1(x)
            x = self.bn1(x)
            x = self.relu(x)
            x = self.maxpool(x)
            
            x = self.layer1(x)
            x = self.layer2(x)
            x = self.layer3(x)
            x = self.layer4(x)
            
        elif self.model_type == "densenet":
            # DenseNet forward pass
            x = self.conv1(x)
            x = self.bn1(x)
            x = self.relu(x)
            x = self.maxpool(x)
            
            x = self.dense1(x)
            x = self.trans1(x)
            x = self.dense2(x)
            x = self.trans2(x)
            x = self.dense3(x)
            x = self.trans3(x)
            x = self.dense4(x)
            
            x = F.relu(x, inplace=True)
            
        # Classification
        x = self.classifier(x)
        return x
        
    def predict(self, image_input, llm_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make prediction on brain MRI image
        
        Args:
            image_input: Input image (tensor, array, or path)
            llm_context: Optional context from LLM analysis
            
        Returns:
            Prediction results with confidence scores
        """
        try:
            start_time = time.time()
            
            # Preprocess image
            if isinstance(image_input, (str, Path)):
                # Load image from path
                image_tensor = self._load_and_preprocess_image(image_input)
            elif isinstance(image_input, torch.Tensor):
                image_tensor = image_input
            elif isinstance(image_input, tuple):
                # Assume it's a volume of slices
                image_tensor = self._create_3d_volume(image_input)
            else:
                # Assume it's a 2D image array
                image_tensor = self._preprocess_2d_image(image_input)
                
            # Ensure proper shape
            if image_tensor.dim() == 3:
                image_tensor = image_tensor.unsqueeze(0)  # Add batch dimension
                
            # Forward pass
            with torch.no_grad():
                self.eval()
                outputs = self.forward(image_tensor)
                probabilities = F.softmax(outputs, dim=1)
                predicted_class = torch.argmax(probabilities, dim=1).item()
                confidence = probabilities[0, predicted_class].item()
                
            # Get all class probabilities
            class_probabilities = {
                class_name: prob.item() 
                for class_name, prob in zip(settings.class_names, probabilities[0])
            }
            
            # Prepare result
            result = {
                "prediction": {
                    "class": settings.class_names[predicted_class],
                    "class_id": predicted_class,
                    "confidence": confidence,
                    "probabilities": class_probabilities
                },
                "model_info": {
                    "model_type": self.model_type,
                    "architecture": "3D_CNN",
                    "device": self.device,
                    "inference_time": time.time() - start_time
                },
                "metadata": {
                    "input_shape": list(image_tensor.shape),
                    "llm_context_provided": llm_context is not None
                }
            }
            
            if llm_context:
                result["llm_context"] = llm_context
                
            return result
            
        except Exception as e:
            logger.error(f"Prediction failed: {str(e)}")
            return self._get_fallback_prediction()
            
    def _load_and_preprocess_image(self, image_path) -> torch.Tensor:
        """Load and preprocess image from file path"""
        # This would integrate with your image loading utilities
        # For now, return a placeholder tensor
        # In practice, you'd use PIL, OpenCV, or medical imaging libraries
        dummy_volume = torch.randn(1, settings.num_slices, settings.image_size, settings.image_size)
        return dummy_volume
        
    def _create_3d_volume(self, image_slices) -> torch.Tensor:
        """Create 3D volume from 2D slices"""
        # Stack slices to create 3D volume
        slices_tensor = torch.stack([slice for slice in image_slices])
        return slices_tensor.unsqueeze(0)  # Add channel dimension
        
    def _preprocess_2d_image(self, image_array) -> torch.Tensor:
        """Preprocess 2D image to 3D format"""
        # Create a dummy 3D volume from 2D image
        # In practice, you'd expand to multiple slices or use sliding windows
        dummy_volume = torch.randn(1, settings.num_slices, settings.image_size, settings.image_size)
        return dummy_volume
        
    def _get_fallback_prediction(self) -> Dict[str, Any]:
        """Get fallback prediction when inference fails"""
        return {
            "prediction": {
                "class": "error",
                "class_id": -1,
                "confidence": 0.0,
                "probabilities": {cls: 0.0 for cls in settings.class_names}
            },
            "model_info": {
                "model_type": self.model_type,
                "architecture": "3D_CNN",
                "device": self.device,
                "error": "Prediction failed"
            },
            "metadata": {
                "fallback": True
            }
        }
        
    def train_model(self, train_loader, val_loader, num_epochs: int = None):
        """Train the model (placeholder implementation)"""
        if num_epochs is None:
            num_epochs = settings.num_epochs
            
        logger.info(f"Training {self.model_type} model for {num_epochs} epochs...")
        
        # Ensure model is on the correct device
        self.to(self.device)
        
        # Placeholder training loop
        # In practice, you'd implement full training with:
        # - Loss function (CrossEntropyLoss)
        # - Optimizer (Adam)
        # - Learning rate scheduler
        # - Validation metrics
        # - Checkpointing
        
        self.train()
        optimizer = torch.optim.Adam(self.parameters(), lr=settings.learning_rate)
        criterion = nn.CrossEntropyLoss()
        
        for epoch in range(num_epochs):
            # Training epoch
            epoch_loss = 0.0
            for batch_idx, (data, target) in enumerate(train_loader):
                data, target = data.to(self.device), target.to(self.device)
                
                optimizer.zero_grad()
                output = self.forward(data)
                loss = criterion(output, target)
                loss.backward()
                optimizer.step()
                
                epoch_loss += loss.item()
                
                if batch_idx % 10 == 0:
                    logger.info(f'Epoch {epoch}, Batch {batch_idx}, Loss: {loss.item():.4f}')
                    
            # Validation
            if val_loader:
                val_loss, val_acc = self._validate(val_loader, criterion)
                logger.info(f'Epoch {epoch}: Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.4f}')
                
        logger.info("Training completed")
        
    def _validate(self, val_loader, criterion) -> Tuple[float, float]:
        """Validate model performance"""
        self.eval()
        val_loss = 0.0
        correct = 0
        total = 0
        
        with torch.no_grad():
            for data, target in val_loader:
                data, target = data.to(self.device), target.to(self.device)
                output = self.forward(data)
                val_loss += criterion(output, target).item()
                
                _, predicted = torch.max(output.data, 1)
                total += target.size(0)
                correct += (predicted == target).sum().item()
                
        accuracy = correct / total
        return val_loss / len(val_loader), accuracy
        
    def save_model(self, save_path: str):
        """Save model weights"""
        torch.save({
            'model_state_dict': self.state_dict(),
            'model_type': self.model_type,
            'num_classes': self.num_classes,
            'config': {
                'device': self.device,
                'pretrained': self.pretrained
            }
        }, save_path)
        
    def load_model(self, load_path: str):
        """Load model weights"""
        checkpoint = torch.load(load_path, map_location=self.device)
        self.load_state_dict(checkpoint['model_state_dict'])
        logger.info(f"Model loaded from {load_path}")
        
    def cleanup(self):
        """Cleanup model resources"""
        # Clear GPU cache
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        logger.info("3D CNN model cleanup completed")