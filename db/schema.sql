CREATE TABLE IF NOT EXISTS orders (
    order_id text PRIMARY KEY,
    customer text NOT NULL,
    item text NOT NULL,
    total numeric(8, 2) NOT NULL,
    status text NOT NULL
);
CREATE TABLE IF NOT EXISTS order_events (
    id serial PRIMARY KEY,
    order_id text NOT NULL REFERENCES orders (order_id),
    at date NOT NULL,
    event text NOT NULL,
    note text
);
-- A refund request waits for the store manager, who sets its status to approved or declined.
CREATE TABLE IF NOT EXISTS refund_requests (
    request_id text PRIMARY KEY,
    order_id text NOT NULL REFERENCES orders (order_id),
    reason text NOT NULL,
    amount numeric(8, 2) NOT NULL,
    status text NOT NULL DEFAULT 'awaiting manager approval'
);
