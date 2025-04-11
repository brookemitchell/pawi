# Veterinary Inventory Optimization PoC - UI Enhancements Checklist

## Phase UI0: Prerequisites

-   [ ] **Manual DB Change:** Add `category` TEXT column to `item_parameters` table in `inventory_poc.db`.
-   [ ] **Manual DB Change:** Populate the `category` column for all items (e.g., 'Test Kit', 'Consumable', 'Reagent'). Verify data.

## Phase UI1: Category & History Foundation

-   **Prompt UI1.1: Update Data Loader & State for Category**
    -   [ ] Modify `data_loader.py`: Update `load_inventory_data` SQL query to include `category`.
    -   [ ] Verify `item_params_df` returned by loader contains `category`.
    -   [ ] Modify `app.py`: Ensure initial state handles `item_params_df` with the new `category` column.
    -   [ ] Modify `app.py`: Initialize `st.session_state['history'] = []` in the initial state setup block.
-   **Prompt UI1.2: Implement History Recording**
    -   [ ] Modify `app.py`: Update `advance_day_callback`.
    -   [ ] Add logic inside the callback to iterate through items *after* `advance_day` runs.
    -   [ ] Calculate `total_qoh` per item from the updated batches DataFrame.
    -   [ ] Append `{'day': day, 'item_name': item_name, 'total_qoh': total_qoh}` to `st.session_state['history']` list.

## Phase UI2: Inventory Trend Graph

-   **Prompt UI2.1: Add Inventory Trend Graph**
    -   [ ] Modify `app.py`: Add `st.subheader("Inventory Trends")`.
    -   [ ] Get `item_list` from `item_params_df` index.
    -   [ ] Add `st.multiselect` for item selection.
    *   [ ] Check if history and selected items exist.
    *   [ ] Convert `st.session_state['history']` list to DataFrame (`history_df`).
    *   [ ] Filter `history_df` based on `selected_items`.
    *   [ ] Pivot `filtered_history` DataFrame for `st.line_chart` (index='day', columns='item_name', values='total_qoh').
    *   [ ] Display `st.line_chart(chart_data)`.
    *   [ ] Add informational messages for missing history or selections.

## Phase UI3: Reorder Summary & Bulk Action

-   **Prompt UI3.1: Add Reorder Suggestions Section & Button**
    -   [ ] Modify `app.py`: Add section header in sidebar (e.g., `st.sidebar.subheader("Reorder Suggestions")`).
    -   [ ] Add checks for data availability in state.
    -   [ ] Implement logic to iterate items, calculate status, and build `items_to_reorder` list (dict of 'Item', 'Reorder Qty').
    -   [ ] If `items_to_reorder` is not empty:
        -   [ ] Convert list to DataFrame (`reorder_df`).
        -   [ ] Display `reorder_df` in sidebar (`st.sidebar.dataframe`).
        -   [ ] Add `st.sidebar.button("Reorder All Suggested", ...)` below the table.
    -   [ ] If empty, display info message in sidebar.
    -   [ ] Handle case where initial dataframes are not loaded.
-   **Prompt UI3.2: Implement "Reorder All" Callback**
    -   [ ] Modify `app.py`: Define `reorder_all_callback()` function.
    -   [ ] Add state checks inside callback.
    -   [ ] Implement logic to iterate through items.
    -   [ ] Calculate status for each item.
    -   [ ] If status is "Reorder Needed", call `simulate_order_callback(item_name)`.
    -   [ ] (Optional) Add `st.toast` confirmation message.

## Phase UI4: Expiry Discard Action

-   **Prompt UI4.1: Implement Batch Discard Logic**
    -   [ ] Modify `simulation.py`: Create `discard_batch(batches_df, batch_id_to_discard)` function.
    -   [ ] Implement logic to copy DataFrame.
    -   [ ] Implement logic to drop row based on `batch_id_to_discard` (using index). Handle errors.
    -   [ ] Return modified DataFrame copy.
-   **Prompt UI4.2: Implement "Discard Batch" Callback**
    -   [ ] Modify `app.py`: Import `discard_batch`.
    -   [ ] Define `discard_batch_callback(batch_id)` function.
    -   [ ] Add state checks.
    -   [ ] Call `discard_batch` logic.
    -   [ ] Call `update_expiry_status_column` on the result.
    -   [ ] Update `st.session_state['batches_df']` with the final result.
    -   [ ] (Optional) Add `st.toast` confirmation.
-   **Prompt UI4.3: Add "Discard" Buttons to Expiry Alerts Table**
    -   [ ] Modify `app.py`: Locate the "Expiring & Expired Batches" section.
    -   [ ] Replace `st.dataframe(display_df)` with a custom loop (`alerts_df.iterrows()`).
    -   [ ] Use `st.columns()` for layout (Item Name, Qty, Expires, Status, Action).
    -   [ ] Add headers for the columns.
    -   [ ] Display data in respective columns.
    -   [ ] Add `st.button("Discard", ...)` in the 'Action' column, passing `batch_index` (batch_id) as key/arg to `discard_batch_callback`.

## Phase UI5: Testing (UI Enhancements - Manual)

-   [ ] **Test Category & History:**
    -   [ ] Verify app loads after DB change & code updates.
    -   [ ] Advance day several times.
    -   [ ] Verify history graph section appears.
    -   [ ] Select items; verify graph plots correctly.
    -   [ ] Verify graph updates after more "Advance Day" clicks.
    -   [ ] (Optional) Check if `category` column exists in `item_params_df` in state (e.g., via debug).
-   [ ] **Test Reorder Summary & Bulk Action:**
    -   [ ] Advance day until several items are "Reorder Needed".
    -   [ ] Verify the "Reorder Suggestions" table appears in the sidebar and lists the correct items and quantities.
    -   [ ] Click "Reorder All Suggested".
    -   [ ] Verify the `Total QoH` for the ordered items increases in the main table.
    -   [ ] Verify the overall `Status` for ordered items updates (likely to "OK").
    -   [ ] Verify the "Reorder Suggestions" table becomes empty or updates correctly after the reorder.
    -   [ ] Verify `st.toast` confirmation appears (if implemented).
-   [ ] **Test Expiry Discard Action:**
    -   [ ] Advance day until items appear in the "Expiring & Expired Batches" section.
    -   [ ] Verify the section now uses `st.columns` and has a "Discard" button for each row.
    -   [ ] Click "Discard" for one batch.
    -   [ ] Verify the batch disappears from the "Expiry Alerts" section (after rerun).
    -   [ ] Verify the `Total QoH` for the corresponding item decreases in the main table.
    -   [ ] Verify the "Alerts" summary column in the main table updates correctly.
    -   [ ] Verify `st.toast` confirmation appears (if implemented).
-   [ ] **Test Overall UI:**
    -   [ ] Check layout consistency.
    -   [ ] Check section headers and titles.
    -   [ ] Check readability of tables and graph.

## Phase UI6: Final Review (UI Enhancements)

-   [ ] Code review for clarity, Streamlit best practices, callback logic.
-   [ ] Final check against UI design influences and requirements.
-   [ ] Update `README.md` if needed.