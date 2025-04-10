import os
import sqlalchemy
from sqlalchemy import text

# --- Configuration ---
DB_FILE = "inventory.db"
SQL_FILE = "data.sql"
DB_URL = f"sqlite:///{DB_FILE}"
# ---------------------

def read_sql_file(filepath):
    """Reads SQL file content and returns a list of statements."""
    if not os.path.exists(filepath):
        print(f"Error: SQL file not found at: {filepath}")
        return None
    try:
        with open(filepath, 'r') as file:
            sql_content = file.read()
            # Split statements by semicolon, filter out empty ones and comments
            statements = [
                stmt.strip() for stmt in sql_content.split(';')
                if stmt.strip() and not stmt.strip().startswith('--')
            ]
        return statements
    except Exception as e:
        print(f"Error reading SQL file {filepath}: {e}")
        return None

def seed_database():
    """Creates and seeds the SQLite database if it doesn't exist."""
    if os.path.exists(DB_FILE):
        print(f"Database '{DB_FILE}' already exists. Skipping seeding.")
        return

    print(f"Database '{DB_FILE}' not found. Creating and seeding...")
    sql_statements = read_sql_file(SQL_FILE)

    if not sql_statements:
        print("No SQL statements found to execute. Seeding aborted.")
        return

    try:
        engine = sqlalchemy.create_engine(DB_URL)
        with engine.connect() as connection:
            with connection.begin(): # Start a transaction
                for statement in sql_statements:
                    if statement: # Ensure statement is not empty
                        connection.execute(text(statement))
        print(f"Database '{DB_FILE}' created and seeded successfully from '{SQL_FILE}'!")
    except Exception as e:
        print(f"Error executing SQL statements: {e}")
        # Attempt to clean up the potentially partially created db file on error
        if os.path.exists(DB_FILE):
            try:
                os.remove(DB_FILE)
                print(f"Removed partially created database file '{DB_FILE}'.")
            except OSError as rm_err:
                print(f"Error removing partially created database file: {rm_err}")

if __name__ == "__main__":
    seed_database()
