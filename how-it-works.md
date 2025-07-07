# How the AI Travel Agent Works: A Deep Dive

This document provides a detailed, step-by-step explanation of how the entire system works, from the first message to the final booking, based on the project's codebase.

### High-Level Overview

The application functions as a **stateful, platform-agnostic conversational agent**. At its heart is the `app/core_logic.py` file, which contains a state machine that manages the entire user conversation. This central logic is completely independent of the messaging platform.

Webhook endpoints for each platform (`/webhook` for Twilio/WhatsApp and `/telegram-webhook` for Telegram) act as thin adapters. They are responsible for:
1.  Receiving incoming messages.
2.  Extracting the user ID and message content in a standardized format.
3.  Passing this information to the `process_message` function in `core_logic.py`.
4.  Taking the response from the core logic and sending it back to the user on the appropriate platform.

This design makes it easy to add new platforms in the future without changing the core business logic.

---

### The Step-by-Step User Journey

Let's walk through the exact sequence of events as a user interacts with the agent.

#### Step 1: The Initial Handshake (User -> Platform -> App)

1.  **User Sends Message:** A user sends a message, either to the Twilio WhatsApp number or to the Telegram Bot.
2.  **Platform Webhook:** The respective platform (Twilio or Telegram) receives the message and immediately makes an HTTP `POST` request to the public URL of your application.
    *   **WhatsApp:** Hits the `/webhook` endpoint.
    *   **Telegram:** Hits the `/telegram-webhook` endpoint.
3.  **Application Entry Point (`app/main.py`):**
    *   The Flask server receives the `POST` request.
    *   The relevant webhook function extracts the `user_id` and `message` from the request payload.
    *   It then calls the central `process_message(user_id, message)` function.
    *   **Technology:** Flask, Twilio API, Telegram Bot API.

#### Step 2: Core Logic, Session, and AI Processing

This all happens inside the `process_message` function in `app/core_logic.py`.

1.  **Session Loading (`app/new_session_manager.py`):**
    *   The first step is to call `load_session(user_id)`.
    *   This function queries the **PostgreSQL database** directly to find the user's current session, which includes their conversation state and history.
    *   If the user is not found, it means they are a new user. It returns a fresh session object with the default state: `GATHERING_INFO`.
    *   **Technology:** PostgreSQL with SQLAlchemy.

2.  **AI Processing (`app/ai_service.py`):**
    *   The core logic sees the user's state is `GATHERING_INFO`.
    *   It calls `get_ai_response(incoming_msg, conversation_history)`.
    *   This function sends the user's latest message and the conversation history to the **IO Intelligence API** (using the OpenAI SDK format).
    *   The AI's system prompt instructs it to act as a travel agent and extract key "slots" of information (origin, destination, date, etc.).
    *   If the AI has all the information it needs, its response will contain the special tag `[INFO_COMPLETE]`.

3.  **State Transition & Session Saving:**
    *   The code checks the AI's response for the `[INFO_COMPLETE]` tag.
    *   If the tag is present, it transitions the user's state (e.g., to `AWAITING_CONFIRMATION`).
    *   Finally, it calls `save_session(...)` to write the updated state and conversation history back to the **PostgreSQL database**.

#### Step 3: Flight Search (Amadeus Integration)

1.  **User Confirmation:** The user replies "Yes" to confirm the gathered details.
2.  **State Check:** The `process_message` function loads the session and sees the state is `AWAITING_CONFIRMATION`.
3.  **Service Calls (`app/amadeus_service.py`):**
    *   The application calls `extract_flight_details_from_history` to get structured data from the conversation.
    *   It calls the **Amadeus API** via `amadeus_service.get_iata_code()` to convert city names into airport IATA codes.
    *   It then calls `amadeus_service.search_flights()` to perform a live search for available flights.

4.  **Presenting Options:**
    *   The flight offers from Amadeus are formatted into a user-friendly, numbered list.
    *   This list is returned from `process_message` and sent back to the user by the platform-specific webhook.
    *   The state is changed to `FLIGHT_SELECTION`, and the full flight offer details are saved in the user's session.

#### Step 4: Payment Initiation (Stripe Integration)

1.  **User Selects Flight:** The user replies with a number, e.g., "1".
2.  **State Check:** The `process_message` function loads the `FLIGHT_SELECTION` state.
3.  **Checkout Creation (`app/payment_service.py`):**
    *   The application retrieves the full details for the selected flight from the session data.
    *   It calls `create_checkout_session(selected_flight, user_id)`.
    *   This function calls the **Stripe API** to generate a secure, hosted payment link. The `user_id` is passed as the `client_reference_id` so Stripe can link the payment back to our user.
    *   The generated Stripe URL is sent to the user.
    *   The state is updated to `AWAITING_PAYMENT`.

#### Step 5: Asynchronous Booking Confirmation (Stripe Webhook)

1.  **User Pays:** The user clicks the link and completes the payment on Stripe's page.
2.  **Stripe Notifies App:** After the payment succeeds, Stripe sends an asynchronous `POST` request to `/stripe-webhook`.
3.  **Platform-Aware Webhook Handling (`app/main.py`):**
    *   The `/stripe-webhook` endpoint verifies the request came from Stripe.
    *   It extracts the `user_id` from the Stripe event's `client_reference_id`.
    *   **Crucially, it checks if the `user_id` belongs to a WhatsApp or Telegram user.**
    *   Based on the platform, it uses the appropriate client (**Twilio** or **Telegram**) to send a proactive confirmation message to the user, asking for their full name and date of birth.
    *   It loads the user's session, transitions the state to `GATHERING_BOOKING_DETAILS`, and saves it.

#### Step 6: Finalization

1.  **User Provides Details:** The user replies with their full name and DOB.
2.  **Final State Check:** `process_message` loads the session and sees the state is `GATHERING_BOOKING_DETAILS`.
3.  **Booking (`app/amadeus_service.py`):**
    *   `extract_traveler_details` parses the final details.
    *   `amadeus_service.book_flight()` is called. This makes the final, definitive booking request to the Amadeus API.
4.  **Confirmation:**
    *   If the booking is successful, Amadeus returns a booking ID.
    *   A final confirmation message is sent to the user.
    *   The state is changed to `BOOKING_COMPLETE`.

### Technology Stack Summary

*   **Backend Framework:** **Flask** provides the web server and routing.
*   **Messaging Platforms:** **Twilio** for WhatsApp, **Telegram Bot API** for Telegram.
*   **Natural Language Understanding:** **IO Intelligence API** acts as the "brain" of the agent.
*   **Flight Data & Booking:** **Amadeus** provides real-world flight data and booking capabilities.
*   **Payments:** **Stripe** handles secure payment processing.
*   **Persistent Storage:** **PostgreSQL** serves as the durable database for all session data. **SQLAlchemy** is the library used to interact with it.
*   **Testing:** **Pytest** is used to test every component of the application. 