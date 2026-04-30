import cv2
import numpy as np
import base64
import os


cascade_path = os.path.join(os.getcwd(), "haarcascade_frontalface_default.xml")
face_cascade = cv2.CascadeClassifier(cascade_path)


eye_cascade_path = os.path.join(os.getcwd(), "haarcascade_eye.xml")
eye_cascade = cv2.CascadeClassifier(eye_cascade_path) if os.path.exists(eye_cascade_path) else None

def base64_to_image(base64_string):
   
    if "," in base64_string:
        base64_string = base64_string.split(",")[1]
    
    img_data = base64.b64decode(base64_string)
    nparr = np.frombuffer(img_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img

def detect_face(image):
   
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    
    gray = cv2.equalizeHist(gray)
    
    
    faces = face_cascade.detectMultiScale(
        gray, 
        scaleFactor=1.1, 
        minNeighbors=3 
    )
    
    if len(faces) == 0:
        faces = face_cascade.detectMultiScale(gray, 1.2, 2)
        
    if len(faces) == 0:
        faces = face_cascade.detectMultiScale(gray, 1.3, 1)
        
    if len(faces) == 0:
        return None, None
    
   
    faces = sorted(faces, key=lambda x: x[2] * x[3], reverse=True)
    (x, y, w, h) = faces[0]
    
    
    return gray[y:y+h, x:x+w], (x, y, w, h)

def detect_eye_blink(image):
    """
    Robust blink detection. 
    If haarcascade_eye.xml is missing, it uses ROI analysis.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)
    
    faces = face_cascade.detectMultiScale(gray, 1.1, 5)
    if len(faces) == 0:
        return False

    (x, y, w, h) = faces[0]
    roi_gray = gray[y:y+int(h/2), x:x+w] # Top half of face
    
    if eye_cascade is not None:
        # Method A: Use Cascade if available
        eyes = eye_cascade.detectMultiScale(roi_gray, 1.1, 15)
        return len(eyes) == 0 # No eyes found = Blink
    else:
        # Method B: Smart Pixel Analysis (Model-Free)
        # We look for "dark pupils" in the eye region. 
        # When eyes close, the "darkness" of pupils disappears.
        _, thresh = cv2.threshold(roi_gray, 50, 255, cv2.THRESH_BINARY_INV)
        dark_pixels = cv2.countNonZero(thresh)
        
        # If very few dark pixels are found in the eye region, eyes are likely closed.
        return dark_pixels < 50

def process_onboarding_images(images_base64):
   
    processed = []
    for b64 in images_base64:
        img = base64_to_image(b64)
        face, _ = detect_face(img)
        if face is not None:
            processed.append(face)
        else:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            processed.append(gray)
    return processed