# How the AI Travel Agent Works: A Deep Dive

This document provides a detailed, step-by-step explanation of how the entire system works. The application is built on a **two-service architecture** (a web service and a worker service) to ensure it is responsive, scalable, and resilient.

### High-Level Architecture

The application is composed of two primary microservices that communicate via a **Redis** message queue:

1.  **The Web Service (`ai-travel-agent-web`)**: A public-facing Flask application. Its only job is to handle incoming HTTP requests from messaging platforms (like Telegram), manage the conversation state, and quickly offload any time-consuming work to the worker service. It runs using the `gunicorn app.main:app` command.

2.  **The Worker Service (`ai-travel-agent-worker`)**: A private, background Celery service. It constantly listens for tasks on the Redis queue. It performs the "heavy lifting" like calling external APIs (Amadeus for flight searches) and sends proactive messages back to the user. It is started using `python app/health.py`, which cleverly runs both the Celery worker and a minimal Flask server to satisfy Cloud Run's health check requirements.

This separation of concerns ensures that a slow API call for one user never blocks the web service from responding instantly to other users.

---

### The Step-by-Step User Journey

Let's walk through the exact sequence of events as a user interacts with the agent.

#### Step 1: The Initial Handshake (The Web Service)

1.  **User Sends Message:** A user sends "Hi" to the Telegram Bot.
2.  **Platform Webhook:** Telegram makes an HTTP `POST` request to the public URL of the **Web Service**.
3.  **Application Entry Point (`app/main.py`):** The Flask server receives the request. The `/telegram-webhook` function extracts the user's ID and message and passes them to the central `process_message` function in `app/core_logic.py`.

#### Step 2: Core Logic and State Management (The Web Service)

This all happens inside the `process_message` function in `app/core_logic.py`.

1.  **Session Loading (`app/new_session_manager.py`):** The function immediately calls `load_session(user_id)` to fetch the user's conversation state from **Redis**. If the user is new, it creates a new session with the state `GATHERING_INFO`.

2.  **AI Processing (`app/ai_service.py`):** Based on the current state, `get_ai_response` is called. It sends the conversation history to the **IO Intelligence API**, which asks clarifying questions until it has all the details (origin, destination, date, etc.). When complete, the AI returns the special tag `[INFO_COMPLETE]`.

3.  **State Transition & Session Saving:** The web service sees the `[INFO_COMPLETE]` tag, transitions the user's state to `AWAITING_CONFIRMATION`, and saves the updated session back to **Redis**. The confirmation summary is sent back to the user as an immediate HTTP response.

#### Step 3: The Asynchronous Handoff (Web Service -> Redis -> Worker Service)

This is the most critical part of the architecture.

1.  **User Confirms:** The user replies "Yes". The web service receives this message.
2.  **Task Dispatching (`app/core_logic.py`):**
    *   The `process_message` function loads the session and sees the state is `AWAITING_CONFIRMATION`.
    *   It immediately sends the user the message "Okay, I'm searching for the best flights..."
    *   Crucially, it **does not** search for flights itself. Instead, it calls `search_flights_task.delay(user_id, flight_details)`.
    *   The `.delay()` method places the flight search task and its parameters onto the **Redis** queue.
    *   The web service's job is now complete for this request, and it returns an immediate `200 OK` response to Telegram.

#### Step 4: Background Flight Search (The Worker Service)

1.  **Task Consumption (`app/tasks.py`):**
    *   Meanwhile, the **Worker Service** is running independently and is constantly monitoring the Redis queue.
    *   It immediately sees the new `search_flights_task` and pulls it from the queue.
2.  **Execution:** The worker executes the task's code:
    *   It calls the Amadeus API to get IATA codes.
    *   It calls the Amadeus API again to perform the live flight search. This can take several seconds.
3.  **Proactive Response:**
    *   Once the search is complete, the worker formats the flight offers into a user-friendly list.
    *   It then connects directly to the Telegram API and sends the results as a **new, proactive message** to the user.
4.  **Final State Update:** The worker updates the user's state in Redis to `FLIGHT_SELECTION` and saves the flight offers to their session.

#### Step 5: Payment and Final Booking

The rest of the flow follows a similar pattern, with the web service handling direct user interactions and the worker service handling any follow-up asynchronous notifications (like after a Stripe payment is confirmed).

### Technology Stack Summary

*   **Web Service:** **Flask**, **Gunicorn**.
*   **Worker Service:** **Celery**, enabled by a minimal **Flask** health-checker.
*   **Messaging Platforms:** **Twilio** for WhatsApp, **Telegram Bot API** for Telegram.
*   **Natural Language Understanding:** **IO Intelligence API**.
*   **Flight Data & Booking:** **Amadeus**.
*   **Payments:** **Stripe**.
*   **Session Storage & Task Queue:** **Redis** is the backbone of the system, used for both storing conversation state and as a message broker for Celery.
*   **Testing:** **Pytest**. 