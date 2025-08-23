# Tech Context

## Stack
- Python 3.11, Flask, Gunicorn
- Redis (Render managed)
- Web3.py (planned, for Circle Layer)
- Twilio (WhatsApp), Telegram Bot API
- Stripe, Circle (USDC)
- Amadeus SDK
- FPDF2, Cloudinary
- Pytest

## Setup
- Env via .env or Render environment
- `pip install -r requirements.txt`
- `gunicorn app.main:app`

## Constraints
- Single web dyno; background tasks must be lightweight
- Ephemeral filesystem; use cloud storage for media

## Dependencies to watch
- Amadeus rate limits
- Stripe/Circle webhooks vs polling reliability
- RPC stability for Circle Layer testnet 