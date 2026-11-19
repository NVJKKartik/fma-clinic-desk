# Corner Bookshop order desk, with a tools service

A small chat agent for a bookshop's order desk, and the shop's tools service it calls over HTTP.

## Run it with Docker Compose

`docker compose up --build` starts the whole desk. The agent can't run on its own: every tool it has is an HTTP call
to the tools service (`TOOLS_API_URL`), and the tools service keeps the shop's records in Postgres. Three services in
`docker-compose.yml`:

- `agent` (root `Dockerfile`, `python agent.py`, port 8080): serves `POST /v1/chat/completions` and `GET /health`.
  It reaches the model only through `LLM_BASE_URL`, `LLM_API_KEY` and `LLM_MODEL`, and the shop only through
  `TOOLS_API_URL`.
- `tools-api` (`tools-api/`, port 8080): the shop's records at `DATABASE_URL`.
  - `GET /orders/{order_id}`: an order's customer, item, total and status.
  - `GET /orders/{order_id}/history`: the events it went through, oldest first.
  - `POST /refunds` with `{"order_id", "reason"}`: files a refund request for a delivered order.
  - `GET /refunds/{request_id}`: a refund request and the manager's decision so far.
- `postgres`: the shop's records. `db/schema.sql` defines `orders`, `order_events` and `refund_requests`;
  `db/seed.sql` holds three orders.

## People

- **The customer** writes to the order desk about an order.
- **The store manager** is a separate person. The manager reviews refund requests in the shop's records and decides
  each one: sets its `status` in `refund_requests` to `approved` or `declined`. The desk never decides a refund.

This branch is a test agent for recorded replay through a tools service. It has no planted bugs.
