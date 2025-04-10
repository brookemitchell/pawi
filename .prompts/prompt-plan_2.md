Okay, let's generate the LLM prompts for implementing the Expiry Management feature, following the detailed plan and iterative breakdown we established.

**Phase 0: Preparation (Manual Task - Not an LLM Prompt)**

*   **Task:** Modify the existing `inventory_poc.db` SQLite database.
    *   **Rename:** Rename the existing `inventory_items` table to `_backup_inventory_items` (or similar).
    *   **Create:** Create the new `item_parameters` table.
        *   Schema: `item_name` TEXT PRIMARY KEY, `min_daily_usage` INTEGER, `max_daily_usage` INTEGER, `buffer_days` INTEGER, `target_days` INTEGER, `reorder_point` INTEGER, `reorder_quantity` INTEGER, `standard_shelf_life_months` INTEGER.
    *   **Create:** Create the new `inventory_batches` table.
        *   Schema: `batch_id` INTEGER PRIMARY KEY AUTOINCREMENT, `item_name` TEXT, `quantity_on_hand` INTEGER, `expiry_date` DATE.
    *   **Populate `item_parameters`:** Copy `item_name`, `min_daily_usage`, `max_daily_usage`, `buffer_days`, `target_days`, `reorder_point`, `reorder_quantity` from the backup table. Add a `standard_shelf_life_months` value for each item (e.g., 12, 18, 24 - choose sensible defaults).
    *   **Populate `inventory_batches`:** For each item in `item_parameters`, insert one initial batch row into `inventory_batches`. Use the `initial_quantity_on_hand` from the *original spec* (e.g., Parvo=12, Blood Cartridges=105). Calculate an `expiry_date` for each initial batch (e.g., Today + `standard_shelf_life_months / 2`).

*(This manual database work prepares the foundation for the code changes)*

---

**Prompt E1.1: Update Data Loader for New Schema**

```text
Objective: Modify the data loading function to read from the new two-table database schema (`item_parameters` and `inventory_batches`).

Context: The SQLite database (`inventory_poc.db`) has been restructured. We previously had a `load_inventory_data` function in `data_loader.py` that read from a single table. We need to update it to read from the new `item_parameters` and `inventory_batches` tables and return two separate DataFrames.

Task:
Modify `data_loader.py`:
1.  Update the `load_inventory_data(db_path='inventory_poc.db')` function.
2.  Inside the function (within the `try` block):
    *   Query `SELECT * FROM item_parameters;`. Load the result into a Pandas DataFrame called `item_params_df`. Set `item_name` as the index for `item_params_df`.
    *   Query `SELECT batch_id, item_name, quantity_on_hand, expiry_date FROM inventory_batches;`. Load the result into a Pandas DataFrame called `batches_df`.
    *   **Crucially:** Convert the `expiry_date` column in `batches_df` to datetime objects using `pd.to_datetime(batches_df['expiry_date'])`. Handle potential errors during conversion if necessary (e.g., `errors='coerce'`).
    *   Set `batch_id` as the index for `batches_df`.
3.  Modify the function to return *both* DataFrames: `return item_params_df, batches_df`.
4.  Update the `except` block to handle potential errors during either query and return `None, None`.

Provide the complete updated content for `data_loader.py`.
```

---

**Prompt E1.2: Adapt App State & Basic Display**

```text
Objective: Update the main Streamlit app (`app.py`) to use the new data loader, manage the two DataFrames and a simulation date in session state, and display a basic table showing total quantity per item.

Context: Building on Prompt E1.1, `data_loader.py` now returns two DataFrames (`item_params_df`, `batches_df`). We need to store these in session state, add a simulation date, and adapt the UI to show total quantity per item (temporarily removing ROP/Status/Action features).

Task:
Modify `app.py`:
1.  Import `datetime` from `datetime`.
2.  Update the initial state setup logic (`if 'inventory_df' not in st.session_state:` block needs changing):
    *   Check if `'item_params_df'` is *not* in `st.session_state`.
    *   If not present:
        *   Call `item_params_df, batches_df = load_inventory_data()`.
        *   Store both DataFrames: `st.session_state['item_params_df'] = item_params_df` and `st.session_state['batches_df'] = batches_df`.
        *   Initialize the simulation date: `st.session_state['current_sim_date'] = datetime.date.today()`.
        *   Initialize `st.session_state['day_count'] = 0`.
3.  Update the main display logic:
    *   Check if `st.session_state['item_params_df']` and `st.session_state['batches_df']` are valid (not None).
    *   If valid:
        *   Display the simulation date prominently (e.g., `st.metric("Current Simulation Date", st.session_state['current_sim_date'].strftime('%Y-%m-%d'))`). (Keep the Day Counter metric in the sidebar).
        *   Modify the table rendering loop:
            *   Iterate through items using `st.session_state['item_params_df'].index`.
            *   Inside the loop, get the `item_name`.
            *   Filter the batches: `item_batches = st.session_state['batches_df'][st.session_state['batches_df']['item_name'] == item_name]`.
            *   Calculate `total_qoh = item_batches['quantity_on_hand'].sum()`.
            *   Use `st.columns()` to display only the `item_name` (index) and the calculated `total_qoh`. Adjust column count accordingly (e.g., `cols = st.columns(2)`).
            *   **Remove or comment out** the display logic for ROP, Status, Rec. RoQ, and the Action column/button for now.
            *   Update table headers to reflect the simplified columns (Item Name, Total QoH).
    *   If loading failed, display the error message `st.error(...)`.
4.  **Temporarily disable or comment out** the existing callbacks (`advance_day_callback`, `simulate_order_callback`) and the buttons that trigger them, as the underlying logic is incompatible until updated.

Provide the complete updated content for `app.py`.
```

---

**Prompt E2.1: Implement FEFO Consumption Logic**

```text
Objective: Implement the First-Expired, First-Out (FEFO) consumption logic in the simulation engine.

Context: Building on E1.2, the app displays total quantities. We need to rewrite the `advance_day` function in `simulation.py` to correctly consume stock from the earliest expiring batches first, using the new data structures.

Task:
Modify `simulation.py`:
1.  Import `datetime` from `datetime` and `pandas as pd` (if not already).
2.  **Replace** the existing `advance_day` function with a new version:
    `advance_day(batches_df: pd.DataFrame, item_params_df: pd.DataFrame, current_sim_date: datetime.date) -> pd.DataFrame:`
3.  Inside the new function:
    *   Create a copy: `df_copy = batches_df.copy()`.
    *   Iterate through each `item_name` in `item_params_df.index`.
    *   Get `min_usage` and `max_usage` for the item from `item_params_df`.
    *   Calculate `daily_consumption = random.randint(min_usage, max_usage)`.
    *   If `daily_consumption == 0`, continue to the next item.
    *   Filter `df_copy` for active batches of the current item:
        *   `item_batches_idx = df_copy[(df_copy['item_name'] == item_name) & (df_copy['quantity_on_hand'] > 0) & (df_copy['expiry_date'] >= current_sim_date)].index`
    *   If no active batches found (`item_batches_idx.empty`), continue to the next item.
    *   Sort these active batches by expiry date: `sorted_batches = df_copy.loc[item_batches_idx].sort_values(by='expiry_date')`.
    *   Iterate through the `sorted_batches.iterrows()`:
        *   Get the `batch_index` and `batch_data`.
        *   `batch_qoh = batch_data['quantity_on_hand']`.
        *   `consume_amount = min(daily_consumption, batch_qoh)`.
        *   Update the quantity in the *main copy* (`df_copy`): `df_copy.loc[batch_index, 'quantity_on_hand'] -= consume_amount`.
        *   `daily_consumption -= consume_amount`.
        *   If `daily_consumption <= 0`, break the inner loop (consumption for this item is done).
    *   After iterating through items, remove batches with zero quantity: `df_copy = df_copy[df_copy['quantity_on_hand'] > 0]`.
4.  Return the final modified `df_copy`.
5. Keep the `calculate_status` function (from previous PoC) for now, although it's not used yet.

Provide the complete updated content for `simulation.py`.
```

---

**Prompt E2.2: Integrate FEFO Simulation into App**

```text
Objective: Re-enable the "Advance One Day" button and connect it to the new FEFO `advance_day` simulation logic.

Context: Building on E2.1, we have the FEFO consumption logic in `simulation.py`. We need to update the callback in `app.py` to use it and update the simulation date and batch state.

Task:
Modify `app.py`:
1.  Import the updated `advance_day` function from `simulation`.
2.  **Re-enable/uncomment** the `advance_day_callback()` function definition.
3.  Modify the `advance_day_callback()` function:
    *   Check if `st.session_state['item_params_df']` and `st.session_state['batches_df']` are valid.
    *   Increment `st.session_state['day_count']` by 1.
    *   Increment `st.session_state['current_sim_date']` by `datetime.timedelta(days=1)`.
    *   Call the new simulation logic:
        `updated_batches_df = advance_day(st.session_state['batches_df'], st.session_state['item_params_df'], st.session_state['current_sim_date'])`
    *   Update the batch state: `st.session_state['batches_df'] = updated_batches_df`.
4.  **Re-enable/uncomment** the `st.sidebar.button("Advance One Day", ...)` line to make the button appear and trigger the callback.
5.  Keep the `simulate_order_callback` function and its button commented out/disabled.

Provide the complete updated content for `app.py`. Ensure the app runs, the button advances the date, and the total QoH values decrease based on the new FEFO logic.
```

---

**Prompt E3.1: Implement Batch Addition Logic**

```text
Objective: Implement the logic in `simulation.py` to add a new batch when an order is simulated.

Context: Building on E2.2, the FEFO simulation runs. Now we need the function to handle adding a new batch with a calculated expiry date based on the item's standard shelf life.

Task:
Modify `simulation.py`:
1.  Import `pandas as pd` and `datetime` if not already present.
2.  **Replace** the old `simulate_order` function (if it still exists from the previous PoC) with a new function:
    `add_new_batch(batches_df: pd.DataFrame, item_params_df: pd.DataFrame, item_name: str, current_sim_date: datetime.date) -> pd.DataFrame:`
3.  Inside the function:
    *   Create a copy: `df_copy = batches_df.copy()`.
    *   Check if `item_name` exists in `item_params_df.index`. If not, return `df_copy` unchanged.
    *   Get parameters from `item_params_df.loc[item_name]`: `shelf_life_months`, `reorder_quantity`.
    *   Calculate `expiry_date = current_sim_date + pd.DateOffset(months=int(shelf_life_months))`. Ensure `shelf_life_months` is treated as an integer. Convert the result to a standard date object if necessary (`expiry_date.date()` if it becomes a Timestamp).
    *   Create a dictionary for the new batch: `new_batch_data = {'item_name': item_name, 'quantity_on_hand': reorder_quantity, 'expiry_date': expiry_date}`.
    *   Convert the dictionary to a DataFrame: `new_batch_df = pd.DataFrame([new_batch_data])`.
    *   Append the new batch to the copy: `df_copy = pd.concat([df_copy.reset_index(), new_batch_df], ignore_index=True)`. **Important:** Reset index before concat and use `ignore_index=True` to avoid index conflicts and allow the database to handle `batch_id` on actual persistence (which we aren't doing in this step). Re-establish an index if needed, perhaps just a default integer index for runtime (`df_copy.set_index('batch_id', drop=False)` if you kept `batch_id` column, or just let concat manage it). *Let's keep it simple for now: reset index on concat.*
4.  Return the updated `df_copy`.

Provide the complete updated content for `simulation.py`.
```

---

**Prompt E3.2: Update Order Callback Function**

```text
Objective: Update the `simulate_order_callback` function in `app.py` to use the new `add_new_batch` logic.

Context: Building on E3.1, we have the `add_new_batch` function. We need to update the corresponding callback in `app.py` (though the button itself is still disabled).

Task:
Modify `app.py`:
1.  Import the `add_new_batch` function from `simulation`.
2.  **Re-enable/uncomment** the `simulate_order_callback(item_name: str)` function definition.
3.  Modify the `simulate_order_callback` function:
    *   Check if `st.session_state['item_params_df']` and `st.session_state['batches_df']` are valid.
    *   Call the batch addition logic:
        `updated_batches_df = add_new_batch(st.session_state['batches_df'], st.session_state['item_params_df'], item_name, st.session_state['current_sim_date'])`
    *   Update the batch state: `st.session_state['batches_df'] = updated_batches_df`.
4.  Keep the actual "Simulate Order" button in the UI commented out/disabled.

Provide the complete updated content for `app.py`.
```

---

**Prompt E4.1: Implement Expiry Status Calculation**

```text
Objective: Implement the logic to determine the expiry status ("OK", "Nearing Expiry", "Expired") for each batch.

Context: Building on E3.2, we can simulate consumption and ordering affecting batches. Now we need to calculate the expiry status based on the current simulation date.

Task:
1.  In `simulation.py`:
    *   Import `datetime` and `pandas` if needed.
    *   Define a constant near the top: `ALERT_DAYS_BEFORE_EXPIRY = 30`.
    *   Create the function `calculate_expiry_status(expiry_date, current_date, alert_days=ALERT_DAYS_BEFORE_EXPIRY) -> str`:
        *   Handle potential `NaT` or `None` expiry dates: return "Unknown" or "OK".
        *   Convert `current_date` to datetime if it's not already, for comparison. Ensure `expiry_date` is also comparable (they should be from the `pd.to_datetime` conversion earlier).
        *   If `expiry_date < current_date`, return "Expired".
        *   Calculate `alert_date = current_date + datetime.timedelta(days=alert_days)`.
        *   If `current_date <= expiry_date < alert_date`, return "Nearing Expiry".
        *   Otherwise, return "OK".
2.  In `app.py`:
    *   Import `calculate_expiry_status` and `ALERT_DAYS_BEFORE_EXPIRY` from `simulation`.
    *   Define a helper function `update_expiry_status_column(batches_df: pd.DataFrame) -> pd.DataFrame`:
        *   Check if `batches_df` is None or empty; if so, return it.
        *   Ensure the 'expiry_date' column is in datetime format.
        *   Get `current_sim_date = st.session_state['current_sim_date']`.
        *   Apply the `calculate_expiry_status` function to create/update an `expiry_status` column:
            `df['expiry_status'] = df.apply(lambda row: calculate_expiry_status(row['expiry_date'], current_sim_date, ALERT_DAYS_BEFORE_EXPIRY), axis=1)`
        *   Return the DataFrame with the new/updated column.
    *   Modify the app logic to call `update_expiry_status_column`:
        *   Call it *after* initial load and storing `batches_df` in session state.
        *   Call it *inside* `advance_day_callback` after `advance_day` returns the updated `batches_df`.
        *   Call it *inside* `simulate_order_callback` after `add_new_batch` returns the updated `batches_df`.
        *   Make sure the result is stored back into `st.session_state['batches_df']` in all cases.

Provide the updated content for `simulation.py` and `app.py`.
```

---

**Prompt E4.2: Add Expiry Alerts UI Section**

```text
Objective: Add a new section to the Streamlit UI displaying batches that are nearing expiry or expired.

Context: Building on E4.1, the `batches_df` in session state now contains an `expiry_status` column. We need to display alerts based on this.

Task:
Modify `app.py`:
1.  In the main UI rendering section (after the main inventory table loop):
    *   Add a subheader: `st.subheader("Expiry Alerts")`.
    *   Check if `st.session_state['batches_df']` is valid.
    *   Filter the DataFrame:
        `alerts_df = st.session_state['batches_df'][st.session_state['batches_df']['expiry_status'].isin(['Nearing Expiry', 'Expired'])]`
    *   Check if `alerts_df` is empty.
        *   If empty, display a message: `st.info("No items currently nearing expiry or expired.")`
        *   If not empty:
            *   Select and potentially rename columns for display: `display_df = alerts_df[['item_name', 'quantity_on_hand', 'expiry_date', 'expiry_status']]`. Format the `expiry_date` column as string (`strftime('%Y-%m-%d')`) for cleaner display in the table.
            *   Display the filtered data: `st.dataframe(display_df)`. (Consider `st.data_editor` if simple editing were needed later, but `st.dataframe` is fine for display). Add conditional formatting later if desired.

Provide the complete updated content for `app.py`.
```

---

**Prompt E5.1: Enhance Main Table with Expiry Summary**

```text
Objective: Enhance the main inventory table to include summary expiry information (earliest expiry date, count of nearing/expired batches) for each item.

Context: Building on E4.2, we have the expiry alerts section. Now we need to integrate summary expiry info into the main item overview table.

Task:
Modify `app.py` within the main table rendering loop (where it iterates through `item_params_df.index`):
1.  Inside the loop (after filtering `item_batches` for the current `item_name`):
    *   Calculate summary statistics from `item_batches`:
        *   `earliest_expiry_date = item_batches['expiry_date'].min()`
        *   `nearing_count = item_batches[item_batches['expiry_status'] == 'Nearing Expiry'].shape[0]`
        *   `expired_count = item_batches[item_batches['expiry_status'] == 'Expired'].shape[0]`
    *   Format the `earliest_expiry_date` for display (e.g., `strftime('%Y-%m-%d')`, handle `NaT` by displaying "N/A" or "-").
    *   Create an alert summary string or use icons:
        *   `alert_text = []`
        *   `if nearing_count > 0: alert_text.append(f":warning: {nearing_count} Nearing")`
        *   `if expired_count > 0: alert_text.append(f":x: {expired_count} Expired")`
        *   `alert_display = " / ".join(alert_text) if alert_text else ":heavy_check_mark:"` (or similar visual representation)
2.  Modify the `st.columns()` setup for the main table rows to add columns for "Earliest Expiry" and "Alerts". Adjust the total column count.
3.  Display the calculated `earliest_expiry_date` (formatted string) and `alert_display` string/icons in their respective new columns within the loop.
4.  Update the table headers (`st.columns` outside the loop) to include the new column names.

Provide the complete updated content for `app.py`.
```

---

**Prompt E5.2: Restore ROP/Status/Ordering Functionality**

```text
Objective: Re-integrate the overall item status calculation (OK/Low/Reorder), display ROP/Rec. RoQ, and re-enable the conditional "Simulate Order" button in the main table.

Context: Building on E5.1, the main table shows expiry summaries. Now we restore the original stockout prevention features based on the total quantity per item.

Task:
Modify `app.py`:
1.  Import the original `calculate_status` function from `simulation` (ensure it's still there from Prompt E2.1 or re-add if needed).
2.  Inside the main table rendering loop (iterating by `item_name`):
    *   Retrieve `rop = st.session_state['item_params_df'].loc[item_name, 'reorder_point']`.
    *   Retrieve `roq = st.session_state['item_params_df'].loc[item_name, 'reorder_quantity']`.
    *   Calculate the overall item status using the `total_qoh` (calculated in E1.4/E5.1) and the retrieved `rop`: `item_status = calculate_status(total_qoh, rop)`.
    *   Modify the `st.columns()` layout for the main table rows again. Ensure columns exist for: Item Name, Total QoH, ROP, Status (Overall), Earliest Expiry, Alerts, Rec. Order Qty, Action. Adjust count/widths.
    *   Display the retrieved `rop` in the 'ROP' column.
    *   Display the calculated `item_status` in the 'Status' column, applying the Red/Orange/Green coloring logic from the original PoC (using `st.markdown`).
    *   Display the retrieved `roq` in the 'Rec. Order Qty' column.
    *   Re-enable the conditional 'Action' button:
        *   `if item_status == "Reorder Needed":`
            *   `cols[ACTION_COLUMN_INDEX].button("Simulate Order", key=f"order_{item_name}", on_click=simulate_order_callback, args=(item_name,))`
        *   `else: cols[ACTION_COLUMN_INDEX].write("")`
3.  Update the table headers (`st.columns` outside the loop) to reflect all columns accurately.

Provide the complete updated content for `app.py`. This should result in the fully functional application incorporating both stockout prevention and expiry management features.
```

---

This sequence of prompts systematically builds the expiry management feature, starting with data structure changes and layering on logic and UI elements incrementally, mirroring the refined step-by-step plan.