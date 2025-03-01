import face_recognition
import cv2
import numpy as np
import os
import threading
import queue
import time
import pickle
from gtts import gTTS
import pygame

# Step 1: Encode the known faces with caching
def load_known_faces(directory):
    known_face_encodings = []
    known_face_names = []
    print("Loading encodings for faces...")

    for filename in os.listdir(directory):
        if filename.lower().endswith((".jpg", ".png")):
            image_path = os.path.join(directory, filename)
            name, _ = os.path.splitext(filename)
            pkl_path = os.path.join(directory, f"{name}.pkl")

            if os.path.exists(pkl_path):
                # Load encoding from pickle file
                try:
                    with open(pkl_path, 'rb') as pkl_file:
                        encoding = pickle.load(pkl_file)
                        known_face_encodings.append(encoding)
                        known_face_names.append(name)
                        print(f"Loaded encoding from {pkl_path}")
                except Exception as e:
                    print(f"Error loading {pkl_path}: {e}")
                    # If loading fails, proceed to generate encoding
            else:
                # Generate encoding and save to pickle
                try:
                    image = face_recognition.load_image_file(image_path)
                    face_encodings = face_recognition.face_encodings(image)
                    if face_encodings:
                        encoding = face_encodings[0]
                        known_face_encodings.append(encoding)
                        known_face_names.append(name)
                        print(f"Generated and saved encoding for {image_path}")

                        with open(pkl_path, 'wb') as pkl_file:
                            pickle.dump(encoding, pkl_file)
                        
                        language = 'en'
                        sound = gTTS(text=f"Welcome {name}", lang=language, slow=False)

                        sound.save(f"known_faces/{name}.mp3")
                        time.sleep(1)
                    else:
                        print(f"No faces found in {image_path}. Skipping.")
                except Exception as e:
                    print(f"Error processing {image_path}: {e}")
            

    # Convert to NumPy array for faster computations
    known_face_encodings = np.array(known_face_encodings)
    return known_face_encodings, known_face_names

known_faces_dir = "known_faces"
known_face_encodings, known_face_names = load_known_faces(known_faces_dir)

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 20)
current_faces = []


while True:
    ret, frame = cap.read()
    if not ret:
        break
    #frame = cv2.flip(frame, 1)
    #print("Frame Shape: ", frame.shape)

    

    # Resize frame to 1/2 size for faster processing
    #small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)

    # Convert the image from BGR (OpenCV) to RGB (face_recognition)
    #rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
    #print("rgb_small_frame: ", rgb_small_frame.shape)
    # Detect all faces and their encodings in the current frame
    face_locations = face_recognition.face_locations(frame, model='hog')
    face_encodings = face_recognition.face_encodings(frame, face_locations)

    face_names = []
    names = []
    for face_encoding in face_encodings:
        # Compare the detected face with known faces
        distances = np.linalg.norm(known_face_encodings - face_encoding, axis=1)
        best_match_index = np.argmin(distances)

        name = "Unknown"
        confidence = 1.0  # Default confidence for unknown faces

        if distances[best_match_index] <= 0.6:  # 0.6 is a common threshold
            name = known_face_names[best_match_index]
            confidence = (1 - distances[best_match_index]) * 100  # Convert to percentage

        face_names.append((name, confidence))
        names.append(name)

    # Display the results
    for (top, right, bottom, left), (name, confidence) in zip(face_locations, face_names):
        label = f"{name} ({confidence:.0f}%)"

        if name == "Unknown":
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
            cv2.putText(frame, label, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2)
        
        else:
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(frame, label, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)

        
    for name in names:
        if name not in current_faces and not name == 'Unknown':
            current_faces.append(name)

            pygame.mixer.init()
            pygame.mixer.music.load(f"known_faces/{name}.mp3")
            pygame.mixer.music.play()

    current_faces = names
    cv2.imshow('Webcam', frame)

    if cv2.waitKey(1) & 0xFF == ord('c'):
        break

cap.release()
cv2.destroyAllWindows()