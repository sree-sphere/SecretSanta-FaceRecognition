
import streamlit as st
import itertools
import random

# # Define the participants
# participants = ['Sreeprad', 'Sreekari', 'Ram', 'Sreenidh', 'Akhila']

# # Define the restrictions
# restrictions = {
#     'Akhila': ['Sreenidh'],
#     'Sreenidh': ['Akhila'],
#     'Sreekari': ['Ram'],
#     'Ram': ['Sreekari']
# }
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

# Example usage
if st.button("Submit"):
    # You can use the participants and restrictions variables here
    st.write("Participants:", participants)
    st.write("Restrictions:", restrictions)

def is_valid_combination(combination):
    # Check if a person is gifting to themselves
    for i, (giver, receiver) in enumerate(zip(participants, combination)):
        if giver == receiver:
            return False

    # Check the restrictions
    for i, giver in enumerate(participants):
        receiver = combination[i]
        if receiver in restrictions.get(giver, []):
            return False

    return True

def generate_combinations():
    # Generate all permutations of participants
    for combination in itertools.permutations(participants):
        if is_valid_combination(combination):
            yield combination

def get_random_valid_combination():
    valid_combinations = list(generate_combinations())
    return random.choice(valid_combinations)

# Generate a random valid combination when the app starts
if 'combination' not in st.session_state:
    st.session_state.combination = get_random_valid_combination()

# Create a dictionary mapping participants to their gift recipients
gift_recipients = dict(zip(participants, st.session_state.combination))

st.title("Secret Gift Game")

selected_name = st.selectbox("Your name", participants)

col1, col2 = st.columns(2)

with col1:
    if st.button("Check"):
        if selected_name in gift_recipients:
            st.write(f"You, {selected_name}, gift to {gift_recipients[selected_name]}.")
        else:
            st.write("Invalid name selected.")

with col2:
    if st.button("Reshuffle"):
        st.session_state.combination = get_random_valid_combination()
        gift_recipients = dict(zip(participants, st.session_state.combination))
        st.write("Gift assignments have been reshuffled.")
        st.rerun()
