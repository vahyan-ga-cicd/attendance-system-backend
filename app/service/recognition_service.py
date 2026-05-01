import cv2
import numpy as np
import os
import time
from app.core.aws import s3
from app.core.config import settings

recognizer = cv2.face.LBPHFaceRecognizer_create()

GLOBAL_MODEL_KEY = "employee_records/global_model.yml"
GLOBAL_MODEL_PATH = "/tmp/global_model.yml"

# MEMORY CACHE: Keep the model loaded in the Lambda RAM
_cached_model_time = 0
_is_model_loaded = False

def load_model_if_needed():
    global _cached_model_time, _is_model_loaded
    
    try:
        # Check S3 metadata for the last modified time
        response = s3.head_object(Bucket=settings.S3_BUCKET, Key=GLOBAL_MODEL_KEY)
        s3_last_modified = response['LastModified'].timestamp()
        
        # If model not loaded OR S3 has a newer version, download it
        if not _is_model_loaded or s3_last_modified > _cached_model_time:
            print("CACHE_MISS: Downloading/Reloading model from S3...")
            s3.download_file(settings.S3_BUCKET, GLOBAL_MODEL_KEY, GLOBAL_MODEL_PATH)
            recognizer.read(GLOBAL_MODEL_PATH)
            _cached_model_time = s3_last_modified
            _is_model_loaded = True
        else:
            # CACHE_HIT: Model is already current in memory
            pass
            
    except Exception as e:
        print(f"Model load warning (might be first run): {e}")

def train_model(employee_id, faces):
    global _is_model_loaded
    
    try:
        # Extract numeric part of ID (e.g., VAH001 -> 1)
        label = int(''.join(filter(str.isdigit, employee_id)))
    except:
        label = int(time.time()) # Unique fallback
    
    face_samples = []
    labels = []
    
    for face in faces:
        if face is not None and face.shape[0] > 40: 
            labels.append(label)
            face_samples.append(face)
    
    if not face_samples:
        return
    
    # Try to load existing model to update it
    load_model_if_needed()
    
    if _is_model_loaded:
        recognizer.update(face_samples, np.array(labels))
    else:
        recognizer.train(face_samples, np.array(labels))
    
    # Save and Upload
    recognizer.save(GLOBAL_MODEL_PATH)
    with open(GLOBAL_MODEL_PATH, "rb") as f:
        s3.put_object(Bucket=settings.S3_BUCKET, Key=GLOBAL_MODEL_KEY, Body=f.read())
    
    # Force reload on next identification
    _is_model_loaded = True
    _cached_model_time = time.time()

def identify_face(face_img):
    try:
        load_model_if_needed()
        
        if not _is_model_loaded:
            return None, 100
            
        label, confidence = recognizer.predict(face_img)
        
        # LBPH: Lower confidence is better match. 120 is standard strict threshold.
        if confidence < 115: 
            return label, confidence
        return None, confidence
    except Exception as e:
        print(f"Identify error: {e}")
        return None, 100