-- init.sql
CREATE TABLE billing_events (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(100) UNIQUE NOT NULL,
    terminal_id VARCHAR(50) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    container_id VARCHAR(50),
    customer_code VARCHAR(50) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    event_data JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP
);

-- Indexes for better performance
CREATE INDEX idx_billing_events_customer ON billing_events(customer_code);
CREATE INDEX idx_billing_events_created ON billing_events(created_at);
CREATE INDEX idx_billing_events_type ON billing_events(event_type);

-- Insert some test data to verify setup
INSERT INTO billing_events (event_id, terminal_id, event_type, customer_code, amount, processed_at) 
VALUES 
    ('test-001', 'SEA001', 'CONTAINER_MOVE', 'MAERSK', 250.00, NOW()),
    ('test-002', 'SEA001', 'TRUCK_ENTRY', 'FEDEX', 45.00, NOW());