Okay, here is the updated todo.md checklist with the original tasks marked as completed and the new tasks for the Expiry Management feature added.

# Veterinary Inventory Optimization PoC - Development Checklist

## Phase 0: Setup & Prerequisites

-   [x] Create project directory.
-   [x] Set up Python virtual environment (e.g., `python -m venv venv`).
-   [x] Activate virtual environment.
-   [x] Create `requirements.txt` with `streamlit` and `pandas`.
-   [x] Install requirements: `pip install -r requirements.txt`.
-   [x] Create initial empty files: `app.py`, `data_loader.py`, `simulation.py`.
-   [x] Create SQLite database file: `inventory_poc.db`.
-   [x] Define `inventory_items` table schema in SQLite.
-   [x] Populate (seed) `inventory_items` table in `inventory_poc.db` with the 9 specified items and their parameter values. Verify data accuracy.

## Phase 1: Core Implementation (Stockout PoC)

-   **Prompt 1: Project Setup & Data Loader Foundation**
    -   [x] Implement `data_loader.py`: `load_inventory_data` function.
    -   [x] Include SQLite connection logic.
    -   [x] Include DataFrame creation from query results.
    -   [x] Set `item_name` as index.
    -   [x] Calculate `reorder_point` column.
    -   [x] Calculate `reorder_quantity` column.
    -   [x] Rename `initial_quantity_on_hand` to `quantity_on_hand`.
    -   [x] Ensure function returns the DataFrame.
    -   [x] Implement basic `try...except` for DB errors (return None on failure).
-   **Prompt 2: Basic Streamlit App & Initial Data Display**
    -   [x] Implement basic `app.py` structure.
    -   [x] Import `load_inventory_data`.
    -   [x] Add `st.title`.
    -   [x] Call `load_inventory_data` on app run.
    -   [x] Add check for successful data load (DataFrame is not None).
    -   [x] Display loaded DataFrame using `st.dataframe()`.
    -   [x] Display `st.error()` if data loading failed.
-   **Prompt 3: Introducing State Management**
    -   [x] Modify `app.py` to use `st.session_state`.
    -   [x] Load data into `st.session_state['inventory_df']` only if it doesn't exist.
    -   [x] Handle failed load case by storing `None` in session state.
    -   [x] Initialize `st.session_state['day_count'] = 0` only on first load.
    -   [x] Display DataFrame *from* session state.
    -   [x] Add sidebar metric displaying `st.session_state['day_count']`.
-   **Prompt 4: Implementing the Simulation Logic**
    -   [x] Implement `simulation.py`: `advance_day` function (original version).
    -   [x] Function accepts and returns a DataFrame.
    -   [x] Create a copy of the DataFrame inside the function.
    -   [x] Iterate through rows.
    -   [x] Calculate random consumption using `min/max_daily_usage`.
    -   [x] Calculate `new_qoh` ensuring it's `>= 0`.
    -   [x] Update `quantity_on_hand` in the DataFrame copy.
    -   [x] Return the modified DataFrame copy.
-   **Prompt 5: Connecting Simulation to UI Button**
    -   [x] Modify `app.py`: Import `advance_day` (original).
    -   [x] Define `advance_day_callback()` function (original).
    -   [x] Callback increments `day_count` in session state.
    -   [x] Callback calls `advance_day` using DataFrame from session state.
    -   [x] Callback updates DataFrame in session state with the result.
    -   [x] Add `st.sidebar.button("Advance One Day", ...)` triggering the callback.
-   **Prompt 6: Calculating and Displaying Item Status**
    -   [x] Implement `simulation.py`: `calculate_status` function ("Reorder Needed", "Low Stock", "OK").
    -   [x] Modify `app.py`: Import `calculate_status`.
    -   [x] Modify `app.py`: Define `update_status_column(df)` function (original).
    -   [x] Call `update_status_column` after initial load into session state.
    -   [x] Call `update_status_column` within `advance_day_callback`.
    -   [x] Ensure the displayed DataFrame reflects the `status` column.
-   **Prompt 7: Implementing Order Simulation Logic**
    -   [x] Modify `simulation.py`: Implement `simulate_order` function (original - update QoH).
-   **Prompt 8: Preparing the Order Callback Function**
    -   [x] Modify `app.py`: Import `simulate_order` (original).
    -   [x] Define `simulate_order_callback(item_name)` function (original).
    -   [x] Callback calls `simulate_order`.
    -   [x] Callback calls `update_status_column`.
    -   [x] Callback updates DataFrame in session state.
-   **Prompt 9: Custom Table Rendering**
    -   [x] Modify `app.py`: Replace `st.dataframe` with custom rendering loop.
    -   [x] Add table headers using `st.columns` and `st.markdown`.
    -   [x] Iterate through DataFrame rows (`.iterrows()`).
    -   [x] Use `st.columns()` for each row's layout (original columns).
    -   [x] Display data for Item Name, QoH, ROP, Status (text), Rec. RoQ.
    -   [x] Use `cols[ACTION_INDEX].empty()` as placeholder for Action column.
-   **Prompt 10: Adding Conditional Order Buttons and Status Coloring**
    -   [x] Modify `app.py` rendering loop: Implement status coloring (Red/Orange/Green).
    -   [x] Modify `app.py` rendering loop: Implement conditional action button.
    -   [x] Ensure button uses correct `key`, `on_click`, `args`.
    -   [x] Ensure non-applicable rows have an empty action column.
-   **Prompt 11: Final Polish - Error Handling**
    -   [x] Refine `data_loader.py`: Ensure `try...except` around DB operations (original version).
    -   [x] Refine `app.py`: Ensure initial load logic robustly checks for `None` return and displays `st.error`.

## Phase 2: Testing (Stockout PoC - Manual)

-   [x] Test Initialization
-   [x] Test Simulation (`Advance One Day`)
-   [x] Test Ordering (`Simulate Order`)
-   [x] Test UI/Layout
-   [x] Test Error Handling

## Phase 3: Final Review (Stockout PoC)

-   [x] Code review for clarity, comments, and adherence to structure.
-   [x] Final check against all requirements in the specification document.
-   [x] Ensure `requirements.txt` is accurate.
-   [x] Add a simple `README.md` explaining how to set up and run the PoC.

---

## Phase 4: Expiry Management Feature Implementation

-   **E0: Preparation (Manual DB Changes)**
    -   [ ] Backup existing `inventory_items` table.
    -   [ ] Create `item_parameters` table (Schema: item_name PK, usage, buffer/target, ROP, RoQ, shelf_life_months).
    -   [ ] Create `inventory_batches` table (Schema: batch_id PK AUTOINCREMENT, item_name, quantity_on_hand, expiry_date DATE).
    -   [ ] Populate `item_parameters` from backup, adding `standard_shelf_life_months`.
    -   [ ] Populate `inventory_batches` with one initial batch per item using original initial QoH and calculated initial expiry date.
-   **E1: Data Model & Foundation Refactor**
    -   **Prompt E1.1: Update Data Loader for New Schema**
        -   [ ] Modify `data_loader.py`: Update `load_inventory_data` function.
        -   [ ] Query `item_parameters` into `item_params_df`, set index.
        -   [ ] Query `inventory_batches` into `batches_df`, set index.
        -   [ ] Convert `batches_df['expiry_date']` to datetime objects (`pd.to_datetime`).
        -   [ ] Return both `item_params_df, batches_df`.
        -   [ ] Update error handling to return `None, None`.
    -   **Prompt E1.2: Adapt App State & Basic Display**
        -   [ ] Modify `app.py`: Import `datetime`.
        -   [ ] Update initial state check for `'item_params_df'`.
        -   [ ] Store `item_params_df` and `batches_df` in session state.
        -   [ ] Initialize `st.session_state['current_sim_date']`.
        -   [ ] Display `current_sim_date` metric.
        -   [ ] Modify main table loop to iterate `item_params_df.index`.
        -   [ ] Calculate `total_qoh` from `batches_df` per item.
        -   [ ] Display only `Item Name` and `Total QoH` initially.
        -   [ ] Comment out/remove previous ROP, Status, RoQ, Action display.
        -   [ ] Comment out/disable `advance_day_callback`, `simulate_order_callback` and buttons.
-   **E2: FEFO Consumption**
    -   **Prompt E2.1: Implement FEFO Consumption Logic**
        -   [ ] Modify `simulation.py`: Replace `advance_day` function signature.
        -   [ ] Implement iteration by item.
        -   [ ] Implement random consumption calculation per item.
        -   [ ] Filter active, non-expired batches for item.
        -   [ ] Sort active batches by `expiry_date`.
        -   [ ] Implement consumption loop depleting batches according to FEFO.
        -   [ ] Update `quantity_on_hand` in main DataFrame copy.
        -   [ ] Remove zero-quantity batches after processing all items.
        -   [ ] Return updated `batches_df` copy.
    -   **Prompt E2.2: Integrate FEFO Simulation into App**
        -   [ ] Modify `app.py`: Import new `advance_day`.
        -   [ ] Re-enable `advance_day_callback()` function.
        -   [ ] Update callback to increment `current_sim_date`.
        -   [ ] Update callback to call new `advance_day` with correct arguments.
        -   [ ] Update callback to store result in `st.session_state['batches_df']`.
        -   [ ] Re-enable the "Advance One Day" button.
-   **E3: Batch Receiving Simulation**
    -   **Prompt E3.1: Implement Batch Addition Logic**
        -   [ ] Modify `simulation.py`: Replace `simulate_order` with `add_new_batch` function.
        -   [ ] Function accepts batches, params, item name, current date.
        -   [ ] Get `shelf_life_months` and `reorder_quantity` from params.
        -   [ ] Calculate `expiry_date` using `current_sim_date` and `shelf_life_months`.
        -   [ ] Create new batch data dictionary/row.
        -   [ ] Use `pd.concat` to add the new batch row to DataFrame copy (handle index).
        -   [ ] Return updated `batches_df` copy.
    -   **Prompt E3.2: Update Order Callback Function**
        -   [ ] Modify `app.py`: Import `add_new_batch`.
        -   [ ] Re-enable `simulate_order_callback(item_name)` function.
        -   [ ] Update callback to call `add_new_batch` with correct arguments.
        -   [ ] Update callback to store result in `st.session_state['batches_df']`.
        -   [ ] Keep UI button disabled for now.
-   **E4: Expiry Status Calculation & Alert Display**
    -   **Prompt E4.1: Implement Expiry Status Calculation**
        -   [ ] Modify `simulation.py`: Define `ALERT_DAYS_BEFORE_EXPIRY` constant.
        -   [ ] Modify `simulation.py`: Create `calculate_expiry_status` function (returns "Expired", "Nearing Expiry", "OK", handles NaT).
        -   [ ] Modify `app.py`: Import `calculate_expiry_status`, `ALERT_DAYS_BEFORE_EXPIRY`.
        -   [ ] Modify `app.py`: Define `update_expiry_status_column(batches_df)` function.
        -   [ ] Call `update_expiry_status_column` after initial load, `advance_day`, and `add_new_batch`.
        -   [ ] Ensure result stored back in `st.session_state['batches_df']`.
    -   **Prompt E4.2: Add Expiry Alerts UI Section**
        -   [ ] Modify `app.py`: Add `st.subheader("Expiry Alerts")`.
        -   [ ] Filter `batches_df` for "Nearing Expiry" or "Expired" statuses.
        -   [ ] Display message if filter is empty.
        -   [ ] Display filtered alerts data (`item_name`, `quantity_on_hand`, `expiry_date`, `expiry_status`) using `st.dataframe()`. Format date.
-   **E5: UI Integration & Restoration**
    -   **Prompt E5.1: Enhance Main Table with Expiry Summary**
        -   [ ] Modify `app.py` main table loop: Calculate `earliest_expiry_date`, `nearing_count`, `expired_count` per item from filtered `batches_df`.
        -   [ ] Format `earliest_expiry_date` and create `alert_display` string/icons.
        -   [ ] Modify `st.columns` layout to add "Earliest Expiry", "Alerts" columns.
        -   [ ] Display calculated summary info in new columns.
        -   [ ] Update table headers.
    -   **Prompt E5.2: Restore ROP/Status/Ordering Functionality**
        -   [ ] Modify `app.py` main table loop: Import/ensure `calculate_status` exists.
        -   [ ] Retrieve item `rop` and `roq` from `item_params_df`.
        -   [ ] Calculate overall `item_status` using `total_qoh` and `rop`.
        -   [ ] Update `st.columns` layout to include all needed columns (Item Name, Total QoH, ROP, Status(Overall), Earliest Expiry, Alerts, Rec. Order Qty, Action).
        -   [ ] Display `rop`.
        -   [ ] Display overall `item_status` with color formatting.
        -   [ ] Display `roq`.
        -   [ ] Re-enable conditional "Simulate Order" button based on `item_status`. Ensure it calls `simulate_order_callback(item_name)`.
        -   [ ] Update table headers.

## Phase 5: Testing (Expiry Feature - Manual)

-   [ ] **Test Data Loading & Initial State:**
    -   [ ] App loads without errors after DB changes.
    -   [ ] Initial `current_sim_date` is displayed correctly.
    -   [ ] Main table shows items with correct initial `Total QoH` (matching seeded batch quantities).
    -   [ ] Initial "Earliest Expiry" dates look reasonable (based on seeding).
    -   [ ] Initial "Alerts" column looks correct (likely "OK" or ":heavy_check_mark:" initially).
    -   [ ] ROP, overall Status, Rec. RoQ, and Action button are displayed correctly based on initial total QoH.
    -   [ ] Initial "Expiry Alerts" section is empty or shows correct initial alerts based on seeding.
-   [ ] **Test FEFO Consumption (`Advance One Day`):**
    -   [ ] Advance day. `current_sim_date` updates.
    -   [ ] `Total QoH` decreases.
    -   [ ] **Crucially:** Advance day until a batch for an item is expected to be fully consumed. Verify the next day's consumption for that item comes from the *next* earliest expiring batch. (May require inspecting `st.session_state['batches_df']` via debugger or temporary print).
    -   [ ] Verify `Earliest Expiry` date updates correctly in main table if the earliest batch is consumed.
-   [ ] **Test Batch Receiving (`Simulate Order`):**
    -   [ ] Trigger "Simulate Order" for an item needing reorder.
    -   [ ] Verify `Total QoH` increases by the correct `reorder_quantity`.
    -   [ ] Verify a new batch appears for that item (check `st.session_state['batches_df']` or potentially add temporary batch display). Verify its expiry date is correctly calculated (`current_sim_date + shelf_life`).
    -   [ ] Verify overall item status updates correctly after ordering.
-   [ ] **Test Expiry Status & Alerts:**
    -   [ ] Advance day until a batch's `expiry_date` is less than `current_sim_date`. Verify its status becomes "Expired". Verify it appears in the "Expiry Alerts" section. Verify the "Alerts" summary column updates.
    -   [ ] Advance day until a batch's `expiry_date` is within `ALERT_DAYS_BEFORE_EXPIRY` of `current_sim_date`. Verify its status becomes "Nearing Expiry". Verify it appears in the "Expiry Alerts" section. Verify the "Alerts" summary column updates.
    -   [ ] Verify consumption logic skips "Expired" batches.
-   [ ] **Test UI Integration:**
    -   [ ] Confirm all columns in the main table display correct, relevant data.
    -   [ ] Confirm layout of main table and Expiry Alerts section.
    -   [ ] Confirm conditional formatting (status colors, alert icons) works as expected.

## Phase 6: Final Review (Expiry Feature)

-   [ ] Code review for clarity, comments, handling of dates/DataFrames, and adherence to structure.
-   [ ] Final check against requirements for the expiry management feature.
-   [ ] Update `README.md` if setup or running instructions changed.
