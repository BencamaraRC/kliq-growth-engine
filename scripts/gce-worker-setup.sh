#!/usr/bin/env bash
# KLIQ Growth Engine — GCE Worker Setup
# Creates a GCE VM running Docker Compose with Redis + Celery worker.
# Idempotent — safe to re-run.
#
# Usage:
#   bash scripts/gce-worker-setup.sh
#
# Prerequisites:
#   - gcloud CLI authenticated (gcloud auth login)
#   - Project set: gcloud config set project rcwl-development
#   - Worker image built and pushed: make build-worker && make push

set -euo pipefail

PROJECT_ID="rcwl-development"
REGION="europe-west1"
ZONE="${REGION}-b"
INSTANCE="kliq-growth-worker"
MACHINE_TYPE="e2-standard-2"
REGISTRY="${REGION}-docker.pkg.dev/${PROJECT_ID}/kliq-growth-engine"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== KLIQ Growth Engine — GCE Worker Setup ==="
echo "Project:  ${PROJECT_ID}"
echo "Zone:     ${ZONE}"
echo "Instance: ${INSTANCE}"
echo ""

# --- Step 1: Enable Compute Engine API ---
echo "[1/6] Enabling Compute Engine API..."
gcloud services enable compute.googleapis.com --project="${PROJECT_ID}" 2>/dev/null || true

# --- Step 2: Create service account (skip if exists) ---
echo "[2/6] Creating service account..."
SA_EMAIL="kliq-growth-engine@${PROJECT_ID}.iam.gserviceaccount.com"
if gcloud iam service-accounts describe "${SA_EMAIL}" --project="${PROJECT_ID}" &>/dev/null; then
    echo "  Service account already exists."
else
    gcloud iam service-accounts create kliq-growth-engine \
        --display-name="KLIQ Growth Engine" \
        --project="${PROJECT_ID}"
    echo "  Service account created."

    # Grant necessary roles
    for ROLE in roles/artifactregistry.reader roles/logging.logWriter roles/monitoring.metricWriter; do
        gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
            --member="serviceAccount:${SA_EMAIL}" \
            --role="${ROLE}" \
            --quiet
    done
    echo "  IAM roles granted."
fi

# --- Step 3: Create the VM (skip if exists) ---
echo "[3/6] Creating GCE VM..."
if gcloud compute instances describe "${INSTANCE}" --zone="${ZONE}" --project="${PROJECT_ID}" &>/dev/null; then
    echo "  VM already exists, skipping creation."
else
    gcloud compute instances create "${INSTANCE}" \
        --project="${PROJECT_ID}" \
        --zone="${ZONE}" \
        --machine-type="${MACHINE_TYPE}" \
        --image-family=cos-stable \
        --image-project=cos-cloud \
        --boot-disk-size=20GB \
        --boot-disk-type=pd-ssd \
        --service-account="${SA_EMAIL}" \
        --scopes=cloud-platform \
        --tags=kliq-worker \
        --metadata=google-logging-enabled=true

    echo "  VM created. Waiting 30s for startup..."
    sleep 30
fi

# --- Step 4: Copy .env to VM ---
echo "[4/6] Copying env file to VM..."

# Check .env.production exists
if [ ! -f "${SCRIPT_DIR}/../.env.production" ]; then
    echo ""
    echo "ERROR: .env.production not found!"
    echo "Copy .env.production.template to .env.production and fill in secrets:"
    echo "  cp .env.production.template .env.production"
    echo "  # Edit .env.production with real values"
    echo "  # Then re-run this script"
    exit 1
fi

gcloud compute scp "${SCRIPT_DIR}/../.env.production" \
    "${INSTANCE}:~/.env" \
    --zone="${ZONE}" \
    --project="${PROJECT_ID}"

echo "  Env file copied."

# --- Step 5: Configure Docker and pull images ---
echo "[5/6] Configuring Docker and pulling images..."

gcloud compute ssh "${INSTANCE}" \
    --zone="${ZONE}" \
    --project="${PROJECT_ID}" \
    --command="
        # Configure Docker auth for Artifact Registry
        docker-credential-gcr configure-docker --registries=${REGION}-docker.pkg.dev 2>/dev/null || true

        # Pull latest images
        echo 'Pulling Redis...'
        docker pull redis:7-alpine

        echo 'Pulling worker image...'
        docker pull ${REGISTRY}/worker:latest
    "

echo "  Images pulled."

# --- Step 6: Start containers ---
# Note: COS doesn't have docker-compose, so we use docker run directly
echo "[6/6] Starting containers..."

gcloud compute ssh "${INSTANCE}" \
    --zone="${ZONE}" \
    --project="${PROJECT_ID}" \
    --command="
        # Create network
        docker network create kliq-net 2>/dev/null || true

        # Stop existing containers
        docker rm -f kliq-redis kliq-worker 2>/dev/null || true

        # Start Redis
        echo 'Starting Redis...'
        docker run -d \
            --name kliq-redis \
            --network kliq-net \
            --restart always \
            -v redis_data:/data \
            redis:7-alpine

        sleep 3

        # Start Celery worker
        echo 'Starting Celery worker...'
        docker run -d \
            --name kliq-worker \
            --network kliq-net \
            --restart always \
            --env-file ~/.env \
            -e REDIS_URL=redis://kliq-redis:6379/0 \
            ${REGISTRY}/worker:latest \
            celery -A app.workers.celery_app worker --loglevel=info --concurrency=4

        echo ''
        echo 'Container status:'
        docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}'
    "

echo ""
echo "=== Deployment complete! ==="
echo ""
echo "Useful commands:"
echo "  make gce-ssh       # SSH into the VM"
echo "  make gce-logs      # Tail worker logs"
echo "  make gce-restart   # Restart containers"
echo "  make gce-stop      # Stop VM (save costs)"
echo "  make gce-start     # Start VM"
