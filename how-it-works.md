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

This is the final part of the journey, which now offers two distinct paths: traditional card payment (Stripe) and cryptocurrency (USDC).

1.  **User Selects Flight:** The user receives the list of flights and replies with the number of their choice (e.g., "1").

2.  **Payment Method Selection (`app/core_logic.py`):**
    *   The system transitions the user's state to `AWAITING_PAYMENT_SELECTION`.
    *   It sends the message: "You've selected a great flight. How would you like to pay? (Reply with 'Card' or 'USDC')"

---
##### Path A: Paying with a Card (Stripe)

1.  **User Selects Card:** The user replies "Card".
2.  **Stripe Checkout (`app/payment_service.py`):** The system calls `create_checkout_session`, which generates a secure, unique payment link from the **Stripe API**.
3.  **User Pays:** The user is sent the Stripe link, completes the payment, and Stripe sends a `checkout.session.completed` event to the `/stripe-webhook`.

---
##### Path B: Paying with USDC (Circle)

1.  **User Selects USDC:** The user replies "USDC".
2.  **Currency Conversion (`app/currency_service.py`):** The system first checks the flight's currency. If it's not already in USD, it makes a live API call to a currency conversion service to get the exact price in USD.
3.  **Payment Intent Generation (`app/circle_service.py`):** This is a two-step process using Circle's **Payment Intents API**, which is the correct and robust method for creating one-time payment addresses.
    *   **Step A: Create Payment Intent:** The application first makes a `POST` request to Circle's `/v1/paymentIntents` endpoint. This call includes the amount, currency (`USDC`), and a unique idempotency key. It tells Circle we *intend* to receive a payment, but it doesn't create the address just yet.
    *   **Step B: Poll for the Address:** For security reasons, Circle does not return the address synchronously. The application must poll the `GET /v1/paymentIntents/{id}` endpoint. The code enters a loop, making a request every second for up to 30 seconds, until the `address` field appears in the `paymentMethods` object of the response.
    *   **Step C: Save Mapping:** It saves a mapping of the payment intent `id` to the `user_id` in Redis. This is critical for identifying the user when the payment confirmation webhook arrives.
4.  **User Pays:** The user is sent two separate messages to make copying the address easier: one with the instructions and amount, and a second message containing only the generated wallet address. The user then completes the transfer from their own crypto wallet.
    *   **NOTE FOR TESTING:** To work with the limitations of the [Circle Testnet Faucet](https://faucet.circle.com/), which only provides 10 testnet USDC at a time, the application currently **ignores the real flight price** for USDC payments. It will always request a payment of **10.00 USDC** as a hardcoded amount. This is a temporary measure for development and testing.

---
#### Step 6: Confirmation via Webhook

The final confirmation step is handled by the appropriate webhook, depending on the payment method chosen.

##### Stripe Webhook (`/stripe-webhook` in `app/main.py`)

1.  **Payment Success:** Stripe sends a `checkout.session.completed` event.
2.  **PDF Generation Loop:** The handler loads the user's session, which contains the list of traveler names. It then loops through this list. For each name, it:
    *   Retrieves the flight offer they paid for.
    *   Calls the `pdf_service` to generate a flight itinerary PDF, passing the specific traveler's name.
    *   Sends the newly generated, personalized PDF directly to the user.
3.  **Final Confirmation:** After all tickets are sent, a single confirmation message is sent (e.g., "Thank you... I've sent 2 separate tickets.").
4.  **State Update:** The user's state is updated to `BOOKING_CONFIRMED`.

##### Circle Webhook (`/circle-webhook` in `app/main.py`)

1.  **Payment Success:** Once the USDC transaction is confirmed on the blockchain, Circle sends a notification for a `payments` event, typically when the payment intent is marked as `COMPLETE`.
2.  **User Lookup:** The webhook extracts the `paymentIntentId` from the payload and uses it to load the correct `user_id` from the Redis mapping created earlier.
3.  **PDF Generation & Final Steps:** From here, the process is identical to the Stripe flow. The handler loads the session, generates and sends a personalized PDF for each traveler, sends a final confirmation message, and updates the user's state to `BOOKING_CONFIRMED`.

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
*   **Payments:** **Stripe**, **Circle**.
*   **Session Storage:** **Redis** is the backbone of the system, used for storing conversation state.
*   **Testing:** **Pytest**.
*   **Hosting:** **Render**. 