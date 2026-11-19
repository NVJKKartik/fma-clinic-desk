# Corner Bookshop order desk, with a tools service

A small chat agent for a bookshop's order desk, and the shop's tools service it calls over HTTP. Two services in
`docker-compose.yml`:

- `agent` (`python agent.py`, port 8080): serves `POST /v1/chat/completions` and `GET /health`. It reaches the model
  only through `LLM_BASE_URL`, `LLM_API_KEY` and `LLM_MODEL`, and the shop only through `TOOLS_API_URL`.
- `tools-api` (`tools_api/server.py`, port 8081): the shop's orders, seeded in memory.
  - `GET /orders/{order_id}`: an order's customer, item, total and status.
  - `GET /orders/{order_id}/history`: the events it went through, oldest first.
  - `POST /refunds` with `{"order_id", "reason"}`: files a refund request for a delivered order.

## People

- **The customer** writes to the order desk about an order.
- **The store manager** is a separate person who approves or declines every refund request. The desk never approves
  one itself.

This branch is a test agent for recorded replay through a tools service. It has no planted bugs.
