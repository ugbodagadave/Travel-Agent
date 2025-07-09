# Google Cloud Deployment Guide

This guide provides step-by-step instructions for deploying the AI Travel Agent to Google Cloud Run. This application requires **two separate Cloud Run services** to function correctly: a web service and a worker service.

## Prerequisites
1.  A Google Cloud Project with the Cloud Run, Cloud Build, Artifact Registry, and Secret Manager APIs enabled.
2.  `gcloud` CLI installed and authenticated.
3.  A Docker repository created in Google Artifact Registry.
4.  All required secrets (API keys, etc.) stored in Google Secret Manager.

---

## Step 1: Build and Push the Docker Image

The same Docker image will be used for both services. The `CMD` in the `Dockerfile` will be overridden at deployment time for the worker service.

1.  **Build the image:**
    ```bash
    gcloud builds submit --tag us-central1-docker.pkg.dev/YOUR_PROJECT_ID/YOUR_REPO/app:latest
    ```
    (Replace `YOUR_PROJECT_ID` and `YOUR_REPO`)

---

## Step 2: Deploy the Web Service

This service will run the Gunicorn web server and handle incoming HTTP requests from users.

1.  **Deploy the service:**
    ```bash
    gcloud run deploy ai-travel-agent-web \
      --image us-central1-docker.pkg.dev/YOUR_PROJECT_ID/YOUR_REPO/app:latest \
      --platform managed \
      --region us-central1 \
      --allow-unauthenticated \
      --add-vpc-connector YOUR_VPC_CONNECTOR \
      --vpc-egress private-ranges-only
    ```
    (Replace placeholder values).

2.  **Map Secrets**: In the Cloud Run console, go to your `ai-travel-agent-web` service, edit the revision, and map all the required secrets from Secret Manager to the container as environment variables.

---

## Step 3: Deploy the Worker Service

This service will run the Celery worker to process background tasks. It does not need a public URL.

1.  **Deploy the service:**
    ```bash
    gcloud run deploy ai-travel-agent-worker \
      --image us-central1-docker.pkg.dev/YOUR_PROJECT_ID/YOUR_REPO/app:latest \
      --platform managed \
      --region us-central1 \
      --no-allow-unauthenticated \
      --add-vpc-connector YOUR_VPC_CONNECTOR \
      --vpc-egress private-ranges-only \
      --set-command "celery" \
      --set-args "-A,app.celery_worker.celery_app,worker,--loglevel=info"
    ```
    - `--no-allow-unauthenticated`: Prevents public access.
    - `--set-command` and `--set-args`: This is the crucial step. It overrides the Dockerfile's `CMD` and tells the container to start the Celery worker instead of Gunicorn.

2.  **Map Secrets**: Just like the web service, you MUST map all the same secrets from Secret Manager to this worker service. **This is the most likely cause of the current problem.** The worker cannot function without the API keys.

By following these steps, you will have both the web and worker services running correctly, which should permanently resolve the issue of flight searches getting stuck. 