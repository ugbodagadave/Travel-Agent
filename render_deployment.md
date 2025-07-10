# Render Deployment Guide

This guide provides step-by-step instructions for migrating the AI Travel Agent from Google Cloud to Render. The goal is to simplify the deployment process while maintaining the application's two-service architecture (web and worker).

We will use Render's "Infrastructure as Code" feature by creating a `render.yaml` file to define all the necessary services.

---

## Phase 1: Codebase Cleanup & Preparation

The first step is to remove all legacy Google Cloud and Docker-specific files from the repository and prepare it for Render.

### 1.1: Delete Google Cloud & Docker Files

The following files are no longer needed and should be deleted from your project:
- `google_cloud_deployment.md`
- `Dockerfile.web`
- `Dockerfile.worker`
- `.github/workflows/deploy.yml` (or the entire `.github` directory if it only contains the deployment workflow).

This is a critical step to ensure there's no confusion and the project is clean.

**Test:** After deleting these files, your application should still run locally without issues.

### 1.2: Verify `requirements.txt`

Render uses the `requirements.txt` file to install all necessary Python packages. Ensure that it contains all dependencies for both the web and worker services. It should look similar to this:

```
Flask
gunicorn
celery
redis
python-dotenv
requests
twilio
# ... any other packages
```

### 1.3: Create `render.yaml`

Create a new file named `render.yaml` in the root of your project. This file tells Render how to build and deploy your application.

```yaml
services:
  # A Redis instance for session storage and as a Celery message broker
  - name: redis
    type: redis
    plan: free
    maxmemoryPolicy: noeviction

  # The public-facing Flask web service
  - name: ai-travel-agent-web
    type: web
    plan: free
    env: python
    buildCommand: 'pip install -r requirements.txt'
    startCommand: 'gunicorn app.main:app'
    healthCheckPath: /
    envVars:
      - key: REDIS_URL
        fromService:
          type: redis
          name: redis
          property: connectionString
      - key: PYTHON_VERSION
        value: 3.11

  # The private Celery background worker
  - name: ai-travel-agent-worker
    type: worker
    plan: free
    env: python
    buildCommand: 'pip install -r requirements.txt'
    startCommand: 'celery -A app.celery_worker.celery_app worker --loglevel=info'
    envVars:
      - key: REDIS_URL
        fromService:
          type: redis
          name: redis
          property: connectionString
      - key: PYTHON_VERSION
        value: 3.11
```

**Note on Free Plan:** The `plan: free` setting is used here. Be aware of the limitations of Render's free tier, such as services spinning down after inactivity. For production use, you should upgrade to a paid plan.

### 1.4: Final Local Test

Before pushing your changes, run the local test suite one last time to ensure that the cleanup and new configuration file haven't introduced any regressions.

```bash
pytest -sv
```

---

## Phase 2: Deployment to Render

With the codebase prepared, you can now deploy it to Render.

### 2.1: Create the Blueprint on Render

1.  Push your updated code (including `render.yaml` and the deleted files) to your GitHub repository.
2.  Go to the [Render Dashboard](https://dashboard.render.com/).
3.  Click **New** > **Blueprint**.
4.  Connect your GitHub repository. Render will automatically detect and parse your `render.yaml` file.
5.  Click **Approve** to create the services.

Render will now build and deploy your three services: `redis`, `ai-travel-agent-web`, and `ai-travel-agent-worker`.

### 2.2: Configure Environment Variables

Your services will not start correctly until you provide them with the necessary API keys and secrets.

1.  In the Render Dashboard, navigate to the **Environment** tab for both your `ai-travel-agent-web` service and your `ai-travel-agent-worker` service.
2.  You MUST add all the secrets from your original `.env` file as environment variables here. The `REDIS_URL` is already handled by the `render.yaml` file, but you still need to add:
    - `TWILIO_ACCOUNT_SID`
    - `TWILIO_AUTH_TOKEN`
    - `TWILIO_PHONE_NUMBER`
    - `TELEGRAM_BOT_TOKEN`
    - `IO_API_KEY`
    - `AMADEUS_CLIENT_ID`
    - `AMADEUS_CLIENT_SECRET`
    - `STRIPE_PUBLISHABLE_KEY`
    - `STRIPE_SECRET_KEY`
    - `STRIPE_WEBHOOK_SECRET`

**IMPORTANT:** Both the web and worker services need these variables to function correctly.

---

## Phase 3: Testing and Go-Live

Now that the services are deployed and configured, it's time to test them.

### 3.1: Test the Web Service

1.  In the Render Dashboard, find your `ai-travel-agent-web` service.
2.  Copy the public URL (it will look like `https://ai-travel-agent-web-xxxx.onrender.com`).
3.  This URL is your new application endpoint.

### 3.2: Update Webhook URLs

Your messaging platforms need to know the new address of your web service.

1.  **For Telegram:**
    - Open a chat with the `@BotFather`.
    - Use the `/setwebhook` command.
    - Select your bot and paste your new Render URL, appending `/telegram-webhook`.
    - Example: `https://ai-travel-agent-web-xxxx.onrender.com/telegram-webhook`

2.  **For Twilio (WhatsApp):**
    - Go to the Twilio Console.
    - Navigate to your phone number's configuration page.
    - Under "Messaging", find the "A MESSAGE COMES IN" webhook setting.
    - Paste your new Render URL there, appending `/twilio-webhook`.
    - Example: `https://ai-travel-agent-web-xxxx.onrender.com/twilio-webhook`

### 3.3: End-to-End Test

Send a message to your agent on both Telegram and WhatsApp. Go through the entire flow:
- Start a conversation.
- Provide trip details.
- Confirm the flight search.
- **Verify that you receive the flight results.** This confirms the web service, Redis, and worker service are all communicating correctly.

Congratulations! Your application is now running on Render.

---

## Phase 4: Consolidating to a Single Service (Render Free Tier)

**Problem:** Render's free tier for individual accounts does not include the "Background Worker" service type, which is required to run a separate Celery process.

**Solution:** We will refactor the application to run flight searches in a background thread within the main `ai-travel-agent-web` service. This preserves a responsive user experience while working within the free tier's limitations. The Redis instance will still be used for session management.

### 4.1: Code Refactoring Plan

1.  **Implement Threading for Background Tasks:**
    *   In `app/core_logic.py`, the `search_flights_task.delay(...)` call will be replaced.
    *   The new implementation will use Python's built-in `threading` module to start `search_flights_task` in a new, non-blocking thread. This will look something like:
        ```python
        import threading
        from app.tasks import search_flights_task

        # ... inside the process_message function ...
        task_thread = threading.Thread(target=search_flights_task, args=(user_id, flight_details))
        task_thread.start()
        ```

2.  **Simplify Celery Components:**
    *   The `@celery_app.task` decorator will be removed from the function in `app/tasks.py`. It will become a standard Python function.
    *   The `app/celery_worker.py` and `app/health.py` files will be deleted as they are no longer needed.
    *   The `celery` package will be removed from `requirements.txt`.

### 4.2: Update `render.yaml`

The `render.yaml` file will be modified to remove the `ai-travel-agent-worker` service definition entirely. The file will only define two services: `redis` and `ai-travel-agent-web`. The `startCommand` for the web service will remain `gunicorn app.main:app`.

### 4.3: Testing the New Architecture

1.  **Update Unit Tests:** Existing tests that mock Celery's `.delay()` method must be updated. The new tests will assert that `threading.Thread` is created and started with the correct function and arguments.
2.  **Local End-to-End Test:** The application will be run locally to confirm the entire flow works as expected. A flight search must be triggered to verify that results are sent back proactively without blocking the main application.
3.  **Push and Deploy:** Once all tests pass, the changes will be pushed to GitHub, and Render will automatically deploy the new, single-service version of the application. 