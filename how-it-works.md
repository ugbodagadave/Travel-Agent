# How the AI Travel Agent Works: A Deep Dive

This document provides a detailed, step-by-step explanation of how the entire system works, from the first message to the final booking, based on the project's codebase.

### High-Level Overview

The application functions as a **stateful conversational agent**. This means it not only understands individual messages but also remembers the entire context of the conversation for each user. It guides the user through a series of states (e.g., `GATHERING_INFO`, `FLIGHT_SELECTION`, `AWAITING_PAYMENT`) to achieve the final goal of booking a flight.

---

### The Step-by-Step User Journey

Let's walk through the exact sequence of events as a user interacts with the agent.

#### Step 1: The Initial Handshake (User -> Twilio -> App)

1.  **User Sends Message:** A user sends a WhatsApp message (e.g., "Hi") to your Twilio phone number.
2.  **Twilio Webhook:** Twilio receives this message and immediately makes an HTTP `POST` request to the public URL of your application, specifically to the `/webhook` endpoint.
3.  **Application Entry Point (`app/main.py`):**
    *   The Flask server receives this `POST` request.
    *   Inside the `@app.route("/webhook")` function, the application extracts two key pieces of information from the request data:
        *   `From`: The user's WhatsApp ID (e.g., `whatsapp:+15551234567`). This is the unique identifier for the user.
        *   `Body`: The content of the message (e.g., "Hi").
    *   **Technology:** Flask, Twilio API.

#### Step 2: The AI Conversation & Information Gathering

1.  **Session Loading (`app/new_session_manager.py`):**
    *   The first thing the `/webhook` does is call `load_session(user_id)`.
    *   This function implements a **cache-aside pattern**:
        *   **Check Redis (Cache):** It first tries to fetch the session data from Redis, which is extremely fast.
        *   **Check PostgreSQL (Database):** If the data isn't in Redis (a "cache miss"), it queries the PostgreSQL database for that `user_id`. If found, it stores the result in Redis for future requests before returning it.
        *   **New User:** If the user is found in neither, it means they are a new user. It returns a fresh session with the default state: `GATHERING_INFO`.
    *   **Technology:** Redis (for caching), PostgreSQL with SQLAlchemy (for persistent storage).

2.  **AI Processing (`app/ai_service.py`):**
    *   The application sees the user's state is `GATHERING_INFO`.
    *   It calls `get_ai_response(incoming_msg, conversation_history)`.
    *   This function sends the user's latest message along with the entire past conversation history to the **IO Intelligence API**.
    *   The AI has a system prompt that instructs it to act as a travel agent, understand user intent, and extract key "slots" of information (origin, destination, date, number of travelers).
    *   The AI's response is returned. If it has all the information it needs, the AI includes a special tag: `[INFO_COMPLETE]`. Otherwise, it asks a clarifying question.

3.  **State Transition:**
    *   Back in `app/main.py`, the code checks the AI's response.
    *   If `[INFO_COMPLETE]` is present, it transitions the user's state to `AWAITING_CONFIRMATION`.
    *   The user is sent a summary of the details for them to verify.

4.  **Session Saving (`app/new_session_manager.py`):**
    *   The `/webhook` function calls `save_session(...)` with the new state and the updated conversation history.
    *   This function writes the complete session data to **both Redis and PostgreSQL**, ensuring the cache is hot and the data is durably saved.

#### Step 3: Flight Search (Amadeus Integration)

1.  **User Confirmation:** The user replies "Yes".
2.  **State Check:** The `/webhook` loads the session and sees the state is `AWAITING_CONFIRMATION`.
3.  **Service Calls (`app/amadeus_service.py`, `app/timezone_service.py`):**
    *   The application calls `extract_flight_details_from_history` to get the structured data (origin: 'Paris', destination: 'NYC').
    *   It determines the local timezone using `get_timezone_for_city` to provide more relevant flight times.
    *   It calls the **Amadeus API** twice via `amadeus_service.get_iata_code()` to convert city names into official airport IATA codes.
    *   Finally, it calls `amadeus_service.search_flights()` with these IATA codes. This makes a live API request to Amadeus to find real, available flights.

4.  **Presenting Options:**
    *   The flight offers from Amadeus are formatted into a user-friendly, numbered list.
    *   This list is sent back to the user as a WhatsApp message.
    *   The state is changed to `FLIGHT_SELECTION`, and the *full, detailed flight offer objects* are saved in the user's session.

#### Step 4: Payment Initiation (Stripe Integration)

1.  **User Selects Flight:** The user replies with a number, e.g., "1".
2.  **State Check:** The `/webhook` loads the `FLIGHT_SELECTION` state and the list of flight offers.
3.  **Checkout Creation (`app/payment_service.py`):**
    *   The application retrieves the full details for the selected flight from the session data.
    *   It calls `create_checkout_session(selected_flight, user_id)`.
    *   This function calls the **Stripe API** to generate a secure, hosted payment link. It includes the price, currency, and, most importantly, the `user_id` as a `client_reference_id`.
    *   The generated Stripe URL is sent to the user.
    *   The state is updated to `AWAITING_PAYMENT` and saved.

#### Step 5: Asynchronous Booking Confirmation (Stripe Webhook)

1.  **User Pays:** The user clicks the link, goes to the Stripe page, and completes the payment.
2.  **Stripe Notifies App:** After the payment succeeds, Stripe's servers send an asynchronous `POST` request to a *different* endpoint in our app: `/stripe-webhook`.
3.  **Webhook Handling (`app/main.py`):**
    *   The `/stripe-webhook` endpoint first performs a crucial security check using your webhook secret to verify the request is legitimate.
    *   It processes the event and sees it's a `checkout.session.completed`.
    *   It extracts the `user_id` from the `client_reference_id` we stored in Step 4.
    *   It loads the user's session, which is still in the `AWAITING_PAYMENT` state.
    *   It transitions the state to `GATHERING_BOOKING_DETAILS` and saves the session.
    *   Using the proactive **Twilio Client**, it sends a *new* message to the user, asking for their full name and date of birth.

#### Step 6: Finalization

1.  **User Provides Details:** The user replies with their full name and DOB.
2.  **Final State Check:** The `/webhook` loads the session and sees the state is `GATHERING_BOOKING_DETAILS`.
3.  **Booking (`app/amadeus_service.py`):**
    *   `extract_traveler_details` is called to parse the final details.
    *   A `traveler` object is created in the exact format required by Amadeus.
    *   `amadeus_service.book_flight()` is called. This makes the final, definitive booking request to the Amadeus API.
4.  **Confirmation:**
    *   If the booking is successful, Amadeus returns an official booking ID.
    *   A final confirmation message, including the booking ID, is sent to the user.
    *   The state is changed to `BOOKING_COMPLETE`, and the conversation is successfully concluded.

### Technology Stack Summary

*   **Backend Framework:** **Flask** provides the web server and routing.
*   **Messaging:** **Twilio** bridges the gap between WhatsApp and your application.
*   **Natural Language Understanding:** **IO Intelligence** acts as the "brain," understanding user intent and extracting information.
*   **Flight Data & Booking:** **Amadeus** provides real-world flight data and the functionality to book tickets.
*   **Payments:** **Stripe** handles secure payment processing and notifies your application of success via webhooks.
*   **Session Caching:** **Redis** provides a high-speed, in-memory cache for active conversations.
*   **Persistent Storage:** **PostgreSQL** serves as the durable, long-term database, ensuring no conversation data is lost. **SQLAlchemy** is the library used to interact with it.
*   **Testing:** **Pytest** and **unittest.mock** are used to test every component of the application. 