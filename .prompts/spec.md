Okay, here is the comprehensive, developer-ready specification document for the Veterinary Diagnostics Inventory Optimization Proof of Concept (PoC), based on our collaborative discussion.

---

**Project Specification: Veterinary Inventory Optimization PoC v1.0**

**1. Project Overview**

*   **Goal:** Develop a Proof of Concept (PoC) application using Python, Streamlit, Pandas, and SQLite to demonstrate core inventory optimization features for veterinary diagnostics supplies.
*   **Primary Focus:** Simulate and visualize stock level tracking, stockout prevention through dynamic reorder points (ROP), and simulated optimized reordering based on dynamic recommended reorder quantities (RoQ).
*   **Target Audience:** Internal demonstration, potential feedback gathering from target users (vet lab/clinic staff).
*   **Out of Scope (for this PoC):** Expiry date tracking/alerts, direct supplier integration, advanced AI forecasting models, user authentication, multi-user support.

**2. Core Requirements**

*   **Inventory Tracking:** Track quantity on hand (QoH) for a predefined list of 9 veterinary inventory items.
*   **Consumption Simulation:** Simulate daily consumption for each item using random values within defined minimum and maximum daily usage ranges.
*   **Dynamic Reorder Points (ROP):** Calculate the ROP for each item based on its maximum daily usage and a configurable buffer period (in days).
    *   `ROP = Max Daily Usage * Buffer Days`
*   **Dynamic Reorder Quantity (RoQ):** Calculate a recommended quantity to order for each item based on its maximum daily usage and a configurable target coverage period (in days). This represents the quantity needed to replenish stock from the ROP up to a target level.
    *   `RoQ = Max Daily Usage * Target Days`
*   **Target Stock Level:** The desired stock level after replenishment.
    *   `Target Stock Level = ROP + RoQ`
*   **Status Monitoring:** Display the current inventory status with a three-tier indicator:
    *   **Reorder Needed:** `QoH <= ROP`
    *   **Low Stock:** `ROP < QoH <= ROP * 1.25`
    *   **OK:** `QoH > ROP * 1.25`
*   **Simulation Control:** Allow the user to advance the simulation one day at a time via a button click.
*   **Simulated Ordering:** Allow the user to simulate placing an order for items flagged as "Reorder Needed". This action should increase the item's QoH to its calculated `Target Stock Level`.
*   **Stockout Prevention:** Ensure simulated QoH cannot fall below zero.

**3. Technology Stack**

*   **Language:** Python (version 3.8+)
*   **UI Framework:** Streamlit
*   **Data Manipulation:** Pandas
*   **Data Storage:** SQLite

**4. Architecture & Code Structure**

Implement the application with a logical separation of concerns:

*   **`data_loader.py` (or similar):**
    *   Handles connection to the SQLite database (`inventory_poc.db`).
    *   Reads the `inventory_items` table into a Pandas DataFrame.
    *   Performs initial calculations (ROP, RoQ).
    *   Returns the initialized DataFrame.
*   **`simulation.py` (or similar):**
    *   Contains functions for the simulation logic:
        *   `advance_day(inventory_df)`: Takes the current DataFrame, calculates daily usage for each item (`random.randint(min, max)`), updates QoH ensuring it doesn't go below zero (`new_QoH = max(0, current_QoH - consumption)`), and returns the updated DataFrame.
        *   `calculate_status(qoh, rop)`: Helper function to determine the status string ("OK", "Low Stock", "Reorder Needed").
        *   `simulate_order(inventory_df, item_name)`: Takes the DataFrame and item name, calculates the quantity needed to reach the `Target Stock Level` (`quantity_to_add = max(0, (item_ROP + item_RoQ) - current_QoH)`), updates the QoH for that item, and returns the updated DataFrame.
*   **`app.py` (Main Streamlit script):**
    *   **State Management:** Utilizes `st.session_state` to store and persist the main inventory DataFrame across user interactions.
    *   **Initialization:** On first run, calls the data loading function and stores the result in `st.session_state`. Initializes a 'day counter' in session state.
    *   **UI Rendering:** Defines the Streamlit layout (sidebar, main area). Renders the current day, control buttons, and the inventory table using data from `st.session_state`.
    *   **Callbacks:** Defines functions triggered by button clicks ("Advance One Day", "Simulate Order Placement") which call the relevant simulation logic functions and update the DataFrame in `st.session_state`, causing the UI to refresh.

**5. Data Handling**

*   **Database:** A single SQLite file named `inventory_poc.db`.
*   **Table Schema (`inventory_items`):**
    *   `item_name` (TEXT, PRIMARY KEY)
    *   `min_daily_usage` (INTEGER)
    *   `max_daily_usage` (INTEGER)
    *   `buffer_days` (INTEGER)
    *   `target_days` (INTEGER)
    *   `initial_quantity_on_hand` (INTEGER)
*   **Seeding Data:** The `inventory_poc.db` must be pre-populated with the following data:

    | item\_name          | min\_daily\_usage | max\_daily\_usage | buffer\_days | target\_days | initial\_quantity\_on\_hand |
    | :------------------ | ----------------: | ----------------: | -----------: | -----------: | --------------------------: |
    | Parvo tests         |                 0 |                 5 |            3 |            7 |                          12 |
    | Blood cartridges    |                 8 |                30 |            3 |           10 |                         105 |
    | Antigen tests       |                10 |                25 |            3 |           10 |                          70 |
    | Slide type 1        |                 5 |                20 |            5 |           14 |                         200 |
    | Slide type 2        |                 5 |                20 |            5 |           14 |                         250 |
    | Cover glass         |                10 |                45 |            5 |           14 |                         450 |
    | Applicator type 1   |                10 |                30 |            4 |           10 |                         140 |
    | Applicator type 2   |                 5 |                20 |            4 |           14 |                         220 |
    | Applicator type 3   |                 5 |                20 |            4 |           14 |                         240 |

*   **Runtime Data Structure:** A Pandas DataFrame stored in `st.session_state['inventory_df']`. This DataFrame will contain the columns loaded from SQLite plus dynamically calculated columns:
    *   `reorder_point` (int)
    *   `reorder_quantity` (int) - *Note: This is the RoQ amount covering Target Days, not the amount to order.*
    *   `quantity_on_hand` (int) - *Initialized with `initial_quantity_on_hand`, then dynamically updated.*
    *   `status` (string) - *Dynamically calculated.*

**6. User Interface (Streamlit `app.py`)**

*   **Layout:** Use `st.sidebar` for controls and the main page area for the data table.
*   **Sidebar:**
    *   Display current simulation day: `st.sidebar.metric("Simulation Day", st.session_state['day_count'])`
    *   "Advance One Day" button: `st.sidebar.button("Advance One Day", on_click=advance_day_callback)`
*   **Main Area:**
    *   Title: `st.title("Veterinary Inventory PoC")`
    *   Inventory Table: Display `st.session_state['inventory_df']` using `st.dataframe` or potentially looping to create a more custom table with `st.columns` if needed for button integration.
    *   **Table Columns:**
        1.  `Item Name` (from DataFrame index)
        2.  `Quantity on Hand` (`quantity_on_hand` column)
        3.  `Reorder Point` (`reorder_point` column)
        4.  `Status` (`status` column - Apply conditional formatting/colors: e.g., Red for "Reorder Needed", Orange for "Low Stock", Green for "OK").
        5.  `Recommended Order Qty` (`reorder_quantity` column - Show the *size* of a typical order, potentially highlight when status is Reorder Needed).
        6.  `Action` (Conditional Button):
            *   If `status` is "Reorder Needed": Display `st.button("Simulate Order", key=f"order_{item_name}", on_click=simulate_order_callback, args=(item_name,))`.
            *   Otherwise, display nothing in this column.

**7. Functional Details**

*   **Initialization:**
    *   Check if `inventory_df` exists in `st.session_state`. If not:
        *   Load data using the `data_loader` function.
        *   Calculate `reorder_point` and `reorder_quantity` columns.
        *   Rename/use `initial_quantity_on_hand` as the live `quantity_on_hand`.
        *   Calculate initial `status` for all rows.
        *   Store DataFrame in `st.session_state['inventory_df']`.
        *   Initialize `st.session_state['day_count'] = 0`.
*   **`advance_day_callback`:**
    *   Increment `st.session_state['day_count']`.
    *   Call `simulation.advance_day(st.session_state['inventory_df'])` to get the updated DataFrame.
    *   Recalculate `status` for all rows based on the new QoH.
    *   Update `st.session_state['inventory_df']` with the result.
*   **`simulate_order_callback(item_name)`:**
    *   Call `simulation.simulate_order(st.session_state['inventory_df'], item_name)` to get the updated DataFrame (this function calculates quantity needed to reach target level and updates QoH).
    *   Recalculate `status` for the updated item.
    *   Update `st.session_state['inventory_df']` with the result.

**8. Error Handling / Edge Cases**

*   **Stock Depletion:** The `simulation.advance_day` function must implement the `max(0, current_QoH - consumption)` logic.
*   **Database Connection:** Wrap initial database loading in a `try...except` block to catch `sqlite3.Error` or `FileNotFoundError` and display an informative error using `st.error()`.
*   **State Initialization:** Ensure `st.session_state` is properly initialized on the first run.

**9. Testing Plan (PoC Level)**

*   **Manual Testing Focus:**
    *   **Initialization:**
        *   Verify the app loads without errors.
        *   Verify the initial Day is 0.
        *   Verify the table displays all 9 items.
        *   Check if initial QoH, ROP match the predefined values and calculations.
        *   Check if the initial statuses (Reorder Needed, Low Stock, OK) are correctly assigned based on initial QoH vs ROP.
        *   Verify the correct "Simulate Order" buttons appear only for items needing reorder.
    *   **Simulation (`Advance One Day`):**
        *   Click button multiple times.
        *   Verify Day counter increments.
        *   Verify QoH decreases for items (spot check a few). Check if decreases seem random but within min/max bounds.
        *   Verify QoH stops at 0 and does not go negative.
        *   Observe status changes: Items transitioning from OK -> Low Stock -> Reorder Needed as QoH drops.
        *   Verify "Simulate Order" buttons appear when status changes to "Reorder Needed".
    *   **Ordering (`Simulate Order Placement`):**
        *   For an item needing reorder, click its "Simulate Order" button.
        *   Verify the button disappears (or the action column becomes empty for that row).
        *   Verify QoH increases to the correct Target Stock Level (`ROP + RoQ`).
        *   Verify the item's status updates (should likely become "OK").
    *   **UI/Layout:**
        *   Confirm sidebar/main area layout.
        *   Confirm table columns are correct.
        *   Confirm status indicators (colors/badges) are displayed correctly.

**10. Deliverables**

*   Python script(s) (`app.py`, `data_loader.py`, `simulation.py` or organized as appropriate).
*   The pre-seeded `inventory_poc.db` SQLite database file.
*   A `requirements.txt` file listing necessary packages (`streamlit`, `pandas`).

---

This specification provides a detailed blueprint for the developer to build the PoC as discussed.