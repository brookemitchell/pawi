import pandas as pd
import sqlite3
import os # Import os to construct the path robustly

def load_inventory_data(db_name='inventory_poc.db') -> pd.DataFrame | None:
    """
    Loads inventory data from the specified SQLite database file.

    Args:
        db_name (str): The name of the SQLite database file. Assumed to be
                       in the same directory as this script.

    Returns:
        pd.DataFrame | None: A DataFrame containing the inventory data with
                              calculated ROP and RoQ, or None if loading fails.
    """
    # Construct the full path to the database file relative to this script
    script_dir = os.path.dirname(__file__)
    db_path = os.path.join(script_dir, db_name)

    try:
        # Check if the database file exists
        if not os.path.exists(db_path):
            print(f"Error: Database file not found at {db_path}")
            # Consider raising a specific error or logging here
            # For now, returning None as per original plan for basic handling
            return None

        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Query the inventory_items table
        query = "SELECT * FROM inventory_items;"
        cursor.execute(query)
        rows = cursor.fetchall()
        column_names = [description[0] for description in cursor.description]

        # Close the connection
        conn.close()

        # Load the query result into a Pandas DataFrame
        df = pd.DataFrame(rows, columns=column_names)

        # Set 'item_name' as the DataFrame index
        if 'item_name' in df.columns:
            df = df.set_index('item_name')
        else:
            print("Error: 'item_name' column not found in the database table.")
            return None # Or raise an error

        # Ensure necessary columns exist before calculations
        required_cols = ['max_daily_usage', 'buffer_days', 'target_days', 'initial_quantity_on_hand']
        if not all(col in df.columns for col in required_cols):
            print(f"Error: Missing one or more required columns: {required_cols}")
            return None # Or raise an error

        # Calculate the 'reorder_point' column
        df['reorder_point'] = df['max_daily_usage'] * df['buffer_days']

        # Calculate the 'reorder_quantity' column (RoQ)
        df['reorder_quantity'] = df['max_daily_usage'] * df['target_days']

        # Rename the 'initial_quantity_on_hand' column to 'quantity_on_hand'
        df = df.rename(columns={'initial_quantity_on_hand': 'quantity_on_hand'})

        # Ensure quantity_on_hand is integer type
        df['quantity_on_hand'] = df['quantity_on_hand'].astype(int)

        print(f"Successfully loaded data from {db_path}")
        return df

    except sqlite3.Error as e:
        print(f"SQLite error occurred: {e}")
        return None
    except FileNotFoundError:
        # This specific exception might be redundant if os.path.exists check is done,
        # but kept for robustness in case of race conditions or other issues.
        print(f"Error: Database file not found at {db_path}")
        return None
    except Exception as e:
        # Catch other potential errors during DataFrame processing
        print(f"An unexpected error occurred during data loading: {e}")
        return None

# Example usage (optional, for testing the function directly)
if __name__ == '__main__':
    inventory_data = load_inventory_data()
    if inventory_data is not None:
        print("\nInventory Data loaded successfully:")
        print(inventory_data.info())
        print(inventory_data.head())
    else:
        print("\nFailed to load inventory data.")
