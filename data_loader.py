import pandas as pd
import sqlite3
import os # Import os to construct the path robustly

def _seed_database(db_path, seed_file='seed_data.sql'):
    """Creates and seeds the database from a SQL file."""
    seed_file_path = os.path.join(os.path.dirname(db_path), seed_file)
    if not os.path.exists(seed_file_path):
        print(f"Error: Seed file not found at {seed_file_path}")
        return False # Indicate seeding failure

    conn = None
    try:
        print(f"Database not found. Seeding database from {seed_file_path}...")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        with open(seed_file_path, 'r') as f:
            sql_script = f.read()
        cursor.executescript(sql_script)
        conn.commit()
        print("Database seeded successfully.")
        return True # Indicate seeding success
    except sqlite3.Error as e:
        print(f"SQLite error during seeding: {e}")
        # Attempt to remove potentially corrupted DB file
        if conn: conn.close() # Close connection before removing
        if os.path.exists(db_path): os.remove(db_path)
        return False # Indicate seeding failure
    except IOError as e:
        print(f"Error reading seed file {seed_file_path}: {e}")
        if conn: conn.close()
        return False # Indicate seeding failure
    finally:
        if conn:
            conn.close()

def load_inventory_data(db_name='inventory_poc.db') -> pd.DataFrame | None:
    """
    Loads inventory data from the specified SQLite database file.
    If the database file does not exist, it attempts to create and
    seed it using 'seed_data.sql'.

    Args:
        db_name (str): The name of the SQLite database file. Assumed to be
                       in the same directory as this script.

    Returns:
        tuple[pd.DataFrame | None, pd.DataFrame | None]: A tuple containing:
            - inventory_status_df: DataFrame with item parameters, current QOH,
                                   calculated reorder points/quantities, indexed by item_name.
            - batches_df: DataFrame with raw batch details, indexed by batch_id.
            Returns (None, None) if loading fails.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__)) # Use abspath for reliability
    db_path = os.path.join(script_dir, db_name)

    # --- Seeding Logic ---
    if not os.path.exists(db_path):
        if not _seed_database(db_path):
            # Seeding failed, error message printed in _seed_database
            return None # Cannot proceed without database

    # --- Data Loading Logic (proceeds if DB exists or was seeded) ---
    conn = None
    try:
        conn = sqlite3.connect(db_path)

        # Load item parameters
        params_query = "SELECT * FROM inventory_items;"
        item_params_df = pd.read_sql_query(params_query, conn)

        if item_params_df.empty:
            print("Error: No data found in item_parameters table.")
            return None, None
        if 'item_name' not in item_params_df.columns:
            print("Error: 'item_name' column not found in item_parameters table.")
            return None, None
        item_params_df = item_params_df.set_index('item_name')
        print("Loaded item_parameters table.")

        # Load inventory batches
        batches_query = "SELECT batch_id, item_name, quantity_on_hand, expiry_date FROM inventory_batches;"
        batches_df = pd.read_sql_query(batches_query, conn)

        if batches_df.empty:
            print("Warning: No data found in inventory_batches table. Returning empty DataFrame.")
            # Return parameters but empty batches - might be valid if starting fresh
            # Ensure required columns exist even if empty for consistency downstream
            batches_df = pd.DataFrame(columns=['batch_id', 'item_name', 'quantity_on_hand', 'expiry_date'])
        else:
             # Convert expiry_date to datetime objects
            if 'expiry_date' in batches_df.columns:
                batches_df['expiry_date'] = pd.to_datetime(batches_df['expiry_date'], errors='coerce')
                if batches_df['expiry_date'].isnull().any():
                    print("Warning: Some expiry dates could not be parsed and were set to NaT.")
            else:
                print("Error: 'expiry_date' column not found in inventory_batches table.")
                return item_params_df, None # Return params, but signal batch error

            # Set batch_id as index
            if 'batch_id' in batches_df.columns:
                batches_df = batches_df.set_index('batch_id')
            else:
                print("Error: 'batch_id' column not found in inventory_batches table.")
                return item_params_df, None # Return params, but signal batch error

        # --- Calculate Aggregated QOH and Merge ---
        if not batches_df.empty:
            # Calculate total quantity on hand per item from batches
            qoh_agg = batches_df.groupby('item_name')['quantity_on_hand'].sum().reset_index()
            qoh_agg = qoh_agg.rename(columns={'quantity_on_hand': 'calculated_qoh'})

            # Merge aggregated QOH into item_params_df
            # Use left merge to keep all items from item_params_df
            inventory_status_df = pd.merge(item_params_df.reset_index(), qoh_agg, on='item_name', how='left')

            # Fill NaN in calculated_qoh with 0 (items with params but no batches)
            inventory_status_df['calculated_qoh'] = inventory_status_df['calculated_qoh'].fillna(0).astype(int)

            # Decide which QOH to use (currently using calculated from batches)
            # We might want logic here later to use initial_quantity_on_hand if batches are empty
            inventory_status_df['quantity_on_hand'] = inventory_status_df['calculated_qoh']
            # Drop the intermediate column and the initial one if no longer needed directly
            inventory_status_df = inventory_status_df.drop(columns=['calculated_qoh', 'initial_quantity_on_hand'])

        else:
            # If batches_df is empty, use initial_quantity_on_hand as current QOH
            print("Warning: Batches table is empty. Using initial_quantity_on_hand as current quantity.")
            inventory_status_df = item_params_df.reset_index() # Keep item_name as column temporarily
            inventory_status_df['quantity_on_hand'] = inventory_status_df['initial_quantity_on_hand']
            inventory_status_df = inventory_status_df.drop(columns=['initial_quantity_on_hand'])


        # --- Calculate Reorder Point and Quantity ---
        # Ensure required columns exist before calculation
        if all(col in inventory_status_df.columns for col in ['max_daily_usage', 'buffer_days', 'target_days']):
            inventory_status_df['reorder_point'] = inventory_status_df['max_daily_usage'] * inventory_status_df['buffer_days']
            inventory_status_df['reorder_quantity'] = inventory_status_df['max_daily_usage'] * inventory_status_df['target_days']
        else:
            print("Error: Missing columns required for reorder point/quantity calculation.")
            # Add empty columns to prevent KeyErrors downstream, but signal the issue
            inventory_status_df['reorder_point'] = 0
            inventory_status_df['reorder_quantity'] = 0


        # Set item_name back as index for the final status DataFrame
        inventory_status_df = inventory_status_df.set_index('item_name')

        print(f"Successfully loaded and processed data from {db_path}")
        return inventory_status_df, batches_df # Return the enhanced status df and original batches df

    except sqlite3.Error as e:
        print(f"SQLite error occurred during data loading: {e}")
        return None, None
    except Exception as e:
        # Catch other potential errors during DataFrame processing
        print(f"An unexpected error occurred during data loading: {e}")
        return None, None
    finally:
        if conn:
            conn.close()

# Example usage (optional, for testing the function directly)
if __name__ == '__main__':
    item_params, inventory_batches = load_inventory_data()
    if item_params is not None and inventory_batches is not None:
        print("\nItem Parameters loaded successfully:")
        print(item_params.info())
        print(item_params.head())
        print("\nInventory Batches loaded successfully:")
        print(inventory_batches.info())
        print(inventory_batches.head())
    else:
        print("\nFailed to load inventory data.")
