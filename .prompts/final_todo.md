
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