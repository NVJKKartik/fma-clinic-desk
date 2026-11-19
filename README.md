# Corner Bookshop order desk

A small chat agent for a bookshop's order desk. It answers customers about their orders, reads an order's history,
and takes refund requests.

## People

- **The customer** writes to the order desk about an order.
- **The store manager** is a separate person. The manager reviews every refund request and approves or declines it.
  The order desk never approves a refund itself; it files the request and tells the customer it waits for the
  manager.

## Tools

- `lookup_order(order_id)`: an order's customer, item, total and status.
- `order_history(order_id)`: the events an order went through, oldest first. It is a generator: it yields one event
  at a time.
- `request_refund(order_id, reason)`: files a refund request for a delivered order, for the manager to decide.

## Run

`python agent.py` serves `POST /v1/chat/completions` and `GET /health` on `$PORT` (default 8080). It reaches the model
only through `LLM_BASE_URL`, `LLM_API_KEY` and `LLM_MODEL`. Orders are seeded in memory at startup; there is no
database and no other network call.

This branch is a test agent for recorded replay. It has no planted bugs.
