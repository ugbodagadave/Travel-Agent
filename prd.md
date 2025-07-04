# Cursor AI Travel Agent – Product Requirements Document

## Overview

This project builds an AI-powered travel agent accessible via WhatsApp. The agent will:

- Receive WhatsApp messages from users describing trip plans.
- Use [IO Intelligence](https://docs.io.net/reference/get-started-with-io-intelligence-api) for natural language understanding, slot-filling, and reasoning.
- Retrieve live flight options from a free-tier flight search API.
- Return flight details and checkout links.
- Handle timezone-aware scheduling.
- Persist session context so users can pause and resume.
- Deploy on Render free hosting.

---

## Core Technologies

- **Programming Language:** Python 3.x
- **Web Framework:** Flask or FastAPI
- **Hosting:** [Render](https://render.com/) free tier Web Service
- **WhatsApp Integration:** [Twilio WhatsApp Sandbox](https://www.twilio.com/docs/whatsapp/sandbox)
- **AI Conversation Layer:** [IO Intelligence Agents API](https://docs.io.net/reference/agents/overview)
- **Flight Data API:** [Amadeus Self-Service APIs](https://developers.amadeus.com/)
- **Payment Processing API:** [Stripe](https://stripe.com/)
- **Database:** Postgres (Persistent Storage) & Redis (Session Caching)

---

## Implementation Steps

### 1. WhatsApp Messaging Setup

- Create a [Twilio account](https://www.twilio.com/try-twilio).
- Set up the [Twilio WhatsApp Sandbox](https://www.twilio.com/docs/whatsapp/sandbox) to get:
  - Sandbox number
  - Join keyword
- **Prompt user to obtain Twilio Account SID and Auth Token.**
- In Twilio Console, configure the **Incoming Webhook URL** to point to your Render app endpoint `/webhook`.

---

### 2. IO Intelligence Configuration

- Sign up for [IO Intelligence](https://io.net/).
- **Prompt user to obtain an IO API Key.**
- Store the key as an environment variable:
- Install the Python SDK:

- Use the [Agents API](https://docs.io.net/reference/agents/overview) to create an Agent with custom instructions:
- Collect trip details (destination, origin, dates, number of travelers, time preference).
- Confirm any ambiguous data.
- Persist slot-filling progress.
- Use the [Chat Completion API](https://docs.io.net/reference/chat/create) for free-form natural language conversation.
- Optionally, use the [Embeddings API](https://docs.io.net/reference/embeddings/create) to generate embeddings of user messages for retrieval.

---

### 3. Conversation and Slot-Filling Logic

- Implement logic to:
- Detect and extract:
  - Origin (auto-detect via user timezone/city).
  - Destination.
  - Departure date.
  - Return date (if applicable).
  - Number of adults/kids.
  - Preferred departure time of day.
- Confirm details back to the user before searching flights.
- If information is incomplete, ask clarifying questions.

---

### 4. Timezone Handling

- Try to infer timezone by:
- Matching departure city to timezone via [pytz](https://pypi.org/project/pytz/) or similar.
- If unable to detect:
- Prompt the user to confirm their timezone or city.

---

### 5. Flight Search & Selection

- Register for a free [Amadeus for Developers](https://developers.amadeus.com/) account.
- **Prompt user to obtain Amadeus API Key and API Secret.**
- Use the API to:
  - Convert user's city names to IATA codes.
  - Search flights with parameters collected from the user.
  - Filter by time-of-day preference.
  - Retrieve departure time, duration, and price.
  - Format results for WhatsApp:
    - "Option 1: Depart 8:00 AM, Duration 7h, Price $350."
  - Store the selected flight offer to be used in the payment and booking phase.

---

### 5a. Payment & Booking

- Create a [Stripe account](https://stripe.com/).
- **Prompt user to obtain Stripe Publishable Key and Secret Key.**
- After the user selects a flight, generate a Stripe Checkout session.
- The session will contain metadata linking it to the user's conversation and selected flight.
- Send the user the secure Stripe Checkout URL to complete payment.
- Create a Stripe Webhook to listen for successful payment events.
- When a payment is successful, use the Amadeus API to formally book the flight.
- Send a final booking confirmation to the user.

---

### 6. Session Context Persistence

- Deploy a Postgres or Redis instance on Render:
- [Render Postgres Guide](https://render.com/docs/databases#postgresql)
- [Render Redis Guide](https://render.com/docs/redis)
- For each user (identified by WhatsApp number), store:
- Conversation state (slots filled, current step).
- Embeddings (if used).
- Timestamps of last interaction.
- On each incoming message:
- Load the saved state.
- Resume the conversation seamlessly.

---

### 7. Backend Deployment

- Host the backend API on [Render Free Web Service](https://render.com/docs/deploy-flask).
- Push your code to GitHub.
- Create a Render Web Service:
- Environment: Python 3.x
- Build command:
  ```
  pip install -r requirements.txt
  ```
- Start command:
  ```
  gunicorn app:app
  ```
- Add environment variables in Render:
- `IO_API_KEY`
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `POSTGRES_URL`
- `REDIS_URL`
- `AMADEUS_CLIENT_ID`
- `AMADEUS_CLIENT_SECRET`
- `STRIPE_PUBLISHABLE_KEY`
- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`
- Ensure your webhook URL is HTTPS and public.

---

### 8. WhatsApp Webhook Handling

- Create a Flask/FastAPI route:
- `POST /webhook`
- Use the [Twilio Python SDK](https://www.twilio.com/docs/whatsapp/tutorial/send-whatsapp-notification-python#install-python-helper-library) to:
- Parse incoming messages.
- Send replies to the user.
- Example flow:
- Receive a message.
- Check conversation state.
- Pass message to IO Agent for processing.
- Save updated state.
- Send formatted response back to WhatsApp.

---

### 9. Error Handling and Edge Cases

- If no flights are found:
- Apologize and ask if the user wants to adjust dates or preferences.
- If date or city is ambiguous:
- Prompt for clarification.
- If the user does not reply after a period:
- Keep the session open and resume later.
- Monitor API quotas and log usage.

---

## Reference Documentation Links

- [IO Intelligence Getting Started](https://docs.io.net/reference/get-started-with-io-intelligence-api)
- [IO Agents API Overview](https://docs.io.net/reference/agents/overview)
- [IO Chat Completion API](https://docs.io.net/reference/chat/create)
- [IO Embeddings API](https://docs.io.net/reference/embeddings/create)
- [Twilio WhatsApp Sandbox](https://www.twilio.com/docs/whatsapp/sandbox)
- [Twilio Python SDK Guide](https://www.twilio.com/docs/whatsapp/tutorial/send-whatsapp-notification-python)
- [Render Flask Deployment](https://render.com/docs/deploy-flask)
- [Amadeus Self-Service APIs](https://developers.amadeus.com/)
- [Stripe Documentation](https://stripe.com/docs)

---

**Note:** All API keys and secrets must be stored in environment variables. Prompt the user to generate and input them before deployment. 