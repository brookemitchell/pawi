# Veterinary Inventory Optimization PoC - Development Checklist

## Phase 0: Setup & Prerequisites

-   [x] Create project directory. (Assumed)
-   [x] Set up Python virtual environment (e.g., `python -m venv venv`). (Assumed)
-   [x] Activate virtual environment. (Assumed)
-   [x] Create `requirements.txt` with `streamlit` and `pandas`. (Verified)
-   [x] Install requirements: `pip install -r requirements.txt`. (Assumed)
-   [x] Create initial empty files: `app.py`, `data_loader.py`, `simulation.py`. (Verified)
-   [x] Create SQLite database file: `inventory_poc.db`. (Verified existence, seeding handled)
-   [x] Define `inventory_items` table schema in SQLite: (Verified in `seed_data.sql`)
    -   `item_name` (TEXT, PRIMARY KEY)
    *   `min_daily_usage` (INTEGER)
    *   `max_daily_usage` (INTEGER)
    *   `buffer_days` (INTEGER)
    *   `target_days` (INTEGER)
    *   `initial_quantity_on_hand` (INTEGER)
-   [x] Populate (seed) `inventory_items` table in `inventory_poc.db` with the 9 specified items and their parameter values. Verify data accuracy. (Verified seed script content and loading mechanism in `data_loader.py`)

## Phase 1: Core Implementation (Following LLM Prompts)

-   **Prompt 1: Project Setup & Data Loader Foundation**
    -   [x] Implement `data_loader.py`: `load_inventory_data` function. (Verified)
    -   [x] Include SQLite connection logic. (Verified)
    -   [x] Include DataFrame creation from query results. (Verified)
    *   [x] Set `item_name` as index. (Verified)
    *   [x] Calculate `reorder_point` column. (Verified)
    *   [x] Calculate `reorder_quantity` column. (Verified)
    *   [x] Rename `initial_quantity_on_hand` to `quantity_on_hand`. (Verified via `df.rename`)
    *   [x] Ensure function returns the DataFrame. (Verified)
    *   [x] Implement basic `try...except` for DB errors (return None on failure). (Verified - Refined as per Prompt 11)
-   **Prompt 2: Basic Streamlit App & Initial Data Display**
    -   [x] Implement basic `app.py` structure. (Verified)
    -   [x] Import `load_inventory_data`. (Verified)
    -   [x] Add `st.title`. (Verified)
    -   [x] Call `load_inventory_data` on app run. (Verified within state init)
    -   [x] Add check for successful data load (DataFrame is not None). (Verified)
    -   [x] Display loaded DataFrame using `st.dataframe()`. (Verified - Superseded by custom rendering, but goal achieved)
    -   [x] Display `st.error()` if data loading failed. (Verified)
-   **Prompt 3: Introducing State Management**
    -   [x] Modify `app.py` to use `st.session_state`. (Verified)
    -   [x] Load data into `st.session_state['inventory_df']` only if it doesn't exist. (Verified)
    -   [x] Handle failed load case by storing `None` in session state. (Verified)
    -   [x] Initialize `st.session_state['day_count'] = 0` only on first load. (Verified)
    -   [x] Display DataFrame *from* session state. (Verified)
    -   [x] Add sidebar metric displaying `st.session_state['day_count']`. (Verified)
-   **Prompt 4: Implementing the Simulation Logic**
    -   [x] Implement `simulation.py`: `advance_day` function. (Verified)
    -   [x] Function accepts and returns a DataFrame. (Verified)
    -   [x] Create a copy of the DataFrame inside the function. (Verified)
    -   [x] Iterate through rows. (Verified)
    -   [x] Calculate random consumption using `min/max_daily_usage`. (Verified)
    -   [x] Calculate `new_qoh` ensuring it's `>= 0`. (Verified)
    -   [x] Update `quantity_on_hand` in the DataFrame copy. (Verified)
    -   [x] Return the modified DataFrame copy. (Verified)
-   **Prompt 5: Connecting Simulation to UI Button**
    -   [x] Modify `app.py`: Import `advance_day`. (Verified)
    -   [x] Define `advance_day_callback()` function. (Verified)
    -   [x] Callback increments `day_count` in session state. (Verified)
    -   [x] Callback calls `advance_day` using DataFrame from session state. (Verified)
    -   [x] Callback updates DataFrame in session state with the result. (Verified, includes status update)
    -   [x] Add `st.sidebar.button("Advance One Day", ...)` triggering the callback. (Verified)
-   **Prompt 6: Calculating and Displaying Item Status**
    -   [x] Implement `simulation.py`: `calculate_status` function with "Reorder Needed", "Low Stock", "OK" logic. (Verified)
    -   [x] Modify `app.py`: Import `calculate_status`. (Verified)
    -   [x] Modify `app.py`: Define `update_status_column(df)` function. (Verified)
    -   [x] Call `update_status_column` after initial load into session state. (Verified)
    -   [x] Call `update_status_column` within `advance_day_callback` after `advance_day`. (Verified)
    -   [x] Ensure the displayed DataFrame reflects the new `status` column. (Verified via custom rendering)
-   **Prompt 7: Implementing Order Simulation Logic**
    -   [x] Modify `simulation.py`: Implement `simulate_order` function. (Verified)
    -   [x] Function accepts DataFrame and `item_name`. (Verified)
    -   [x] Create a copy of the DataFrame. (Verified)
    -   [x] Find item ROP and RoQ. (Verified)
    -   [x] Calculate `target_stock_level = rop + roq`. (Verified)
    -   [x] Update item's `quantity_on_hand` to `target_stock_level`. (Verified)
    -   [x] Return modified DataFrame copy. (Verified)
-   **Prompt 8: Preparing the Order Callback Function**
    -   [x] Modify `app.py`: Import `simulate_order`. (Verified)
    -   [x] Define `simulate_order_callback(item_name)` function. (Verified)
    -   [x] Callback calls `simulate_order` using DataFrame from session state. (Verified)
    -   [x] Callback calls `update_status_column` on the result of `simulate_order`. (Verified)
    -   [x] Callback updates DataFrame in session state with the final result. (Verified)
-   **Prompt 9: Custom Table Rendering**
    -   [x] Modify `app.py`: Replace `st.dataframe` with custom rendering loop. (Verified)
    -   [x] Add table headers using `st.columns` and `st.markdown`. (Verified)
    -   [x] Iterate through DataFrame rows (`.iterrows()`). (Verified)
    -   [x] Use `st.columns(6)` for each row's layout. (Verified)
    -   [x] Display data for Item Name, QoH, ROP, Status (text), Rec. RoQ. (Verified)
    -   [x] Use `cols[5].empty()` as placeholder for Action column. (Verified via conditional logic)
-   **Prompt 10: Adding Conditional Order Buttons and Status Coloring**
    -   [x] Modify `app.py` rendering loop: Implement status coloring using conditional `st.markdown` (Red/Orange/Green). (Verified)
    -   [x] Modify `app.py` rendering loop: Implement conditional action button using `if status == "Reorder Needed": cols[5].button(...)`. (Verified)
    -   [x] Ensure button uses correct `key` (e.g., `f"order_{item_name}"`). (Verified)
    -   [x] Ensure button uses correct `on_click` (`simulate_order_callback`) and `args` (`(item_name,)`). (Verified)
    -   [x] Ensure non-applicable rows have an empty action column (`cols[5].write("")`). (Verified)
-   **Prompt 11: Final Polish - Error Handling**
    -   [x] Refine `data_loader.py`: Ensure `try...except` around DB operations handles `FileNotFoundError` and `sqlite3.Error` correctly, prints error, returns `None`. (Verified - Includes seeding logic, file not found handled by seeding attempt, other errors handled)
    -   [x] Refine `app.py`: Ensure initial load logic robustly checks for `None` return from `load_inventory_data` and displays `st.error` correctly. (Verified)

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
-   [x] Add a simple `README.md` explaining how to set up and run the PoC. (Verified)
