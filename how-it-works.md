# How the AI Travel Agent Works: A Deep Dive

This document provides a detailed, step-by-step explanation of how the entire system works. The application is built on a **single-service architecture** that uses background threading to ensure it is responsive, scalable, and resilient.

### High-Level Architecture

The application is a single, robust **Flask web service**. It's designed to handle all user interactions, from receiving initial messages to sending final confirmations.

To prevent long-running operations (like searching for flights) from blocking the application, these tasks are executed in a **separate background thread**. This ensures the main web service is always available to respond instantly to new user messages.

**Redis** is used as a fast, in-memory database to store each user's conversation state, allowing for seamless, multi-turn dialogues.

This single-service, multi-threaded architecture simplifies deployment and maintenance while preserving a highly responsive user experience.

---

### The Step-by-Step User Journey

Let's walk through the exact sequence of events as a user interacts with the agent.

#### Step 1: The Initial Handshake

1.  **User Sends Message:** A user sends "Hi" to the Telegram Bot.
2.  **Platform Webhook:** Telegram makes an HTTP `POST` request to the public URL of the **Web Service**.
3.  **Application Entry Point (`app/main.py`):** The Flask server receives the request. The `/telegram-webhook` function extracts the user's ID and message and passes them to the central `process_message` function in `app/core_logic.py`.

#### Step 2: Core Logic and State Management

This all happens inside the `process_message` function in `app/core_logic.py`.

1.  **Session Loading (`app/new_session_manager.py`):** The function immediately calls `load_session(user_id)` to fetch the user's conversation state from **Redis**. If the user is new, it creates a new session with the state `GATHERING_INFO`.

2.  **AI Processing (`app/ai_service.py`):** Based on the current state, `get_ai_response` is called. It sends the conversation history to the **IO Intelligence API**, which asks clarifying questions until it has all the details (origin, destination, date, travel class, etc.). When complete, the AI returns the special tag `[INFO_COMPLETE]`.

3.  **Check for Multiple Travelers:** The application sees the `[INFO_COMPLETE]` tag and immediately extracts the structured flight details, including the `number_of_travelers`.
    *   **If there is only one traveler,** the flow continues to the next step as usual.
    *   **If there are multiple travelers,** the system transitions to a new state: `GATHERING_NAMES`. It saves the session and asks the user to provide the full names of all travelers.

#### Step 2a: Collecting Traveler Names (New)

This step only occurs if there is more than one traveler.

1.  **User Provides Names:** The user replies with the names, typically in a single message (e.g., "David Ugbodaga, Esther Ugbodaga").
2.  **Name Extraction (`app/ai_service.py`):** The `extract_traveler_names` function is called. It uses another AI prompt to parse the user's message and pull out the exact number of names required.
3.  **State Transition & Session Saving:** Once the names are successfully extracted, they are added to the session's `flight_details`. The state is transitioned to `AWAITING_CONFIRMATION`, and the session is saved to Redis. A confirmation message is sent to the user, now listing all extracted traveler names along with the other flight details.

#### Step 3: The Asynchronous Handoff (The Background Thread)

This is the most critical part of the architecture.

1.  **User Confirms:** The user replies "Yes" to the confirmation message (which now includes all traveler names). The web service receives this message.
2.  **Task Dispatching (`app/core_logic.py`):**
    *   The `process_message` function loads the session and sees the state is `AWAITING_CONFIRMATION`.
    *   It immediately sends the user the message "Okay, I'm searching for the best flights..."
    *   Crucially, it **does not** search for flights in the main request thread. Instead, it starts a new background thread using Python's built-in `threading` module to run the `search_flights_task` function.
    *   The web service's job is now complete for this request, and it returns an immediate `200 OK` response to Telegram.

#### Step 4: Background Flight Search

1.  **Independent Execution (`app/tasks.py`):**
    *   Meanwhile, the `search_flights_task` function runs independently in its own thread.
2.  **Execution:** The task's code executes:
    *   It calls the Amadeus API to get IATA codes.
    *   It calls the Amadeus API again to perform the live flight search, passing the user's selected travel class. This can take several seconds without affecting the main application.
    *   For each flight offer returned, it makes an additional call to the Amadeus API to look up the full airline name from its `carrierCode`.
3.  **Proactive Response:**
    *   Once the search is complete, the background thread formats the flight offers into a user-friendly list, now including the airline name and travel class.
    *   It then connects directly to the Telegram API and sends the results as a **new, proactive message** to the user.
4.  **Final State Update:** The thread updates the user's state in Redis to `FLIGHT_SELECTION` and saves the flight offers to their session.

#### Step 5: Payment and Itinerary Delivery

This is the final part of the journey, which now offers three distinct paths: traditional card payment (Stripe), cryptocurrency (USDC), and native blockchain tokens (Circle Layer).

1.  **User Selects Flight:** The user receives the list of flights and replies with the number of their choice (e.g., "1").

2.  **Payment Method Selection (`app/core_logic.py`):**
    *   The system transitions the user's state to `AWAITING_PAYMENT_SELECTION`.
    *   It sends the message: "You've selected a great flight. How would you like to pay? (Reply with 'Card', 'USDC', or 'On-chain')"

---
##### Path A: Paying with a Card (Stripe)

1.  **User Selects Card:** The user replies "Card".
2.  **Stripe Checkout (`app/payment_service.py`):** The system calls `create_checkout_session`, which generates a secure, unique payment link from the **Stripe API**.
3.  **User Pays:** The user is sent the Stripe link, completes the payment, and Stripe sends a `checkout.session.completed` event to the `/stripe-webhook`.

---
##### Path B: Paying with USDC (Circle)

1.  **User Selects USDC:** The user replies "USDC".
2.  **Currency Conversion (`app/currency_service.py`):** The system first checks the flight's currency. If it's not already in USD, it makes a live API call to a currency conversion service to get the exact price in USD.
3.  **Payment Intent and Address Generation (`app/circle_service.py`):** The application uses Circle's **Payment Intents API** to create a one-time payment address.
    *   **Step A: Create Payment Intent:** A `POST` request is sent to Circle's `/v1/paymentIntents` endpoint with the amount and currency.
    *   **Step B: Poll for Address:** The application polls the `GET /v1/paymentIntents/{id}` endpoint until Circle provides the unique `address` for the payment.
    *   **Step C: Save Mapping:** It saves a mapping of the payment intent `id` to the `user_id` in Redis. This is critical for the polling task to identify the user later.
4.  **User Pays:** The user is sent two separate messages to make copying the address easier: one with the instructions and amount, and a second message containing only the generated wallet address. The user then completes the transfer from their own crypto wallet.
5.  **Start Background Polling (`app/core_logic.py` & `app/tasks.py`):**
    *   As soon as the address is sent to the user, a new background thread is started to run the `poll_usdc_payment_task`.
    *   The main application's work is done for now, and it can respond to other users.
    *   **NOTE FOR TESTING:** To work with the limitations of the [Circle Testnet Faucet](https://faucet.circle.com/), the application currently **ignores the real flight price** for USDC payments and always requests **10.00 USDC**.

---
##### Path C: Paying with Circle Layer (Native CLAYER Token)

1.  **User Selects Circle Layer:** The user replies "On-chain" (or "circle layer", "clayer", "circlelayer" for backward compatibility).
2.  **Unique Address Generation (`app/circlelayer_service.py`):** The system generates a unique, deterministic deposit address using the merchant's mnemonic and an incrementing index to prevent address reuse.
3.  **Initial Balance Recording:** The system records the initial balance of the deposit address before requesting payment to track balance increases.
4.  **User Pays:** The user is sent two separate messages: one with instructions to send exactly 1.00 CLAYER, and a second message containing only the deposit address for easy copying.
5.  **Start Background Polling (`app/core_logic.py` & `app/tasks.py`):**
    *   As soon as the address is sent to the user, a new background thread is started to run the `poll_circlelayer_payment_task`.
    *   The polling task checks the native CLAYER balance of the deposit address every 15 seconds.
    *   **Security Enhancement:** The system only confirms payment when the balance increases by the expected amount, preventing false confirmations from addresses with existing balances.
    *   **Native Token Benefits:** Direct blockchain balance checking without smart contract complexity.

---
#### Step 6: Confirmation and Ticket Delivery

The final confirmation step is handled differently depending on the payment method.

##### Stripe Confirmation (via Webhook)

1.  **Payment Success Webhook:** Stripe sends a `checkout.session.completed` event to the `/stripe-webhook` endpoint.
2.  **Unified Handler:** The webhook extracts the `user_id` and calls the central `handle_successful_payment(user_id)` function.
3.  **PDF Generation & Delivery:** This function loads the user's session, generates a personalized PDF for each traveler, sends the tickets, and updates the user's state to `BOOKING_CONFIRMED`.

##### Circle Confirmation (via Polling)

1.  **Background Polling (`app/tasks.py`):** The `poll_usdc_payment_task` function, which has been running in the background since the payment address was created, continues to execute.
2.  **Status Check:** Every 30 seconds, the task calls Circle's `GET /v1/paymentIntents/{id}` API endpoint to check the payment status.
3.  **Payment Complete:** When the API returns a status of `complete`, the polling task knows the payment has succeeded.
4.  **Unified Handler:** The polling task calls the same central `handle_successful_payment(user_id)` function.
5.  **PDF Generation & Delivery:** Just like with Stripe, this function generates and sends the PDF tickets and updates the user's state. The polling task then stops.
6.  **(Legacy) Circle Webhook:** The `/circle-webhook` endpoint is still present to handle any initial subscription confirmations from Circle, but it no longer processes payment success notifications. Its primary role in the payment flow is now handled by the polling task.

---

### Production Considerations: Handling PDF Files

**IMPORTANT:** The current method for sending PDFs on WhatsApp is designed for **testing and local development only**.

*   **Current Test Implementation:** The application saves the PDF to a local `temp_files` directory on the server and serves it via a special `/files/<filename>` endpoint. This works for a single, local server but is not suitable for a real-world deployment.

*   **Why This Fails in Production:**
    *   **Ephemeral Filesystem:** Hosting platforms like Render use ephemeral filesystems. Any files written to the local disk (like our PDFs) will be **permanently deleted** every time the service restarts or redeploys.
    *   **Not Scalable:** If the application were scaled to run on multiple instances, a request for a file would only succeed if it hit the specific server instance that generated it.

*   **Recommended Production Architecture:**
    1.  **Use Cloud Storage:** Integrate a dedicated cloud storage service like **Amazon S3**, **Google Cloud Storage**, or **Cloudinary**.
    2.  **Direct Upload:** When the `pdf_service` generates the PDF, instead of saving it locally, upload the file bytes directly to your cloud storage bucket.
    3.  **Use Public URL:** The cloud storage service will provide a stable, publicly accessible URL for the uploaded file.
    4.  **Send to Twilio:** Use this permanent public URL as the `media_url` when calling the Twilio API.

This approach ensures that files are persisted reliably and can be accessed from anywhere, which is essential for a scalable and robust production application.

### Technology Stack Summary

*   **Web Service:** **Flask**, **Gunicorn**.
*   **Background Tasks:** Python's built-in **`threading`** module.
*   **Messaging Platforms:** **Twilio** for WhatsApp, **Telegram Bot API** for Telegram.
*   **Natural Language Understanding:** **IO Intelligence API**.
*   **Flight Data & Booking:** **Amadeus**.
*   **Payments:** **Stripe**, **Circle**, **Circle Layer blockchain**.
*   **Session Storage:** **Redis** is the backbone of the system, used for storing conversation state.
*   **Testing:** **Pytest**.
*   **Hosting:** **Render**.

### Production Reliability Features

#### Error Handling & Resilience
The system is designed to be resilient and provide a good user experience even when components fail:

- **Redis Failures**: If Redis is unavailable, the system continues working with in-memory conversation state
- **AI Service Fallbacks**: If the AI service fails, users receive helpful responses instead of generic error messages
- **Session Management**: Graceful degradation when session storage operations fail
- **Payment Monitoring**: Robust polling with timeout and retry mechanisms for all payment methods

#### Monitoring & Debugging
- **Health Check Endpoint**: `GET /health` provides real-time system status
- **Comprehensive Logging**: Detailed debug messages for troubleshooting deployment issues
- **Environment Variable Validation**: Clear error messages for missing configuration
- **E2E Testing**: Complete test suite for deployment validation

#### Admin Tools
- **Redis Management**: `GET /admin/clear-redis/{secret}` - Clear Redis database for testing
- **System Status**: Health endpoint shows Redis connection and environment variable status
- **Error Tracking**: Detailed logs help identify and resolve issues quickly 