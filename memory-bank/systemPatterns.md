# System Patterns

- Single-service Flask app; background tasks via threading for non-blocking UX.
- Redis-backed session store keyed by user_id with state machine per conversation.
- External integrations:
  - IO Intelligence (LLM) for slot-filling and confirmation control tokens.
  - Amadeus API for IATA lookup and flight offers; simple in-memory caches.
  - Stripe webhooks for card payments; unified success handler.
  - Circle USDC via Payment Intents + polling.
  - Planned: Circle Layer EVM payments via Web3 polling.
- PDF generation via FPDF2; uploaded to Cloudinary for WhatsApp.
- Render deployment using render.yaml; Redis provisioned as service.
- Testing via pytest; services mocked in unit tests.
