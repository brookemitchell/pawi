# --- Imports ---
import streamlit as st
import pandas as pd
from datetime import date, timedelta # Import date and timedelta
from data_loader import load_inventory_data
from simulation import advance_day, add_new_batch, calculate_expiry_status, ALERT_DAYS_BEFORE_EXPIRY # Import new functions/constants
# from simulation import calculate_status # Keep calculate_status commented for now

# --- Page Config (Optional but Recommended) ---
st.set_page_config(page_title="Pawfect inventory", layout="wide")

# --- Helper Functions ---
# def update_status_column(df: pd.DataFrame) -> pd.DataFrame:
#     """Calculates and updates the 'status' column of the DataFrame."""
#     if df is None or df.empty:
#         return df
#     # Ensure required columns exist
#     if 'quantity_on_hand' in df.columns and 'reorder_point' in df.columns:
#          # Use .apply to calculate status for each row
#         df['status'] = df.apply(
#             lambda row: calculate_status(row['quantity_on_hand'], row['reorder_point']),
#             axis=1
#         )
#     else:
#         print("Error: Missing 'quantity_on_hand' or 'reorder_point' column for status calculation.")
#         # Optionally add an error status column or handle differently
#         df['status'] = 'Error'
#     return df

def update_expiry_status_column(batches_df: pd.DataFrame) -> pd.DataFrame:
    """Applies expiry status calculation to the batches DataFrame."""
    if batches_df is None or batches_df.empty:
        return batches_df

    # Ensure 'expiry_date' is datetime - should be handled by loader/simulation, but good practice
    if 'expiry_date' in batches_df.columns and not pd.api.types.is_datetime64_any_dtype(batches_df['expiry_date']):
        batches_df['expiry_date'] = pd.to_datetime(batches_df['expiry_date'], errors='coerce')

    if 'current_sim_date' not in st.session_state:
        st.error("Simulation date not found in session state. Cannot calculate expiry status.")
        return batches_df # Return unchanged if date is missing

    current_sim_date = st.session_state['current_sim_date']
    df = batches_df.copy() # Work on a copy

    # Apply the calculation function
    df['expiry_status'] = df.apply(
        lambda row: calculate_expiry_status(row.get('expiry_date'), current_sim_date, ALERT_DAYS_BEFORE_EXPIRY),
        axis=1
    )
    return df


# --- Callback Functions ---
def advance_day_callback():
    """Callback function to advance the simulation by one day using FEFO."""
    if 'item_params_df' in st.session_state and st.session_state['item_params_df'] is not None \
       and 'batches_df' in st.session_state and st.session_state['batches_df'] is not None \
       and 'current_sim_date' in st.session_state:

        st.session_state['day_count'] += 1
        # Increment the simulation date
        st.session_state['current_sim_date'] += timedelta(days=1)

        # Call the new simulation function with FEFO logic
        updated_batches_df = advance_day(
            st.session_state['batches_df'],
            st.session_state['item_params_df'],
            st.session_state['current_sim_date']
        )
        # Update the batches DataFrame in session state AFTER calculating status
        st.session_state['batches_df'] = update_expiry_status_column(updated_batches_df)
        print(f"Advanced to Day {st.session_state['day_count']}, Sim Date: {st.session_state['current_sim_date']}") # Debug print
    else:
        # Handle the case where data isn't loaded or state is incomplete
        st.warning("Inventory data not fully loaded or session state incomplete. Cannot advance day.")

def simulate_order_callback(item_name: str):
    """Callback function to simulate placing an order (adding a new batch) for a specific item."""
    if 'item_params_df' in st.session_state and st.session_state['item_params_df'] is not None \
       and 'batches_df' in st.session_state and st.session_state['batches_df'] is not None \
       and 'current_sim_date' in st.session_state:

        # Call the function to add a new batch
        updated_batches_df = add_new_batch(
            st.session_state['batches_df'],
            st.session_state['item_params_df'],
            item_name,
            st.session_state['current_sim_date']
        )
        # Update the batches DataFrame in session state AFTER calculating status
        st.session_state['batches_df'] = update_expiry_status_column(updated_batches_df)
        print(f"Simulated order for {item_name}. New batch added.") # Debug print
    else:
        st.warning("Inventory data not fully loaded or session state incomplete. Cannot simulate order.")

# --- Title ---
st.title("Pawfect inventory")

# --- Session State Initialization ---
# Check if the item parameters DataFrame is already in the session state
if 'item_params_df' not in st.session_state:
    print("Initializing session state...")
    # Attempt to load data only if it's not already loaded
    item_params_df, batches_df = load_inventory_data() # Unpack the tuple
    if item_params_df is not None and batches_df is not None: # Check if both loaded successfully
        st.session_state['item_params_df'] = item_params_df
        # Calculate initial expiry status right after loading
        st.session_state['batches_df'] = update_expiry_status_column(batches_df)
        st.session_state['current_sim_date'] = date.today() # Initialize simulation date
        st.session_state['day_count'] = 0 # Initialize day count on successful load
        print("Data loaded successfully into session state and initial expiry status calculated.")
    else:
        # Store None if loading failed, to prevent trying again
        st.session_state['item_params_df'] = None
        st.session_state['batches_df'] = None
        st.session_state['current_sim_date'] = date.today() # Initialize date even on failure
        st.session_state['day_count'] = 0 # Initialize day count even on failure
        print("Failed to load data during initialization.")

# --- Sidebar ---
st.sidebar.header("Simulation Controls")
# Display the current day count from session state
current_day = st.session_state.get('day_count', 0)
st.sidebar.metric("Simulation Day", current_day)

# Add the button to trigger the simulation step
st.sidebar.button("Advance One Day", on_click=advance_day_callback)

# --- Main Area: Display Data or Error ---
st.header("Inventory Status")

# Check the DataFrames stored in session state
item_params_df = st.session_state.get('item_params_df', None)
batches_df = st.session_state.get('batches_df', None)
current_sim_date = st.session_state.get('current_sim_date', date.today())

# Display current simulation date
st.metric("Current Simulation Date", current_sim_date.strftime('%Y-%m-%d'))

if item_params_df is not None and batches_df is not None:
    # --- Simplified Table Display ---
    # Define headers
    col_headers = st.columns(2) # Only two columns now
    headers = ["Item Name", "Total Quantity on Hand"]
    for col, header in zip(col_headers, headers):
        col.markdown(f"**{header}**") # Use markdown for bold headers

    st.divider() # Add a visual separator

    # Iterate through the item parameters index (item names)
    for item_name in item_params_df.index:
        cols = st.columns(2) # Match header columns
        cols[0].write(item_name)

        # Filter batches for the current item
        item_batches = batches_df[batches_df['item_name'] == item_name]
        # Calculate total quantity on hand for the item
        total_qoh = item_batches['quantity_on_hand'].sum()
        cols[1].write(total_qoh)

        # --- ROP, Status, Rec. Order Qty, Action columns are removed/commented out ---
        # cols[2].write(row_data['reorder_point'])
        # status = row_data['status']
        # if status == "Reorder Needed":
        #     cols[3].markdown(f":red[{status}]")
        # elif status == "Low Stock":
        #     cols[3].markdown(f":orange[{status}]")
        # elif status == "OK":
        #     cols[3].markdown(f":green[{status}]")
        # else:
        #     cols[3].write(status)
        # cols[4].write(row_data['reorder_quantity']) # Recommended Order Qty
        # if status == "Reorder Needed":
        #     cols[5].button("Order",
        #                    key=f"order_{item_name}",
        #                    on_click=simulate_order_callback,
        #                    args=(item_name,))
        # else:
        #     cols[5].write("")

    # st.caption(f"Displaying inventory status at the end of Day {current_day}.") # Caption removed/modified

else:
    # Display an error message if loading failed during initialization
    st.error("Failed to load inventory data. Please check the database file ('inventory_poc.db') and ensure it's correctly seeded with the new schema (item_parameters, inventory_batches).")

# --- Placeholder for future elements ---
# Add other controls or display elements later
