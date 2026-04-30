import cv2
import numpy as np
import os
from app.core.aws import s3
from app.core.config import settings

recognizer = cv2.face.LBPHFaceRecognizer_create()

GLOBAL_MODEL_KEY = "employee_records/global_model.yml"
GLOBAL_MODEL_PATH = "/tmp/global_model.yml"

def train_model(employee_id, faces):
    
    try:
        label = int(''.join(filter(str.isdigit, employee_id)))
    except:
        label = 1 # Fallback

    face_samples = []
    ids = []
    
    for face in faces:
       
        if face is not None and face.shape[0] > 50: 
            ids.append(label)
            face_samples.append(face)
    
    if not face_samples:
        print(f"WARNING: No valid faces found to train for {employee_id}")
        return
    
    labels = np.array(ids)
    
    
    try:
        # Load and update
        s3.download_file(settings.S3_BUCKET, "employee_records/global_model.yml", GLOBAL_MODEL_PATH)
        recognizer.read(GLOBAL_MODEL_PATH)
        recognizer.update(face_samples, labels) 
    except:
       
        recognizer.train(face_samples, labels)
    
    
    recognizer.save(GLOBAL_MODEL_PATH)
    with open(GLOBAL_MODEL_PATH, "rb") as f:
        s3.put_object(
            Bucket=settings.S3_BUCKET,
            Key=GLOBAL_MODEL_KEY,
            Body=f.read()
        )

def identify_face(face_img):
    
    try:
        s3.download_file(settings.S3_BUCKET, GLOBAL_MODEL_KEY, GLOBAL_MODEL_PATH)
        recognizer.read(GLOBAL_MODEL_PATH)
        label, confidence = recognizer.predict(face_img)
        
        
        if confidence < 120:
            return label, confidence
        return None, confidence
    except Exception as e:
        print(f"Error in identification: {e}")
        return None, 100