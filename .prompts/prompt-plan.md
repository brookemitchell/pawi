Okay, let's break down the development process for the Veterinary Inventory Optimization PoC, starting with the blueprint, then iterative chunks, granular steps, and finally, the specific LLM prompts.

**Phase 1: Detailed Blueprint Drafting**

Based on the specification, here's the technical blueprint:

1.  **High-level System Architecture:**
    *   Single-page web application using Streamlit.
    *   Backend logic running within the same Python process.
    *   Data persistence for initial configuration via a seeded SQLite database.
    *   Runtime data management using Pandas DataFrames.
    *   State management handled by Streamlit's session state (`st.session_state`).

2.  **Key Functional Components:**
    *   **Data Loader (`data_loader.py`):** Connects to SQLite, reads initial data, calculates static ROP/RoQ, returns initial DataFrame.
    *   **Simulation Engine (`simulation.py`):** Contains logic for daily consumption (`advance_day`), status calculation (`calculate_status`), and order simulation (`simulate_order`).
    *   **Main Application (`app.py`):** Handles Streamlit UI rendering (sidebar, table), state management initialization and updates, button callbacks, and orchestrates calls to other components.

3.  **Data Requirements:**
    *   **Source:** Pre-seeded SQLite database (`inventory_poc.db`) with `inventory_items` table (schema defined in spec).
    *   **Runtime Schema:** Pandas DataFrame (structure defined in spec: index=`item_name`, columns=`min_daily_usage`, `max_daily_usage`, `buffer_days`, `target_days`, `reorder_point`, `reorder_quantity`, `quantity_on_hand`, `status`).
    *   **Storage:** Initial parameters in SQLite; runtime state (QoH, day count) in `st.session_state`.

4.  **AI/ML Models:** None in this PoC. Calculations are rule-based (ROP, RoQ, Status).

5.  **Technology Stack:** Python 3.8+, Streamlit, Pandas, SQLite3.

6.  **Integration Points:** None (self-contained PoC).

7.  **User Interface (UI) / User Experience (UX):**
    *   Streamlit-based interface.
    *   Sidebar for global controls (Advance Day, Day Counter).
    *   Main area for inventory table.
    *   Table Columns: Item Name, QoH, ROP, Status (with color cues), Recommended Order Qty, Action (conditional button).
    *   Clear visual indication of status.
    *   Simple button interactions for simulation progression and ordering.

**Phase 2: Iterative Chunking (Epics/Features)**

Decomposing the blueprint into logical, value-adding chunks:

*   **Chunk 1: Foundation & Basic Data Display:** Set up the project, load data from SQLite, perform initial calculations, and display the raw inventory data in a basic Streamlit table. (Value: See the initial state).
*   **Chunk 2: Simulation Core:** Implement the "Advance Day" logic (random consumption, QoH update, day counter) and link it to a button. Introduce state management for persistence. (Value: See inventory levels change over time).
*   **Chunk 3: Status Calculation & Ordering Logic:** Implement the status calculation (OK, Low, Reorder), display it, implement the order simulation logic, and add the conditional "Simulate Order" button. (Value: Identify items needing action and simulate replenishment).
*   **Chunk 4: UI Refinement & Finalization:** Implement status coloring, refine button placement within the table, ensure robust state handling, add basic error handling, and ensure all components are wired correctly. (Value: Polished, functional PoC matching the spec).

**Phase 3 & 4: Granular Step Breakdown & Refinement**

Breaking down chunks into small, actionable, right-sized steps:

**(Pre-computation Task)**
*   **Step 0:** Create the `inventory_poc.db` SQLite file and populate the `inventory_items` table with the specified seeding data.

**(Chunk 1 Steps)**
*   **Step 1.1:** Set up Python environment (`requirements.txt`: `streamlit`, `pandas`) and create initial project files (`app.py`, `data_loader.py`, `simulation.py`).
*   **Step 1.2 (`data_loader.py`):** Implement the function to connect to `inventory_poc.db`, read the `inventory_items` table into a Pandas DataFrame, and calculate the `reorder_point` and `reorder_quantity` columns. Return this DataFrame.
*   **Step 1.3 (`app.py`):** Create a basic Streamlit app structure. Import the data loading function. Call it *once* on the first run to load data. Display the raw loaded DataFrame (including calculated ROP/RoQ) using `st.dataframe()`. *Defer session state for now*.

**(Chunk 2 Steps)**
*   **Step 2.1 (`app.py`):** Introduce Streamlit session state (`st.session_state`). Modify Step 1.3 logic to load the DataFrame *into* `st.session_state['inventory_df']` only if it doesn't already exist. Display the DataFrame *from* session state. Add a day counter to session state (`st.session_state['day_count']`).
*   **Step 2.2 (`simulation.py`):** Implement the `advance_day(inventory_df)` function. It should iterate through the DataFrame, calculate random consumption (`random.randint(min, max)`), update QoH (`new_QoH = max(0, current_QoH - consumption)`), and return the modified DataFrame.
*   **Step 2.3 (`app.py`):** Add the "Advance One Day" button to the sidebar. Create a callback function for this button that:
    *   Increments `st.session_state['day_count']`.
    *   Calls `simulation.advance_day` using the DataFrame from session state.
    *   Updates the DataFrame in `st.session_state` with the returned result.
    *   Display the day counter in the sidebar.

**(Chunk 3 Steps)**
*   **Step 3.1 (`simulation.py`):** Implement the `calculate_status(qoh, rop)` helper function returning "Reorder Needed", "Low Stock", or "OK" based on the spec's logic.
*   **Step 3.2 (`app.py`):** Modify the app logic: After loading data (Step 2.1) and after advancing the day (Step 2.3 callback), calculate the `status` column for the DataFrame in session state using `df.apply()` with the `calculate_status` function. Ensure the updated DataFrame (now including status) is stored in session state and displayed.
*   **Step 3.3 (`simulation.py`):** Implement the `simulate_order(inventory_df, item_name)` function. It should:
    *   Find the target item row using `item_name`.
    *   Calculate the `target_stock_level = rop + roq`.
    *   Update the item's `quantity_on_hand` to this `target_stock_level`.
    *   Return the modified DataFrame.
*   **Step 3.4 (`app.py`):** Define a `simulate_order_callback(item_name)` function that:
    *   Calls `simulation.simulate_order` using the DataFrame from session state and the passed `item_name`.
    *   Recalculates the `status` for the *entire* DataFrame (simpler than just one row for now).
    *   Updates the DataFrame in `st.session_state` with the result. *Defer adding the actual button to the UI until the next chunk*.

**(Chunk 4 Steps)**
*   **Step 4.1 (`app.py`):** Refine the table display. Instead of `st.dataframe`, iterate through the DataFrame rows (using `st.session_state['inventory_df'].iterrows()`) and use `st.columns` to manually lay out the data for each item: Item Name, QoH, ROP, Status, Rec. RoQ, Action. This allows placing a button in the 'Action' column.
*   **Step 4.2 (`app.py`):** Implement the conditional "Simulate Order" button logic within the loop from Step 4.1. In the 'Action' column, *if* the item's status is "Reorder Needed", display `st.button("Simulate Order", key=f"order_{item_name}", on_click=simulate_order_callback, args=(item_name,))`.
*   **Step 4.3 (`app.py`):** Implement status coloring. When displaying the 'Status' text in Step 4.1, use Markdown with colors (e.g., `st.markdown(f":red[Reorder Needed]")`, `st.markdown(f":orange[Low Stock]")`, `st.markdown(f":green[OK]")`) based on the status value.
*   **Step 4.4 (`data_loader.py` & `app.py`):** Add basic error handling for database connection in `data_loader.py` (`try...except FileNotFoundError, sqlite3.Error`) and display errors using `st.error()` in `app.py` if loading fails. Ensure session state initialization is robust.

*Self-Correction/Refinement during Sizing:* The steps seem reasonably sized. Chunk 1 establishes the base. Chunk 2 adds the core simulation dynamic. Chunk 3 layers on the business logic (status/ordering). Chunk 4 focuses purely on wiring the UI as specified and polishing. Breaking down the table rendering (4.1) from the conditional button logic (4.2) and coloring (4.3) prevents one overly complex UI step. Moving ROP/RoQ calculation earlier (1.2) simplified later steps. Deferring the button addition (3.4 vs 4.2) ensures the backend logic is sound before integrating complex UI elements.

**Phase 5: LLM Prompt Generation**

Here are the sequential prompts designed for a code-generation LLM, building on each other:

---

**Prompt 1: Project Setup & Data Loader Foundation**

```text
Objective: Set up the basic project structure and create the initial data loading functionality for our Veterinary Inventory PoC.

Context: This is the first coding step. We need to create the initial files and a function to load data from a pre-existing SQLite database (`inventory_poc.db`) with an `inventory_items` table (columns: `item_name` TEXT PK, `min_daily_usage` INT, `max_daily_usage` INT, `buffer_days` INT, `target_days` INT, `initial_quantity_on_hand` INT).

Task:
1.  Create the necessary Python files: `app.py`, `data_loader.py`, `simulation.py`.
2.  Create a `requirements.txt` file listing `streamlit` and `pandas`.
3.  In `data_loader.py`:
    *   Import `pandas` and `sqlite3`.
    *   Define a function `load_inventory_data(db_path='inventory_poc.db')`.
    *   Inside the function:
        *   Connect to the SQLite database specified by `db_path`. Use a `try...except` block to handle potential `sqlite3.Error` or `FileNotFoundError`, printing an error message and returning `None` on failure.
        *   Query `SELECT * FROM inventory_items;`.
        *   Load the query result into a Pandas DataFrame.
        *   Set `item_name` as the DataFrame index.
        *   Calculate the `reorder_point` column as (`max_daily_usage * buffer_days`).
        *   Calculate the `reorder_quantity` column as (`max_daily_usage * target_days`).
        *   Rename the `initial_quantity_on_hand` column to `quantity_on_hand`.
        *   Return the fully prepared DataFrame.
Provide the complete content for `data_loader.py` and the initial empty structures for `app.py` and `simulation.py`, plus the content for `requirements.txt`.
```

---

**Prompt 2: Basic Streamlit App & Initial Data Display**

```text
Objective: Create a basic Streamlit application that loads the inventory data using the function from Prompt 1 and displays it in a raw table.

Context: Building on Prompt 1, we have a `data_loader.py` with the `load_inventory_data` function. We now need to create a minimal Streamlit app to visualize this data. We are deferring session state for now.

Task:
In `app.py`:
1.  Import `streamlit as st` and `pandas as pd`.
2.  Import the `load_inventory_data` function from `data_loader`.
3.  Add a title: `st.title("Veterinary Inventory PoC")`.
4.  Call `load_inventory_data()` to get the initial DataFrame.
5.  Check if the returned DataFrame is not `None` (i.e., loading was successful).
6.  If successful, display the entire DataFrame using `st.dataframe(df)`.
7.  If loading failed (DataFrame is `None`), display an error message using `st.error("Failed to load inventory data. Check database file.")`.

Provide the complete updated content for `app.py`.
```

---

**Prompt 3: Introducing State Management**

```text
Objective: Integrate Streamlit's session state to manage the inventory data and add a day counter, ensuring data persistence across interactions.

Context: Building on Prompt 2, the app currently loads and displays data on each run. We need to load it only once and store it, along with a simulation day counter, in `st.session_state`.

Task:
Modify `app.py`:
1.  Check if `'inventory_df'` is *not* in `st.session_state`.
    *   If it's not present, call `load_inventory_data()`.
    *   If loading is successful, store the returned DataFrame in `st.session_state['inventory_df']`.
    *   If loading fails, store `None` in `st.session_state['inventory_df']`.
    *   Also initialize `st.session_state['day_count'] = 0` only when `'inventory_df'` is first initialized.
2.  Modify the display logic:
    *   Check if `st.session_state['inventory_df']` is not `None`.
    *   If it's valid, display the DataFrame using `st.dataframe(st.session_state['inventory_df'])`.
    *   If it's `None`, display the error message `st.error(...)`.
3.  In the sidebar (`st.sidebar`), display the current day using `st.sidebar.metric("Simulation Day", st.session_state.get('day_count', 0))`. (Use `.get` for safety before initialization).

Provide the complete updated content for `app.py`.
```

---

**Prompt 4: Implementing the Simulation Logic**

```text
Objective: Implement the core daily consumption simulation logic.

Context: Building on Prompt 3, we have the app structure with state management. We now need the function that simulates one day passing.

Task:
In `simulation.py`:
1.  Import `pandas as pd` and `random`.
2.  Define the function `advance_day(inventory_df: pd.DataFrame) -> pd.DataFrame`:
    *   It should take the current inventory DataFrame as input.
    *   Create a copy of the input DataFrame to avoid modifying the original directly within the function (`df = inventory_df.copy()`).
    *   Iterate through each row of the DataFrame copy (e.g., using `df.iterrows()`).
    *   For each item (row):
        *   Get `min_usage = row['min_daily_usage']` and `max_usage = row['max_daily_usage']`.
        *   Calculate `daily_consumption = random.randint(min_usage, max_usage)`.
        *   Get `current_qoh = row['quantity_on_hand']`.
        *   Calculate `new_qoh = max(0, current_qoh - daily_consumption)` (ensure stock doesn't go below zero).
        *   Update the DataFrame copy's `quantity_on_hand` for the current item's index: `df.loc[index, 'quantity_on_hand'] = new_qoh`.
    *   Return the modified DataFrame copy.

Provide the complete content for `simulation.py`.
```

---

**Prompt 5: Connecting Simulation to UI Button**

```text
Objective: Add the "Advance One Day" button to the UI and connect it to the simulation logic, updating the state.

Context: Building on Prompts 3 and 4, we have the state management and the `advance_day` simulation function. We need to trigger the simulation from the UI.

Task:
Modify `app.py`:
1.  Import the `advance_day` function from `simulation`.
2.  Define a callback function `advance_day_callback()`:
    *   Inside the callback, check if `st.session_state['inventory_df']` is not `None`.
    *   If valid, increment `st.session_state['day_count']` by 1.
    *   Call `updated_df = advance_day(st.session_state['inventory_df'])`.
    *   Update the state: `st.session_state['inventory_df'] = updated_df`.
3.  In the sidebar, add the button: `st.sidebar.button("Advance One Day", on_click=advance_day_callback)`. Ensure this is placed *after* the day counter metric.

Provide the complete updated content for `app.py`.
```

---

**Prompt 6: Calculating and Displaying Item Status**

```text
Objective: Implement the status calculation logic and display the status for each item in the table.

Context: Building on Prompt 5, the simulation runs, but we don't see the item status (OK, Low, Reorder). We need to calculate and show this.

Task:
1.  In `simulation.py`:
    *   Define the function `calculate_status(qoh: int, rop: int) -> str`:
        *   Implement the logic:
            *   If `qoh <= rop`, return "Reorder Needed".
            *   Else if `qoh <= rop * 1.25`, return "Low Stock".
            *   Else, return "OK".
2.  Modify `app.py`:
    *   Import the `calculate_status` function from `simulation`.
    *   **Crucially, update the status calculation logic:**
        *   Define a function `update_status_column(df: pd.DataFrame) -> pd.DataFrame`:
            *   If the DataFrame is None or empty, return it as is.
            *   Calculate the 'status' column using `df.apply(lambda row: calculate_status(row['quantity_on_hand'], row['reorder_point']), axis=1)`.
            *   Return the DataFrame with the updated 'status' column.
        *   Call `update_status_column` **immediately after** loading the initial data into session state (inside the `if 'inventory_df' not in st.session_state:` block).
        *   Call `update_status_column` **inside the `advance_day_callback` function**, right after the `advance_day` call returns the updated DataFrame and before it's stored back into session state. This ensures the status is updated after every day advance.
    *   Ensure the displayed DataFrame now includes the calculated 'status' column.

Provide the updated content for `simulation.py` and `app.py`.
```

---

**Prompt 7: Implementing Order Simulation Logic**

```text
Objective: Implement the logic to simulate placing an order, bringing stock up to the target level.

Context: Building on Prompt 6, we can see item statuses. Now we need the backend function to handle the "Simulate Order" action.

Task:
Modify `simulation.py`:
1.  Define the function `simulate_order(inventory_df: pd.DataFrame, item_name: str) -> pd.DataFrame`:
    *   It takes the current inventory DataFrame and the name (index) of the item to reorder.
    *   Create a copy of the input DataFrame (`df = inventory_df.copy()`).
    *   Check if `item_name` exists in the DataFrame index. If not, return the original DataFrame copy without changes (basic error check).
    *   Get the item's `rop = df.loc[item_name, 'reorder_point']` and `roq = df.loc[item_name, 'reorder_quantity']`.
    *   Calculate `target_stock_level = rop + roq`.
    *   Update the DataFrame copy: `df.loc[item_name, 'quantity_on_hand'] = target_stock_level`.
    *   Return the modified DataFrame copy.

Provide the updated content for `simulation.py`.
```

---

**Prompt 8: Preparing the Order Callback Function**

```text
Objective: Create the callback function in the Streamlit app that will trigger the order simulation logic.

Context: Building on Prompt 7, we have the `simulate_order` function. We now need the Streamlit callback function that will eventually be linked to the order buttons.

Task:
Modify `app.py`:
1.  Import the `simulate_order` function from `simulation`.
2.  Define the callback function `simulate_order_callback(item_name: str)`:
    *   Inside the callback, check if `st.session_state['inventory_df']` is not `None`.
    *   If valid, call `ordered_df = simulate_order(st.session_state['inventory_df'], item_name)`.
    *   **Important:** After simulating the order, recalculate the status for all items using the `update_status_column` function created in Prompt 6: `final_df = update_status_column(ordered_df)`.
    *   Update the state: `st.session_state['inventory_df'] = final_df`.
    *   (We are *not* adding the UI button yet).

Provide the complete updated content for `app.py`.
```

---

**Prompt 9: Custom Table Rendering**

```text
Objective: Change the UI from using `st.dataframe` to a custom layout using `st.columns` to prepare for adding buttons within rows.

Context: Building on Prompt 8, we have all the backend logic. Standard `st.dataframe` makes adding buttons difficult. We need to render the table row-by-row manually.

Task:
Modify `app.py`:
1.  Locate the section where `st.dataframe(st.session_state['inventory_df'])` is called.
2.  Replace it with the following logic:
    *   Check if `st.session_state['inventory_df']` is valid.
    *   Display table headers using `st.columns` and `st.markdown` for boldness (e.g., `col1.markdown("**Item Name**")`, `col2.markdown("**QoH**")`, etc. for Item Name, QoH, ROP, Status, Rec. RoQ, Action).
    *   Iterate through the DataFrame in session state using `st.session_state['inventory_df'].iterrows()`.
    *   For each row (`index`, `row_data`):
        *   Create columns using `cols = st.columns(6)` (matching the number of headers).
        *   Display the data in the respective columns:
            *   `cols[0].write(index)` (Item Name)
            *   `cols[1].write(row_data['quantity_on_hand'])`
            *   `cols[2].write(row_data['reorder_point'])`
            *   `cols[3].write(row_data['status'])` (Status - *will be colored later*)
            *   `cols[4].write(row_data['reorder_quantity'])` (Rec. RoQ)
            *   `cols[5].empty()` (Placeholder for the Action button)

Provide the complete updated content for `app.py`.
```

---

**Prompt 10: Adding Conditional Order Buttons and Status Coloring**

```text
Objective: Add the "Simulate Order" button conditionally to the 'Action' column for items needing reorder, and apply status coloring.

Context: Building on Prompt 9, we have a custom table layout. Now we need to add the actual order buttons and visual status cues.

Task:
Modify `app.py` within the table rendering loop (`for index, row_data in ...`):
1.  **Status Coloring:**
    *   Instead of `cols[3].write(row_data['status'])`, use conditional markdown:
        *   `status = row_data['status']`
        *   `if status == "Reorder Needed": cols[3].markdown(f":red[{status}]")`
        *   `elif status == "Low Stock": cols[3].markdown(f":orange[{status}]")`
        *   `else: cols[3].markdown(f":green[{status}]")`
2.  **Conditional Button:**
    *   Instead of `cols[5].empty()`, add the conditional button:
        *   `if status == "Reorder Needed":`
            *   `cols[5].button("Simulate Order", key=f"order_{index}", on_click=simulate_order_callback, args=(index,))`
        *   `else: cols[5].write("")` (Or `cols[5].empty()` if preferred for spacing)

Provide the complete updated content for `app.py`.
```

---

**Prompt 11: Final Polish - Error Handling**

```text
Objective: Add basic error handling around the initial data loading process.

Context: Building on Prompt 10, the application is functionally complete. We need to make the initial data loading slightly more robust.

Task:
1.  Modify `data_loader.py`: Ensure the `load_inventory_data` function includes the `try...except` block around the database connection and query, handling `FileNotFoundError` and `sqlite3.Error`. It should print an error to console and return `None` on failure.
2.  Modify `app.py`: Ensure the initial state setup logic (where `load_inventory_data` is called) correctly handles the case where `load_inventory_data` returns `None` by setting `st.session_state['inventory_df'] = None` and displaying the `st.error(...)` message prominently if this occurs.

Provide the final updated content for `data_loader.py` and `app.py`.
```

---

These prompts provide a step-by-step guide for the LLM, ensuring incremental development and integration of each piece towards the final specified PoC application. Remember to provide the LLM with the output of the previous step when issuing the next prompt.