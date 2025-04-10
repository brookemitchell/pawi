# --- Imports ---
import streamlit as st
import pandas as pd
from datetime import date, timedelta # Import date and timedelta
from data_loader import load_inventory_data
from simulation import advance_day, add_new_batch, calculate_expiry_status, ALERT_DAYS_BEFORE_EXPIRY, calculate_status, discard_batch # Import calculate_status and discard_batch

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

        # --- Record History ---
        day = st.session_state['day_count']
        item_names = st.session_state['item_params_df'].index
        for item_name in item_names:
            # Ensure total_qoh calculation handles cases where an item might temporarily have no batches
            total_qoh = updated_batches_df[updated_batches_df['item_name'] == item_name]['quantity_on_hand'].sum() if not updated_batches_df[updated_batches_df['item_name'] == item_name].empty else 0
            st.session_state['history'].append({'day': day, 'item_name': item_name, 'total_qoh': total_qoh})
        # --- End Record History ---

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

def reorder_all_callback():
    """Callback to simulate ordering all items currently flagged as 'Reorder Needed'."""
    print("Reorder All callback triggered.") # Debug print
    if 'item_params_df' in st.session_state and st.session_state['item_params_df'] is not None \
       and 'batches_df' in st.session_state and st.session_state['batches_df'] is not None:

        ordered_items_count = 0
        local_item_params_df = st.session_state['item_params_df']
        local_batches_df = st.session_state['batches_df']

        for item_name in local_item_params_df.index:
            try:
                # Calculate total QoH for the item
                item_batches = local_batches_df[local_batches_df['item_name'] == item_name]
                total_qoh = item_batches['quantity_on_hand'].sum()

                # Get ROP safely
                rop = int(local_item_params_df.loc[item_name, 'reorder_point'])

                # Calculate status
                item_status = calculate_status(total_qoh, rop)

                if item_status == "Reorder Needed":
                    print(f"Reordering {item_name}...") # Debug print
                    simulate_order_callback(item_name) # Call the existing single-item order function
                    ordered_items_count += 1
            except (KeyError, ValueError) as e:
                st.warning(f"Skipping reorder check for {item_name} due to data issue: {e}")

        if ordered_items_count > 0:
            st.toast(f"Triggered reorder simulation for {ordered_items_count} items.")
        else:
             st.toast("No items required reordering at this time.") # Feedback even if none ordered

    else:
        st.warning("Cannot perform reorder action: Inventory data not fully loaded.")

def discard_batch_callback(batch_id):
    """Callback to discard a specific batch."""
    print(f"Discard Batch callback triggered for batch_id: {batch_id}") # Debug print
    if 'batches_df' in st.session_state and st.session_state['batches_df'] is not None:
        # Ensure the batch_id exists before attempting discard
        if batch_id in st.session_state['batches_df'].index:
            updated_df = discard_batch(st.session_state['batches_df'], batch_id)
            # Recalculate expiry status after discard and update state
            st.session_state['batches_df'] = update_expiry_status_column(updated_df)
            st.toast(f"Discarded batch {batch_id}.")
        else:
            st.warning(f"Batch ID {batch_id} not found. Cannot discard.")
    else:
        st.warning("Cannot discard batch: Batch data not loaded.")

def advance_week_callback():
    """Callback function to advance the simulation by one week (7 days)."""
    print("Advance Week callback triggered.") # Debug print
    if 'item_params_df' in st.session_state and st.session_state['item_params_df'] is not None \
       and 'batches_df' in st.session_state and st.session_state['batches_df'] is not None \
       and 'current_sim_date' in st.session_state:

        # Get local references to state variables for the loop
        local_batches_df = st.session_state['batches_df']
        local_item_params_df = st.session_state['item_params_df']
        local_current_sim_date = st.session_state['current_sim_date']
        local_day_count = st.session_state['day_count']

        for _ in range(7): # Loop 7 times for 7 days
            local_day_count += 1
            local_current_sim_date += timedelta(days=1)

            # Call the core daily simulation logic
            local_batches_df = advance_day(
                local_batches_df,
                local_item_params_df,
                local_current_sim_date
            )

            # --- Record History for each day within the week ---
            day = local_day_count
            item_names = local_item_params_df.index
            for item_name in item_names:
                total_qoh = local_batches_df[local_batches_df['item_name'] == item_name]['quantity_on_hand'].sum() if not local_batches_df[local_batches_df['item_name'] == item_name].empty else 0
                st.session_state['history'].append({'day': day, 'item_name': item_name, 'total_qoh': total_qoh})
            # --- End Record History ---

        # Update session state AFTER the loop completes
        st.session_state['day_count'] = local_day_count
        st.session_state['current_sim_date'] = local_current_sim_date
        # Update expiry status based on the final date and final batches state
        st.session_state['batches_df'] = update_expiry_status_column(local_batches_df)

        print(f"Advanced by 7 days. Now Day {st.session_state['day_count']}, Sim Date: {st.session_state['current_sim_date']}") # Debug print
        st.toast("Advanced simulation by 7 days.")
    else:
        st.warning("Inventory data not fully loaded or session state incomplete. Cannot advance week.")

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
        # Initialize simulation date BEFORE calculating expiry status
        st.session_state['current_sim_date'] = date.today() # Initialize simulation date
        # Calculate initial expiry status right after loading
        st.session_state['batches_df'] = update_expiry_status_column(batches_df)
        st.session_state['day_count'] = 0 # Initialize day count on successful load
        st.session_state['history'] = [] # Initialize history list on successful load
        print("Data loaded successfully into session state and initial expiry status calculated.")
    else:
        # Store None if loading failed, to prevent trying again
        st.session_state['item_params_df'] = None
        st.session_state['batches_df'] = None
        st.session_state['current_sim_date'] = date.today() # Initialize date even on failure
        st.session_state['day_count'] = 0 # Initialize day count even on failure
        st.session_state['history'] = [] # Initialize history list even on failure
        print("Failed to load data during initialization.")

# --- Sidebar ---
st.sidebar.header("Simulation Controls")
# Display the current day count from session state
current_day = st.session_state.get('day_count', 0)
st.sidebar.metric("Simulation Day", current_day)

# Add the button to trigger the simulation step
st.sidebar.button("Advance One Day", on_click=advance_day_callback)
st.sidebar.button("Advance One Week", on_click=advance_week_callback)


# --- Main Area: Display Data or Error ---
st.header("Inventory Status")

# Check the DataFrames stored in session state
item_params_df = st.session_state.get('item_params_df', None)
batches_df = st.session_state.get('batches_df', None)
current_sim_date = st.session_state.get('current_sim_date', date.today())

# Display current simulation date
st.metric("Current Simulation Date", current_sim_date.strftime('%Y-%m-%d'))

if item_params_df is not None and batches_df is not None:
    # --- Fully Integrated Table Display ---
    # Define headers - Now 8 columns
    col_headers = st.columns(8)
    headers = ["Item Name", "Total QoH", "ROP", "Status", "Earliest Expiry", "Expiry Alerts", "Rec. Order Qty", "Action"] # Renamed "Alerts"
    for col, header in zip(col_headers, headers):
        col.markdown(f"**{header}**") # Use markdown for bold headers

    st.divider() # Add a visual separator

    # Iterate through the item parameters index (item names)
    for item_name in item_params_df.index:
        cols = st.columns(8) # Match header columns
        cols[0].write(item_name) # Column 0: Item Name

        # Filter batches for the current item
        item_batches = batches_df[batches_df['item_name'] == item_name]
        # Calculate total quantity on hand for the item
        total_qoh = item_batches['quantity_on_hand'].sum()
        cols[1].write(total_qoh) # Column 1: Total QoH

        # Get ROP and RoQ from item_params_df
        try:
            rop = int(item_params_df.loc[item_name, 'reorder_point'])
            roq = int(item_params_df.loc[item_name, 'reorder_quantity'])
        except (KeyError, ValueError):
            rop = 0 # Default if missing or invalid
            roq = 0 # Default if missing or invalid
            st.warning(f"Missing/invalid ROP/RoQ for {item_name}")

        cols[2].write(rop) # Column 2: ROP

        # Calculate overall item status
        item_status = calculate_status(total_qoh, rop)

        # Column 3: Status (Overall) - with color
        if item_status == "Reorder Needed":
            cols[3].markdown(f":red[{item_status}]")
        elif item_status == "Low Stock":
            cols[3].markdown(f":orange[{item_status}]")
        elif item_status == "OK":
            cols[3].markdown(f":green[{item_status}]")
        else: # Fallback for "Error" status from calculate_status
            cols[3].write(item_status)

        # Calculate expiry summary stats
        if not item_batches.empty and 'expiry_date' in item_batches.columns and 'expiry_status' in item_batches.columns:
            earliest_expiry_date = item_batches['expiry_date'].min()
            nearing_count = item_batches[item_batches['expiry_status'] == 'Nearing Expiry'].shape[0]
            expired_count = item_batches[item_batches['expiry_status'] == 'Expired'].shape[0]

            # Format earliest expiry date
            if pd.isna(earliest_expiry_date):
                expiry_display = "N/A"
            else:
                try:
                    # Ensure it's datetime before formatting
                    expiry_display = pd.to_datetime(earliest_expiry_date).strftime('%Y-%m-%d')
                except ValueError:
                    expiry_display = "Invalid Date"

            # Create alert display string
            alert_text = []
            if nearing_count > 0:
                alert_text.append(f":warning: {nearing_count} Nearing")
            if expired_count > 0:
                alert_text.append(f":x: {expired_count} Expired")
            alert_display = " / ".join(alert_text) if alert_text else ":heavy_check_mark:" # Green check if no alerts

        else: # Handle cases with no batches or missing columns
            expiry_display = "N/A"
            alert_display = ":heavy_check_mark:" # Assume OK if no batches

        cols[4].write(expiry_display) # Column 4: Earliest Expiry
        cols[5].markdown(alert_display) # Column 5: Expiry Alerts (Expiry Summary) - Use markdown for icons

        cols[6].write(roq) # Column 6: Rec. Order Qty

        # Column 7: Action Button (Conditional)
        if item_status == "Reorder Needed":
            cols[7].button("Simulate Order",
                           key=f"order_{item_name}",
                           on_click=simulate_order_callback,
                           args=(item_name,))
        else:
            cols[7].write("") # Keep the column empty if no action is needed

    # st.caption(f"Displaying inventory status at the end of Day {current_day}.") # Optional caption

    st.divider() # Add separator before the alerts section

    # --- Reorder Suggestions Section (Moved from Sidebar) ---
    st.divider() # Keep the divider for separation
    st.subheader("Reorder Suggestions")

    # Check if data is loaded before attempting to calculate suggestions
    if 'item_params_df' in st.session_state and st.session_state['item_params_df'] is not None \
       and 'batches_df' in st.session_state and st.session_state['batches_df'] is not None:

        items_to_reorder = []
        local_item_params_df = st.session_state['item_params_df'] # Local reference
        local_batches_df = st.session_state['batches_df']       # Local reference

        for item_name in local_item_params_df.index:
            try:
                # Calculate total QoH for the item
                item_batches = local_batches_df[local_batches_df['item_name'] == item_name]
                total_qoh = item_batches['quantity_on_hand'].sum()

                # Get ROP and RoQ safely
                rop = int(local_item_params_df.loc[item_name, 'reorder_point'])
                roq = int(local_item_params_df.loc[item_name, 'reorder_quantity'])

                # Calculate status
                item_status = calculate_status(total_qoh, rop)

                if item_status == "Reorder Needed":
                    items_to_reorder.append({'Item': item_name, 'Reorder Qty': roq})
            except (KeyError, ValueError) as e:
                st.warning(f"Data issue for {item_name}: {e}") # Warn about specific item issues

        if items_to_reorder:
            reorder_df = pd.DataFrame(items_to_reorder)
            st.dataframe(reorder_df, hide_index=True) # Use st.dataframe (no sidebar)
            st.button("Reorder All Suggested", on_click=reorder_all_callback, key="reorder_all_main") # Use st.button, changed key
        else:
            st.info("No items need reordering.") # Use st.info (no sidebar)
    else:
        st.warning("Inventory data not loaded.") # Use st.warning (no sidebar)

    # --- Inventory Trends Graph ---
    st.subheader("Inventory Trends")
    if 'item_params_df' in st.session_state and st.session_state['item_params_df'] is not None:
        item_list = st.session_state['item_params_df'].index.tolist()
    else:
        item_list = []

    if not item_list:
        st.info("Item list not available for trend graph.")
    else:
        selected_items = st.multiselect(
            "Select items to plot history:",
            item_list,
            default=item_list[:min(2, len(item_list))] # Default to first 2 items or fewer
        )

        if st.session_state.get('history') and selected_items:
            history_df = pd.DataFrame(st.session_state['history'])
            filtered_history = history_df[history_df['item_name'].isin(selected_items)]

            if not filtered_history.empty:
                chart_data = filtered_history.pivot(index='day', columns='item_name', values='total_qoh')
                st.line_chart(chart_data)
            else:
                st.info("No history recorded yet for selected items.")
        else:
            st.info("Run simulation or select items to see history graph.")

    # --- Expiring & Expired Batches Section ---
    st.subheader("Expiring & Expired Batches") # Renamed section header
    if batches_df is not None and 'expiry_status' in batches_df.columns:
        # Filter for expiring/expired batches
        alerts_df = batches_df[batches_df['expiry_status'].isin(['Nearing Expiry', 'Expired'])]

        if alerts_df.empty:
            st.info("No items currently nearing expiry or expired.")
        else:
            st.warning("Items requiring attention:") # Add a title/warning

            # --- Custom Table with Discard Buttons ---
            # Define headers
            col_headers = st.columns(5)
            headers = ["Item Name", "Qty", "Expires", "Status", "Action"]
            for col, header in zip(col_headers, headers):
                col.markdown(f"**{header}**")
            st.divider()

            # Iterate through the filtered alerts DataFrame
            for batch_index, row_data in alerts_df.iterrows():
                cols = st.columns(5)
                cols[0].write(row_data['item_name'])
                cols[1].write(row_data['quantity_on_hand'])
                # Format expiry date safely
                expiry_date_str = pd.to_datetime(row_data['expiry_date']).strftime('%Y-%m-%d') if pd.notna(row_data['expiry_date']) else "N/A"
                cols[2].write(expiry_date_str)
                cols[3].write(row_data['expiry_status'])
                # Add the discard button in the 'Action' column
                cols[4].button("Discard", key=f"discard_{batch_index}", on_click=discard_batch_callback, args=(batch_index,))
            # --- End Custom Table ---

    else:
        st.info("Batch data or expiry status not available for alerts.")


else:
    # Display an error message if loading failed during initialization
    st.error("Failed to load inventory data. Please check the database file ('inventory_poc.db') and ensure it's correctly seeded with the new schema (item_parameters, inventory_batches).")

# --- Placeholder for future elements ---
# Add other controls or display elements later
