# AI Travel Agent

This project is an AI-powered travel agent accessible via WhatsApp. It uses natural language processing to understand user requests, search for real-time flight information, and book flights.

## Current Features
- **WhatsApp Integration**: Communicates with users through the Twilio WhatsApp API.
- **Natural Language Understanding**: Leverages the IO Intelligence API to understand conversations, manage a state machine (e.g., `GATHERING_INFO`, `FLIGHT_SELECTION`), and extract structured data like destinations, dates, and traveler details.
- **Live Flight Search**: Integrates with the Amadeus Self-Service API to search for real-time flight offers based on the user's criteria.
- **Live Flight Booking**: Allows users to select a flight and books it directly via the Amadeus API, returning a real booking confirmation.
- **Session Persistence**: Maintains conversation state for each user.

## Core Technologies
- **Programming Language:** Python 3.x
- **Web Framework:** Flask
- **WhatsApp Integration:** Twilio WhatsApp Sandbox
- **AI Conversation Layer:** IO Intelligence API
- **Flight Data API:** Amadeus Self-Service APIs
- **Testing**: Pytest

## Project Structure
```
├── app/
│   ├── ai_service.py         # Handles all IO Intelligence API interactions
│   ├── amadeus_service.py    # Handles all Amadeus API interactions
│   ├── main.py               # Main Flask application, routes, and webhook logic
│   └── session_manager.py    # Manages user session state
├── tests/
│   ├── integration/
│   │   ├── test_ai_service_integration.py
│   │   └── test_amadeus_integration.py
│   └── test_app.py
├── .env                      # Local environment variables (ignored by git)
├── requirements.txt          # Python dependencies
├── plan.md                   # Step-by-step development plan
└── prd.md                    # Product requirements document
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
    Create a file named `.env` in the project root and add the following variables. These are required to connect to the various services.

    ```
    TWILIO_ACCOUNT_SID=
    TWILIO_AUTH_TOKEN=
    IO_API_KEY=
    REDIS_URL=
    DATABASE_URL=
    AMADEUS_CLIENT_ID=
    AMADEUS_CLIENT_SECRET=
    ```

## Running Tests
To ensure everything is configured correctly, run the test suite:
```bash
pytest -s
```

## Next Steps
The next major feature is to integrate **Stripe** for payment processing. This will involve:
1. Generating a Stripe Checkout link when a user selects a flight.
2. Creating a webhook to listen for successful payments.
3. Triggering the final Amadeus booking only after a payment is confirmed. 