# AI Travel Agent

This project is an AI-powered travel agent accessible via WhatsApp and Telegram. It uses natural language processing to understand user requests, search for real-time flight information, and book flights. It is deployed as a single, multi-threaded web service on Render.

## Current Features
- **Multi-Platform Support**: Communicates with users via the Twilio API for WhatsApp and the Telegram Bot API.
- **Natural Language Understanding**: Leverages the IO Intelligence API to understand conversations, manage a state machine (e.g., `GATHERING_INFO`, `FLIGHT_SELECTION`), and extract structured data like destinations, dates, and traveler details.
- **Live Flight Search**: Integrates with the Amadeus Self-Service API to search for real-time flight offers based on the user's criteria.
- **Airline Name Display**: Looks up and displays the full airline name (e.g., "American Airlines") for each flight option, providing a clearer user experience.
- **Flight Class Selection**: Users can specify their preferred travel class (e.g., Economy, Business, First Class). The application searches based on this preference and displays it in the flight options and on the final PDF ticket.
- **Multi-Traveler Booking**: If a booking is for more than one person, the agent collects the full names of all travelers. After payment, it generates and delivers a separate, personalized PDF ticket for each individual.
- **Dual Payment Options & Confirmation**:
  - **Stripe**: Creates secure Stripe Checkout links for card payments, confirmed via webhook.
  - **USDC**: Uses Circle's API to generate a unique payment address. Payment confirmation is now handled by a robust **background polling mechanism**, which reliably checks the payment status until it's complete, ensuring timely ticket delivery.
- **Persistent State**: Maintains conversation state for each user in a Redis database.
- **Responsive & Resilient Architecture**: Long-running tasks like flight searches and payment polling are run in background threads, so the main application is never blocked and can recover from external service delays.

## Core Technologies
- **Programming Language:** Python 3.11
- **Web Framework:** Flask
- **Deployment:** Render
- **Platform Integration:** Twilio (WhatsApp), Telegram Bot API
- **AI Conversation Layer:** IO Intelligence API
- **Flight Data API:** Amadeus Self-Service APIs
- **Payment Processing API:** Stripe
- **Session Storage:** Render Redis
- **Testing**: Pytest

## Project Structure
```
├── app/
│   ├── main.py               # Main Flask application entrypoint
│   ├── core_logic.py         # Platform-agnostic core conversation logic
│   ├── ai_service.py         # Handles all IO Intelligence API interactions
│   ├── amadeus_service.py    # Handles all Amadeus API interactions
│   ├── circle_service.py     # Manages Circle API for USDC payments
│   ├── currency_service.py   # Handles real-time currency conversion
│   ├── payment_service.py    # Handles all Stripe API interactions
│   ├── telegram_service.py   # Handles sending messages to Telegram
│   ├── new_session_manager.py# Manages user session state in Redis
│   └── tasks.py              # Defines background tasks (e.g., flight search)
├── tests/
│   ├── integration/
│   │   ├── test_ai_service_integration.py
│   │   └── test_amadeus_integration.py
│   └── test_app.py
├── .env                      # Local environment variables (ignored by git)
├── requirements.txt          # Python dependencies
└── render.yaml               # Infrastructure-as-Code for Render deployment
```

## How It Works

This application runs as a **single web service** on Render.

It's a Flask application that handles incoming webhooks from Twilio and Telegram. To ensure the service is always responsive, it processes messages, manages conversation state (including a new state for gathering traveler names), and runs long-running tasks in background threads. After a user completes a payment via a Stripe webhook, the application generates a personalized PDF of the flight itinerary for each traveler and sends it back to the user on their messaging platform. User session data is stored in a connected Render Redis instance.

This single-service, multi-threaded architecture simplifies deployment while maintaining a great user experience.

For a simple, user-focused explanation, see `how-it-works.txt`.
For a detailed, technical deep-dive (including production considerations), see `how-it-works.md`.

## Current Status & Limitations
**Please Note:** This application is currently configured for sandbox testing. The final step of booking a flight with the Amadeus API after payment is **intentionally not yet implemented**. This is because real flight booking requires a production environment. The current post-payment flow focuses on generating and sending a mock itinerary for testing purposes.

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

    # IO Intelligence API Key
    IO_API_KEY=

    # Amadeus API Credentials
    AMADEUS_CLIENT_ID=
    AMADEUS_CLIENT_SECRET=

    # Circle API Key (for USDC Payments)
    CIRCLE_API_KEY=

    # Stripe API Keys
    STRIPE_PUBLISHABLE_KEY=
    STRIPE_SECRET_KEY=
    STRIPE_WEBHOOK_SECRET=

    # Redis URL (for local development)
    # On Render, this is set automatically. For local, you might use:
    REDIS_URL=redis://localhost:6379

    # The base URL of the deployed application (e.g., https://your-app.onrender.com)
    # This is required for creating correct Stripe redirect URLs.
    BASE_URL=http://127.0.0.1:5000
    ```

    **How to get the API keys:**
    - **Twilio**: Create a Twilio account and get your `Account SID`, `Auth Token`, and a Twilio phone number from the console.
    - **Telegram**: Create a new bot by talking to the `@BotFather` on Telegram. It will give you a `Bot Token`.
    - **IO Intelligence**: Create an account on the IO Intelligence platform and generate an API key.
    - **Amadeus**: Register for a Self-Service account on the Amadeus for Developers portal to get your `Client ID` and `Client Secret`.
    - **Circle**: Sign up for a Circle developer account and get your API key from the dashboard.
    - **Stripe**: Sign up for a Stripe account and find your `Publishable Key`, `Secret Key`, and `Webhook Secret` in the Developers dashboard.
    - **Redis**: For local development, you need to run a Redis server. On Render, the `REDIS_URL` is automatically provided to the service.

## Running Tests
To ensure everything is configured correctly, run the test suite:
```bash
pytest -sv
```

## Running Locally
To run the application locally, you just need to start the web server. Make sure you have a local Redis instance running first.

```bash
gunicorn app.main:app
```

## Deployment
This application is designed for easy deployment to **Render** using the `render.yaml` file.

1.  Push your code to a GitHub repository.
2.  In the Render Dashboard, create a new "Blueprint" and connect your repository.
3.  Render will automatically detect `render.yaml` and create the `web` service and the `redis` instance.
4.  Add all the secret environment variables from your `.env` file to the service's "Environment" tab in the Render UI.
5.  Update your Twilio and Telegram webhooks to point to your new Render service URL.

For more detailed deployment instructions, please see `render_deployment.md`. 