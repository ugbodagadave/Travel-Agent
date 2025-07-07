# AI Travel Agent

This project is an AI-powered travel agent accessible via WhatsApp and Telegram. It uses natural language processing to understand user requests, search for real-time flight information, and book flights.

## Current Features
- **Multi-Platform Support**: Communicates with users via the Twilio API for WhatsApp and the Telegram Bot API.
- **Natural Language Understanding**: Leverages the IO Intelligence API (via the OpenAI SDK) to understand conversations, manage a state machine (e.g., `GATHERING_INFO`, `FLIGHT_SELECTION`), and extract structured data like destinations, dates, and traveler details.
- **Live Flight Search**: Integrates with the Amadeus Self-Service API to search for real-time flight offers based on the user's criteria.
- **Payment Processing**: Creates secure Stripe Checkout links when a user selects a flight and confirms the payment via webhooks.
- **Persistent State**: Maintains conversation state for each user in a PostgreSQL database.

## Core Technologies
- **Programming Language:** Python 3.x
- **Web Framework:** Flask
- **Platform Integration:** Twilio (WhatsApp), Telegram Bot API
- **AI Conversation Layer:** IO Intelligence API
- **Flight Data API:** Amadeus Self-Service APIs
- **Payment Processing API:** Stripe
- **Persistent Storage:** PostgreSQL
- **Testing**: Pytest

## Project Structure
```
├── app/
│   ├── main.py               # Main Flask application, routes, and webhook logic
│   ├── core_logic.py         # Platform-agnostic core conversation logic
│   ├── ai_service.py         # Handles all IO Intelligence API interactions
│   ├── amadeus_service.py    # Handles all Amadeus API interactions
│   ├── payment_service.py    # Handles all Stripe API interactions
│   ├── telegram_service.py   # Handles sending messages to Telegram
│   ├── new_session_manager.py# Manages user session state in the database
│   └── database.py           # Defines the database schema and connection
├── tests/
│   ├── integration/
│   │   ├── test_ai_service_integration.py
│   │   └── test_amadeus_integration.py
│   └── test_app.py
├── .env                      # Local environment variables (ignored by git)
├── requirements.txt          # Python dependencies
└── render.yaml               # Render deployment configuration
```

## Setup and Installation

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/ugbodagadave/Travel-Agent
    cd Travel-Agent
    ```

2.  **Create a Virtual Environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set Up Environment Variables:**
    Create a file named `.env` in the project root and add the following variables.

    ```
    # Twilio API Credentials (for WhatsApp)
    TWILIO_ACCOUNT_SID=
    TWILIO_AUTH_TOKEN=
    TWILIO_PHONE_NUMBER=

    # Telegram Bot API Credentials
    TELEGRAM_BOT_TOKEN=
    TELEGRAM_CHAT_ID= # Optional: For sending admin notifications

    # IO Intelligence API Key
    IO_API_KEY=

    # Amadeus API Credentials
    AMADEUS_CLIENT_ID=
    AMADEUS_CLIENT_SECRET=

    # Stripe API Keys
    STRIPE_PUBLISHABLE_KEY=
    STRIPE_SECRET_KEY=
    STRIPE_WEBHOOK_SECRET=

    # Database URL (for session storage)
    DATABASE_URL= # e.g., postgresql://user:password@host:port/dbname
    ```

    **How to get the API keys:**
    - **Twilio**: Create a Twilio account and get your `Account SID`, `Auth Token`, and a Twilio phone number from the console.
    - **Telegram**: Create a new bot by talking to the `@BotFather` on Telegram. It will give you a `Bot Token`. Get your `Chat ID` by talking to `@userinfobot`.
    - **IO Intelligence**: Create an account on the IO Intelligence platform and generate an API key.
    - **Amadeus**: Register for a Self-Service account on the Amadeus for Developers portal to get your `Client ID` and `Client Secret`.
    - **Stripe**: Sign up for a Stripe account and find your `Publishable Key`, `Secret Key`, and `Webhook Secret` in the Developers dashboard.
    - **Database**: You can use a free-tier PostgreSQL database from a cloud provider like Render, or run one locally.

## Running Tests
To ensure everything is configured correctly, run the test suite:
```bash
pytest -sv
```

## Next Steps
The next major phases are:
1.  **Persistent Storage**: Integrate a PostgreSQL database to provide long-term, durable storage for conversation history, complementing the Redis cache.
2.  **Deployment**: Prepare the application for production and deploy it to a live environment on Render. 