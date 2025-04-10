# --- Imports ---
import streamlit as st
import pandas as pd
from data_loader import load_inventory_data # Keep this import
from simulation import advance_day # Import the simulation function

# --- Page Config (Optional but Recommended) ---
st.set_page_config(
    page_title="Veterinary Inventory PoC",
    layout="wide"
)

# --- Callback Functions ---
def advance_day_callback():
    """Callback function to advance the simulation by one day."""
    if 'inventory_df' in st.session_state and st.session_state['inventory_df'] is not None:
        st.session_state['day_count'] += 1
        # Call the simulation function
        updated_df = advance_day(st.session_state['inventory_df'])
        # Update the DataFrame in session state
        st.session_state['inventory_df'] = updated_df
    else:
        # Optionally handle the case where data isn't loaded
        st.warning("Inventory data not loaded. Cannot advance day.")

# --- Title ---
st.title("Veterinary Inventory PoC")

# --- Session State Initialization ---
# Check if the inventory DataFrame is already in the session state
if 'inventory_df' not in st.session_state:
    print("Initializing session state...") # Add print statement for debugging
    # Attempt to load data only if it's not already loaded
    loaded_df = load_inventory_data()
    if loaded_df is not None:
        st.session_state['inventory_df'] = loaded_df
        st.session_state['day_count'] = 0 # Initialize day count on successful load
        print("Data loaded successfully into session state.")
    else:
        # Store None if loading failed, to prevent trying again
        st.session_state['inventory_df'] = None
        st.session_state['day_count'] = 0 # Initialize day count even on failure
        print("Failed to load data during initialization.")

# --- Sidebar ---
st.sidebar.header("Simulation Controls")
# Display the current day count from session state
# Use .get() to provide a default value if state isn't fully initialized yet
current_day = st.session_state.get('day_count', 0)
st.sidebar.metric("Simulation Day", current_day)

# Add the button to trigger the simulation step
st.sidebar.button("Advance One Day", on_click=advance_day_callback)

# --- Main Area: Display Data or Error ---
st.header("Inventory Status")

# Check the inventory DataFrame stored in session state
if st.session_state['inventory_df'] is not None:
    # Display the DataFrame from session state
    st.dataframe(st.session_state['inventory_df'])
    st.caption(f"Displaying inventory status at the end of Day {current_day}.")
else:
    # Display an error message if loading failed during initialization
    st.error("Failed to load inventory data. Please check the database file ('inventory_poc.db') and ensure it's correctly seeded.")

# --- Placeholder for future elements ---
# Add other controls or display elements later
