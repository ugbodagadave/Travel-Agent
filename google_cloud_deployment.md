# Comprehensive Guide to Migrating and Deploying on Google Cloud via GitHub Actions

This document provides a complete step-by-step guide to migrating your Python Flask application from Render to Google Cloud. We will use Google Cloud Run for hosting, Memorystore for Redis as a persistent data store, and a GitHub Actions workflow for continuous deployment.

This new plan ensures that any changes pushed to your `main` branch will automatically trigger a build and deployment to Cloud Run, providing a seamless and automated CI/CD pipeline.

---

## Phase 1: Google Cloud Project Setup (Manual)

This phase involves setting up your Google Cloud environment. You will need to perform these steps in the Google Cloud Console.

### Step 1: Create a Google Cloud Project

1.  Go to the [Google Cloud Console](https://console.cloud.google.com/).
2.  Click on the project selector dropdown in the top bar and click **"NEW PROJECT"**.
3.  Give your project a name (e.g., `ai-travel-agent`) and click **"CREATE"**.
4.  Make sure billing is enabled for your project.

### Step 2: Enable Necessary APIs

We need to enable all the APIs for the services we'll be using.

1.  In the Cloud Console, search for "APIs & Services" and go to the "Enabled APIs & services" page.
2.  Click **"+ ENABLE APIS AND SERVICES"**.
3.  Search for and enable the following APIs one by one:
    *   **Cloud Run Admin API** (for deploying our service)
    *   **Artifact Registry API** (to store our Docker containers)
    *   **Cloud Build API** (for building our container from source)
    *   **Memorystore for Redis API** (for our Redis instance)
    *   **Secret Manager API** (for managing our environment variables securely)
    *   **Serverless VPC Access API** (to connect Cloud Run to Redis)
    *   **IAM Credentials API** (to allow GitHub Actions to impersonate a service account)

---

## Phase 2: Setting Up Redis and Networking (Manual)

Now, we'll create our Redis instance and the necessary networking to allow Cloud Run to access it.

### Step 1: Create a Memorystore for Redis Instance

1.  In the Google Cloud Console, search for **"Memorystore"** and select **"Redis"**.
2.  Click **"CREATE INSTANCE"**.
3.  Fill in the instance details:
    *   **Instance ID:** Give it a name (e.g., `session-storage`).
    *   **Region:** Choose a region. **This region must be the same one you use for your Cloud Run service.**
    *   **Tier:** Select **Basic**.
    *   **Capacity:** Start with 1 GB.
    *   **Version:** Choose a recent Redis version.
4.  Under **"Persistence"**, select **Append Only File (AOF)** for durability.
5.  Click **"CREATE"**.
6.  Once created, **note down the `IP address` and `Port`**.

### Step 2: Create a Serverless VPC Access Connector

1.  In the Google Cloud Console, search for **"Serverless VPC Access"**.
2.  Click **"CREATE CONNECTOR"**.
3.  Configure the connector:
    *   **Name:** Give it a name (e.g., `cloud-run-connector`).
    *   **Region:** **Must be the same region** as your Memorystore instance.
    *   **Network:** Select the `default` VPC network.
    *   **Subnet:** Select **"Custom IP range"** and provide an unused `/28` IP range (e.g., `10.8.0.0`).
4.  Click **"CREATE"**.

### Step 3: Configure Cloud NAT for Internet Access

By default, the VPC network cannot access the public internet. This is required for your app to connect to external APIs like Amadeus and Stripe.

1.  In the Google Cloud Console, search for **"Cloud NAT"**.
2.  Click **"Create NAT Gateway"**.
3.  Configure the gateway:
    *   **Gateway name:** `cloud-run-nat-gateway`
    *   **VPC network:** `default`
    *   **Region:** Must match your Cloud Run and VPC Connector region.
    *   **Cloud Router:** Click "**Create new router**", give it a name (e.g., `cloud-run-router`), and click "**Create**".
4.  Click the final "**Create**" button.

---

## Phase 3: Setting Up Secrets and Permissions (Manual)

We will use Google Secret Manager for sensitive data and set up a service account for GitHub Actions to use.

### Step 1: Create Secrets in Secret Manager

For each secret in your current `.env` file, create a corresponding secret in Secret Manager.

1.  In the Google Cloud Console, search for **"Secret Manager"**.
2.  Click **"CREATE SECRET"** for each environment variable.
3.  Create secrets for:
    *   `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `IO_API_KEY`, `AMADEUS_CLIENT_ID`, `AMADEUS_CLIENT_SECRET`, `STRIPE_PUBLISHABLE_KEY`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `TELEGRAM_BOT_TOKEN`.
    *   `REDIS_URL`: Use the format `redis://<REDIS_IP_ADDRESS>:<REDIS_PORT>` with the values from your Memorystore instance.

### Step 2: Create a Service Account for GitHub Actions

1.  In the Cloud Console, navigate to **"IAM & Admin" > "Service Accounts"**.
2.  Click **"CREATE SERVICE ACCOUNT"**.
3.  Name it `github-actions-deployer`.
4.  Grant it the following roles:
    *   **Cloud Run Admin** (`roles/run.admin`): To deploy and manage the Cloud Run service.
    *   **Artifact Registry Writer** (`roles/artifactregistry.writer`): To push Docker images.
    *   **Service Account User** (`roles/iam.serviceAccountUser`): To allow Cloud Run to run as another service account.
    *   **Secret Manager Secret Accessor** (`roles/secretmanager.secretAccessor`): To access secrets during the deployment process.
5.  Click **"DONE"**.

### Step 3: Configure Workload Identity Federation

This allows GitHub Actions to authenticate as the service account without needing a static key file.

1.  Navigate to **"IAM & Admin" > "Workload Identity Federation"**.
2.  Click **"CREATE POOL"**, name it `github-pool`, and continue.
3.  Under "Provider type", select **"OpenID Connect (OIDC)"**.
4.  For "Provider configuration":
    *   **Issuer (URL):** `https://token.actions.githubusercontent.com`
    *   **Audience:** Leave as default.
5.  Under "Attribute mapping", add the following:
    *   `google.subject`: `assertion.sub`
    *   `attribute.actor`: `assertion.actor`
    *   `attribute.repository`: `assertion.repository`
6.  Save the provider.
7.  Now, grant the Service Account access to this pool. Go back to the **Service Accounts** page, select the `github-actions-deployer` account, go to the **"Permissions"** tab, and click **"GRANT ACCESS"**.
    *   **New principal:** `principalSet://iam.googleapis.com/projects/<YOUR_PROJECT_NUMBER>/locations/global/workloadIdentityPools/github-pool/attribute.repository/<YOUR_GITHUB_USERNAME>/<YOUR_REPO_NAME>`
    *   **Role:** `Workload Identity User` (`roles/iam.workloadIdentityUser`)
    *   Replace placeholders with your project number, GitHub username, and repository name.

---

## Phase 4: Application Code Modification (AI Agent Task)

This phase will be handled entirely by me. I will modify the application to remove the PostgreSQL dependency and rely solely on the new Memorystore for Redis instance.

*   Modify `app/new_session_manager.py` to remove all database logic.
*   Delete `app/database.py`.
*   Remove `SQLAlchemy` and `psycopg2-binary` from `requirements.txt`.
*   Remove database initialization from `app/main.py`.
*   Delete the `render.yaml` file.
*   Create a `Dockerfile` for the application.

*I will run tests after each file modification to ensure the application remains stable.*

---

## Phase 5: GitHub Actions Deployment (AI Agent Task)

This phase is also handled by me. I will create a GitHub Actions workflow file (`.github/workflows/deploy.yml`). This workflow will:
1.  Trigger on every push to the `main` branch.
2.  Authenticate to Google Cloud using Workload Identity Federation.
3.  Build a Docker image of the application.
4.  Push the image to Google Artifact Registry.
5.  Deploy the new image to Google Cloud Run, injecting all the necessary secrets from Secret Manager.

---

## Phase 6: Post-Deployment Steps (Manual)

Once the application is successfully deployed for the first time via the GitHub workflow, we will get a public URL for the service. You will need to use this URL to update your webhooks.

### Step 1: Update Webhooks

1.  **Twilio/WhatsApp:** Go to your Twilio console, navigate to your WhatsApp sandbox settings, and update the "WHEN A MESSAGE COMES IN" webhook URL to `YOUR_NEW_URL/webhook`.
2.  **Telegram:** You will need to use the Telegram Bot API to set the webhook. You can do this by visiting the following URL in your browser (make sure to replace the placeholders):
    `https://api.telegram.org/bot<YOUR_TELEGRAM_BOT_TOKEN>/setWebhook?url=YOUR_NEW_URL/telegram-webhook`

### Step 2: Test the Application

After updating the webhooks, send a message to your WhatsApp and Telegram bots to confirm that everything is working as expected.

---

This comprehensive plan covers all the necessary steps for a successful migration with automated deployments from GitHub. The AI assistant will now create a to-do list to begin the migration tasks. 