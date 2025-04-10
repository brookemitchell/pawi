Okay, here is a thorough todo.md checklist based on our specification and the breakdown, suitable for tracking development progress.

# Veterinary Inventory Optimization PoC - Development Checklist

## Phase 0: Setup & Prerequisites

-   [ ] Create project directory.
-   [ ] Set up Python virtual environment (e.g., `python -m venv venv`).
-   [ ] Activate virtual environment.
-   [ ] Create `requirements.txt` with `streamlit` and `pandas`.
-   [ ] Install requirements: `pip install -r requirements.txt`.
-   [ ] Create initial empty files: `app.py`, `data_loader.py`, `simulation.py`.
-   [ ] Create SQLite database file: `inventory_poc.db`.
-   [ ] Define `inventory_items` table schema in SQLite:
    -   `item_name` (TEXT, PRIMARY KEY)
    *   `min_daily_usage` (INTEGER)
    *   `max_daily_usage` (INTEGER)
    *   `buffer_days` (INTEGER)
    *   `target_days` (INTEGER)
    *   `initial_quantity_on_hand` (INTEGER)
-   [ ] Populate (seed) `inventory_items` table in `inventory_poc.db` with the 9 specified items and their parameter values. Verify data accuracy.

## Phase 1: Core Implementation (Following LLM Prompts)

-   **Prompt 1: Project Setup & Data Loader Foundation**
    -   [ ] Implement `data_loader.py`: `load_inventory_data` function.
    -   [ ] Include SQLite connection logic.
    -   [ ] Include DataFrame creation from query results.
    *   [ ] Set `item_name` as index.
    *   [ ] Calculate `reorder_point` column.
    *   [ ] Calculate `reorder_quantity` column.
    *   [ ] Rename `initial_quantity_on_hand` to `quantity_on_hand`.
    *   [ ] Ensure function returns the DataFrame.
    *   [ ] Implement basic `try...except` for DB errors (return None on failure). (Refined in Prompt 11)
-   **Prompt 2: Basic Streamlit App & Initial Data Display**
    -   [ ] Implement basic `app.py` structure.
    -   [ ] Import `load_inventory_data`.
    -   [ ] Add `st.title`.
    -   [ ] Call `load_inventory_data` on app run.
    -   [ ] Add check for successful data load (DataFrame is not None).
    -   [ ] Display loaded DataFrame using `st.dataframe()`.
    -   [ ] Display `st.error()` if data loading failed.
-   **Prompt 3: Introducing State Management**
    -   [ ] Modify `app.py` to use `st.session_state`.
    -   [ ] Load data into `st.session_state['inventory_df']` only if it doesn't exist.
    -   [ ] Handle failed load case by storing `None` in session state.
    -   [ ] Initialize `st.session_state['day_count'] = 0` only on first load.
    -   [ ] Display DataFrame *from* session state.
    -   [ ] Add sidebar metric displaying `st.session_state['day_count']`.
-   **Prompt 4: Implementing the Simulation Logic**
    -   [ ] Implement `simulation.py`: `advance_day` function.
    -   [ ] Function accepts and returns a DataFrame.
    -   [ ] Create a copy of the DataFrame inside the function.
    -   [ ] Iterate through rows.
    -   [ ] Calculate random consumption using `min/max_daily_usage`.
    -   [ ] Calculate `new_qoh` ensuring it's `>= 0`.
    -   [ ] Update `quantity_on_hand` in the DataFrame copy.
    -   [ ] Return the modified DataFrame copy.
-   **Prompt 5: Connecting Simulation to UI Button**
    -   [ ] Modify `app.py`: Import `advance_day`.
    -   [ ] Define `advance_day_callback()` function.
    -   [ ] Callback increments `day_count` in session state.
    -   [ ] Callback calls `advance_day` using DataFrame from session state.
    -   [ ] Callback updates DataFrame in session state with the result.
    -   [ ] Add `st.sidebar.button("Advance One Day", ...)` triggering the callback.
-   **Prompt 6: Calculating and Displaying Item Status**
    -   [ ] Implement `simulation.py`: `calculate_status` function with "Reorder Needed", "Low Stock", "OK" logic.
    -   [ ] Modify `app.py`: Import `calculate_status`.
    -   [ ] Modify `app.py`: Define `update_status_column(df)` function.
    -   [ ] Call `update_status_column` after initial load into session state.
    -   [ ] Call `update_status_column` within `advance_day_callback` after `advance_day`.
    -   [ ] Ensure the displayed DataFrame reflects the new `status` column.
-   **Prompt 7: Implementing Order Simulation Logic**
    -   [ ] Modify `simulation.py`: Implement `simulate_order` function.
    -   [ ] Function accepts DataFrame and `item_name`.
    -   [ ] Create a copy of the DataFrame.
    -   [ ] Find item ROP and RoQ.
    -   [ ] Calculate `target_stock_level = rop + roq`.
    -   [ ] Update item's `quantity_on_hand` to `target_stock_level`.
    -   [ ] Return modified DataFrame copy.
-   **Prompt 8: Preparing the Order Callback Function**
    -   [ ] Modify `app.py`: Import `simulate_order`.
    -   [ ] Define `simulate_order_callback(item_name)` function.
    -   [ ] Callback calls `simulate_order` using DataFrame from session state.
    -   [ ] Callback calls `update_status_column` on the result of `simulate_order`.
    -   [ ] Callback updates DataFrame in session state with the final result.
-   **Prompt 9: Custom Table Rendering**
    -   [ ] Modify `app.py`: Replace `st.dataframe` with custom rendering loop.
    -   [ ] Add table headers using `st.columns` and `st.markdown`.
    -   [ ] Iterate through DataFrame rows (`.iterrows()`).
    -   [ ] Use `st.columns(6)` for each row's layout.
    -   [ ] Display data for Item Name, QoH, ROP, Status (text), Rec. RoQ.
    -   [ ] Use `cols[5].empty()` as placeholder for Action column.
-   **Prompt 10: Adding Conditional Order Buttons and Status Coloring**
    -   [ ] Modify `app.py` rendering loop: Implement status coloring using conditional `st.markdown` (Red/Orange/Green).
    -   [ ] Modify `app.py` rendering loop: Implement conditional action button using `if status == "Reorder Needed": cols[5].button(...)`.
    -   [ ] Ensure button uses correct `key` (e.g., `f"order_{index}"`).
    -   [ ] Ensure button uses correct `on_click` (`simulate_order_callback`) and `args` (`(index,)`).
    -   [ ] Ensure non-applicable rows have an empty action column (`cols[5].write("")`).
-   **Prompt 11: Final Polish - Error Handling**
    -   [ ] Refine `data_loader.py`: Ensure `try...except` around DB operations handles `FileNotFoundError` and `sqlite3.Error` correctly, prints error, returns `None`.
    -   [ ] Refine `app.py`: Ensure initial load logic robustly checks for `None` return from `load_inventory_data` and displays `st.error` correctly.

## Phase 2: Testing (Manual)

-   [ ] **Test Initialization:**
    -   [ ] App loads without Python errors.
    -   [ ] Initial Day shown is 0.
    -   [ ] All 9 items are displayed in the table.
    -   [ ] Initial QoH values match the seeded `initial_quantity_on_hand`.
    -   [ ] Calculated ROP values are correct (`max_usage * buffer_days`).
    -   [ ] Initial Status values correctly reflect initial QoH vs ROP (check examples: Parvo=Reorder, Blood Cartridges=Low, Slide 1=OK).
    -   [ ] Status colors (Red/Orange/Green) match the Status text.
    -   [ ] "Simulate Order" button appears *only* for items with "Reorder Needed" status initially (e.g., Parvo, Antigen).
-   [ ] **Test Simulation (`Advance One Day`):**
    -   [ ] Click "Advance One Day". Day counter increments to 1.
    -   [ ] QoH values decrease for all items.
    -   [ ] Click multiple times. QoH continues to decrease.
    -   [ ] Advance day until an item's QoH is low (e.g., < 5). Verify next day's consumption doesn't make QoH negative (it should become 0).
    -   [ ] Observe status changes as QoH drops (e.g., watch an "OK" item become "Low Stock", then "Reorder Needed").
    -   [ ] Verify status colors update correctly with status changes.
    -   [ ] Verify "Simulate Order" button appears dynamically when status changes to "Reorder Needed".
-   [ ] **Test Ordering (`Simulate Order`):**
    -   [ ] Identify an item with "Reorder Needed" status. Note its QoH, ROP, Rec. RoQ.
    -   [ ] Click its "Simulate Order" button.
    -   [ ] Verify the button disappears (or Action column becomes empty).
    *   [ ] Verify the item's QoH increases to the Target Stock Level (`ROP + Rec. RoQ`).
    *   [ ] Verify the item's Status updates (should likely become "OK").
    *   [ ] Verify the Status color updates correctly.
-   [ ] **Test UI/Layout:**
    -   [ ] Confirm overall layout (sidebar for controls, main area for table).
    -   [ ] Confirm table columns are present and in the correct order.
    -   [ ] Confirm headers are clear.
    -   [ ] Confirm data alignment within columns looks reasonable.
-   [ ] **Test Error Handling:**
    -   [ ] Temporarily rename `inventory_poc.db` and run the app. Verify a clear error message ("Failed to load...") is shown instead of crashing. Restore the filename.

## Phase 3: Final Review

-   [ ] Code review for clarity, comments, and adherence to structure.
-   [ ] Final check against all requirements in the specification document.
-   [ ] Add a simple `README.md` explaining how to set up and run the PoC.


This checklist provides a structured path from setup through implementation and testing, ensuring all aspects of the specification are addressed.