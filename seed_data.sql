-- Drop the table if it exists (optional, useful for ensuring a clean seed)
DROP TABLE IF EXISTS inventory_items;

-- Create the table schema
CREATE TABLE inventory_items (
    item_name TEXT PRIMARY KEY,
    min_daily_usage INTEGER NOT NULL,
    max_daily_usage INTEGER NOT NULL,
    buffer_days INTEGER NOT NULL,
    target_days INTEGER NOT NULL,
    initial_quantity_on_hand INTEGER NOT NULL,
    standard_shelf_life_months INTEGER NOT NULL DEFAULT 12 -- Added shelf life column with a default
);

-- Create the inventory_batches table schema
DROP TABLE IF EXISTS inventory_batches;
CREATE TABLE inventory_batches (
    batch_id INTEGER PRIMARY KEY, -- INTEGER PRIMARY KEY is auto-incrementing by default
    item_name TEXT NOT NULL,
    quantity_on_hand INTEGER NOT NULL,
    expiry_date DATE, -- Store expiry date as DATE
    FOREIGN KEY (item_name) REFERENCES inventory_items(item_name)
);

-- Insert the seeding data for inventory_items including standard_shelf_life_months
-- Using example shelf life values (in months)
INSERT INTO inventory_items (item_name, min_daily_usage, max_daily_usage, buffer_days, target_days, initial_quantity_on_hand, standard_shelf_life_months) VALUES
('Parvo tests', 0, 5, 3, 7, 12, 12),          -- 12 months
('Blood cartridges', 8, 30, 3, 10, 105, 6),   -- 6 months
('Antigen tests', 10, 25, 3, 10, 70, 12),     -- 12 months
('Slide type 1', 5, 20, 5, 14, 200, 36),      -- 36 months
('Slide type 2', 5, 20, 5, 14, 250, 36),      -- 36 months
('Cover glass', 10, 45, 5, 14, 450, 60),      -- 60 months (very long)
('Applicator type 1', 10, 30, 4, 10, 140, 24), -- 24 months
('Applicator type 2', 5, 20, 4, 14, 220, 24), -- 24 months
('Applicator type 3', 5, 20, 4, 14, 240, 24); -- 24 months

-- Insert initial batch data based on initial_quantity_on_hand from inventory_items
-- Using varied expiry dates relative to the current date (approx 2025-04-11) for testing alerts
INSERT INTO inventory_batches (item_name, quantity_on_hand, expiry_date) VALUES
('Parvo tests', 12, '2025-04-25'),          -- Nearing Expiry (within 30 days)
('Blood cartridges', 105, '2025-03-15'),    -- Expired (in the past)
('Antigen tests', 70, '2025-08-01'),        -- OK (future)
('Slide type 1', 200, '2025-05-01'),        -- Nearing Expiry (within 30 days)
('Slide type 2', 250, '2099-12-31'),        -- OK (far future)
('Cover glass', 450, '2099-12-31'),        -- OK (far future)
('Applicator type 1', 140, '2025-02-10'),    -- Expired (in the past)
('Applicator type 2', 220, '2099-12-31'),    -- OK (far future)
('Applicator type 3', 240, '2099-12-31');    -- OK (far future)


-- Commit the changes (handled by Python's connection context or explicit commit)
