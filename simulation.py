import pandas as pd
import random
from datetime import date, timedelta, datetime # Ensure date, timedelta, datetime are imported

# --- Constants ---
ALERT_DAYS_BEFORE_EXPIRY = 30

# --- Simulation Functions ---
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

def calculate_expiry_status(expiry_date, current_date, alert_days=ALERT_DAYS_BEFORE_EXPIRY) -> str:
    """
    Calculates the expiry status of a batch based on the current date.

    Args:
        expiry_date: The expiry date of the batch (should be datetime-like or NaT).
        current_date: The current simulation date (should be datetime-like).
        alert_days: The number of days before expiry to trigger the "Nearing Expiry" status.

    Returns:
        A string: "Expired", "Nearing Expiry", "OK", or "Unknown".
    """
    # Ensure dates are comparable datetime objects
    if pd.isna(expiry_date):
        return "Unknown" # Handle NaT or None expiry dates

    # Ensure expiry_date is datetime-like (it should be from loading/creation)
    if not isinstance(expiry_date, (datetime, date, pd.Timestamp)):
         try:
             expiry_date = pd.to_datetime(expiry_date)
         except ValueError:
             return "Unknown" # Cannot parse expiry date

    # Ensure current_date is datetime-like
    if not isinstance(current_date, (datetime, date, pd.Timestamp)):
        try:
            current_date = pd.to_datetime(current_date)
        except ValueError:
            return "Error" # Should not happen if current_sim_date is managed correctly

    # Normalize to date objects to avoid time comparison issues if Timestamps are used
    expiry_date_obj = expiry_date.date() if hasattr(expiry_date, 'date') else expiry_date
    current_date_obj = current_date.date() if hasattr(current_date, 'date') else current_date

    if expiry_date_obj < current_date_obj:
        return "Expired"

    alert_date_obj = current_date_obj + timedelta(days=alert_days)

    if current_date_obj <= expiry_date_obj < alert_date_obj:
        return "Nearing Expiry"
    else:
        return "OK"


def add_new_batch(batches_df: pd.DataFrame, item_params_df: pd.DataFrame, item_name: str, current_sim_date: date) -> pd.DataFrame:
    """
    Simulates receiving a new batch for a specific item.

    Adds a new row to the batches DataFrame with the item's reorder quantity
    and calculates the expiry date based on its standard shelf life.

    Args:
        batches_df: The current DataFrame of inventory batches.
        item_params_df: DataFrame containing item parameters (incl. 'standard_shelf_life_months', 'reorder_quantity').
        item_name: The name of the item for which to add a batch.
        current_sim_date: The current simulation date, used as the receiving date.

    Returns:
        A new DataFrame with the added batch. Returns the original DataFrame
        if the item_name is not found in item_params_df or input is invalid.
    """
    if batches_df is None or item_params_df is None or not item_name or current_sim_date is None:
        print("Error: Invalid input to add_new_batch.")
        return batches_df

    df_copy = batches_df.copy()

    if item_name not in item_params_df.index:
        print(f"Error: Item '{item_name}' not found in item parameters. Cannot add batch.")
        return df_copy # Return the unmodified copy

    try:
        # Get parameters from item_params_df
        item_params = item_params_df.loc[item_name]
        shelf_life_months = int(item_params['standard_shelf_life_months'])
        reorder_quantity = int(item_params['reorder_quantity'])

        # Calculate expiry date
        # Ensure current_sim_date is datetime-like for DateOffset
        current_sim_date_dt = pd.to_datetime(current_sim_date)
        expiry_date_ts = current_sim_date_dt + pd.DateOffset(months=shelf_life_months)
        # Convert Timestamp back to date object if needed, or keep as Timestamp
        # Let's keep as Timestamp for consistency within pandas
        expiry_date = expiry_date_ts # pd.to_datetime handles this well

        # Create new batch data
        # Note: We are not assigning a batch_id here. It's assumed the DB would handle this
        # upon actual persistence. For runtime, concat with ignore_index handles it.
        new_batch_data = {
            'item_name': item_name,
            'quantity_on_hand': reorder_quantity,
            'expiry_date': expiry_date
            # 'batch_id': None # Explicitly not setting it here
        }
        print(f"Adding new batch for {item_name}: Qty={reorder_quantity}, Expires={expiry_date.strftime('%Y-%m-%d')}")

        # Convert dictionary to a DataFrame
        new_batch_df = pd.DataFrame([new_batch_data])

        # Append the new batch DataFrame
        # Reset index of the original df_copy IF it has a meaningful index (like batch_id)
        # that would conflict. If it's just a default range index, it might not be necessary.
        # Using ignore_index=True is the safest approach for runtime concatenation
        # when the new row doesn't have a pre-assigned index matching the existing scheme.
        # If df_copy still has 'batch_id' as index from loading, we need to reset it first.
        if df_copy.index.name == 'batch_id':
             df_updated = pd.concat([df_copy.reset_index(), new_batch_df], ignore_index=True)
             # Decide if we need to set an index back. For now, let's leave it as a default RangeIndex.
             # If we need batch_id later, we might need to adjust.
             # df_updated = df_updated.set_index('batch_id') # Optional: reinstate index if needed
        else:
             # If index is not 'batch_id' (e.g., default RangeIndex), just concat
             df_updated = pd.concat([df_copy, new_batch_df], ignore_index=True)


        return df_updated

    except KeyError as e:
        print(f"Error adding batch for {item_name}: Missing expected column {e} in item_params_df.")
        return df_copy
    except (ValueError, TypeError) as e:
        print(f"Error adding batch for {item_name}: Invalid data type for calculation ({e}).")
        return df_copy
    except Exception as e:
        print(f"An unexpected error occurred adding batch for {item_name}: {e}")
        return df_copy

# --- Placeholder for future simulation functions ---
