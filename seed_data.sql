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

-- Insert the seeding data
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
