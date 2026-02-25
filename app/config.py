from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application
    app_env: str = "development"
    app_debug: bool = True
    app_port: int = 8000

    # Growth Engine PostgreSQL
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/kliq_growth_engine"

    # RCWL-CMS MySQL (direct writes for store population)
    cms_database_url: str = "mysql+aiomysql://root:password@localhost:3306/rcwlcmsweb2022"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # YouTube Data API v3
    youtube_api_key: str = ""

    # Anthropic (Claude API)
    anthropic_api_key: str = ""

    # Brevo (Email)
    brevo_api_key: str = ""
    brevo_sender_email: str = "growth@joinkliq.io"
    brevo_sender_name: str = "KLIQ Growth Team"

    # AWS S3
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_s3_bucket: str = "dev-rcwl-assets"
    aws_s3_region: str = "eu-west-1"

    # Google BigQuery
    gcp_project_id: str = "rcwl-development"
    gcp_dataset: str = "powerbi_dashboard"
    google_application_credentials: str = "./service-account.json"

    # Apify (Skool scraping)
    apify_api_token: str = ""

    # Patreon API v2
    patreon_client_id: str = ""
    patreon_client_secret: str = ""

    # Claim Flow
    claim_base_url: str = "https://admin.joinkliq.io/claim"
    claim_secret_key: str = "change-me-in-production"

    # Rate Limits
    youtube_max_daily_units: int = 10000
    scrape_delay_seconds: int = 2
    max_concurrent_scrapes: int = 5

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
