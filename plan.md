# AI Travel Agent: Step-by-Step Build Plan

This document outlines the development plan for the AI Travel Agent project. We will follow a test-driven development (TDD) approach for each feature.

**Development Workflow:**
1.  **Create/Update Feature:** Implement a new piece of functionality.
2.  **Write Tests:** Create unit and integration tests for the new feature.
3.  **Run Tests:** Execute the test suite to ensure the new feature works as expected and doesn't break existing code.
4.  **Fix Errors:** If tests fail, debug and fix the code.
5.  **Repeat:** Continue running tests until all pass, then move to the next feature.

---

## Phase 0: Project Setup

### Feature/Build
- Initialize the project structure, version control, and virtual environment.

### Implementation Steps
1.  Create the main project directory.
2.  Initialize a Git repository: `git init`
3.  Create a Python virtual environment: `python -m venv venv`
4.  Activate the virtual environment: `source venv/bin/activate` (on Unix) or `venv\Scripts\activate` (on Windows).
5.  Create initial project folders: `app`, `tests`.
6.  Create an empty `__init__.py` in both folders.
7.  Install `pytest`: `pip install pytest`
8.  Create `.gitignore` to exclude `venv`, `__pycache__`, `.env`, etc.

---

## Phase 1: Basic Web Server and WhatsApp Webhook

### Feature/Build
- A basic Flask web server with a `/webhook` endpoint that can receive POST requests.

### Tests
- Create `tests/test_app.py`.
- Write a test that sends a POST request to `/webhook` and asserts a `200 OK` response.

### Implementation Steps
1.  **Install Flask:** `pip install Flask`
2.  **Create `app/main.py`:**
    - Import `Flask`.
    - Create a Flask app instance.
    - Define a `/webhook` route that accepts `POST` requests.
    - The route should return a simple "OK" message with a 200 status code for now.

### Testing
- Run `pytest` from the root directory.

---

## Phase 2: Twilio Integration

### Feature/Build
- Receive and parse incoming WhatsApp messages from Twilio.
- Send a simple, static reply back to the user via Twilio.

### Tests
- Mock the Twilio request object.
- Write a test to ensure the `/webhook` correctly parses the `From` and `Body` from a simulated Twilio POST request.
- Write a test to assert that the endpoint returns a valid TwiML response to send a message.

### Implementation Steps
1.  **Install Twilio SDK:** `pip install twilio`
2.  **Credential Prompt:** I will now ask you for your **Twilio Account SID** and **Auth Token**. Please have them ready. We will store them in a `.env` file for local development.
3.  **Update `/webhook`:**
    - Import `MessagingResponse` from `twilio.rest`.
    - Modify the endpoint to read the incoming message body.
    - Create a TwiML response to send a reply (e.g., "Message received!").
    - Return the TwiML response as an XML string.
4.  Install `python-dotenv` to manage environment variables: `pip install python-dotenv`. Load variables in `main.py`.

### Testing
- Run `pytest`.

---

## Phase 3: IO Intelligence for Basic Conversation

### Feature/Build
- Pass the user's message to the IO Intelligence Chat Completion API and return the AI's response.

### Tests
- Mock the IO Intelligence API client.
- Write a test that verifies the webhook sends the received message to the IO API.
- Write a test that asserts the webhook correctly formats and returns the response from the mocked IO API.

### Implementation Steps
1.  **Install IO SDK:** I will search for the correct SDK and install it.
2.  **Credential Prompt:** I will now ask you for your **IO Intelligence API Key**.
3.  **Create an IO client:**
    - Create a new module, e.g., `app/ai_service.py`.
    - Write a function that takes a user message, sends it to the IO Chat Completion API, and returns the response.
4.  **Update `/webhook`:**
    - Call the new AI service function with the message body.
    - Use the AI's response in the TwiML reply.

### Testing
- Run `pytest`.

---

## Phase 4: Conversation Logic and Slot-Filling

### Feature/Build
- Use the IO Intelligence Agents API to extract structured data (slots) from user messages, such as origin, destination, and dates.

### Tests
- Write tests for the slot-filling logic with various inputs:
    - A message with all required information.
    - A message with partial information.
    - A message with ambiguous information.
- Assert that the correct slots are extracted or that the agent asks appropriate clarifying questions.

### Implementation Steps
1.  **Design Agent Instructions:** Define a clear set of instructions for the IO Agent on how to extract flight details.
2.  **Update `ai_service.py`:**
    - Create a new function to interact with the IO Agents API.
    - This function will manage the conversation flow, passing the user message and current state to the agent.
3.  **Update `/webhook`:**
    - Replace the call to the chat completion API with a call to the new agent service.

### Testing
- Run `pytest`.

---

## Phase 5: Session Persistence with Redis

### Feature/Build
- Store and retrieve the conversation state for each user, allowing for multi-turn conversations.

### Tests
- Write a test to verify that after a message is processed, the user's session state (e.g., filled slots) is saved to a mocked Redis instance.
- Write a test to verify that on a new message from an existing user, their previous state is loaded correctly.

### Implementation Steps
1.  **Install Redis:** `pip install redis`
2.  **Set up Redis on Render:** I will guide you through setting up a free Redis instance on Render to get the connection URL.
3.  **Create `app/session_manager.py`:**
    - Implement functions to `save_session` and `load_session` using the user's WhatsApp number as the key.
4.  **Update `/webhook`:**
    - Before calling the AI service, load the user's session.
    - After receiving the AI's response, save the updated session state.

### Testing
- Run `pytest`.

---

## Phase 5a: Add Persistent Storage with PostgreSQL

### Feature/Build
- Integrate a PostgreSQL database as the primary, durable storage for conversation history.
- Keep Redis as a high-speed caching layer for active sessions to reduce database load and improve latency.

### Tests
- Update tests to mock both the PostgreSQL and Redis clients.
- Write a test to verify the "cache-aside" logic:
    - On a cache miss (session not in Redis), verify the app fetches from Postgres, saves to Redis, and then proceeds.
    - On a cache hit, verify the app uses the Redis data directly without querying Postgres.
- Write a test to verify that session data is always written to PostgreSQL.

### Implementation Steps
1.  **Get Credentials:** I will ask you for your PostgreSQL Internal Database URL from Render.
2.  **Install DB Driver:** `pip install psycopg2-binary SQLAlchemy`
3.  **Create `app/database.py`:**
    - Set up the database connection using SQLAlchemy.
    - Define a `Conversation` table/model to store the history.
    - Create a function to initialize the database table.
4.  **Update `app/session_manager.py`:**
    - Modify `load_session` to check Redis first, then fall back to Postgres if not found (and cache the result in Redis).
    - Modify `save_session` to write to both Postgres and Redis.

### Testing
- Run `pytest`.

---

## Phase 6: Timezone Handling

### Feature/Build
- Infer the user's timezone from the origin city to handle dates and times correctly.

### Tests
- Write a test to check if a city name (e.g., "Paris") is correctly mapped to its timezone (e.g., "Europe/Paris").
- Write a test for the fallback mechanism when a timezone cannot be determined.

### Implementation Steps
1.  **Install pytz:** `pip install pytz`
2.  **Implement Timezone Logic:**
    - Create a helper function that takes a city name and returns a timezone.
3.  **Integrate with Slot-Filling:**
    - After the origin city is extracted, call the timezone helper.
    - Store the timezone in the user's session.

### Testing
- Run `pytest`.

---

## ~~Phase 7: Flight Search Integration~~ (Deprecated)

- **This phase has been replaced by the Amadeus & Stripe Integration phases below.**

---

## Phase 7: Amadeus Flight Search Integration

- **Goal:** Find real flight offers based on the user's request and allow them to select one.
- **Credentials:** Amadeus API Key and Amadeus API Secret will be required.

### Tests
- Create `tests/test_amadeus_service.py`.
- Mock the Amadeus API client.
- Test the IATA code lookup for cities.
- Test that the flight search function calls the correct Amadeus endpoint with the correct parameters.
- Test the parsing and formatting of the flight offer results.

### Implementation Steps
1.  **Install SDK:** Add `amadeus` to `requirements.txt` and install it.
2.  **Add Credentials to `.env`:** Add `AMADEUS_CLIENT_ID` and `AMADEUS_CLIENT_SECRET`.
3.  **Create `app/amadeus_service.py`:** This new module will encapsulate all interaction with the Amadeus API.
4.  **Implement IATA Code Lookup:** Create a function to call the Amadeus `reference_data.locations` endpoint to convert origin/destination city names to IATA codes.
5.  **Implement Flight Offer Search:** Create a function to call the `shopping.flight_offers_search.get` endpoint.
6.  **Update `app/main.py`:**
    - Once the AI confirms all slots are filled, call the new `amadeus_service.search_flights` function.
    - Format the best 3-5 flight options and send them to the user in a numbered list.
    - Store the full JSON data for each presented offer in Redis with a temporary unique ID (e.g., `flight_option:USER_PHONE_NUMBER:1`).
7.  **Update `app/ai_service.py`:** The system prompt for the AI must be updated. It should be instructed that once it has gathered all flight details, its final output should be a simple JSON object like `{"status": "complete"}` and nothing else. This will be the trigger for our Flask app to initiate the flight search. It should no longer be responsible for creating the summary message itself.

### Testing
- Run `pytest`.

---

## Phase 8: Stripe Payment Initiation

- **Goal:** When a user selects a flight, generate and send them a secure Stripe payment link.
- **Credentials:** Stripe Publishable Key and Stripe Secret Key will be required.

### Tests
- Create `tests/test_payment_service.py`.
- Mock the Stripe API client.
- Test that the `create_checkout_session` function correctly constructs the Stripe session with:
    - The correct price and currency from the flight offer.
    - The `success_url` and `cancel_url`.
    - A `metadata` object containing our internal `conversation_id` and `flight_option_id`.

### Implementation Steps
1.  **Install SDK:** Add `stripe` to `requirements.txt`.
2.  **Add Credentials to `.env`:** Add `STRIPE_PUBLISHABLE_KEY` and `STRIPE_SECRET_KEY`.
3.  **Create `app/payment_service.py`:** This new module will handle all Stripe interactions.
4.  **Implement `create_checkout_session`:**
    - The function will accept the chosen flight offer object.
    - It will create a Stripe Checkout Session.
    - **Crucially, it will populate the `metadata` parameter** with the `conversation_id` and the temporary `flight_option_id` to link the payment back to our internal state.
5.  **Update `app/main.py`:**
    - When the user replies with their flight selection (e.g., "book option 1"), retrieve the full flight data from Redis.
    - Call `payment_service.create_checkout_session` to get a Stripe URL.
    - Send the Stripe Checkout URL to the user on WhatsApp.

### Testing
- Run `pytest`.

---

## Phase 9: Booking Confirmation via Stripe Webhook

- **Goal:** Listen for successful payments from Stripe, formally book the flight with Amadeus, and notify the user.

### Tests
- Update `tests/test_app.py`.
- Write a new end-to-end test for the `/stripe-webhook` endpoint.
- The test will simulate a `checkout.session.completed` request from Stripe.
- It will mock the database and Redis to provide the necessary conversation and flight data based on the metadata in the simulated request.
- It will mock the `amadeus_service.book_flight` call and assert that it's called with the correct data.
- It will assert that a final confirmation message is sent via the mocked Twilio client.

### Implementation Steps
1.  **Add Traveler Info to Slots:** Update the AI prompt in `ai_service.py` to also require the user's "Full Name as on Passport". This must be stored in the session.
2.  **Create `/stripe-webhook` Endpoint:** Add a new `POST` endpoint in `app/main.py`. This is the URL we will provide to Stripe.
3.  **Handle `checkout.session.completed` Event:** The webhook will:
    a. Securely verify the event signature using the webhook secret to ensure it came from Stripe.
    b. Extract the `metadata` object from the event data.
    c. Use the IDs from the metadata to retrieve the conversation history from PostgreSQL and the chosen flight offer from Redis.
4.  **Implement `book_flight` in `amadeus_service.py`:**
    - This new function will take the flight offer JSON and traveler details.
    - It will call the Amadeus `booking.flight_orders.post` endpoint to finalize the booking.
5.  **Trigger Booking & Final Confirmation:**
    - In the webhook, after retrieving all data, call `amadeus_service.book_flight`.
    - If successful, send a final confirmation message to the user with their booking reference.

### Testing
- Run `pytest`.

---

## Phase 10: Deployment to Render

### Feature/Build
- Prepare the application for deployment on a live server.

### Implementation Steps
1.  **Create `requirements.txt`:** `pip freeze > requirements.txt`
2.  **Create `render.yaml`:** Define the web service, database (Redis), build commands, and start commands.
3.  **Configure Gunicorn:** Install `gunicorn` and set the start command in `render.yaml` to `gunicorn app.main:app`.
4.  **GitHub and Render Setup:**
    - I will instruct you to push the code to a new GitHub repository.
    - I will guide you on creating a new Web Service on Render and linking it to your GitHub repo.
5.  **Environment Variables:** I will instruct you on how to add all the API keys and secrets (`TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `IO_API_KEY`, `POSTGRES_URL`, `REDIS_URL`, `AMADEUS_CLIENT_ID`, `AMADEUS_CLIENT_SECRET`, `STRIPE_PUBLISHABLE_KEY`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`) to the Render environment.
6.  **Final Webhook Configuration:**
    - Update the Twilio WhatsApp Sandbox webhook URL to point to your live Render application's `/webhook` endpoint.
    - Create a new webhook endpoint in your Stripe dashboard and point it to your live Render application's `/stripe-webhook` endpoint.

### Testing
- Manually send a message to your Twilio WhatsApp number to perform an end-to-end test of the live application. 