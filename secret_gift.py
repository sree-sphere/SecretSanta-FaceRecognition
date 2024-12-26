import streamlit as st
import itertools
import random
import cv2
import numpy as np
from PIL import Image
import face_recognition
import logging
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO)

st.set_page_config(page_title="Secret Gift Exchange", page_icon="🎁", layout="wide", initial_sidebar_state="collapsed")

# CSS for better styling
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    .main {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
    }
    .stButton>button {
        background: linear-gradient(45deg, #2937f0, #9f1ae2);
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 10px;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    .success-message {
        background: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #28a745;
    }
    .error-message {
        background: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #dc3545;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize StreamLit session states
def init_session_states():
    if 'setup_complete' not in st.session_state:
        st.session_state.setup_complete = False
    if 'participants' not in st.session_state:
        st.session_state.participants = []
    if 'restrictions' not in st.session_state:
        st.session_state.restrictions = {}
    if 'mandates' not in st.session_state:
        st.session_state.mandates = {}
    if 'combination' not in st.session_state:
        st.session_state.combination = None
    if 'face_encodings' not in st.session_state:
        st.session_state.face_encodings = {}
    if 'registration_status' not in st.session_state:
        st.session_state.registration_status = {}
    if 'verified_identity' not in st.session_state:
        st.session_state.verified_identity = None

init_session_states()

def save_face_data():
    """Save face encodings to a file"""
    face_data = {name: encoding.tolist() if isinstance(encoding, np.ndarray) else encoding for name, encoding in st.session_state.face_encodings.items()}
    try:
        with open('face_data.json', 'w') as f:
            json.dump(face_data, f)
    except Exception as e:
        st.error(f"Error saving face data: {str(e)}")

def load_face_data():
    """Load face encodings from file"""
    try:
        with open('face_data.json', 'r') as f:
            face_data = json.load(f)
        st.session_state.face_encodings = {name: np.array(encoding) if isinstance(encoding, list) else encoding for name, encoding in face_data.items()}
    except FileNotFoundError:
        pass
    except Exception as e:
        st.error(f"Error loading face data: {str(e)}")

def setup_participants():
    st.markdown("""
        <div style='text-align: center; padding: 2rem;'>
            <h1 style='color: #2937f0;'>🎁 Secret Gift Exchange Setup</h1>
            <p style='font-size: 1.2rem; color: #666;'>Set up your participants and their gifting rules</p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 👥 Add Participants")
        new_participants = st.text_area("Enter participant names (comma-separated)", help="Enter multiple names separated by commas (Eg: Ram, Sita, Kannan)")
        
        if st.button("Add Participants") and new_participants:
            names = [name.strip() for name in new_participants.split(',') if name.strip()]
            for name in names:
                if name not in st.session_state.participants:
                    st.session_state.participants.append(name)
            st.success(f"Added {len(names)} new participant(s)!")

        # participant management
        st.markdown("### ✏️ Edit Participants")
        for i, participant in enumerate(st.session_state.participants):
            col_name, col_remove = st.columns([3, 1])
            with col_name:
                new_name = st.text_input(f"Participant {i+1}", value=participant, key=f"edit_{i}")
                if new_name != participant:
                    # Edit participant names
                    idx = st.session_state.participants.index(participant)
                    st.session_state.participants[idx] = new_name
                    
                    # edit restrictions
                    if participant in st.session_state.restrictions:
                        st.session_state.restrictions[new_name] = st.session_state.restrictions.pop(participant)
                    for p, restricted in st.session_state.restrictions.items():
                        if participant in restricted:
                            restricted[restricted.index(participant)] = new_name
                    
                    # Edit mandates
                    if participant in st.session_state.mandates:
                        st.session_state.mandates[new_name] = st.session_state.mandates.pop(participant)
                    for p, mandated in st.session_state.mandates.items():
                        if mandated == participant:
                            st.session_state.mandates[p] = new_name
                    
                    # Update face encodings
                    if participant in st.session_state.face_encodings:
                        st.session_state.face_encodings[new_name] = st.session_state.face_encodings.pop(participant)
                    
                    # Update registration status
                    if participant in st.session_state.registration_status:
                        st.session_state.registration_status[new_name] = st.session_state.registration_status.pop(participant)
                    
                    st.success(f"Updated {participant} to {new_name}")
                    
            with col_remove:
                if st.button("❌", key=f"remove_{i}"):
                    st.session_state.participants.remove(participant)
                    # Remove from all data structures
                    st.session_state.restrictions.pop(participant, None)
                    st.session_state.mandates.pop(participant, None)
                    st.session_state.face_encodings.pop(participant, None)
                    st.session_state.registration_status.pop(participant, None)
                    st.success(f"Removed {participant}")
                    st.rerun()

    with col2:
        if st.session_state.participants:
            st.markdown("### 🚫 Set Restrictions & Mandates")
            person = st.selectbox("Select person", st.session_state.participants, key="restriction_person")
            restriction_type = st.radio("Rule type", ["Can't gift to", "Must gift to"])
            
            other_person = st.selectbox(
                "Select other person", 
                [p for p in st.session_state.participants if p != person],
                key="restriction_other"
            )

            if st.button("Add Rule"):
                # Handle "Can't gift to"
                if restriction_type == "Can't gift to":
                    if person in st.session_state.mandates and st.session_state.mandates[person] == other_person:
                        st.error(f"Conflict detected: {person} must gift to {other_person}. Cannot add restriction.")
                    else:
                        if person not in st.session_state.restrictions:
                            st.session_state.restrictions[person] = []
                        if other_person not in st.session_state.restrictions[person]:
                            st.session_state.restrictions[person].append(other_person)
                            st.success(f"Added restriction: {person} can't gift to {other_person}")
                
                # Handle "Must gift to"
                else:
                    if person in st.session_state.restrictions and other_person in st.session_state.restrictions[person]:
                        st.error(f"Conflict detected: {person} can't gift to {other_person}. Cannot add mandate.")
                    else:
                        st.session_state.mandates[person] = other_person
                        st.success(f"Added mandate: {person} must gift to {other_person}")

            # Rules management
            st.markdown("### ✏️ Edit Rules")
            st.markdown("#### Restrictions:")
            for person, restricted in st.session_state.restrictions.items():
                for restricted_person in restricted:
                    col_rule, col_remove = st.columns([3, 1])
                    with col_rule:
                        st.write(f"{person} can't gift to {restricted_person}")
                    with col_remove:
                        if st.button("❌", key=f"remove_restriction_{person}_{restricted_person}"):
                            st.session_state.restrictions[person].remove(restricted_person)
                            if not st.session_state.restrictions[person]:
                                del st.session_state.restrictions[person]
                            st.success("Restriction removed")
                            st.rerun()

            st.markdown("#### Mandates:")
            for person, mandated in st.session_state.mandates.items():
                col_rule, col_remove = st.columns([3, 1])
                with col_rule:
                    st.write(f"{person} must gift to {mandated}")
                with col_remove:
                    if st.button("❌", key=f"remove_mandate_{person}"):
                        del st.session_state.mandates[person]
                        st.success("Mandate removed")
                        st.rerun()

    # Setup completion
    if len(st.session_state.participants) >= 2:
        if st.button("Complete Setup", type="primary"):
            st.session_state.setup_complete = True
            st.rerun()

def is_valid_combination(combination):
    """Check if a combination is valid given restrictions and mandates"""
    for i, (giver, receiver) in enumerate(zip(st.session_state.participants, combination)):
        # Check self-gifting
        if giver == receiver:
            return False
        
        # Check restrictions
        if giver in st.session_state.restrictions and receiver in st.session_state.restrictions[giver]:
            return False
        
        # Check mandates
        if giver in st.session_state.mandates and st.session_state.mandates[giver] != receiver:
            return False
    
    return True

def generate_combinations():
    """Generate valid combinations considering restrictions and mandates"""
    for combination in itertools.permutations(st.session_state.participants):
        if is_valid_combination(combination):
            yield combination

def get_random_valid_combination():
    """Get a random valid combination of gift assignments"""
    if st.session_state.combination is None:
        valid_combinations = list(generate_combinations())
        if valid_combinations:
            combination = random.choice(valid_combinations)
            st.session_state.combination = combination
            return True
        return False
    return True

def main_game():
    st.markdown("""
        <div style='text-align: center; padding: 2rem;'>
            <h1 style='color: #2937f0;'>🎁 Secret Gift Exchange</h1>
            <p style='font-size: 1.2rem; color: #666;'>Find out who you're gifting to!</p>
        </div>
    """, unsafe_allow_html=True)

    # Get valid combination
    if not get_random_valid_combination():
        st.error("No valid combinations possible with current restrictions and mandates!")
        if st.button("Reset Setup"):
            st.session_state.setup_complete = False
            st.rerun()
        return


    selected_name = st.selectbox("Select your name", st.session_state.participants)
    tab1, tab2 = st.tabs(["📸 Register Face", "🎁 Check Gift Recipient"])

    with tab1:
        st.markdown("""
            <div style='background: #f8f9fa; padding: 1rem; border-radius: 10px;'>
                <h3>Register Your Face</h3>
                <p>Take a clear photo in good lighting for best results.</p>
            </div>
        """, unsafe_allow_html=True)
        
        if selected_name in st.session_state.registration_status:
            st.markdown(
                f"""<div class='success-message'>
                    Face already registered for {selected_name}
                </div>""",
                unsafe_allow_html=True
            )
        
        picture = st.camera_input("Take a picture for registration")
        
        if picture is not None:
            try:
                image = Image.open(picture)
                image_array = np.array(image)
                face_locations = face_recognition.face_locations(image_array)
                
                if face_locations:
                    # Face detection with multiple attempts
                    face_encoding = face_recognition.face_encodings(
                        image_array, 
                        face_locations,
                        num_jitters=6  # multiple samples for better accuracy
                    )[0]
                    st.session_state.face_encodings[selected_name] = face_encoding.tolist()
                    st.session_state.registration_status[selected_name] = True
                    save_face_data()
                    st.markdown(
                        f"""<div class='success-message'>
                            Face registered successfully for {selected_name}!
                        </div>""",
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        """<div class='error-message'>
                            No face detected. Please ensure:
                            <ul>
                                <li>Good lighting</li>
                                <li>Face is clearly visible</li>
                                <li>Looking directly at the camera</li>
                            </ul>
                        </div>""",
                        unsafe_allow_html=True
                    )
            except Exception as e:
                st.error(f"An error occurred during registration: {str(e)}")

    with tab2:
        st.markdown("""
            <div style='background: #f8f9fa; padding: 1rem; border-radius: 10px;'>
                <h3>Check Your Gift Recipient</h3>
                <p>Verify your identity to see who you're gifting to!</p>
            </div>
        """, unsafe_allow_html=True)
        
        if selected_name not in st.session_state.registration_status:
            st.warning(f"No face registered for {selected_name}. Please register first.")
        else:
            verify_picture = st.camera_input("Take a picture to verify")
            
            if verify_picture is not None:
                try:
                    verify_image = Image.open(verify_picture)
                    verify_array = np.array(verify_image)
                    verify_face_locations = face_recognition.face_locations(verify_array)
                    verify_encoding = None
                    
                    if verify_face_locations:
                        verify_encoding = face_recognition.face_encodings(
                            verify_array,
                            verify_face_locations,
                            num_jitters=3
                        )[0]
                        
                        found_match = False
                        actual_identity = None
                        registered_encoding = None
                        
                        for name, stored_encoding in st.session_state.face_encodings.items():
                            registered_encoding = np.array(stored_encoding)
                            matches = face_recognition.compare_faces(
                                [registered_encoding],
                                verify_encoding,
                                tolerance=0.6  # Adjusted tolerance for better accuracy
                            )
                            
                            if matches[0]:
                                found_match = True
                                actual_identity = name
                                break
                        
                        if found_match:
                            if actual_identity == selected_name:
                                st.balloons()
                                recipient_idx = st.session_state.participants.index(selected_name)
                                recipient = st.session_state.combination[recipient_idx]
                                
                                st.markdown(f"""
                                    <div style='background: linear-gradient(45deg, #85FFBD 0%, #FFFB7D 100%);
                                             padding: 2rem;
                                             border-radius: 15px;
                                             text-align: center;
                                             margin: 2rem 0;'>
                                        <h2 style='color: #1a1a1a;'>🎉 Identity Verified! 🎉</h2>
                                        <h3 style='color: #2937f0;'>You are gifting to:</h3>
                                        <h1 style='color: #1a1a1a; font-size: 3rem;'>{recipient}</h1>
                                        <p style='color: #666;'>Keep it a secret! 🤫</p>
                                    </div>
                                """, unsafe_allow_html=True)
                                
                                st.session_state.verified_identity = actual_identity
                            else:
                                st.markdown(
                                    f"""<div class='error-message'>
                                        This looks like {actual_identity}, not {selected_name}! 
                                        Please select your correct name.
                                    </div>""",
                                    unsafe_allow_html=True
                                )
                        else:
                            st.markdown(
                                """<div class='error-message'>
                                    Face not recognized. Please try again or register first.
                                </div>""",
                                unsafe_allow_html=True
                            )
                    else:
                        st.markdown(
                            """<div class='error-message'>
                                No face detected in the verification image. Please try again.
                            </div>""",
                            unsafe_allow_html=True
                        )
                except Exception as e:
                    st.error(f"An error occurred during verification: {str(e)}")

    # Reshuffle combination button
    if st.button("🔄 Reshuffle Assignments", type="primary"):
        st.session_state.combination = None
        if get_random_valid_combination():
            st.markdown("""
                <div class='success-message'>
                    🎲 Gift assignments have been reshuffled successfully!
                    Everyone will need to verify their identity again to see their new recipient.
                </div>
                """, unsafe_allow_html=True)
            st.balloons()
        else:
            st.error("Couldn't generate new valid combinations. Please check restrictions and mandates.")
        st.rerun()

# Sidebar with debug info and admin controls
with st.sidebar:
    st.markdown("""
        <div style='background: #f8f9fa; padding: 1rem; border-radius: 10px;'>
            <h3>🛠️ Admin Panel</h3>
        </div>
    """, unsafe_allow_html=True)
    
    # Debug section
    with st.expander("📊 System Status"):
        st.write("Registered Users:", list(st.session_state.registration_status.keys()))
        st.write("Currently Verified as:", st.session_state.verified_identity)
        st.write("Total Participants:", len(st.session_state.participants))
    
    # Admin controls
    with st.expander("⚙️ Admin Controls"):
        if st.button("Reset All Data"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            init_session_states()
            st.success("All data has been reset!")
            st.rerun()
        
        if st.button("Export Face Data"):
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f'face_data_backup_{timestamp}.json'
                face_data = {
                    name: encoding.tolist() if isinstance(encoding, np.ndarray) else encoding
                    for name, encoding in st.session_state.face_encodings.items()
                }
                st.download_button(
                    label="Download Face Data Backup",
                    data=json.dumps(face_data),
                    file_name=filename,
                    mime="application/json"
                )
            except Exception as e:
                st.error(f"Error exporting face data: {str(e)}")

def main():
    load_face_data()  # Load saved face data at startup. Empty file will show `Expecting value: line 1 column 1 (char 0)`
    
    if not st.session_state.setup_complete:
        setup_participants()
    else:
        main_game()

if __name__ == "__main__":
    main()