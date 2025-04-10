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
        pd.DataFrame | None: A DataFrame containing the inventory data with
                              calculated ROP and RoQ, or None if loading fails.
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
        query = "SELECT * FROM inventory_items;"
        # Use pandas read_sql_query for simplicity and robustness
        df = pd.read_sql_query(query, conn)

        if df.empty:
            print("Error: No data found in inventory_items table after loading.")
            return None

        # Set 'item_name' as the DataFrame index
        if 'item_name' in df.columns:
            df = df.set_index('item_name')
        else:
            print("Error: 'item_name' column not found in the database table.")
            return None

        # Ensure necessary columns exist before calculations
        required_cols = ['max_daily_usage', 'buffer_days', 'target_days', 'initial_quantity_on_hand']
        if not all(col in df.columns for col in required_cols):
            missing = [col for col in required_cols if col not in df.columns]
            print(f"Error: Missing one or more required columns from DB: {missing}")
            return None

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
        print(f"SQLite error occurred during data loading: {e}")
        return None
    except Exception as e:
        # Catch other potential errors during DataFrame processing
        print(f"An unexpected error occurred during data loading: {e}")
        return None
    finally:
        if conn:
            conn.close()

# Example usage (optional, for testing the function directly)
if __name__ == '__main__':
    inventory_data = load_inventory_data()
    if inventory_data is not None:
        print("\nInventory Data loaded successfully:")
        print(inventory_data.info())
        print(inventory_data.head())
    else:
        print("\nFailed to load inventory data.")
