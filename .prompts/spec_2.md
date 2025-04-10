Okay, planning the addition of the Expiry Management feature requires a structured approach as it significantly impacts the existing data model and logic. Here's a plan following the same methodology we used before:

**1. Goal Ingestion & Clarification (Recap & Elaboration)**

*   **Refined Goal:** Enhance the PoC to track inventory batches with specific expiry dates, implement First-Expired, First-Out (FEFO) consumption, simulate receiving new batches with shelf lives, and alert users to items nearing expiration or already expired.
*   **Pain Point Addressed:** Reducing waste by proactively identifying stock close to its expiry date.
*   **Key Challenges:**
    *   Shifting from item-level tracking to batch-level tracking.
    *   Implementing FEFO logic during consumption simulation.
    *   Handling date calculations (expiry dates, simulation date).
    *   Designing UI elements to display batch/expiry information clearly without overwhelming the user.
*   **Simplifications for PoC v2:**
    *   We will assume storage conditions are always met (no temperature excursion impact).
    *   "Smart discard" will simply mean highlighting expired items, not predicting optimal discard times based on forecasts.
    *   Receiving batches will be simplified: simulating an order adds a new batch with a standard shelf life, rather than requiring manual entry of expiry dates for received goods.

**2. Detailed Blueprint Drafting (Expiry Feature Additions)**

*   **High-level System Architecture:** Remains a Streamlit app using Pandas and SQLite. The core change is the shift to a batch-centric data model.
*   **Key Functional Components (Updates & Additions):**
    *   **Data Model:** Transition from a single inventory table to potentially two: `item_parameters` (static info like ROP, RoQ thresholds, shelf life) and `inventory_batches` (dynamic batch info: item name, quantity, expiry date).
    *   **Data Loader (`data_loader.py`):** Needs updating to read from the new table structure(s).
    *   **Simulation Engine (`simulation.py`):**
        *   `advance_day`: Major rewrite to implement FEFO consumption across batches for each item.
        *   `add_new_batch`: New function to simulate receiving an order, adding a new batch record with a calculated expiry date based on standard shelf life. Replaces the previous simple QoH update logic in `simulate_order`.
        *   `calculate_expiry_status`: New function to determine if a batch is "OK", "Nearing Expiry", or "Expired" based on the current simulation date.
    *   **Main Application (`app.py`):**
        *   **State Management:** Will now need to manage the `batches_df`, `item_params_df`, and the `current_sim_date`.
        *   **UI Rendering:** The main inventory display needs rethinking. It should likely show *summary* information per item (total QoH, earliest expiry, alert count) derived from the batch data. A separate section for detailed "Expiry Alerts" is needed. The "Simulate Order" button logic remains similar but triggers `add_new_batch`.
*   **Data Requirements:**
    *   **New Schema:**
        *   `item_parameters` (SQLite Table): `item_name` (PK), `min_daily_usage`, `max_daily_usage`, `buffer_days`, `target_days`, `reorder_point` (calculated or stored), `reorder_quantity` (calculated or stored), `standard_shelf_life_months`.
        *   `inventory_batches` (SQLite Table & Runtime DataFrame): `batch_id` (PK, auto-increment), `item_name` (FK), `quantity_on_hand`, `expiry_date`.
    *   **Configuration:** Need a system-wide constant for `ALERT_DAYS_BEFORE_EXPIRY` (e.g., 30 days).
*   **Technology Stack:** No changes (Python, Streamlit, Pandas, SQLite).

**3. Iterative Chunking (Epics/Features for Expiry)**

*   **Chunk E1: Data Model & Foundation Refactor:** Restructure the SQLite database and Pandas DataFrames to support `item_parameters` and `inventory_batches`. Update data loading and adapt the main UI to display basic total QoH derived from batches. *This temporarily breaks ROP/status features.*
*   **Chunk E2: FEFO Consumption:** Implement the First-Expired, First-Out consumption logic within the `advance_day` simulation, correctly depleting quantities from the appropriate batches.
*   **Chunk E3: Batch Receiving Simulation:** Implement the `add_new_batch` logic triggered by the "Simulate Order" button, calculating expiry dates based on a standard shelf life per item.
*   **Chunk E4: Expiry Status Calculation & Alert Display:** Calculate expiry status ("OK", "Nearing", "Expired") for each batch based on the simulation date. Add a dedicated "Expiry Alerts" section to the UI showing problematic batches.
*   **Chunk E5: UI Integration & Restoration:** Re-integrate ROP/Status checks based on total QoH per item. Enhance the main inventory table to show summary expiry information (e.g., earliest expiry, alert counts) alongside total QoH.

**4. Granular Step Breakdown & Refinement (Expiry Feature)**

**(Chunk E1 Steps - Data Model & Foundation Refactor)**

*   **Step E1.1:** **Define & Create New DB Schema:**
    *   Modify `inventory_poc.db`.
    *   Create `item_parameters` table (schema above). Populate with existing item names, usage, buffer/target days, ROP/RoQ (or calculate later). Add a new `standard_shelf_life_months` column (e.g., Parvo=12, Slides=24, etc.).
    *   Create `inventory_batches` table (schema above: `batch_id` INTEGER PRIMARY KEY AUTOINCREMENT, `item_name` TEXT, `quantity_on_hand` INTEGER, `expiry_date` DATE).
    *   Populate `inventory_batches` with *one initial batch* per item: Use the `initial_quantity_on_hand` from the previous spec. Calculate an initial `expiry_date` (e.g., `today + standard_shelf_life / 2`).
*   **Step E1.2:** **Update Data Loader (`data_loader.py`):**
    *   Modify `load_inventory_data` to load data from *both* `item_parameters` and `inventory_batches` tables.
    *   Have it return two DataFrames: `item_params_df` (indexed by `item_name`) and `batches_df`.
*   **Step E1.3:** **Update App State (`app.py`):**
    *   Modify initial state setup: Load *both* DataFrames into `st.session_state` (`st.session_state['item_params_df']`, `st.session_state['batches_df']`).
    *   Initialize `st.session_state['current_sim_date']` (e.g., using `datetime.date.today()`).
*   **Step E1.4:** **Adapt Main Display (Basic) (`app.py`):**
    *   Modify the main table rendering loop: It should now iterate based on `item_params_df.index` (the item names).
    *   Inside the loop, calculate `total_qoh = st.session_state['batches_df'][st.session_state['batches_df']['item_name'] == item_name]['quantity_on_hand'].sum()`.
    *   Display only `Item Name` and the calculated `total_qoh` for now. *Comment out/remove ROP, Status, Rec. RoQ, Action columns temporarily.* The app should run and show items and their total quantities based on the new batch structure.

**(Chunk E2 Steps - FEFO Consumption)**

*   **Step E2.1:** **Implement FEFO Logic (`simulation.py`):**
    *   Rewrite `advance_day(batches_df, item_params_df, current_sim_date)`:
        *   Input: Current batches, item parameters, current date.
        *   Output: Updated batches DataFrame.
        *   Make a copy of `batches_df`.
        *   Loop through each `item_name` in `item_params_df`.
        *   Calculate `daily_consumption` for the item (random int based on min/max usage from `item_params_df`).
        *   Filter the `batches_df` copy for the current `item_name`.
        *   Filter out already expired batches (`expiry_date < current_sim_date`).
        *   Sort these active batches by `expiry_date` ascending (FEFO).
        *   Iterate through the sorted, active batches:
            *   If `daily_consumption` > 0:
                *   `consume_amount = min(daily_consumption, batch_qoh)`
                *   Update the batch's `quantity_on_hand` in the main DataFrame copy using its `batch_id`.
                *   `daily_consumption -= consume_amount`
            *   Else: break inner loop.
        *   After iterating, remove rows from the DataFrame copy where `quantity_on_hand <= 0`.
    *   Return the updated DataFrame copy.
*   **Step E2.2:** **Integrate FEFO into App (`app.py`):**
    *   Update `advance_day_callback`:
        *   Increment `st.session_state['current_sim_date']` by one day (`timedelta(days=1)`).
        *   Call the new `advance_day` function, passing the required DataFrames and the *new* `current_sim_date`.
        *   Update `st.session_state['batches_df']` with the result.
    *   Verify that clicking "Advance One Day" correctly reduces the total QoH displayed in the adapted main table (E1.4).

**(Chunk E3 Steps - Batch Receiving Simulation)**

*   **Step E3.1:** **Implement Batch Addition (`simulation.py`):**
    *   Create `add_new_batch(batches_df, item_params_df, item_name, current_sim_date)` function:
        *   Input: Current batches, item params, item name to order, current date.
        *   Output: Updated batches DataFrame.
        *   Make a copy of `batches_df`.
        *   Get `shelf_life = item_params_df.loc[item_name, 'standard_shelf_life_months']`.
        *   Get `quantity_to_add = item_params_df.loc[item_name, 'reorder_quantity']`. (Assuming RoQ is stored/calculable here).
        *   Calculate `expiry_date = current_sim_date + pd.DateOffset(months=shelf_life)`. Ensure this results in a date/datetime object compatible with the column.
        *   Create a new dictionary or DataFrame row: `{'item_name': item_name, 'quantity_on_hand': quantity_to_add, 'expiry_date': expiry_date}`.
        *   Use `pd.concat` to append this new row to the DataFrame copy. **Important:** Ensure the index is handled correctly (e.g., `ignore_index=True` if not using `batch_id` from DB yet, or ensure `batch_id` is managed if applicable). For simplicity, maybe focus on the runtime DataFrame manipulation first.
    *   Return the updated DataFrame copy.
*   **Step E3.2:** **Update Order Callback (`app.py`):**
    *   Modify `simulate_order_callback(item_name)`:
        *   Call `add_new_batch`, passing the required DataFrames, `item_name`, and the `current_sim_date`.
        *   Update `st.session_state['batches_df']` with the result.
    *   *Note: The button triggering this is still commented out from E1.4. We are just updating the callback function for now.*

**(Chunk E4 Steps - Expiry Status Calculation & Alert Display)**

*   **Step E4.1:** **Define Alert Constant (`app.py` or `simulation.py`):**
    *   `ALERT_DAYS_BEFORE_EXPIRY = 30`
*   **Step E4.2:** **Implement Status Calculation (`simulation.py`):**
    *   Create `calculate_expiry_status(expiry_date, current_date, alert_days)` function:
        *   Returns "Expired" if `expiry_date < current_date`.
        *   Returns "Nearing Expiry" if `current_date <= expiry_date < current_date + pd.Timedelta(days=alert_days)`.
        *   Returns "OK" otherwise.
        *   Handle potential NaT/None expiry dates gracefully (return "Unknown" or "OK").
*   **Step E4.3:** **Calculate Status Column (`app.py`):**
    *   Define `update_expiry_status_column(batches_df, current_sim_date, alert_days)` function.
    *   Uses `df.apply()` to create/update an `expiry_status` column in the `batches_df` by calling `calculate_expiry_status`.
    *   Call this function *after* initial load, *after* `advance_day`, and *after* `add_new_batch` to ensure the status is always current. Store the result back in `st.session_state['batches_df']`.
*   **Step E4.4:** **Add Expiry Alerts UI (`app.py`):**
    *   Below the main inventory table, add a new section: `st.subheader("Expiry Alerts")`.
    *   Filter `st.session_state['batches_df']` for rows where `expiry_status` is "Nearing Expiry" or "Expired".
    *   Select relevant columns for display (e.g., `item_name`, `quantity_on_hand`, `expiry_date`, `expiry_status`).
    *   Display this filtered data using `st.dataframe()`. Apply styling later if needed.

**(Chunk E5 Steps - UI Integration & Restoration)**

*   **Step E5.1:** **Calculate Summary Info (`app.py`):**
    *   In the main table rendering loop (iterating by `item_name`):
        *   Filter `batches_df` for the current item.
        *   Calculate `total_qoh` (already done).
        *   Calculate `earliest_expiry = filtered_batches['expiry_date'].min()`. Format nicely (e.g., `strftime('%Y-%m-%d')`, handle NaT).
        *   Calculate `nearing_expiry_count = filtered_batches[filtered_batches['expiry_status'] == 'Nearing Expiry'].shape[0]`
        *   Calculate `expired_count = filtered_batches[filtered_batches['expiry_status'] == 'Expired'].shape[0]`
*   **Step E5.2:** **Enhance Main Table (`app.py`):**
    *   Adapt the `st.columns` layout: Add columns for "Earliest Expiry" and "Alerts" (Nearing/Expired Counts). Adjust column count/widths as needed.
    *   Display the calculated summary info (`earliest_expiry`, counts) in the new columns.
    *   Use conditional formatting/icons in the "Alerts" column (e.g., ":warning:" if nearing > 0, ":x:" if expired > 0).
*   **Step E5.3:** **Re-integrate ROP/Status/Ordering (`app.py`):**
    *   Calculate the overall item `status` (OK, Low, Reorder) based on `total_qoh` vs `item_params_df.loc[item_name, 'reorder_point']`. (Reuse `calculate_status` logic from previous PoC).
    *   Display this overall status (with colors) in the main table.
    *   Display the `reorder_point` from `item_params_df`.
    *   Display the `reorder_quantity` (RoQ) from `item_params_df` in the "Rec. Order Qty" column.
    *   Re-enable the conditional "Simulate Order" button in the "Action" column, based on the overall item status being "Reorder Needed". Ensure it correctly calls `simulate_order_callback(item_name)`.

*Refinement Check:* This breakdown introduces complexity incrementally. E1 is a major structural change. E2 (FEFO) is logically complex. E3 adds the receiving simulation. E4 brings in the core expiry alerting. E5 integrates everything back into a cohesive UI. The steps feel like manageable development units, though E1 and E2 require careful implementation and testing due to the core logic changes. This plan provides a clear path forward for adding the expiry management feature.