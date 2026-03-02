#!/usr/bin/env bash
# =============================================================================
# KLIQ Growth Engine — GCP Infrastructure Setup
# =============================================================================
#
# Run this script ONCE to set up all GCP resources before first deploy.
# Prerequisites: gcloud CLI authenticated with Owner/Editor on rcwl-development
#
# Usage:
#   chmod +x scripts/setup-gcp-infrastructure.sh
#   ./scripts/setup-gcp-infrastructure.sh
#
# The script is idempotent — safe to re-run (existing resources are skipped).
# =============================================================================

set -euo pipefail

# ── Configuration ────────────────────────────────────────────────────────────

PROJECT_ID="rcwl-development"
REGION="europe-west1"
REGISTRY_NAME="kliq-growth-engine"
REGISTRY="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REGISTRY_NAME}"

SERVICE_ACCOUNT_NAME="kliq-growth-engine"
SERVICE_ACCOUNT="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

GITHUB_ORG="BencamaraRC"
GITHUB_REPO="kliq-growth-engine"

WIF_POOL="github-pool"
WIF_PROVIDER="github-provider"

VPC_CONNECTOR="kliq-vpc-connector"

CLOUD_SQL_INSTANCE="kliq-growth-db"
CLOUD_SQL_TIER="db-f1-micro"
CLOUD_SQL_DB="kliq_growth_engine"
CLOUD_SQL_USER="kliq"

# ── Helpers ──────────────────────────────────────────────────────────────────

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { echo -e "${CYAN}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

confirm() {
    echo ""
    echo -e "${YELLOW}────────────────────────────────────────────${NC}"
    echo -e "${YELLOW}  KLIQ Growth Engine — GCP Infrastructure   ${NC}"
    echo -e "${YELLOW}────────────────────────────────────────────${NC}"
    echo ""
    echo "  Project:       ${PROJECT_ID}"
    echo "  Region:        ${REGION}"
    echo "  SQL Instance:  ${CLOUD_SQL_INSTANCE}"
    echo "  Service Acct:  ${SERVICE_ACCOUNT}"
    echo "  GitHub Repo:   ${GITHUB_ORG}/${GITHUB_REPO}"
    echo ""
    read -rp "Proceed with setup? (y/N) " response
    [[ "$response" =~ ^[Yy]$ ]] || { echo "Aborted."; exit 0; }
    echo ""
}

# ── Pre-flight checks ───────────────────────────────────────────────────────

check_prerequisites() {
    info "Checking prerequisites..."

    command -v gcloud >/dev/null 2>&1 || error "gcloud CLI not installed. See https://cloud.google.com/sdk/docs/install"

    CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null)
    if [[ "${CURRENT_PROJECT}" != "${PROJECT_ID}" ]]; then
        warn "Current project is '${CURRENT_PROJECT}', switching to '${PROJECT_ID}'"
        gcloud config set project "${PROJECT_ID}"
    fi
    ok "gcloud configured for project ${PROJECT_ID}"
}

# ── Step 1: Enable required APIs ────────────────────────────────────────────

enable_apis() {
    info "Step 1/9: Enabling required GCP APIs..."

    APIS=(
        "run.googleapis.com"
        "artifactregistry.googleapis.com"
        "sqladmin.googleapis.com"
        "secretmanager.googleapis.com"
        "cloudscheduler.googleapis.com"
        "vpcaccess.googleapis.com"
        "iam.googleapis.com"
        "iamcredentials.googleapis.com"
        "cloudresourcemanager.googleapis.com"
        "bigquery.googleapis.com"
    )

    for api in "${APIS[@]}"; do
        gcloud services enable "${api}" --quiet 2>/dev/null && ok "  ${api}" || warn "  ${api} (may already be enabled)"
    done
}

# ── Step 2: Artifact Registry ───────────────────────────────────────────────

setup_artifact_registry() {
    info "Step 2/9: Setting up Artifact Registry..."

    if gcloud artifacts repositories describe "${REGISTRY_NAME}" \
        --location="${REGION}" --format="value(name)" 2>/dev/null; then
        ok "Artifact Registry '${REGISTRY_NAME}' already exists"
    else
        gcloud artifacts repositories create "${REGISTRY_NAME}" \
            --repository-format=docker \
            --location="${REGION}" \
            --description="KLIQ Growth Engine Docker images"
        ok "Created Artifact Registry '${REGISTRY_NAME}'"
    fi
}

# ── Step 3: Cloud SQL PostgreSQL ────────────────────────────────────────────

setup_cloud_sql() {
    info "Step 3/9: Setting up Cloud SQL PostgreSQL..."

    if gcloud sql instances describe "${CLOUD_SQL_INSTANCE}" --format="value(name)" 2>/dev/null; then
        ok "Cloud SQL instance '${CLOUD_SQL_INSTANCE}' already exists"
    else
        warn "Creating Cloud SQL instance (this takes 3-5 minutes)..."
        gcloud sql instances create "${CLOUD_SQL_INSTANCE}" \
            --database-version=POSTGRES_15 \
            --tier="${CLOUD_SQL_TIER}" \
            --region="${REGION}" \
            --storage-type=SSD \
            --storage-size=10GB \
            --no-assign-ip \
            --network=default \
            --quiet
        ok "Created Cloud SQL instance '${CLOUD_SQL_INSTANCE}'"
    fi

    # Create database
    if gcloud sql databases describe "${CLOUD_SQL_DB}" \
        --instance="${CLOUD_SQL_INSTANCE}" --format="value(name)" 2>/dev/null; then
        ok "Database '${CLOUD_SQL_DB}' already exists"
    else
        gcloud sql databases create "${CLOUD_SQL_DB}" \
            --instance="${CLOUD_SQL_INSTANCE}"
        ok "Created database '${CLOUD_SQL_DB}'"
    fi

    # Create user (prompt for password)
    echo ""
    read -rsp "  Enter password for Cloud SQL user '${CLOUD_SQL_USER}': " DB_PASSWORD
    echo ""
    gcloud sql users create "${CLOUD_SQL_USER}" \
        --instance="${CLOUD_SQL_INSTANCE}" \
        --password="${DB_PASSWORD}" 2>/dev/null \
        && ok "Created user '${CLOUD_SQL_USER}'" \
        || warn "User '${CLOUD_SQL_USER}' may already exist — update password manually if needed"

    # Get connection name for later
    CONNECTION_NAME=$(gcloud sql instances describe "${CLOUD_SQL_INSTANCE}" \
        --format="value(connectionName)")
    ok "Cloud SQL connection name: ${CONNECTION_NAME}"
    echo ""
    echo -e "  ${CYAN}DATABASE_URL for production:${NC}"
    echo "  postgresql+asyncpg://${CLOUD_SQL_USER}:<PASSWORD>@/<CLOUD_SQL_DB>?host=/cloudsql/${CONNECTION_NAME}"
    echo ""
}

# ── Step 4: VPC Connector ──────────────────────────────────────────────────

setup_vpc_connector() {
    info "Step 4/9: Setting up VPC Connector..."

    if gcloud compute networks vpc-access connectors describe "${VPC_CONNECTOR}" \
        --region="${REGION}" --format="value(name)" 2>/dev/null; then
        ok "VPC Connector '${VPC_CONNECTOR}' already exists"
    else
        gcloud compute networks vpc-access connectors create "${VPC_CONNECTOR}" \
            --region="${REGION}" \
            --range="10.8.0.0/28" \
            --min-instances=2 \
            --max-instances=3
        ok "Created VPC Connector '${VPC_CONNECTOR}'"
    fi
}

# ── Step 5: Service Account ────────────────────────────────────────────────

setup_service_account() {
    info "Step 5/9: Setting up Service Account..."

    if gcloud iam service-accounts describe "${SERVICE_ACCOUNT}" --format="value(email)" 2>/dev/null; then
        ok "Service account '${SERVICE_ACCOUNT}' already exists"
    else
        gcloud iam service-accounts create "${SERVICE_ACCOUNT_NAME}" \
            --display-name="KLIQ Growth Engine"
        ok "Created service account '${SERVICE_ACCOUNT}'"
    fi

    # Grant roles
    ROLES=(
        "roles/cloudsql.client"
        "roles/secretmanager.secretAccessor"
        "roles/bigquery.dataEditor"
        "roles/bigquery.jobUser"
        "roles/run.invoker"
        "roles/artifactregistry.reader"
        "roles/logging.logWriter"
        "roles/monitoring.metricWriter"
    )

    info "  Granting IAM roles..."
    for role in "${ROLES[@]}"; do
        gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
            --member="serviceAccount:${SERVICE_ACCOUNT}" \
            --role="${role}" \
            --condition=None \
            --quiet 2>/dev/null
        ok "    ${role}"
    done
}

# ── Step 6: Workload Identity Federation ────────────────────────────────────

setup_workload_identity() {
    info "Step 6/9: Setting up Workload Identity Federation (GitHub → GCP)..."

    # Create workload identity pool
    if gcloud iam workload-identity-pools describe "${WIF_POOL}" \
        --location="global" --format="value(name)" 2>/dev/null; then
        ok "Workload Identity Pool '${WIF_POOL}' already exists"
    else
        gcloud iam workload-identity-pools create "${WIF_POOL}" \
            --location="global" \
            --display-name="GitHub Actions Pool"
        ok "Created Workload Identity Pool '${WIF_POOL}'"
    fi

    # Create OIDC provider
    if gcloud iam workload-identity-pools providers describe "${WIF_PROVIDER}" \
        --workload-identity-pool="${WIF_POOL}" \
        --location="global" --format="value(name)" 2>/dev/null; then
        ok "Workload Identity Provider '${WIF_PROVIDER}' already exists"
    else
        gcloud iam workload-identity-pools providers create-oidc "${WIF_PROVIDER}" \
            --location="global" \
            --workload-identity-pool="${WIF_POOL}" \
            --display-name="GitHub OIDC Provider" \
            --issuer-uri="https://token.actions.githubusercontent.com" \
            --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository" \
            --attribute-condition="assertion.repository == '${GITHUB_ORG}/${GITHUB_REPO}'"
        ok "Created Workload Identity Provider '${WIF_PROVIDER}'"
    fi

    # Allow GitHub repo to impersonate the service account
    WIF_POOL_ID=$(gcloud iam workload-identity-pools describe "${WIF_POOL}" \
        --location="global" --format="value(name)")

    gcloud iam service-accounts add-iam-policy-binding "${SERVICE_ACCOUNT}" \
        --role="roles/iam.workloadIdentityUser" \
        --member="principalSet://iam.googleapis.com/${WIF_POOL_ID}/attribute.repository/${GITHUB_ORG}/${GITHUB_REPO}" \
        --quiet 2>/dev/null
    ok "Linked GitHub ${GITHUB_ORG}/${GITHUB_REPO} → ${SERVICE_ACCOUNT}"

    # Grant service account permission to deploy Cloud Run
    gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
        --member="serviceAccount:${SERVICE_ACCOUNT}" \
        --role="roles/run.admin" \
        --condition=None \
        --quiet 2>/dev/null

    gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
        --member="serviceAccount:${SERVICE_ACCOUNT}" \
        --role="roles/artifactregistry.writer" \
        --condition=None \
        --quiet 2>/dev/null

    # Also needs to act as itself for Cloud Run deploys
    gcloud iam service-accounts add-iam-policy-binding "${SERVICE_ACCOUNT}" \
        --role="roles/iam.serviceAccountUser" \
        --member="serviceAccount:${SERVICE_ACCOUNT}" \
        --quiet 2>/dev/null
    ok "Granted deploy permissions to service account"

    # Print values for GitHub secrets
    PROVIDER_FULL=$(gcloud iam workload-identity-pools providers describe "${WIF_PROVIDER}" \
        --workload-identity-pool="${WIF_POOL}" \
        --location="global" --format="value(name)")

    echo ""
    echo -e "  ${CYAN}Add these as GitHub repo secrets:${NC}"
    echo "  WIF_PROVIDER:        ${PROVIDER_FULL}"
    echo "  WIF_SERVICE_ACCOUNT: ${SERVICE_ACCOUNT}"
    echo ""
}

# ── Step 7: Secret Manager ─────────────────────────────────────────────────

setup_secrets() {
    info "Step 7/9: Setting up Secret Manager..."
    echo ""
    echo "  The following secrets need to be stored in Secret Manager."
    echo "  You can create them now interactively, or later via the console."
    echo ""

    SECRETS=(
        "DATABASE_URL"
        "CMS_DATABASE_URL"
        "REDIS_URL"
        "YOUTUBE_API_KEY"
        "ANTHROPIC_API_KEY"
        "BREVO_API_KEY"
        "AWS_ACCESS_KEY_ID"
        "AWS_SECRET_ACCESS_KEY"
        "APIFY_API_TOKEN"
        "PATREON_CLIENT_ID"
        "PATREON_CLIENT_SECRET"
        "CLAIM_SECRET_KEY"
        "SLACK_WEBHOOK_URL"
        "SCHEDULER_SECRET"
    )

    read -rp "  Create secrets interactively now? (y/N) " create_now
    echo ""

    for secret in "${SECRETS[@]}"; do
        # Create the secret if it doesn't exist
        if gcloud secrets describe "${secret}" --format="value(name)" 2>/dev/null; then
            ok "  Secret '${secret}' already exists"
        else
            gcloud secrets create "${secret}" --replication-policy="automatic" --quiet
            ok "  Created secret '${secret}'"

            if [[ "${create_now}" =~ ^[Yy]$ ]]; then
                read -rsp "    Enter value for ${secret} (or press Enter to skip): " secret_value
                echo ""
                if [[ -n "${secret_value}" ]]; then
                    echo -n "${secret_value}" | gcloud secrets versions add "${secret}" --data-file=-
                    ok "    Set value for '${secret}'"
                else
                    warn "    Skipped — set via: echo -n 'value' | gcloud secrets versions add ${secret} --data-file=-"
                fi
            fi
        fi
    done

    echo ""
    echo -e "  ${CYAN}To set a secret value later:${NC}"
    echo "  echo -n 'your-value' | gcloud secrets versions add SECRET_NAME --data-file=-"
    echo ""
}

# ── Step 8: Cloud Run Migration Job ────────────────────────────────────────

setup_migration_job() {
    info "Step 8/9: Setting up Cloud Run Migration Job..."

    # Build the secret env vars flags for the migration job
    SECRET_ENV_FLAGS=""
    SECRETS_FOR_MIGRATE=("DATABASE_URL" "CMS_DATABASE_URL" "REDIS_URL")
    for secret in "${SECRETS_FOR_MIGRATE[@]}"; do
        SECRET_ENV_FLAGS="${SECRET_ENV_FLAGS} --set-secrets=${secret}=${secret}:latest"
    done

    if gcloud run jobs describe kliq-migrate --region="${REGION}" --format="value(name)" 2>/dev/null; then
        ok "Cloud Run Job 'kliq-migrate' already exists"
        warn "Update it after first image push with:"
        echo "  gcloud run jobs update kliq-migrate --image=${REGISTRY}/api:latest --region=${REGION}"
    else
        warn "Migration job will be created on first deploy (needs image in registry first)."
        echo ""
        echo -e "  ${CYAN}After first image push, run:${NC}"
        echo "  gcloud run jobs create kliq-migrate \\"
        echo "    --image=${REGISTRY}/api:latest \\"
        echo "    --region=${REGION} \\"
        echo "    --service-account=${SERVICE_ACCOUNT} \\"
        echo "    --vpc-connector=${VPC_CONNECTOR} \\"
        echo "    --set-secrets=DATABASE_URL=DATABASE_URL:latest \\"
        echo "    --set-env-vars=APP_ENV=production \\"
        echo "    --command=alembic \\"
        echo "    --args=upgrade,head \\"
        echo "    --max-retries=1 \\"
        echo "    --task-timeout=300s"
    fi
    echo ""
}

# ── Step 9: Cloud Scheduler ────────────────────────────────────────────────

setup_cloud_scheduler() {
    info "Step 9/9: Setting up Cloud Scheduler jobs..."
    echo ""
    echo "  These jobs will be created after the API is deployed."
    echo "  You need the API URL first."
    echo ""
    read -rp "  Enter the API URL (e.g., https://kliq-growth-api-XXXXX.run.app), or press Enter to skip: " API_URL

    if [[ -z "${API_URL}" ]]; then
        warn "Skipping Cloud Scheduler setup. Run the commands below after deploying the API."
        echo ""
        echo -e "  ${CYAN}Replace <API_URL> and <SCHEDULER_SECRET> then run:${NC}"
        API_URL="<API_URL>"
        SCHED_SECRET="<SCHEDULER_SECRET>"
    else
        read -rsp "  Enter the SCHEDULER_SECRET value: " SCHED_SECRET
        echo ""
    fi

    JOBS=(
        "kliq-discovery|0 6 * * *|${API_URL}/api/scheduler/discovery|Daily coach discovery (6 AM UTC)"
        "kliq-outreach|*/30 * * * *|${API_URL}/api/scheduler/outreach|Process outreach queue (every 30 min)"
        "kliq-onboarding|15 */6 * * *|${API_URL}/api/scheduler/onboarding|Onboarding follow-up emails (every 6 hours)"
    )

    for job_def in "${JOBS[@]}"; do
        IFS='|' read -r job_name schedule endpoint description <<< "${job_def}"

        if [[ "${API_URL}" != "<API_URL>" ]]; then
            if gcloud scheduler jobs describe "${job_name}" --location="${REGION}" --format="value(name)" 2>/dev/null; then
                ok "  Scheduler job '${job_name}' already exists"
            else
                gcloud scheduler jobs create http "${job_name}" \
                    --location="${REGION}" \
                    --schedule="${schedule}" \
                    --uri="${endpoint}" \
                    --http-method=POST \
                    --headers="X-Scheduler-Secret=${SCHED_SECRET},Content-Type=application/json" \
                    --attempt-deadline=300s \
                    --description="${description}" \
                    --quiet
                ok "  Created scheduler job '${job_name}' (${schedule})"
            fi
        else
            echo ""
            echo "  gcloud scheduler jobs create http ${job_name} \\"
            echo "    --location=${REGION} \\"
            echo "    --schedule=\"${schedule}\" \\"
            echo "    --uri=${endpoint} \\"
            echo "    --http-method=POST \\"
            echo "    --headers=\"X-Scheduler-Secret=${SCHED_SECRET},Content-Type=application/json\" \\"
            echo "    --attempt-deadline=300s \\"
            echo "    --description=\"${description}\""
        fi
    done
    echo ""
}

# ── Summary ─────────────────────────────────────────────────────────────────

print_summary() {
    echo ""
    echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  Infrastructure setup complete!${NC}"
    echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "  Next steps:"
    echo ""
    echo "  1. Create an Upstash Redis instance at https://console.upstash.com"
    echo "     - Region: eu-west-1 (Ireland) for lowest latency to europe-west1"
    echo "     - Copy the Redis URL and store it:"
    echo "       echo -n 'redis://default:xxx@xxx.upstash.io:6379' | \\"
    echo "         gcloud secrets versions add REDIS_URL --data-file=-"
    echo ""
    echo "  2. Set all secret values in Secret Manager (if not done above):"
    echo "     gcloud secrets list"
    echo ""
    echo "  3. Add GitHub repo secrets at:"
    echo "     https://github.com/${GITHUB_ORG}/${GITHUB_REPO}/settings/secrets/actions"
    echo ""
    echo "     Required secrets:"
    echo "       WIF_PROVIDER        (printed above)"
    echo "       WIF_SERVICE_ACCOUNT (printed above)"
    echo ""
    echo "  4. First deploy — push an image manually, then create the migration job:"
    echo "     make build && make push"
    echo "     (then run the gcloud run jobs create command printed above)"
    echo ""
    echo "  5. After API deploys, set up Cloud Scheduler (if skipped above):"
    echo "     API_URL=\$(gcloud run services describe kliq-growth-api --region=${REGION} --format='value(status.url)')"
    echo "     Then re-run this script or use the commands printed above."
    echo ""
    echo "  6. Update Cloud Run services to use secrets + VPC connector:"
    echo "     For each service (kliq-growth-api, kliq-growth-worker, kliq-growth-dashboard):"
    echo ""
    echo "     gcloud run services update <SERVICE> \\"
    echo "       --region=${REGION} \\"
    echo "       --service-account=${SERVICE_ACCOUNT} \\"
    echo "       --vpc-connector=${VPC_CONNECTOR} \\"
    echo "       --set-secrets=DATABASE_URL=DATABASE_URL:latest,\\"
    echo "CMS_DATABASE_URL=CMS_DATABASE_URL:latest,\\"
    echo "REDIS_URL=REDIS_URL:latest,\\"
    echo "YOUTUBE_API_KEY=YOUTUBE_API_KEY:latest,\\"
    echo "ANTHROPIC_API_KEY=ANTHROPIC_API_KEY:latest,\\"
    echo "BREVO_API_KEY=BREVO_API_KEY:latest,\\"
    echo "AWS_ACCESS_KEY_ID=AWS_ACCESS_KEY_ID:latest,\\"
    echo "AWS_SECRET_ACCESS_KEY=AWS_SECRET_ACCESS_KEY:latest,\\"
    echo "APIFY_API_TOKEN=APIFY_API_TOKEN:latest,\\"
    echo "PATREON_CLIENT_ID=PATREON_CLIENT_ID:latest,\\"
    echo "PATREON_CLIENT_SECRET=PATREON_CLIENT_SECRET:latest,\\"
    echo "CLAIM_SECRET_KEY=CLAIM_SECRET_KEY:latest,\\"
    echo "SLACK_WEBHOOK_URL=SLACK_WEBHOOK_URL:latest,\\"
    echo "SCHEDULER_SECRET=SCHEDULER_SECRET:latest \\"
    echo "       --set-env-vars=APP_ENV=production,APP_DEBUG=false"
    echo ""
    echo -e "  Estimated monthly cost: ${CYAN}\$55–85/month${NC}"
    echo "    Cloud Run API:     \$5-15"
    echo "    Cloud Run Worker:  \$30-50"
    echo "    Cloud Run Dash:    \$2-5"
    echo "    Cloud SQL:         \$8-12"
    echo "    Upstash Redis:     Free tier"
    echo "    VPC Connector:     \$7"
    echo "    Misc:              \$3"
    echo ""
}

# ── Main ────────────────────────────────────────────────────────────────────

main() {
    confirm
    check_prerequisites
    enable_apis
    setup_artifact_registry
    setup_cloud_sql
    setup_vpc_connector
    setup_service_account
    setup_workload_identity
    setup_secrets
    setup_migration_job
    setup_cloud_scheduler
    print_summary
}

main "$@"
