#!/usr/bin/env bash
# =============================================================================
# KLIQ Growth Engine — GCP Infrastructure Setup (non-interactive)
# =============================================================================
#
# Run this script ONCE to set up all GCP resources before first deploy.
# Prerequisites: gcloud CLI authenticated with Owner/Editor on rcwl-development
#
# Usage:
#   # Full setup (skips Cloud Scheduler — no API URL yet):
#   CLOUD_SQL_PASSWORD=mypassword ./scripts/setup-gcp-infrastructure.sh
#
#   # With Cloud Scheduler (after first deploy):
#   API_URL=https://kliq-growth-api-xxx.run.app \
#   SCHEDULER_SECRET=mysecret \
#   ./scripts/setup-gcp-infrastructure.sh --scheduler-only
#
#   # Dry run — prints commands without executing:
#   ./scripts/setup-gcp-infrastructure.sh --dry-run
#
#   # Skip specific steps:
#   SKIP_CLOUD_SQL=1 SKIP_VPC=1 ./scripts/setup-gcp-infrastructure.sh
#
# Environment variables:
#   CLOUD_SQL_PASSWORD  (required for Cloud SQL user creation)
#   API_URL             (optional — Cloud Scheduler endpoint base URL)
#   SCHEDULER_SECRET    (optional — required if API_URL is set)
#   SKIP_APIS=1         Skip enabling APIs
#   SKIP_REGISTRY=1     Skip Artifact Registry
#   SKIP_CLOUD_SQL=1    Skip Cloud SQL
#   SKIP_VPC=1          Skip VPC Connector
#   SKIP_SA=1           Skip Service Account
#   SKIP_WIF=1          Skip Workload Identity Federation
#   SKIP_SECRETS=1      Skip Secret Manager
#   SKIP_MIGRATE=1      Skip Migration Job
#   SKIP_SCHEDULER=1    Skip Cloud Scheduler
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

# From environment
CLOUD_SQL_PASSWORD="${CLOUD_SQL_PASSWORD:-}"
API_URL="${API_URL:-}"
SCHEDULER_SECRET="${SCHEDULER_SECRET:-}"
DRY_RUN=false
SCHEDULER_ONLY=false

# ── Parse arguments ──────────────────────────────────────────────────────────

for arg in "$@"; do
    case "$arg" in
        --dry-run)      DRY_RUN=true ;;
        --scheduler-only) SCHEDULER_ONLY=true ;;
        --help|-h)
            head -37 "$0" | tail -35
            exit 0
            ;;
        *) echo "Unknown argument: $arg"; exit 1 ;;
    esac
done

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

run() {
    if [[ "$DRY_RUN" == true ]]; then
        echo -e "  ${YELLOW}[DRY-RUN]${NC} $*"
    else
        eval "$@"
    fi
}

skip() {
    local var="SKIP_$1"
    [[ "${!var:-}" == "1" ]]
}

# ── Pre-flight checks ───────────────────────────────────────────────────────

check_prerequisites() {
    info "Checking prerequisites..."

    if ! command -v gcloud >/dev/null 2>&1; then
        if [[ "$DRY_RUN" == true ]]; then
            warn "gcloud CLI not installed — dry-run will print commands only"
        else
            error "gcloud CLI not installed. See https://cloud.google.com/sdk/docs/install"
        fi
    fi

    if [[ "$DRY_RUN" == false ]]; then
        CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null)
        if [[ "${CURRENT_PROJECT}" != "${PROJECT_ID}" ]]; then
            warn "Current project is '${CURRENT_PROJECT}', switching to '${PROJECT_ID}'"
            gcloud config set project "${PROJECT_ID}"
        fi
    fi
    ok "gcloud configured for project ${PROJECT_ID}"

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
    echo "  Dry run:       ${DRY_RUN}"
    echo ""
}

# ── Step 1: Enable required APIs ────────────────────────────────────────────

enable_apis() {
    if skip APIS; then warn "Skipping API enablement (SKIP_APIS=1)"; return; fi
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
        run "gcloud services enable '${api}' --quiet 2>/dev/null" && ok "  ${api}" || warn "  ${api} (may already be enabled)"
    done
}

# ── Step 2: Artifact Registry ───────────────────────────────────────────────

setup_artifact_registry() {
    if skip REGISTRY; then warn "Skipping Artifact Registry (SKIP_REGISTRY=1)"; return; fi
    info "Step 2/9: Setting up Artifact Registry..."

    if [[ "$DRY_RUN" == false ]] && gcloud artifacts repositories describe "${REGISTRY_NAME}" \
        --location="${REGION}" --format="value(name)" 2>/dev/null; then
        ok "Artifact Registry '${REGISTRY_NAME}' already exists"
    else
        run "gcloud artifacts repositories create '${REGISTRY_NAME}' \
            --repository-format=docker \
            --location='${REGION}' \
            --description='KLIQ Growth Engine Docker images'"
        ok "Created Artifact Registry '${REGISTRY_NAME}'"
    fi
}

# ── Step 3: Cloud SQL PostgreSQL ────────────────────────────────────────────

setup_cloud_sql() {
    if skip CLOUD_SQL; then warn "Skipping Cloud SQL (SKIP_CLOUD_SQL=1)"; return; fi
    info "Step 3/9: Setting up Cloud SQL PostgreSQL..."

    if [[ -z "${CLOUD_SQL_PASSWORD}" ]]; then
        if [[ "$DRY_RUN" == true ]]; then
            CLOUD_SQL_PASSWORD="<PASSWORD>"
        else
            error "CLOUD_SQL_PASSWORD env var is required. Usage: CLOUD_SQL_PASSWORD=mypassword $0"
        fi
    fi

    # Create instance
    if [[ "$DRY_RUN" == false ]] && gcloud sql instances describe "${CLOUD_SQL_INSTANCE}" --format="value(name)" 2>/dev/null; then
        ok "Cloud SQL instance '${CLOUD_SQL_INSTANCE}' already exists"
    else
        warn "Creating Cloud SQL instance (this takes 3-5 minutes)..."
        run "gcloud sql instances create '${CLOUD_SQL_INSTANCE}' \
            --database-version=POSTGRES_15 \
            --tier='${CLOUD_SQL_TIER}' \
            --region='${REGION}' \
            --storage-type=SSD \
            --storage-size=10GB \
            --no-assign-ip \
            --network=default \
            --quiet"
        ok "Created Cloud SQL instance '${CLOUD_SQL_INSTANCE}'"
    fi

    # Create database
    if [[ "$DRY_RUN" == false ]] && gcloud sql databases describe "${CLOUD_SQL_DB}" \
        --instance="${CLOUD_SQL_INSTANCE}" --format="value(name)" 2>/dev/null; then
        ok "Database '${CLOUD_SQL_DB}' already exists"
    else
        run "gcloud sql databases create '${CLOUD_SQL_DB}' \
            --instance='${CLOUD_SQL_INSTANCE}'"
        ok "Created database '${CLOUD_SQL_DB}'"
    fi

    # Create user
    run "gcloud sql users create '${CLOUD_SQL_USER}' \
        --instance='${CLOUD_SQL_INSTANCE}' \
        --password='${CLOUD_SQL_PASSWORD}' 2>/dev/null" \
        && ok "Created user '${CLOUD_SQL_USER}'" \
        || warn "User '${CLOUD_SQL_USER}' may already exist"

    # Get connection name
    if [[ "$DRY_RUN" == false ]]; then
        CONNECTION_NAME=$(gcloud sql instances describe "${CLOUD_SQL_INSTANCE}" \
            --format="value(connectionName)")
        ok "Cloud SQL connection name: ${CONNECTION_NAME}"
        echo ""
        echo -e "  ${CYAN}DATABASE_URL for production:${NC}"
        echo "  postgresql+asyncpg://${CLOUD_SQL_USER}:${CLOUD_SQL_PASSWORD}@/${CLOUD_SQL_DB}?host=/cloudsql/${CONNECTION_NAME}"
        echo ""
    fi
}

# ── Step 4: VPC Connector ──────────────────────────────────────────────────

setup_vpc_connector() {
    if skip VPC; then warn "Skipping VPC Connector (SKIP_VPC=1)"; return; fi
    info "Step 4/9: Setting up VPC Connector..."

    if [[ "$DRY_RUN" == false ]] && gcloud compute networks vpc-access connectors describe "${VPC_CONNECTOR}" \
        --region="${REGION}" --format="value(name)" 2>/dev/null; then
        ok "VPC Connector '${VPC_CONNECTOR}' already exists"
    else
        run "gcloud compute networks vpc-access connectors create '${VPC_CONNECTOR}' \
            --region='${REGION}' \
            --range='10.8.0.0/28' \
            --min-instances=2 \
            --max-instances=3"
        ok "Created VPC Connector '${VPC_CONNECTOR}'"
    fi
}

# ── Step 5: Service Account ────────────────────────────────────────────────

setup_service_account() {
    if skip SA; then warn "Skipping Service Account (SKIP_SA=1)"; return; fi
    info "Step 5/9: Setting up Service Account..."

    if [[ "$DRY_RUN" == false ]] && gcloud iam service-accounts describe "${SERVICE_ACCOUNT}" --format="value(email)" 2>/dev/null; then
        ok "Service account '${SERVICE_ACCOUNT}' already exists"
    else
        run "gcloud iam service-accounts create '${SERVICE_ACCOUNT_NAME}' \
            --display-name='KLIQ Growth Engine'"
        ok "Created service account '${SERVICE_ACCOUNT}'"
    fi

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
        run "gcloud projects add-iam-policy-binding '${PROJECT_ID}' \
            --member='serviceAccount:${SERVICE_ACCOUNT}' \
            --role='${role}' \
            --condition=None \
            --quiet 2>/dev/null"
        ok "    ${role}"
    done
}

# ── Step 6: Workload Identity Federation ────────────────────────────────────

setup_workload_identity() {
    if skip WIF; then warn "Skipping Workload Identity Federation (SKIP_WIF=1)"; return; fi
    info "Step 6/9: Setting up Workload Identity Federation (GitHub -> GCP)..."

    # Create workload identity pool
    if [[ "$DRY_RUN" == false ]] && gcloud iam workload-identity-pools describe "${WIF_POOL}" \
        --location="global" --format="value(name)" 2>/dev/null; then
        ok "Workload Identity Pool '${WIF_POOL}' already exists"
    else
        run "gcloud iam workload-identity-pools create '${WIF_POOL}' \
            --location='global' \
            --display-name='GitHub Actions Pool'"
        ok "Created Workload Identity Pool '${WIF_POOL}'"
    fi

    # Create OIDC provider
    if [[ "$DRY_RUN" == false ]] && gcloud iam workload-identity-pools providers describe "${WIF_PROVIDER}" \
        --workload-identity-pool="${WIF_POOL}" \
        --location="global" --format="value(name)" 2>/dev/null; then
        ok "Workload Identity Provider '${WIF_PROVIDER}' already exists"
    else
        run "gcloud iam workload-identity-pools providers create-oidc '${WIF_PROVIDER}' \
            --location='global' \
            --workload-identity-pool='${WIF_POOL}' \
            --display-name='GitHub OIDC Provider' \
            --issuer-uri='https://token.actions.githubusercontent.com' \
            --attribute-mapping='google.subject=assertion.sub,attribute.repository=assertion.repository' \
            --attribute-condition=\"assertion.repository == '${GITHUB_ORG}/${GITHUB_REPO}'\""
        ok "Created Workload Identity Provider '${WIF_PROVIDER}'"
    fi

    # Allow GitHub repo to impersonate the service account
    if [[ "$DRY_RUN" == false ]]; then
        WIF_POOL_ID=$(gcloud iam workload-identity-pools describe "${WIF_POOL}" \
            --location="global" --format="value(name)")
    else
        WIF_POOL_ID="projects/${PROJECT_ID}/locations/global/workloadIdentityPools/${WIF_POOL}"
    fi

    run "gcloud iam service-accounts add-iam-policy-binding '${SERVICE_ACCOUNT}' \
        --role='roles/iam.workloadIdentityUser' \
        --member='principalSet://iam.googleapis.com/${WIF_POOL_ID}/attribute.repository/${GITHUB_ORG}/${GITHUB_REPO}' \
        --quiet 2>/dev/null"
    ok "Linked GitHub ${GITHUB_ORG}/${GITHUB_REPO} -> ${SERVICE_ACCOUNT}"

    # Deploy permissions
    run "gcloud projects add-iam-policy-binding '${PROJECT_ID}' \
        --member='serviceAccount:${SERVICE_ACCOUNT}' \
        --role='roles/run.admin' \
        --condition=None \
        --quiet 2>/dev/null"

    run "gcloud projects add-iam-policy-binding '${PROJECT_ID}' \
        --member='serviceAccount:${SERVICE_ACCOUNT}' \
        --role='roles/artifactregistry.writer' \
        --condition=None \
        --quiet 2>/dev/null"

    run "gcloud iam service-accounts add-iam-policy-binding '${SERVICE_ACCOUNT}' \
        --role='roles/iam.serviceAccountUser' \
        --member='serviceAccount:${SERVICE_ACCOUNT}' \
        --quiet 2>/dev/null"
    ok "Granted deploy permissions to service account"

    # Print values for GitHub secrets
    if [[ "$DRY_RUN" == false ]]; then
        PROVIDER_FULL=$(gcloud iam workload-identity-pools providers describe "${WIF_PROVIDER}" \
            --workload-identity-pool="${WIF_POOL}" \
            --location="global" --format="value(name)")
    else
        PROVIDER_FULL="projects/${PROJECT_ID}/locations/global/workloadIdentityPools/${WIF_POOL}/providers/${WIF_PROVIDER}"
    fi

    echo ""
    echo -e "  ${CYAN}Add these as GitHub repo secrets:${NC}"
    echo "  WIF_PROVIDER:        ${PROVIDER_FULL}"
    echo "  WIF_SERVICE_ACCOUNT: ${SERVICE_ACCOUNT}"
    echo ""
}

# ── Step 7: Secret Manager ─────────────────────────────────────────────────

setup_secrets() {
    if skip SECRETS; then warn "Skipping Secret Manager (SKIP_SECRETS=1)"; return; fi
    info "Step 7/9: Setting up Secret Manager (creating empty secrets)..."

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

    for secret in "${SECRETS[@]}"; do
        if [[ "$DRY_RUN" == false ]] && gcloud secrets describe "${secret}" --format="value(name)" 2>/dev/null; then
            ok "  Secret '${secret}' already exists"
        else
            run "gcloud secrets create '${secret}' --replication-policy='automatic' --quiet"
            ok "  Created secret '${secret}'"
        fi
    done

    echo ""
    echo -e "  ${CYAN}Set secret values with:${NC}"
    echo "  echo -n 'your-value' | gcloud secrets versions add SECRET_NAME --data-file=-"
    echo ""
}

# ── Step 8: Cloud Run Migration Job ────────────────────────────────────────

setup_migration_job() {
    if skip MIGRATE; then warn "Skipping Migration Job (SKIP_MIGRATE=1)"; return; fi
    info "Step 8/9: Setting up Cloud Run Migration Job..."

    if [[ "$DRY_RUN" == false ]] && gcloud run jobs describe kliq-migrate --region="${REGION}" --format="value(name)" 2>/dev/null; then
        ok "Cloud Run Job 'kliq-migrate' already exists"
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
    if skip SCHEDULER; then warn "Skipping Cloud Scheduler (SKIP_SCHEDULER=1)"; return; fi
    info "Step 9/9: Setting up Cloud Scheduler jobs..."

    if [[ -z "${API_URL}" ]]; then
        warn "Skipping Cloud Scheduler — API_URL not set."
        echo "  Re-run with: API_URL=https://kliq-growth-api-xxx.run.app SCHEDULER_SECRET=xxx $0 --scheduler-only"
        echo ""
        return
    fi

    if [[ -z "${SCHEDULER_SECRET}" ]]; then
        error "SCHEDULER_SECRET env var is required when API_URL is set."
    fi

    JOBS=(
        "kliq-discovery|0 6 * * *|${API_URL}/api/scheduler/discovery|Daily coach discovery (6 AM UTC)"
        "kliq-outreach|*/30 * * * *|${API_URL}/api/scheduler/outreach|Process outreach queue (every 30 min)"
        "kliq-onboarding|15 */6 * * *|${API_URL}/api/scheduler/onboarding|Onboarding follow-up emails (every 6 hours)"
    )

    for job_def in "${JOBS[@]}"; do
        IFS='|' read -r job_name schedule endpoint description <<< "${job_def}"

        if [[ "$DRY_RUN" == false ]] && gcloud scheduler jobs describe "${job_name}" --location="${REGION}" --format="value(name)" 2>/dev/null; then
            ok "  Scheduler job '${job_name}' already exists"
        else
            run "gcloud scheduler jobs create http '${job_name}' \
                --location='${REGION}' \
                --schedule='${schedule}' \
                --uri='${endpoint}' \
                --http-method=POST \
                --headers='X-Scheduler-Secret=${SCHEDULER_SECRET},Content-Type=application/json' \
                --attempt-deadline=300s \
                --description='${description}' \
                --quiet"
            ok "  Created scheduler job '${job_name}' (${schedule})"
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
    echo "  2. Set all secret values in Secret Manager:"
    echo "     gcloud secrets list"
    echo "     echo -n 'value' | gcloud secrets versions add SECRET_NAME --data-file=-"
    echo ""
    echo "  3. Add GitHub repo secrets at:"
    echo "     https://github.com/${GITHUB_ORG}/${GITHUB_REPO}/settings/secrets/actions"
    echo "     WIF_PROVIDER        (printed above)"
    echo "     WIF_SERVICE_ACCOUNT (printed above)"
    echo ""
    echo "  4. First deploy — push an image manually, then create the migration job:"
    echo "     make build && make push"
    echo ""
    if [[ -z "${API_URL}" ]]; then
        echo "  5. After API deploys, set up Cloud Scheduler:"
        echo "     API_URL=\$(gcloud run services describe kliq-growth-api --region=${REGION} --format='value(status.url)') \\"
        echo "     SCHEDULER_SECRET=your-secret \\"
        echo "     $0 --scheduler-only"
        echo ""
    fi
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
    echo -e "  Estimated monthly cost: ${CYAN}\$55-85/month${NC}"
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
    check_prerequisites

    if [[ "$SCHEDULER_ONLY" == true ]]; then
        setup_cloud_scheduler
        ok "Cloud Scheduler setup done."
        return
    fi

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
