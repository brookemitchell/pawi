import pandas as pd
import random
from datetime import date, timedelta # Ensure date is imported

def advance_day(batches_df: pd.DataFrame, item_params_df: pd.DataFrame, current_sim_date: date) -> pd.DataFrame:
    """
    Simulates one day of inventory consumption using FEFO (First-Expired, First-Out).

    Args:
        batches_df: DataFrame containing current inventory batches.
                    Must include 'item_name', 'quantity_on_hand', 'expiry_date'.
                    Index should be unique (e.g., 'batch_id').
        item_params_df: DataFrame containing item parameters.
                        Must include 'min_daily_usage', 'max_daily_usage'.
                        Index should be 'item_name'.
        current_sim_date: The current date of the simulation.

    Returns:
        A new DataFrame with updated 'quantity_on_hand' for batches,
        reflecting the simulated daily consumption based on FEFO.
        Batches with quantity <= 0 are removed.
        Returns the original DataFrame if input is invalid.
    """
    if batches_df is None or item_params_df is None or current_sim_date is None:
        print("Error: Invalid input to advance_day.")
        return batches_df # Return original if input is invalid

    df_copy = batches_df.copy()

    # Ensure expiry_date is in datetime format for comparison
    # It should already be datetime from data_loader, but double-check
    if not pd.api.types.is_datetime64_any_dtype(df_copy['expiry_date']):
         df_copy['expiry_date'] = pd.to_datetime(df_copy['expiry_date'], errors='coerce')

    # Convert current_sim_date to datetime64[ns] to match pandas datetime objects for comparison
    current_sim_date_dt = pd.to_datetime(current_sim_date)

    for item_name in item_params_df.index:
        try:
            min_usage = int(item_params_df.loc[item_name, 'min_daily_usage'])
            max_usage = int(item_params_df.loc[item_name, 'max_daily_usage'])

            # Calculate daily consumption
            if min_usage > max_usage:
                print(f"Warning: Min usage ({min_usage}) > Max usage ({max_usage}) for item {item_name}. Using min_usage.")
                daily_consumption = min_usage
            elif min_usage == max_usage:
                daily_consumption = min_usage
            else:
                daily_consumption = random.randint(min_usage, max_usage)

            if daily_consumption == 0:
                continue # No consumption for this item today

            # Filter for active, non-expired batches of the current item
            # Compare expiry_date (datetime) with current_sim_date_dt (datetime)
            item_batches_idx = df_copy[
                (df_copy['item_name'] == item_name) &
                (df_copy['quantity_on_hand'] > 0) &
                (df_copy['expiry_date'].notna()) & # Ensure expiry date is not NaT
                (df_copy['expiry_date'] >= current_sim_date_dt) # Compare datetime objects
            ].index

            if item_batches_idx.empty:
                # print(f"No active, non-expired batches found for {item_name} on {current_sim_date}")
                continue # No batches to consume from

            # Sort these active batches by expiry date (FEFO)
            sorted_batches = df_copy.loc[item_batches_idx].sort_values(by='expiry_date')

            # Consume from sorted batches
            for batch_index, batch_data in sorted_batches.iterrows():
                batch_qoh = batch_data['quantity_on_hand']
                consume_amount = min(daily_consumption, batch_qoh)

                # Update quantity in the main DataFrame copy
                df_copy.loc[batch_index, 'quantity_on_hand'] -= consume_amount
                daily_consumption -= consume_amount

                # print(f"  Consumed {consume_amount} from batch {batch_index} (Item: {item_name}). Remaining consumption: {daily_consumption}") # Debug print

                if daily_consumption <= 0:
                    break # Finished consuming for this item

        except KeyError as e:
            print(f"Error processing item {item_name}: Missing expected column {e} in item_params_df. Skipping consumption.")
            continue
        except ValueError as e:
            print(f"Error processing item {item_name}: Invalid data type for usage calculation ({e}). Skipping consumption.")
            continue
        except Exception as e:
            print(f"An unexpected error occurred processing item {item_name}: {e}")
            continue

    # Remove batches that have been fully consumed
    df_copy = df_copy[df_copy['quantity_on_hand'] > 0]

    return df_copy

def calculate_status(qoh: int, rop: int) -> str:
    """
    Calculates the inventory status based on quantity on hand and reorder point.

    Args:
        qoh: Current quantity on hand.
        rop: Reorder point.

    Returns:
        A string indicating the status: "Reorder Needed", "Low Stock", or "OK".
    """
    # Ensure inputs are numeric, handle potential errors gracefully
    try:
        qoh = int(qoh)
        rop = int(rop)
    except (ValueError, TypeError):
        # Handle cases where inputs might not be numbers (e.g., NaN, None)
        return "Error" # Or some other indicator of invalid input

    if qoh <= rop:
        return "Reorder Needed"
    elif qoh <= rop * 1.25:
        return "Low Stock"
    else:
        return "OK"

def simulate_order(inventory_df: pd.DataFrame, item_name: str) -> pd.DataFrame:
    """
    Simulates placing an order for a specific item, updating its quantity
    on hand to the target stock level (ROP + RoQ).

    Args:
        inventory_df: The current inventory status DataFrame.
                      Must include 'reorder_point', 'reorder_quantity',
                      and 'quantity_on_hand' columns.
        item_name: The name (index) of the item to reorder.

    Returns:
        A new DataFrame with the updated quantity_on_hand for the specified item.
        Returns the original DataFrame if the item_name is not found or input is invalid.
    """
    if inventory_df is None or inventory_df.empty:
        print("Error: Cannot simulate order on empty or None DataFrame.")
        return inventory_df

    df = inventory_df.copy() # Work on a copy

    if item_name not in df.index:
        print(f"Error: Item '{item_name}' not found in inventory DataFrame. Cannot simulate order.")
        return df # Return the unmodified copy

    try:
        # Get the item's ROP and RoQ
        rop = int(df.loc[item_name, 'reorder_point'])
        roq = int(df.loc[item_name, 'reorder_quantity'])

        # Calculate the target stock level
        target_stock_level = rop + roq

        # Update the quantity on hand for the item
        df.loc[item_name, 'quantity_on_hand'] = target_stock_level
        print(f"Simulated order for '{item_name}'. Quantity on hand set to {target_stock_level}.")

    except KeyError as e:
        print(f"Error simulating order for {item_name}: Missing expected column {e}.")
        # Return the unmodified copy if data is missing
        return inventory_df.copy()
    except (ValueError, TypeError) as e:
        print(f"Error simulating order for {item_name}: Invalid data type for calculation ({e}).")
        # Return the unmodified copy if data is invalid
        return inventory_df.copy()

    return df

# --- Placeholder for future simulation functions ---
# def simulate_order(inventory_df, item_name): ... # <-- Keep or remove this line as desired
