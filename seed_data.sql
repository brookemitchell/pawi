-- Drop the table if it exists (optional, useful for ensuring a clean seed)
DROP TABLE IF EXISTS inventory_items;

-- Create the table schema
CREATE TABLE inventory_items (
    item_name TEXT PRIMARY KEY,
    min_daily_usage INTEGER NOT NULL,
    max_daily_usage INTEGER NOT NULL,
    buffer_days INTEGER NOT NULL,
    target_days INTEGER NOT NULL,
    initial_quantity_on_hand INTEGER NOT NULL
);

-- Create the inventory_batches table schema
DROP TABLE IF EXISTS inventory_batches;
CREATE TABLE inventory_batches (
    batch_id INTEGER PRIMARY KEY AUTOINCREMENT, -- Use AUTOINCREMENT for unique IDs
    item_name TEXT NOT NULL,
    quantity_on_hand INTEGER NOT NULL,
    expiry_date DATE, -- Store expiry date as DATE
    FOREIGN KEY (item_name) REFERENCES inventory_items(item_name)
);

-- Insert the seeding data for inventory_items
INSERT INTO inventory_items (item_name, min_daily_usage, max_daily_usage, buffer_days, target_days, initial_quantity_on_hand) VALUES
('Parvo tests', 0, 5, 3, 7, 12),
('Blood cartridges', 8, 30, 3, 10, 105),
('Antigen tests', 10, 25, 3, 10, 70),
('Slide type 1', 5, 20, 5, 14, 200),
('Slide type 2', 5, 20, 5, 14, 250),
('Cover glass', 10, 45, 5, 14, 450),
('Applicator type 1', 10, 30, 4, 10, 140),
('Applicator type 2', 5, 20, 4, 14, 220),
('Applicator type 3', 5, 20, 4, 14, 240);

-- Commit the changes (handled by Python's connection context or explicit commit)
