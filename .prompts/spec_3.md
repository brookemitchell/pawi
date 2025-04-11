Okay, let's plan the addition of these UI enhancements inspired by your design influences. We'll follow the established process.

**1. Goal Ingestion & Clarification**

*   **Goal:** Integrate UI elements inspired by the provided designs ("Real-Time Tracking", "Automated Reorder Suggestions", "Expiration Alerts & Recommendations") into the existing Streamlit PoC (which includes expiry tracking).
*   **Design Elements to Incorporate:**
    *   **Inventory Trend Graph:** Visualize stock level changes over simulated time.
    *   **Category Information:** Add item categories and potentially use them for display/filtering.
    *   **Simplified Reorder List:** Show only items needing reordering with their quantities.
    *   **"Reorder All" Button:** A single button to trigger orders for all items currently needing it.
    *   **Enhanced Expiry Action:** Add a "Discard" button for expired/nearing-expiry batches.
*   **Alignment with "Reduce Waste":** The "Discard" button directly addresses waste. The graph and better reorder summary improve visibility, indirectly supporting waste reduction goals.
*   **PoC Scope:** Implement functional versions of these UI elements within the existing Streamlit/Pandas framework. The graph will track history accumulated *during the current session*. "Discard" recommendation remains simple (user clicks button).

**2. Detailed Blueprint Drafting (UI Feature Additions)**

*   **High-level System Architecture:** No change (Streamlit, Pandas, SQLite).
*   **Key Functional Components (Updates & Additions):**
    *   **Data Model:**
        *   `item_parameters` table (SQLite): Add a `category` column (TEXT).
        *   Runtime State (`st.session_state`): Add a `history` list or DataFrame to store `{'day': day, 'item_name': name, 'total_qoh': qoh}` snapshots.
    *   **Data Loader (`data_loader.py`):** Update to load the new `category` column.
    *   **Simulation Engine (`simulation.py`):**
        *   Add `discard_batch(batches_df, batch_id_to_discard)` function.
    *   **Main Application (`app.py`):**
        *   **State Management:** Initialize `st.session_state['history'] = []`. Append data to history in `advance_day_callback`.
        *   **UI Rendering:**
            *   Add a new section for Inventory Trend Graph (`st.line_chart`). Include item selection mechanism (e.g., `st.multiselect`).
            *   Add a new section for "Reorder Suggestions". Filter data to show items with "Reorder Needed" status and their `reorder_quantity`. Add "Reorder All" button.
            *   Modify the main inventory table to optionally display the `category`.
            *   Modify the "Expiry Alerts" table to include a "Discard" button per row.
        *   **Callbacks:** Add `reorder_all_callback()`, `discard_batch_callback(batch_id)`.
*   **Data Requirements:**
    *   `category` data needs to be added to the `item_parameters` table for each item (e.g., "Test Kit", "Consumable", "Reagent").
    *   History storage format decided (list of dicts seems simplest for this PoC).
*   **Technology Stack:** No changes.

**3. Iterative Chunking (Epics/Features for UI Enhancements)**

*   **Chunk UI1: Category & History Foundation:** Modify DB schema, data loader, and state to include 'category'. Implement logic to record QoH history snapshots in session state.
*   **Chunk UI2: Inventory Trend Graph:** Add a UI section displaying a line chart based on the stored history for selected items.
*   **Chunk UI3: Reorder Summary & Bulk Action:** Create the filtered "Reorder Suggestions" UI section, displaying items needing reorder and their RoQ. Implement the "Reorder All" button and its callback.
*   **Chunk UI4: Expiry Discard Action:** Implement the `discard_batch` function in `simulation.py`. Add "Discard" buttons to the "Expiry Alerts" table in the UI and connect them to a new callback.

**4. Granular Step Breakdown & Refinement (UI Enhancements)**

**(Chunk UI1 Steps - Category & History Foundation)**

*   **Step UI1.1 (Manual DB):** Add `category` TEXT column to `item_parameters` table in `inventory_poc.db`. Populate it with appropriate categories for each item.
*   **Step UI1.2:** Modify `data_loader.py`: Update `load_inventory_data` to query and include the `category` column in the returned `item_params_df`.
*   **Step UI1.3:** Modify `app.py`:
    *   Update initial state setup to handle the `category` column in `st.session_state['item_params_df']`.
    *   Initialize `st.session_state['history'] = []` during the initial state setup.
*   **Step UI1.4:** Modify `app.py`: In `advance_day_callback` function, *after* calculating the `updated_batches_df` (before storing it):
    *   Get the current `day = st.session_state['day_count']`.
    *   Iterate through `item_params_df.index` (item names).
    *   Calculate `total_qoh` for each item from `updated_batches_df`.
    *   Append a dictionary `{'day': day, 'item_name': item_name, 'total_qoh': total_qoh}` to `st.session_state['history']`. *Self-correction: Record history *after* the day's consumption.*

**(Chunk UI2 Steps - Inventory Trend Graph)**

*   **Step UI2.1:** Modify `app.py`:
    *   Add a new section, e.g., `st.subheader("Inventory Trends")`.
    *   Get the list of item names: `item_list = st.session_state.get('item_params_df', pd.DataFrame()).index.tolist()`.
    *   Add an item selector: `selected_items = st.multiselect("Select items to plot:", item_list, default=item_list[:min(2, len(item_list))])` (default to first 2 items).
    *   Check if `st.session_state['history']` exists and is not empty, and if `selected_items` is not empty.
    *   If data exists:
        *   Convert history list to DataFrame: `history_df = pd.DataFrame(st.session_state['history'])`.
        *   Filter for selected items: `filtered_history = history_df[history_df['item_name'].isin(selected_items)]`.
        *   Prepare data for `st.line_chart`. It often expects wide format (datetime index, one column per category). Pivot the data: `chart_data = filtered_history.pivot(index='day', columns='item_name', values='total_qoh')`. Handle potential missing days if needed (e.g., `.fillna(method='ffill')`).
        *   Display the chart: `st.line_chart(chart_data)`.
    *   Else: Display `st.info("Run simulation to see history graph.")`.

**(Chunk UI3 Steps - Reorder Summary & Bulk Action)**

*   **Step UI3.1:** Modify `app.py`:
    *   Add a new section, e.g., `st.sidebar.subheader("Reorder Suggestions")` (or main page).
    *   Check if `item_params_df` and `batches_df` exist in state.
    *   Create a list `items_to_reorder = []`.
    *   Iterate through `item_params_df.index` (item names).
        *   Calculate `total_qoh` for the item from `batches_df`.
        *   Get `rop` and `roq` from `item_params_df`.
        *   Calculate `item_status` using `calculate_status(total_qoh, rop)`.
        *   If `item_status == "Reorder Needed"`: Append `{'Item': item_name, 'Reorder Qty': roq}` to `items_to_reorder`.
    *   If `items_to_reorder` is not empty:
        *   Convert list to DataFrame: `reorder_df = pd.DataFrame(items_to_reorder)`.
        *   Display the table: `st.sidebar.dataframe(reorder_df)`.
        *   Add the "Reorder All" button below the table: `st.sidebar.button("Reorder All Suggested", on_click=reorder_all_callback)`.
    *   Else: Display `st.sidebar.info("No items need reordering.")`.
*   **Step UI3.2:** Modify `app.py`:
    *   Define the new callback function `reorder_all_callback()`:
        *   Check if necessary dataframes exist in state.
        *   Iterate through `item_params_df.index` (or reuse the `items_to_reorder` list calculation from UI3.1 for efficiency).
        *   For each `item_name`:
            *   Calculate its `total_qoh` and `rop`.
            *   If `calculate_status(total_qoh, rop) == "Reorder Needed"`:
                *   Call the existing `simulate_order_callback(item_name)`. *Self-correction: Directly call the add_new_batch and update logic here, or ensure simulate_order_callback is robust enough.* Let's call `simulate_order_callback` for simplicity.
        *   (Optional: Add `st.success("Triggered reorder for flagged items.")`).

**(Chunk UI4 Steps - Expiry Discard Action)**

*   **Step UI4.1:** Modify `simulation.py`:
    *   Create `discard_batch(batches_df: pd.DataFrame, batch_id_to_discard)` function:
        *   Input: Current batches DataFrame, batch ID to discard.
        *   Output: Updated batches DataFrame.
        *   Create copy: `df_copy = batches_df.copy()`.
        *   Remove the row with the matching `batch_id`: `df_copy = df_copy.drop(index=batch_id_to_discard, errors='ignore')`. (`errors='ignore'` handles cases where the ID might not exist). Use index if `batch_id` is index, else filter by column. Assuming `batch_id` is index from E1.1 modification.
        *   Return `df_copy`.
*   **Step UI4.2:** Modify `app.py`:
    *   Import `discard_batch` from `simulation`.
    *   Define `discard_batch_callback(batch_id)` function:
        *   Check if `batches_df` exists in state.
        *   Call `updated_df = discard_batch(st.session_state['batches_df'], batch_id)`.
        *   Update state: `st.session_state['batches_df'] = update_expiry_status_column(updated_df)` (recalculate expiry status after discard).
*   **Step UI4.3:** Modify `app.py`:
    *   In the "Expiring & Expired Batches" section, where the `alerts_df` is displayed using `st.dataframe`:
        *   Change from `st.dataframe` to iterating through `alerts_df.iterrows()` and using `st.columns`, similar to the main inventory table.
        *   Add a new column for "Action".
        *   In the "Action" column, add a "Discard" button: `st.button("Discard", key=f"discard_{batch_index}", on_click=discard_batch_callback, args=(batch_index,))`. Use the `batch_id` (which is the DataFrame index from E1.1) as the key/argument.

*Refinement Check:* Steps are incremental. UI1 sets data foundations. UI2 adds visualization. UI3 adds the bulk reorder feature. UI4 adds the discard action. Each chunk builds upon the previous one without excessive complexity per step. The plan separates logic implementation (`simulation.py`) from UI integration (`app.py`).

**5. LLM Prompt Generation (UI Enhancements)**

---

**(Manual Task Reminder)**

```text
Reminder: Before running the first prompt, manually add a 'category' TEXT column to the 'item_parameters' table in 'inventory_poc.db' and populate it with appropriate categories (e.g., 'Test Kit', 'Consumable') for each item.
```

---

**Prompt UI1.1: Update Data Loader & State for Category**

```text
Objective: Modify the data loader and app state to include the new 'category' information for items.

Context: Building on the previous state (Expiry Management features added). A 'category' column has been manually added to the `item_parameters` table in `inventory_poc.db`. We need to load this and store it.

Task:
1.  Modify `data_loader.py`:
    *   In the `load_inventory_data` function, update the SQL query for `item_parameters` to select the new `category` column: `SELECT item_name, ..., category FROM item_parameters;`.
    *   Ensure the returned `item_params_df` includes the `category` column.
2.  Modify `app.py`:
    *   Ensure the initial state setup correctly handles the `item_params_df` now containing the `category` column when storing it in `st.session_state['item_params_df']`. No explicit changes might be needed here if it loads all columns, but verify.
    *   Initialize the history list in the initial state setup: `st.session_state['history'] = []`.

Provide the updated content for `data_loader.py` and `app.py`.
```

---

**Prompt UI1.2: Implement History Recording**

```text
Objective: Implement the logic to record historical Total QoH snapshots in session state after each simulation day advances.

Context: Building on UI1.1, the app state now includes an empty `history` list. We need to append data to this list within the `advance_day_callback`.

Task:
Modify `app.py`:
1.  In the `advance_day_callback` function:
    *   Locate the point *after* the `updated_batches_df = advance_day(...)` call returns and *before* it's stored back into `st.session_state['batches_df']`.
    *   Get the current simulation day: `day = st.session_state['day_count']`.
    *   Get the item names index: `item_names = st.session_state['item_params_df'].index`.
    *   Iterate through `item_names`:
        *   Calculate `total_qoh = updated_batches_df[updated_batches_df['item_name'] == item_name]['quantity_on_hand'].sum()`.
        *   Append a dictionary to the history list: `st.session_state['history'].append({'day': day, 'item_name': item_name, 'total_qoh': total_qoh})`.

Provide the complete updated content for `app.py`.
```

---

**Prompt UI2.1: Add Inventory Trend Graph**

```text
Objective: Add a line chart to visualize the historical Total QoH for user-selected items.

Context: Building on UI1.2, `st.session_state['history']` now accumulates data. We need to add a UI section with a multiselect widget and a line chart.

Task:
Modify `app.py`:
1.  Import `pandas as pd` if not already imported at the top.
2.  After the main "Inventory Status" section (e.g., before the "Expiring & Expired Batches" section), add:
    *   `st.subheader("Inventory Trends")`.
    *   Check if `item_params_df` exists in state. If yes, get `item_list = st.session_state['item_params_df'].index.tolist()`. If not, use `item_list = []`.
    *   Add the multiselect widget: `selected_items = st.multiselect("Select items to plot history:", item_list, default=item_list[:min(2, len(item_list))])`.
    *   Check if `st.session_state.get('history')` is not empty and `selected_items` is not empty.
    *   If True:
        *   Convert history list to DataFrame: `history_df = pd.DataFrame(st.session_state['history'])`.
        *   Filter history for selected items: `filtered_history = history_df[history_df['item_name'].isin(selected_items)]`.
        *   Check if `filtered_history` is not empty.
        *   If not empty, pivot the data for charting: `chart_data = filtered_history.pivot(index='day', columns='item_name', values='total_qoh')`.
        *   Display the line chart: `st.line_chart(chart_data)`.
        *   Add an `else` for the empty `filtered_history` check: `st.info("No history recorded yet for selected items.")`.
    *   Else (no history or no selected items): Display `st.info("Run simulation or select items to see history graph.")`.

Provide the complete updated content for `app.py`.
```

---

**Prompt UI3.1: Add Reorder Suggestions Section & Button**

```text
Objective: Create a new UI section (likely sidebar) showing only items needing reorder and add a "Reorder All Suggested" button.

Context: Building on UI2.1, the main UI shows inventory status and trends. We need a focused view for reordering actions.

Task:
Modify `app.py`:
1.  Add a new section in the sidebar, below the existing controls: `st.sidebar.divider()`, `st.sidebar.subheader("Reorder Suggestions")`.
2.  Check if `item_params_df` and `batches_df` are available in session state.
3.  If available:
    *   Initialize an empty list: `items_to_reorder = []`.
    *   Iterate through `st.session_state['item_params_df'].index`:
        *   Get `item_name`.
        *   Calculate `total_qoh` from `batches_df`.
        *   Get `rop` and `roq` from `item_params_df`. Handle potential `KeyError/ValueError` when accessing rop/roq.
        *   Calculate `item_status = calculate_status(total_qoh, rop)`.
        *   If `item_status == "Reorder Needed"`: Append `{'Item': item_name, 'Reorder Qty': roq}` to `items_to_reorder`.
    *   Check if `items_to_reorder` list is not empty.
        *   If not empty:
            *   Convert list to DataFrame: `reorder_df = pd.DataFrame(items_to_reorder)`.
            *   Display the table in the sidebar: `st.sidebar.dataframe(reorder_df, hide_index=True)`.
            *   Add the button below it: `st.sidebar.button("Reorder All Suggested", on_click=reorder_all_callback, key="reorder_all")`.
        *   Else (list is empty): Display `st.sidebar.info("No items need reordering.")`.
    *   Else (dataframes not available): Display `st.sidebar.warning("Inventory data not loaded.")`.

Provide the complete updated content for `app.py` (Note: `reorder_all_callback` is not defined yet).
```

---

**Prompt UI3.2: Implement "Reorder All" Callback**

```text
Objective: Implement the callback function (`reorder_all_callback`) triggered by the "Reorder All Suggested" button.

Context: Building on UI3.1, the button exists but the callback is missing. The callback needs to iterate through items needing reorder and trigger the existing order simulation logic for each.

Task:
Modify `app.py`:
1.  Define the callback function `reorder_all_callback()`:
    *   Add checks: Ensure `item_params_df` and `batches_df` are in session state and not None.
    *   Initialize a flag or list to track which items were ordered, e.g., `ordered_items_count = 0`.
    *   Iterate through `st.session_state['item_params_df'].index`:
        *   Get `item_name`.
        *   Calculate `total_qoh` from `batches_df`.
        *   Get `rop` from `item_params_df`. Handle potential errors.
        *   Calculate `item_status = calculate_status(total_qoh, rop)`.
        *   If `item_status == "Reorder Needed"`:
            *   Call `simulate_order_callback(item_name)`. # Call the existing single-item order callback
            *   Increment `ordered_items_count`.
    *   (Optional) Display a confirmation message after the loop: `if ordered_items_count > 0: st.toast(f"Triggered reorder simulation for {ordered_items_count} items.")`.
    *   (Important Note): Since `simulate_order_callback` updates session state, calling it in a loop *might* cause multiple Streamlit reruns. This is acceptable for the PoC, but in production, a more efficient approach might update state once after processing all items. For now, calling the existing callback is simpler.

Provide the complete updated content for `app.py`.
```

---

**Prompt UI4.1: Implement Batch Discard Logic**

```text
Objective: Implement the function in `simulation.py` to remove a specific batch from the DataFrame.

Context: Building on UI3.2, the app has reorder features. We now need the backend logic to discard expired/unwanted batches.

Task:
Modify `simulation.py`:
1.  Import `pandas as pd` if needed.
2.  Add the function `discard_batch(batches_df: pd.DataFrame, batch_id_to_discard)`:
    *   Check if `batch_id_to_discard` is None or if `batches_df` is None. Return `batches_df` unchanged if so.
    *   Create a copy: `df_copy = batches_df.copy()`.
    *   Check if `batch_id_to_discard` exists in the DataFrame's index (assuming `batch_id` is the index).
    *   If it exists, drop the row: `df_copy = df_copy.drop(index=batch_id_to_discard, errors='ignore')`.
    *   Return `df_copy`.

Provide the complete updated content for `simulation.py`.
```

---

**Prompt UI4.2: Implement "Discard Batch" Callback**

```text
Objective: Implement the callback function in `app.py` that will be triggered by the "Discard" buttons in the Expiry Alerts table.

Context: Building on UI4.1, we have the `discard_batch` function. We need the Streamlit callback to connect the UI action to this logic.

Task:
Modify `app.py`:
1.  Import `discard_batch` from `simulation`.
2.  Define the callback function `discard_batch_callback(batch_id)`:
    *   Add checks: Ensure `batches_df` is in session state and not None.
    *   Call the discard logic: `updated_df = discard_batch(st.session_state['batches_df'], batch_id)`.
    *   Update session state: `st.session_state['batches_df'] = update_expiry_status_column(updated_df)` (Recalculate expiry status after discard).
    *   (Optional) Add a confirmation: `st.toast(f"Discarded batch {batch_id}.")`.

Provide the complete updated content for `app.py`.
```

---

**Prompt UI4.3: Add "Discard" Buttons to Expiry Alerts Table**

```text
Objective: Modify the "Expiring & Expired Batches" UI section to replace `st.dataframe` with a custom layout including a "Discard" button for each listed batch.

Context: Building on UI4.2, the discard callback exists. We need to change the Expiry Alerts table to use `st.columns` and add the button.

Task:
Modify `app.py`:
1.  Locate the "Expiring & Expired Batches" section.
2.  Find where the filtered `alerts_df` is displayed (likely with `st.dataframe(display_df)`).
3.  Replace the `st.dataframe(display_df)` call with the following structure:
    *   Define headers using `st.columns` (e.g., Item Name, Qty, Expires, Status, Action).
    *   Iterate through the `alerts_df.iterrows()`:
        *   Get the `batch_index` (which should be the `batch_id`) and `row_data`.
        *   Create columns using `st.columns(5)`.
        *   Display data in respective columns: `item_name`, `quantity_on_hand`, formatted `expiry_date`, `expiry_status`.
        *   In the 'Action' column (`cols[4]`), add the button:
            `cols[4].button("Discard", key=f"discard_{batch_index}", on_click=discard_batch_callback, args=(batch_index,))`

Provide the complete updated content for `app.py`. This completes the planned UI enhancements.
```