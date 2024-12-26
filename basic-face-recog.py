import streamlit as st
import itertools
import random
import cv2
import numpy as np
from PIL import Image
import face_recognition
import logging
logging.basicConfig(level=logging.INFO)

# Initialize session states
if 'combination' not in st.session_state:
    st.session_state.combination = None
if 'face_encodings' not in st.session_state:
    st.session_state.face_encodings = {}
if 'gift_recipients' not in st.session_state:
    st.session_state.gift_recipients = {}
if 'registration_status' not in st.session_state:
    st.session_state.registration_status = {}
if 'verified_identity' not in st.session_state:
    st.session_state.verified_identity = None

import streamlit as st

# Create a text area for participants
st.header("Participants")
participants_text = st.text_area("Enter participants (comma separated):")

# Create a text area for restrictions
st.header("Restrictions")
restrictions_text = st.text_area("Enter restrictions (format: 'Name: Restricted Name' or 'Name: Restricted Name1, Restricted Name2', one restriction per line):")

# Parse participants
if participants_text:
    participants = [p.strip() for p in participants_text.split(",")]
else:
    participants = []

# Parse restrictions
if restrictions_text:
    restrictions = {}
    for line in restrictions_text.splitlines():
        parts = line.split(":")
        if len(parts) == 2:
            name = parts[0].strip()
            restricted_names = [rn.strip() for rn in parts[1].split(",")]
            restrictions[name] = restricted_names
else:
    restrictions = {}
if st.button("Submit"):
    st.write("Participants:", participants)
    st.write("Restrictions:", restrictions)

def is_valid_combination(combination):
    for i, (giver, receiver) in enumerate(zip(participants, combination)):
        if giver == receiver:
            return False
    
    for i, giver in enumerate(participants):
        receiver = combination[i]
        if receiver in restrictions.get(giver, []):
            return False
    
    return True

def generate_combinations():
    for combination in itertools.permutations(participants):
        if is_valid_combination(combination):
            yield combination

def get_random_valid_combination():
    if st.session_state.combination is None:
        valid_combinations = list(generate_combinations())
        combination = random.choice(valid_combinations)
        st.session_state.combination = combination
        st.session_state.gift_recipients = {
            giver: receiver for giver, receiver in zip(participants, combination)
        }

st.title("Secret Gift Game")

get_random_valid_combination()

selected_name = st.selectbox("Select your name", participants)

tab1, tab2 = st.tabs(["Register Face", "Check Gift Recipient"])

with tab1:
    st.header("Register Your Face")
    
    if selected_name in st.session_state.registration_status:
        st.success(f"Face already registered for {selected_name}")
    
    picture = st.camera_input("Take a picture for registration")
    
    if picture is not None:
        try:
            image = Image.open(picture)
            image_array = np.array(image)
            face_locations = face_recognition.face_locations(image_array)
            
            if face_locations:
                face_encoding = face_recognition.face_encodings(image_array, face_locations)[0]
                st.session_state.face_encodings[selected_name] = face_encoding.tolist()
                st.session_state.registration_status[selected_name] = True
                st.success(f"Face registered successfully for {selected_name}!")
            else:
                st.error("No face detected in the image. Please try again.")
        except Exception as e:
            st.error(f"An error occurred during registration: {str(e)}")

with tab2:
    st.header("Check Gift Recipient")
    
    # First, verify if the selected name is registered
    if selected_name not in st.session_state.registration_status:
        st.warning(f"No face registered for {selected_name}. Please register first.")
    else:
        verify_picture = st.camera_input("Take a picture to verify")
        
        if verify_picture is not None:
            try:
                verify_image = Image.open(verify_picture)
                verify_array = np.array(verify_image)
                verify_face_locations = face_recognition.face_locations(verify_array)
                
                if verify_face_locations:
                    verify_encoding = face_recognition.face_encodings(verify_array, verify_face_locations)[0]
                    
                    # Check against ALL registered faces
                    found_match = False
                    actual_identity = None
                    
                    for name, stored_encoding in st.session_state.face_encodings.items():
                        registered_encoding = np.array(stored_encoding)
                        matches = face_recognition.compare_faces(
                            [registered_encoding], 
                            verify_encoding,
                            tolerance=0.6
                        )
                        
                        if matches[0]:
                            found_match = True
                            actual_identity = name
                            break
                    
                    if found_match:
                        if actual_identity == selected_name:
                            st.success("Identity verified successfully!")
                            st.write(f"You, {selected_name}, gift to {st.session_state.gift_recipients[selected_name]}.")
                            st.session_state.verified_identity = actual_identity
                        else:
                            st.error(f"This looks like {actual_identity}, not {selected_name}! Please select your correct name.")
                    else:
                        st.error("Face not recognized. Please try again or register first.")
                else:
                    st.error("No face detected in the verification image. Please try again.")
            except Exception as e:
                st.error(f"An error occurred during verification: {str(e)}")

# Reshuffle button at the bottom
if st.button("Reshuffle Assignments"):
    st.session_state.combination = None
    get_random_valid_combination()
    st.success("Gift assignments have been reshuffled.")
    st.rerun()

# Debug information
st.sidebar.write("Debug Information:")
st.sidebar.write("Registered users:", list(st.session_state.registration_status.keys()))
st.sidebar.write("Currently verified as:", st.session_state.verified_identity)
