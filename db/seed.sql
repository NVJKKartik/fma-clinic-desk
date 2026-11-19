INSERT INTO orders (order_id, customer, item, total, status) VALUES
    ('B-1001', 'Ana Ruiz', 'The Left Hand of Darkness', 18.50, 'delivered'),
    ('B-1002', 'Bo Lindqvist', 'A Wizard of Earthsea (boxed set)', 64.00, 'delivered'),
    ('B-1003', 'Chen Wei', 'Piranesi', 22.00, 'shipped')
ON CONFLICT DO NOTHING;

INSERT INTO order_events (order_id, at, event, note) VALUES
    ('B-1001', '2026-11-02', 'placed', NULL),
    ('B-1001', '2026-11-03', 'shipped', NULL),
    ('B-1001', '2026-11-06', 'delivered', NULL),
    ('B-1002', '2026-11-04', 'placed', NULL),
    ('B-1002', '2026-11-05', 'shipped', NULL),
    ('B-1002', '2026-11-09', 'delivered', 'box arrived damaged'),
    ('B-1003', '2026-11-12', 'placed', NULL),
    ('B-1003', '2026-11-14', 'shipped', NULL);
