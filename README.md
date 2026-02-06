# CarNeu0602

Alzheimer Detection Using CNN - CarNeu0602 Project

## Overview

This project implements a CNN-based model for Alzheimer's disease detection from brain MRI images.

## Backend

The backend is built with FastAPI and includes:
- ML model integration for predictions
- User authentication and management
- Dataset management
- Medical report generation

## Directory Structure

```
CarthaNeruo/
├── backend/
│   ├── uploads/          # Uploaded images (ignored by git)
│   ├── models/          # Trained model files (ignored by git)
│   ├── routes/          # API routes
│   ├── ml/              # Machine learning utilities
│   └── main.py          # FastAPI application entry point
├── 0602/                # Project files (ignored by git)
├── uploads/             # Root uploads directory (ignored by git)
├── kaggle_train/        # Kaggle training data (ignored by git)
├── inject_model.py      # Injection script (ignored by git)
├── kagglefile.ipynb     # Kaggle notebook (ignored by git)
└── README.md            # This file (ignored by git)
```

## Setup

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

## License

MIT License
