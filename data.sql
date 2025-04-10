CREATE TABLE supplier (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    contact_info VARCHAR(200),
    api_endpoint VARCHAR(200)
);

CREATE TABLE inventory (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    quantity INT NOT NULL,
    reorder_level INT NOT NULL,
    expiration_date DATE,
    supplier_id INT REFERENCES supplier(id)
);

CREATE TABLE usage_history (
    id SERIAL PRIMARY KEY,
    inventory_id INT REFERENCES inventory(id),
    date DATE NOT NULL,
    quantity_used INT NOT NULL
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    inventory_id INT REFERENCES inventory(id),
    supplier_id INT REFERENCES supplier(id),
    quantity INT NOT NULL,
    status VARCHAR(50) DEFAULT 'Pending',
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sample Supplier Data
INSERT INTO supplier (name, contact_info, api_endpoint) VALUES
('IDEXX Diagnostics', 'contact@idexx.com', 'https://api.idexx.com/order'),
('VetSupplies Inc.', 'support@vetsupplies.com', 'https://api.vetsupplies.com/order'),
('PharmaVet', 'info@pharmavet.com', 'https://api.pharmavet.com/order');

-- Sample Inventory Data
INSERT INTO inventory (name, category, quantity, reorder_level, expiration_date, supplier_id) VALUES
('IDEXX Diagnostic Kit', 'Diagnostic Kits', 50, 20, '2025-05-01', 1),
('Vet Medications - Pain Relievers', 'Medications', 30, 15, '2025-06-01', 1),
('Vet Equipment - Thermometer', 'Equipment', 100, 40, '2025-04-15', 2),
('IDEXX Test Strips', 'Test Supplies', 75, 25, '2025-07-01', 1),
('Medications - Antibiotics', 'Medications', 40, 10, '2025-08-20', 3),
('Vet Surgical Kits', 'Surgical Kits', 15, 5, '2025-09-01', 2),
('Medications - Heartworm Treatment', 'Medications', 50, 20, '2025-12-01', 3),
('Surgical Gloves', 'Surgical Supplies', 200, 100, '2025-11-15', 2);

-- Sample Usage History Data
INSERT INTO usage_history (inventory_id, date, quantity_used) VALUES
(1, '2025-03-01', 5),
(1, '2025-03-02', 6),
(1, '2025-03-03', 4),
(2, '2025-03-01', 3),
(2, '2025-03-02', 2),
(2, '2025-03-03', 3),
(3, '2025-03-01', 10),
(3, '2025-03-02', 5),
(4, '2025-03-01', 8),
(4, '2025-03-02', 6),
(4, '2025-03-03', 5),
(5, '2025-03-01', 4),
(5, '2025-03-02', 3),
(6, '2025-03-01', 3),
(6, '2025-03-02', 2),
(7, '2025-03-01', 5),
(7, '2025-03-02', 4),
(8, '2025-03-01', 10),
(8, '2025-03-02', 8);

-- Sample Order Data
INSERT INTO orders (inventory_id, supplier_id, quantity, status) VALUES
(1, 1, 20, 'Ordered'),
(2, 1, 15, 'Ordered'),
(3, 2, 30, 'Ordered'),
(4, 1, 25, 'Ordered'),
(5, 3, 10, 'Ordered'),
(6, 2, 5, 'Ordered'),
(7, 3, 20, 'Ordered'),
(8, 2, 50, 'Ordered');
