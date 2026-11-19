# Corner Bookshop phone desk

A small LiveKit voice agent for a bookshop's order desk. Callers ask about an order or ask for a refund.

## Tools

- `lookup_order(order_id)`: an order's customer, item, total and status.
- `request_refund(order_id, reason)`: files a refund request for a delivered order. A store manager decides every
  refund; the desk never approves one itself.

Both run their function in `orders.py`, which holds the orders in memory, seeded at startup.

## Run

`python agent.py start` starts the LiveKit worker (`agent_name` from `LIVEKIT_AGENT_NAME`). It needs `LIVEKIT_URL`,
`LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`, `DEEPGRAM_API_KEY` (speech in and out), and `LLM_BASE_URL`, `LLM_API_KEY`,
`LLM_MODEL` for the model through an OpenAI-compatible gateway. There is no database and no other network call.

This branch is a test agent for recorded replay of a voice call. It has no planted bugs.
