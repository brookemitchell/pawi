import pandas as pd
import random

def advance_day(inventory_df: pd.DataFrame) -> pd.DataFrame:
    """
    Simulates one day of inventory consumption.

    Args:
        inventory_df: The current inventory status DataFrame.
                      Must include 'min_daily_usage', 'max_daily_usage',
                      and 'quantity_on_hand' columns.

    Returns:
        A new DataFrame with updated 'quantity_on_hand' for each item,
        reflecting the simulated daily consumption. Returns the original
        DataFrame if input is None or empty.
    """
    if inventory_df is None or inventory_df.empty:
        return inventory_df # Return original if invalid input

    df = inventory_df.copy() # Work on a copy to avoid side effects

    for index, row in df.iterrows():
        try:
            min_usage = int(row['min_daily_usage'])
            max_usage = int(row['max_daily_usage'])
            current_qoh = int(row['quantity_on_hand'])

            # Ensure min_usage is not greater than max_usage
            if min_usage > max_usage:
                # Handle potential data error: use min_usage as consumption
                # Or log a warning and use 0 or max_usage
                print(f"Warning: Min usage ({min_usage}) > Max usage ({max_usage}) for item {index}. Using min_usage.")
                daily_consumption = min_usage
            elif min_usage == max_usage:
                daily_consumption = min_usage # No random needed if range is 0
            else:
                # Generate random consumption within the defined range
                daily_consumption = random.randint(min_usage, max_usage)

            # Calculate new quantity on hand, ensuring it doesn't go below zero
            new_qoh = max(0, current_qoh - daily_consumption)

            # Update the quantity_on_hand in the copied DataFrame
            df.loc[index, 'quantity_on_hand'] = new_qoh

        except KeyError as e:
            print(f"Error processing item {index}: Missing expected column {e}. Skipping consumption.")
            continue # Skip this item if data is missing
        except ValueError as e:
            print(f"Error processing item {index}: Invalid data type for calculation ({e}). Skipping consumption.")
            continue # Skip this item if data is not numeric

    return df

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
