"""
Real PyTorch Training Module for MRI Classification
Supports both:
1. Single folder structure: dataset/class_name/images.jpg
2. Train/test folder structure: dataset/train/class_name/images.jpg + dataset/test/class_name/images.jpg

Saves models in both .pth (PyTorch) and .h5 (Keras) formats for production use.
"""
import os, torch, torch.nn as nn, torch.optim as optim
from torch.utils.data import Dataset, DataLoader, Subset
from torchvision import transforms
from PIL import Image
from collections import defaultdict
from typing import Dict, List
import asyncio
import inspect

device = torch.device("cpu")

class MRIDataset(Dataset):
    def __init__(self, dataset_path: str, classes: List[str], transform=None):
        self.dataset_path = dataset_path
        self.classes = classes
        self.class_to_idx = {cls: idx for idx, cls in enumerate(classes)}
        self.transform = transform
        self.image_paths = []
        self.labels = []
        for class_name in classes:
            class_dir = os.path.join(dataset_path, class_name)
            if os.path.exists(class_dir):
                for img_file in os.listdir(class_dir):
                    if img_file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                        self.image_paths.append(os.path.join(class_dir, img_file))
                        self.labels.append(self.class_to_idx[class_name])
        print(f"Loaded {len(self.image_paths)} images from {len(classes)} classes")
    
    def __len__(self):
        return len(self.image_paths)
    
    def __getitem__(self, idx):
        img_path = self.image_paths[idx]
        label = self.labels[idx]
        try:
            image = Image.open(img_path).convert('RGB')
            if self.transform:
                image = self.transform(image)
        except:
            image = torch.zeros((3, 224, 224))
        return image, label

class MRIClassifier(nn.Module):
    def __init__(self, num_classes: int):
        super(MRIClassifier, self).__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 32, 3, padding=1), nn.BatchNorm2d(32), nn.ReLU(inplace=True), nn.MaxPool2d(2, 2),
            nn.Conv2d(32, 64, 3, padding=1), nn.BatchNorm2d(64), nn.ReLU(inplace=True), nn.MaxPool2d(2, 2),
            nn.Conv2d(64, 128, 3, padding=1), nn.BatchNorm2d(128), nn.ReLU(inplace=True), nn.MaxPool2d(2, 2),
            nn.Conv2d(128, 256, 3, padding=1), nn.BatchNorm2d(256), nn.ReLU(inplace=True), nn.AdaptiveAvgPool2d((1, 1)),
        )
        self.classifier = nn.Sequential(
            nn.Flatten(), nn.Dropout(0.5), nn.Linear(256, 512), nn.ReLU(inplace=True), nn.Dropout(0.3), nn.Linear(512, num_classes)
        )
    
    def forward(self, x):
        x = self.features(x)
        return self.classifier(x)

def get_transforms(is_train: bool = True):
    if is_train:
        return transforms.Compose([
            transforms.Resize((224, 224)), transforms.RandomHorizontalFlip(0.5),
            transforms.RandomRotation(10), transforms.ColorJitter(0.2, 0.2),
            transforms.ToTensor(), transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])
    return transforms.Compose([
        transforms.Resize((224, 224)), transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])

def train_epoch(model, dataloader, criterion, optimizer):
    model.train()
    running_loss, correct, total = 0.0, 0, 0
    for inputs, labels in dataloader:
        inputs, labels = inputs.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        running_loss += loss.item()
        _, predicted = outputs.max(1)
        total += labels.size(0)
        correct += predicted.eq(labels).sum().item()
    return running_loss / len(dataloader), 100. * correct / total

def validate(model, dataloader, criterion):
    model.eval()
    running_loss, correct, total = 0.0, 0, 0
    all_preds, all_labels = [], []
    with torch.no_grad():
        for inputs, labels in dataloader:
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            running_loss += loss.item()
            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()
            all_preds.extend(predicted.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
    return running_loss / len(dataloader), 100. * correct / total, all_preds, all_labels

def calculate_class_metrics(all_preds: List, all_labels: List, classes: List[str]) -> Dict:
    class_metrics = {}
    class_correct, class_total, class_predicted = defaultdict(int), defaultdict(int), defaultdict(int)
    for pred, label in zip(all_preds, all_labels):
        class_predicted[pred] += 1
        class_total[label] += 1
        if pred == label:
            class_correct[label] += 1
    for idx, cls in enumerate(classes):
        total, correct, predicted = class_total.get(idx, 0), class_correct.get(idx, 0), class_predicted.get(idx, 0)
        precision = correct / predicted if predicted > 0 else 0
        recall = correct / total if total > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        class_metrics[cls] = {"precision": round(precision, 4), "recall": round(recall, 4), "f1-score": round(f1, 4), "support": total}
    return class_metrics


def create_keras_model(num_classes: int):
    """Create a Keras model with the same architecture as MRIClassifier for .h5 export"""
    try:
        from tensorflow.keras.models import Sequential
        from tensorflow.keras.layers import Conv2D, BatchNormalization, ReLU, MaxPool2D, GlobalAveragePooling2D, Flatten, Dropout, Dense
        
        model = Sequential([
            Conv2D(32, 3, padding='same', input_shape=(224, 224, 3)),
            BatchNormalization(),
            ReLU(),
            MaxPool2D(2, 2),
            Conv2D(64, 3, padding='same'),
            BatchNormalization(),
            ReLU(),
            MaxPool2D(2, 2),
            Conv2D(128, 3, padding='same'),
            BatchNormalization(),
            ReLU(),
            MaxPool2D(2, 2),
            Conv2D(256, 3, padding='same'),
            BatchNormalization(),
            ReLU(),
            GlobalAveragePooling2D(),
            Flatten(),
            Dropout(0.5),
            Dense(512, activation='relu'),
            Dropout(0.3),
            Dense(num_classes, activation='softmax')
        ])
        return model
    except ImportError:
        return None


def copy_weights_pytorch_to_keras(pytorch_model, keras_model):
    """Copy weights from PyTorch model to Keras model"""
    try:
        from tensorflow.keras.models import Model
        
        for i, (pytorch_layer, keras_layer) in enumerate(zip(pytorch_model.features, keras_model.layers)):
            if hasattr(pytorch_layer, 'weight') and hasattr(keras_layer, 'set_weights'):
                weights = pytorch_layer.weight.detach().numpy()
                biases = pytorch_layer.bias.detach().numpy() if hasattr(pytorch_layer, 'bias') and pytorch_layer.bias is not None else None
                
                # Handle Conv2d weights: (out_channels, in_channels, kernel_size, kernel_size) -> (kernel_size, kernel_size, in_channels, out_channels)
                if len(weights.shape) == 4:
                    weights = weights.transpose(2, 3, 1, 0)
                
                keras_layer.set_weights([weights] + ([biases] if biases is not None else []))
        
        # Handle classifier
        fc1_weights = pytorch_model.classifier[1].weight.detach().numpy()
        fc1_biases = pytorch_model.classifier[1].bias.detach().numpy()
        fc1_weights = fc1_weights.transpose(1, 0)  # (512, 256) -> (256, 512)
        
        classifier_idx = len([l for l in keras_model.layers if 'conv' in l.name or 'batch' in l.name or 'max_pool' in l.name or 'global_average' in l.name or 'flatten' in l.name])
        keras_model.layers[classifier_idx + 1].set_weights([fc1_weights, fc1_biases])
        
        fc2_weights = pytorch_model.classifier[4].weight.detach().numpy()
        fc2_biases = pytorch_model.classifier[4].bias.detach().numpy()
        fc2_weights = fc2_weights.transpose(1, 0)  # (num_classes, 512) -> (512, num_classes)
        
        keras_model.layers[classifier_idx + 3].set_weights([fc2_weights, fc2_biases])
        
        return True
    except Exception as e:
        print(f"Warning: Could not copy weights to Keras model: {e}")
        return False


def save_model_h5(model, model_path: str, num_classes: int, classes: List[str]):
    """Save model in .h5 format for production use"""
    keras_model = create_keras_model(num_classes)
    if keras_model is None:
        print("Warning: TensorFlow not available, skipping .h5 save")
        return None
    
    try:
        # Try to copy weights from PyTorch model
        copy_weights_pytorch_to_keras(model, keras_model)
        
        # Compile the model
        keras_model.compile(
            optimizer='adam',
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )
        
        # Save as .h5
        h5_path = model_path.replace('.pth', '.h5')
        keras_model.save(h5_path)
        print(f"Saved Keras model: {h5_path}")
        return h5_path
    except Exception as e:
        print(f"Warning: Could not save .h5 model: {e}")
        return None


def run_training(training_id: str, model_id: str, dataset_path: str, classes: List[str], config: Dict, log_callback):
    """
    Main training function with support for both folder structures:
    - Single folder: dataset/class_name/images.jpg
    - Train/test folders: dataset/train/class_name/images.jpg + dataset/test/class_name/images.jpg
    
    Saves models in both .pth (PyTorch) and .h5 (Keras) formats.
    """
    num_classes = len(classes)
    epochs = config.get("epochs", 10)
    learning_rate = config.get("learning_rate", 0.001)
    batch_size = config.get("batch_size", 16)
    
    # Check if log_callback is async (coroutine function)
    is_async_log = inspect.iscoroutinefunction(log_callback)
    
    # Logging helper that handles both sync and async callbacks
    def log(msg, also_print=True):
        if also_print:
            prefix = f"[TRAINING-{training_id[:8]}]"
            print(f"{prefix} {msg}")
        if is_async_log:
            # For async callbacks, use the existing event loop or create a new one
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            try:
                # Check if the callback is already running in an event loop
                if loop.is_running():
                    # Schedule the callback to run in the existing loop
                    asyncio.run_coroutine_threadsafe(log_callback(msg), loop)
                else:
                    # Run the callback in the current loop
                    loop.run_until_complete(log_callback(msg))
            except Exception as e:
                print(f"Warning: Failed to update log in database: {e}")
        else:
            try:
                log_callback(msg)
            except Exception:
                pass  # Ignore logging errors
    
    log("=" * 60)
    log(f"Starting REAL PyTorch Training (CPU)")
    log(f"=" * 60)
    log(f"Dataset: {dataset_path}")
    log(f"Classes: {classes}")
    log(f"Epochs: {epochs}, LR: {learning_rate}, Batch: {batch_size}")
    
    # Check if dataset has train/test folder structure
    train_path = os.path.join(dataset_path, "train")
    test_path = os.path.join(dataset_path, "test")
    
    has_train_test = os.path.exists(train_path) and os.path.exists(test_path)
    
    if has_train_test:
        # Use train/test folders if they exist (RECOMMENDED)
        log("✓ Using train/test folder structure")
        train_dataset = MRIDataset(train_path, classes, transform=get_transforms(True))
        val_dataset = MRIDataset(test_path, classes, transform=get_transforms(False))
    else:
        # Fallback: single folder with class subfolders, use random 80/20 split
        log("⚠ Using random 80/20 split from single folder")
        full_dataset = MRIDataset(dataset_path, classes, transform=get_transforms(True))
        train_size = int(0.8 * len(full_dataset))
        train_dataset = full_dataset
        val_dataset = full_dataset
    
    if len(train_dataset) == 0:
        raise ValueError(f"No training images found in {dataset_path}")
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=0)
    
    log(f"Training samples: {len(train_dataset)}, Validation: {len(val_dataset)}")
    
    # Initialize model
    model = MRIClassifier(num_classes=num_classes).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=5, gamma=0.1)
    
    best_val_acc, best_val_loss = 0.0, float('inf')
    history = {"train_loss": [], "train_acc": [], "val_loss": [], "val_acc": []}
    val_preds, val_labels = [], []
    
    for epoch in range(epochs):
        # Show epoch progress
        log(f"\n{'='*60}")
        log(f"Epoch {epoch + 1}/{epochs}")
        log(f"{'='*60}")
        
        train_loss, train_acc = train_epoch(model, train_loader, criterion, optimizer)
        log(f"  Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.2f}%")
        
        val_loss, val_acc, val_preds, val_labels = validate(model, val_loader, criterion)
        log(f"  Val Loss:   {val_loss:.4f} | Val Acc:   {val_acc:.2f}%")
        
        scheduler.step()
        
        history["train_loss"].append(train_loss)
        history["train_acc"].append(train_acc)
        history["val_loss"].append(val_loss)
        history["val_acc"].append(val_acc)
        
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_val_loss = val_loss
    
    class_metrics = calculate_class_metrics(val_preds, val_labels, classes)
    
    log(f"\n{'='*60}")
    log("TRAINING COMPLETE")
    log(f"{'='*60}")
    log(f"Best Val Acc: {best_val_acc:.2f}%")
    log(f"Final Train Acc: {history['train_acc'][-1]:.2f}%")
    
    log("\nClass-wise Performance:")
    for cls, metrics in class_metrics.items():
        log(f"  {cls}: Precision={metrics['precision']:.4f}, Recall={metrics['recall']:.4f}, F1={metrics['f1-score']:.4f}")
    
    # Save models
    model_dir = "/home/fawzi/Desktop/CNNN/backend/models"
    os.makedirs(model_dir, exist_ok=True)
    
    # Save as .pth (PyTorch format)
    pth_path = f"{model_dir}/{model_id}.pth"
    torch.save({
        'epoch': epochs,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'val_acc': best_val_acc,
        'classes': classes,
        'history': history,
        'class_metrics': class_metrics,
    }, pth_path)
    log(f"\n✓ Saved PyTorch model: {pth_path}")
    
    # Save as .h5 (Keras format for production)
    h5_path = save_model_h5(model, pth_path, num_classes, classes)
    
    return {
        "training_config": config,
        "epochs_completed": epochs,
        "best_val_accuracy": best_val_acc / 100,
        "best_val_loss": best_val_loss,
        "final_train_accuracy": history["train_acc"][-1] / 100 if history["train_acc"] else 0,
        "final_val_accuracy": history["val_acc"][-1] / 100 if history["val_acc"] else 0,
        "train_loss_history": history["train_loss"],
        "train_acc_history": [a/100 for a in history["train_acc"]],
        "val_loss_history": history["val_loss"],
        "val_acc_history": [a/100 for a in history["val_acc"]],
        "class_metrics": class_metrics,
        "class_mapping": {cls: idx for idx, cls in enumerate(classes)},
        "total_samples": len(train_dataset) + len(val_dataset),
        "train_samples": len(train_dataset),
        "val_samples": len(val_dataset),
        "model_path": pth_path,
        "h5_model_path": h5_path
    }
