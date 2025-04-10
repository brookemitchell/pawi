# --- Imports ---
import streamlit as st
import pandas as pd
from data_loader import load_inventory_data # Keep this import
from simulation import advance_day, calculate_status, simulate_order # Import the simulation and status functions

# --- Page Config (Optional but Recommended) ---
st.set_page_config(
    page_title="Veterinary Inventory PoC",
layout="wide"
)

# --- Helper Functions ---
def update_status_column(df: pd.DataFrame) -> pd.DataFrame:
    """Calculates and updates the 'status' column of the DataFrame."""
    if df is None or df.empty:
        return df
    # Ensure required columns exist
    if 'quantity_on_hand' in df.columns and 'reorder_point' in df.columns:
         # Use .apply to calculate status for each row
        df['status'] = df.apply(
            lambda row: calculate_status(row['quantity_on_hand'], row['reorder_point']),
            axis=1
        )
    else:
        print("Error: Missing 'quantity_on_hand' or 'reorder_point' column for status calculation.")
        # Optionally add an error status column or handle differently
        df['status'] = 'Error'
    return df

# --- Callback Functions ---
def advance_day_callback():
    """Callback function to advance the simulation by one day."""
    if 'inventory_df' in st.session_state and st.session_state['inventory_df'] is not None:
        st.session_state['day_count'] += 1
        # Call the simulation function
        updated_df = advance_day(st.session_state['inventory_df'])
        # Calculate status AFTER advancing the day
        final_df = update_status_column(updated_df) # <-- Add this line
        # Update the DataFrame in session state
        st.session_state['inventory_df'] = final_df # <-- Update with final_df
    else:
        # Optionally handle the case where data isn't loaded
        st.warning("Inventory data not loaded. Cannot advance day.")

def simulate_order_callback(item_name: str):
    """Callback function to simulate placing an order for a specific item."""
    if 'inventory_df' in st.session_state and st.session_state['inventory_df'] is not None:
        # Call the order simulation function
        ordered_df = simulate_order(st.session_state['inventory_df'], item_name)
        # Recalculate status for the entire DataFrame after the order
        final_df = update_status_column(ordered_df)
        # Update the DataFrame in session state
        st.session_state['inventory_df'] = final_df
    else:
        st.warning("Inventory data not loaded. Cannot simulate order.")

# --- Title ---
st.title("Veterinary Inventory PoC")

# --- Session State Initialization ---
# Check if the inventory DataFrame is already in the session state
if 'inventory_df' not in st.session_state:
    print("Initializing session state...") # Add print statement for debugging
    # Attempt to load data only if it's not already loaded
    loaded_df = load_inventory_data()
    if loaded_df is not None:
        # Calculate initial status right after loading
        st.session_state['inventory_df'] = update_status_column(loaded_df) # <-- Add this line
        st.session_state['day_count'] = 0 # Initialize day count on successful load
        print("Data loaded and initial status calculated successfully into session state.") # Updated print
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
inventory_df = st.session_state.get('inventory_df', None) # Use .get for safety

if inventory_df is not None:
    # --- Custom Table Display ---
    # Define headers
    col_headers = st.columns(6)
    headers = ["Item Name", "Qty on Hand", "Reorder Point", "Status", "Rec. Order Qty", "Action"]
    for col, header in zip(col_headers, headers):
        col.markdown(f"**{header}**") # Use markdown for bold headers

    st.divider() # Add a visual separator

    # Iterate through the DataFrame rows and display data in columns
    for item_name, row_data in inventory_df.iterrows():
        cols = st.columns(6)
        cols[0].write(item_name)
        cols[1].write(row_data['quantity_on_hand'])
        cols[2].write(row_data['reorder_point'])
        # --- Status Display with Color ---
        status = row_data['status']
        if status == "Reorder Needed":
            cols[3].markdown(f":red[{status}]")
        elif status == "Low Stock":
            cols[3].markdown(f":orange[{status}]")
        elif status == "OK":
            cols[3].markdown(f":green[{status}]")
        else: # Fallback for unexpected status values (e.g., "Error")
            cols[3].write(status)
        cols[4].write(row_data['reorder_quantity']) # Recommended Order Qty
        # --- Action Button ---
        if status == "Reorder Needed":
            # Use item_name (which is the index) directly in key and args
            cols[5].button("Simulate Order",
                           key=f"order_{item_name}",
                           on_click=simulate_order_callback,
                           args=(item_name,)) # Pass item_name to the callback
        else:
            cols[5].write("") # Keep the column empty if no action is needed

    st.caption(f"Displaying inventory status at the end of Day {current_day}.") # Keep the caption

else:
    # Display an error message if loading failed during initialization
    st.error("Failed to load inventory data. Please check the database file ('inventory_poc.db') and ensure it's correctly seeded.")

# --- Placeholder for future elements ---
# Add other controls or display elements later
