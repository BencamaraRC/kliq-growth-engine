"""Load Stripe disputes CSV into BigQuery.

Creates dataset `sentinel` and table `stripe_disputes` in the
rcwl-development GCP project. Idempotent — re-running overwrites the table.

Usage:
    cd kliq-growth-engine
    python scripts/load_disputes_to_bq.py
"""

import os
import sys

import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account

# --- Config ---
PROJECT_ID = "rcwl-development"
DATASET_ID = "sentinel"
TABLE_ID = "stripe_disputes"
FULL_TABLE_ID = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"

CSV_PATH = os.path.expanduser(
    "~/Downloads/Disputes_Export_Query_2022-12-01_to_2026-03-01.csv"
)

# Service account — try project-local first, then known GCP keys
SA_PATH = os.path.join(os.path.dirname(__file__), "..", "service-account.json")
SA_PATH = os.path.abspath(SA_PATH)
if not os.path.exists(SA_PATH):
    SA_PATH = os.path.expanduser("~/Downloads/rcwl-development-70f5fda64cb3.json")

# --- Column mapping: CSV header -> BigQuery column name ---
COLUMN_MAP = {
    "id": "dispute_id",
    "Description": "description",
    "Dispute Created (UTC)": "dispute_created_utc",
    "Charge Created (UTC)": "charge_created_utc",
    "Dispute Amount": "dispute_amount",
    "Dispute Currency": "dispute_currency",
    "Charge Amount": "charge_amount",
    "Charge Currency": "charge_currency",
    "Charge ID": "charge_id",
    "Card Fingerprint": "card_fingerprint",
    "Card Brand": "card_brand",
    "Card Funding": "card_funding",
    "Customer Email": "customer_email",
    "Customer ID": "customer_id",
    "Reason": "reason",
    "Status": "status",
    "Due By (UTC)": "due_by_utc",
    "Past Due": "past_due",
    "Has Evidence": "has_evidence",
    "Submission Count": "submission_count",
    "Is Charge Refundable": "is_charge_refundable",
    "Amount Refunded": "amount_refunded",
    "Win Likelihood": "win_likelihood",
    "Is Visa Rapid Dispute Resolution": "is_visa_rapid_dispute_resolution",
    "Visa Compelling Evidence 3 Status": "visa_ce3_status",
    "Visa Compliance Status": "visa_compliance_status",
    "Payment Method Type": "payment_method_type",
    "Payment Intent": "payment_intent",
    "Account ID": "account_id",
}

# BigQuery schema
SCHEMA = [
    bigquery.SchemaField("dispute_id", "STRING"),
    bigquery.SchemaField("description", "STRING"),
    bigquery.SchemaField("dispute_created_utc", "TIMESTAMP"),
    bigquery.SchemaField("charge_created_utc", "TIMESTAMP"),
    bigquery.SchemaField("dispute_amount", "FLOAT"),
    bigquery.SchemaField("dispute_currency", "STRING"),
    bigquery.SchemaField("charge_amount", "FLOAT"),
    bigquery.SchemaField("charge_currency", "STRING"),
    bigquery.SchemaField("charge_id", "STRING"),
    bigquery.SchemaField("card_fingerprint", "STRING"),
    bigquery.SchemaField("card_brand", "STRING"),
    bigquery.SchemaField("card_funding", "STRING"),
    bigquery.SchemaField("customer_email", "STRING"),
    bigquery.SchemaField("customer_id", "STRING"),
    bigquery.SchemaField("reason", "STRING"),
    bigquery.SchemaField("status", "STRING"),
    bigquery.SchemaField("due_by_utc", "TIMESTAMP"),
    bigquery.SchemaField("past_due", "BOOLEAN"),
    bigquery.SchemaField("has_evidence", "BOOLEAN"),
    bigquery.SchemaField("submission_count", "INTEGER"),
    bigquery.SchemaField("is_charge_refundable", "BOOLEAN"),
    bigquery.SchemaField("amount_refunded", "FLOAT"),
    bigquery.SchemaField("win_likelihood", "STRING"),
    bigquery.SchemaField("is_visa_rapid_dispute_resolution", "BOOLEAN"),
    bigquery.SchemaField("visa_ce3_status", "STRING"),
    bigquery.SchemaField("visa_compliance_status", "STRING"),
    bigquery.SchemaField("payment_method_type", "STRING"),
    bigquery.SchemaField("payment_intent", "STRING"),
    bigquery.SchemaField("account_id", "STRING"),
]


def parse_bool(val):
    """Convert string 'true'/'false' to Python bool."""
    if pd.isna(val) or val == "":
        return None
    return str(val).lower() == "true"


def parse_timestamp(val):
    """Parse CSV timestamp string to pandas Timestamp."""
    if pd.isna(val) or val == "":
        return pd.NaT
    return pd.to_datetime(val, format="%Y-%m-%d %H:%M", utc=True)


def parse_int(val):
    """Parse integer, returning None for empty strings."""
    if pd.isna(val) or val == "":
        return None
    return int(val)


def parse_float(val):
    """Parse float, returning None for empty strings."""
    if pd.isna(val) or val == "":
        return None
    return float(val)


def main():
    # Verify service account exists
    if not os.path.exists(SA_PATH):
        print(f"ERROR: Service account not found at {SA_PATH}")
        print("Copy your GCP service account JSON there to proceed.")
        sys.exit(1)

    # Verify CSV exists
    if not os.path.exists(CSV_PATH):
        print(f"ERROR: CSV not found at {CSV_PATH}")
        sys.exit(1)

    # Auth
    credentials = service_account.Credentials.from_service_account_file(
        SA_PATH, scopes=["https://www.googleapis.com/auth/bigquery"]
    )
    client = bigquery.Client(project=PROJECT_ID, credentials=credentials)
    print(f"Authenticated as {credentials.service_account_email}")

    # Create dataset if not exists
    dataset_ref = bigquery.DatasetReference(PROJECT_ID, DATASET_ID)
    dataset = bigquery.Dataset(dataset_ref)
    dataset.location = "US"
    dataset = client.create_dataset(dataset, exists_ok=True)
    print(f"Dataset ready: {PROJECT_ID}.{DATASET_ID}")

    # Read CSV
    df = pd.read_csv(CSV_PATH)
    print(f"Read {len(df)} rows from CSV")

    # Rename columns
    df = df.rename(columns=COLUMN_MAP)

    # Parse types
    bool_cols = [
        "past_due",
        "has_evidence",
        "is_charge_refundable",
        "is_visa_rapid_dispute_resolution",
    ]
    for col in bool_cols:
        df[col] = df[col].apply(parse_bool)

    ts_cols = ["dispute_created_utc", "charge_created_utc", "due_by_utc"]
    for col in ts_cols:
        df[col] = df[col].apply(parse_timestamp)

    df["submission_count"] = df["submission_count"].apply(parse_int)
    df["dispute_amount"] = df["dispute_amount"].apply(parse_float)
    df["charge_amount"] = df["charge_amount"].apply(parse_float)
    df["amount_refunded"] = df["amount_refunded"].apply(parse_float)

    # Ensure win_likelihood is string (pandas reads empty/numeric mix as float)
    df["win_likelihood"] = df["win_likelihood"].apply(
        lambda v: str(int(v)) if pd.notna(v) and v != "" else None
    )

    # Replace NaN with None for string columns
    str_cols = [
        "dispute_id", "description", "dispute_currency", "charge_currency",
        "charge_id", "card_fingerprint", "card_brand", "card_funding",
        "customer_email", "customer_id", "reason", "status",
        "visa_ce3_status", "visa_compliance_status",
        "payment_method_type", "payment_intent", "account_id",
    ]
    for col in str_cols:
        df[col] = df[col].where(df[col].notna(), None)

    # Load to BigQuery
    job_config = bigquery.LoadJobConfig(
        schema=SCHEMA,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )

    job = client.load_table_from_dataframe(df, FULL_TABLE_ID, job_config=job_config)
    job.result()  # Wait for completion

    table = client.get_table(FULL_TABLE_ID)
    print(f"Loaded {table.num_rows} rows to {FULL_TABLE_ID}")


if __name__ == "__main__":
    main()
