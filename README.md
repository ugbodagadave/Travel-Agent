# AI Travel Agent

This project is an AI-powered travel agent that can be used via WhatsApp to book flights.

## Current Progress

So far, we have completed the initial project setup, created a basic web server, integrated the core AI and messaging services, and added session persistence.

### Phase 0: Project Setup
- Initialized a Git repository.
- Created a Python virtual environment (`venv`).
- Set up the project structure with `app` and `tests` directories.
- Installed `pytest` for testing.
- Created a `.gitignore` file.

### Phase 1: Basic Web Server
- Installed Flask.
- Created a basic Flask application in `app/main.py`.
- Implemented a `/webhook` endpoint.
- Wrote and passed a unit test to verify the webhook.

### Phase 2: Twilio Integration
- Installed the `twilio` library.
- Configured the webhook to receive and parse WhatsApp messages.
- Implemented logic to send a TwiML response.
- Wrote and passed a unit test to verify the Twilio integration.

### Phase 3: IO Intelligence Integration
- Installed the `openai` library to use with the IO Intelligence API.
- Created a dedicated `app/ai_service.py` module to handle API calls.
- Integrated the AI service with the webhook to generate dynamic responses.
- Wrote and passed a unit test using a mock to verify the AI service integration.

### Phase 4: Conversation Logic and Slot-Filling
- Implemented a system prompt to guide the AI agent in collecting flight details (origin, destination, dates, etc.).
- Wrote and passed unit tests for multi-turn conversations, ensuring the agent asks clarifying questions and correctly identifies when all slots are filled.

### Phase 5: Session Persistence with Redis
- Installed the `redis` library.
- Set up a free Redis instance on Render for caching.

### Phase 5a: Persistent Storage with PostgreSQL
- Identified the limitation of non-persistent free Redis instances for production use.
- Implemented a robust, dual-storage solution:
    - **PostgreSQL**: Added as the primary, durable database for all conversation history. Installed `psycopg2-binary` and `SQLAlchemy`.
    - **Redis Cache**: Kept Redis as a high-speed caching layer to improve performance.
- Created a `database.py` module to manage the database connection and schema.
- Implemented a "cache-aside" pattern in `session_manager.py` to check Redis first, fall back to Postgres on a miss, and write to both on save.
- Wrote and passed a comprehensive end-to-end test mocking both database connections to verify the new architecture.

### Phase 6: Timezone Handling
- Installed `pytz`, `timezonefinder`, and `geopy` libraries.
- Created a `timezone_service.py` to infer an IANA timezone (e.g., "America/New_York") from a city name.
- Integrated the service into the main webhook to detect the user's timezone based on their origin city.
- Updated the confirmation message to include the detected timezone, providing better feedback to the user.
- Wrote and passed a unit test with a mock to verify the timezone integration.

## Next Steps

The next and most exciting phase is to integrate a real flight search API. Once all the details are collected, the agent will query an external service to find live flight options. 