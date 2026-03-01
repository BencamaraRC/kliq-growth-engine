"""Analyze Stripe disputes from BigQuery and print status report.

Queries the kliq_data_lake.stripe_disputes table loaded by
load_disputes_to_bq.py and prints a comprehensive analysis.

Usage:
    cd kliq-growth-engine
    python scripts/analyze_disputes.py
"""

import os
import sys

from google.cloud import bigquery
from google.oauth2 import service_account

# --- Config ---
PROJECT_ID = "rcwl-development"
DATASET_ID = "sentinel"
TABLE_ID = "stripe_disputes"
TABLE = f"`{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`"

SA_PATH = os.path.join(os.path.dirname(__file__), "..", "service-account.json")
SA_PATH = os.path.abspath(SA_PATH)
if not os.path.exists(SA_PATH):
    SA_PATH = os.path.expanduser("~/Downloads/rcwl-development-70f5fda64cb3.json")


def get_client():
    if not os.path.exists(SA_PATH):
        print(f"ERROR: Service account not found at {SA_PATH}")
        sys.exit(1)
    credentials = service_account.Credentials.from_service_account_file(
        SA_PATH, scopes=["https://www.googleapis.com/auth/bigquery"]
    )
    return bigquery.Client(project=PROJECT_ID, credentials=credentials)


def query(client, sql):
    return list(client.query(sql).result())


def fmt_money(val, currency="USD"):
    if val is None:
        return "$0.00"
    sym = {"USD": "$", "GBP": "£", "EUR": "€"}.get(currency.upper(), "$")
    return f"{sym}{val:,.2f}"


def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def main():
    client = get_client()
    print("KLIQ Dispute Analysis Report")
    print(f"Data source: {PROJECT_ID}.{DATASET_ID}.{TABLE_ID}")

    # 1. Summary
    print_header("1. SUMMARY")
    rows = query(client, f"""
        SELECT
            COUNT(*) as total_disputes,
            ROUND(SUM(dispute_amount), 2) as total_amount,
            COUNT(DISTINCT customer_email) as unique_customers,
            COUNT(DISTINCT account_id) as unique_accounts,
            MIN(dispute_created_utc) as earliest,
            MAX(dispute_created_utc) as latest
        FROM {TABLE}
    """)
    r = rows[0]
    print(f"  Total disputes:     {r.total_disputes}")
    print(f"  Total $ at risk:    {fmt_money(r.total_amount)}")
    print(f"  Unique customers:   {r.unique_customers}")
    print(f"  Unique accounts:    {r.unique_accounts}")
    print(f"  Date range:         {r.earliest.strftime('%Y-%m-%d')} to {r.latest.strftime('%Y-%m-%d')}")

    # 2. By Status
    print_header("2. BY STATUS")
    rows = query(client, f"""
        SELECT
            status,
            COUNT(*) as count,
            ROUND(SUM(dispute_amount), 2) as total_amount,
            ROUND(AVG(dispute_amount), 2) as avg_amount
        FROM {TABLE}
        GROUP BY status
        ORDER BY count DESC
    """)
    print(f"  {'Status':<20} {'Count':>6} {'Total':>12} {'Avg':>10}")
    print(f"  {'-'*48}")
    for r in rows:
        print(f"  {r.status:<20} {r.count:>6} {fmt_money(r.total_amount):>12} {fmt_money(r.avg_amount):>10}")

    # 3. By Reason
    print_header("3. BY REASON")
    rows = query(client, f"""
        SELECT
            reason,
            COUNT(*) as count,
            ROUND(SUM(dispute_amount), 2) as total_amount,
            COUNTIF(status = 'won') as won,
            COUNTIF(status = 'lost') as lost,
            COUNTIF(status = 'needs_response') as pending
        FROM {TABLE}
        GROUP BY reason
        ORDER BY count DESC
    """)
    print(f"  {'Reason':<25} {'Count':>5} {'Total':>11} {'Won':>5} {'Lost':>5} {'Pend':>5}")
    print(f"  {'-'*56}")
    for r in rows:
        print(f"  {r.reason:<25} {r.count:>5} {fmt_money(r.total_amount):>11} {r.won:>5} {r.lost:>5} {r.pending:>5}")

    # 4. By Account (Coach)
    print_header("4. BY ACCOUNT (Top 15)")
    rows = query(client, f"""
        SELECT
            account_id,
            COUNT(*) as count,
            ROUND(SUM(dispute_amount), 2) as total_amount,
            COUNT(DISTINCT customer_email) as unique_customers,
            COUNT(DISTINCT reason) as reason_types
        FROM {TABLE}
        GROUP BY account_id
        ORDER BY count DESC
        LIMIT 15
    """)
    print(f"  {'Account ID':<28} {'#':>4} {'Total':>11} {'Cust':>5} {'Reasons':>7}")
    print(f"  {'-'*55}")
    for r in rows:
        print(f"  {r.account_id:<28} {r.count:>4} {fmt_money(r.total_amount):>11} {r.unique_customers:>5} {r.reason_types:>7}")

    # 5. Serial Disputers
    print_header("5. SERIAL DISPUTERS (3+ disputes from same card)")
    rows = query(client, f"""
        SELECT
            card_fingerprint,
            customer_email,
            COUNT(*) as dispute_count,
            ROUND(SUM(dispute_amount), 2) as total_amount,
            STRING_AGG(DISTINCT reason, ', ') as reasons,
            STRING_AGG(DISTINCT account_id, ', ') as accounts
        FROM {TABLE}
        WHERE card_fingerprint IS NOT NULL AND card_fingerprint != ''
        GROUP BY card_fingerprint, customer_email
        HAVING COUNT(*) >= 3
        ORDER BY dispute_count DESC
    """)
    if rows:
        print(f"  {'Email':<35} {'#':>3} {'Total':>10} {'Reasons'}")
        print(f"  {'-'*70}")
        for r in rows:
            email = r.customer_email or "(unknown)"
            if len(email) > 33:
                email = email[:30] + "..."
            print(f"  {email:<35} {r.dispute_count:>3} {fmt_money(r.total_amount):>10} {r.reasons}")
    else:
        print("  No serial disputers found.")

    # 6. Monthly Trends
    print_header("6. MONTHLY TRENDS")
    rows = query(client, f"""
        SELECT
            FORMAT_TIMESTAMP('%Y-%m', dispute_created_utc) as month,
            COUNT(*) as count,
            ROUND(SUM(dispute_amount), 2) as total_amount
        FROM {TABLE}
        GROUP BY month
        ORDER BY month
    """)
    print(f"  {'Month':<10} {'Count':>6} {'Total':>12}")
    print(f"  {'-'*28}")
    for r in rows:
        bar = "#" * r.count
        print(f"  {r.month:<10} {r.count:>6} {fmt_money(r.total_amount):>12}  {bar}")

    # 7. Win Rate
    print_header("7. WIN RATE")
    rows = query(client, f"""
        SELECT
            reason,
            COUNT(*) as total,
            COUNTIF(status = 'won') as won,
            ROUND(SAFE_DIVIDE(COUNTIF(status = 'won'), COUNT(*)) * 100, 1) as win_pct,
            COUNTIF(has_evidence = true) as with_evidence,
            COUNTIF(submission_count > 0) as with_submissions
        FROM {TABLE}
        WHERE status IN ('won', 'lost')
        GROUP BY reason
        ORDER BY total DESC
    """)
    # Overall
    total_decided = sum(r.total for r in rows)
    total_won = sum(r.won for r in rows)
    overall_pct = (total_won / total_decided * 100) if total_decided > 0 else 0
    print(f"  Overall: {total_won}/{total_decided} ({overall_pct:.1f}%)")
    print()
    print(f"  {'Reason':<25} {'W/L':>7} {'Win%':>6} {'Evidence':>8} {'Submissions':>11}")
    print(f"  {'-'*57}")
    for r in rows:
        wl = f"{r.won}/{r.total}"
        print(f"  {r.reason:<25} {wl:>7} {r.win_pct:>5.1f}% {r.with_evidence:>8} {r.with_submissions:>11}")

    # 8. Currency Breakdown
    print_header("8. CURRENCY BREAKDOWN")
    rows = query(client, f"""
        SELECT
            UPPER(dispute_currency) as currency,
            COUNT(*) as count,
            ROUND(SUM(dispute_amount), 2) as total_amount
        FROM {TABLE}
        GROUP BY currency
        ORDER BY count DESC
    """)
    for r in rows:
        print(f"  {r.currency}: {r.count} disputes, {fmt_money(r.total_amount, r.currency)}")

    # 9. Evidence Gaps
    print_header("9. EVIDENCE GAPS (needs_response + no evidence)")
    rows = query(client, f"""
        SELECT
            dispute_id,
            customer_email,
            dispute_amount,
            dispute_currency,
            reason,
            due_by_utc
        FROM {TABLE}
        WHERE status = 'needs_response' AND has_evidence = false
        ORDER BY due_by_utc ASC
    """)
    if rows:
        print(f"  {len(rows)} disputes need evidence submission:\n")
        print(f"  {'Dispute ID':<30} {'Amount':>8} {'Reason':<22} {'Due By':<12}")
        print(f"  {'-'*72}")
        for r in rows:
            due = r.due_by_utc.strftime('%Y-%m-%d') if r.due_by_utc else "N/A"
            amt = fmt_money(r.dispute_amount, r.dispute_currency)
            print(f"  {r.dispute_id:<30} {amt:>8} {r.reason:<22} {due:<12}")
    else:
        print("  All pending disputes have evidence submitted.")

    # 10. Urgent — needs_response with due dates
    print_header("10. URGENT — Approaching Deadlines")
    rows = query(client, f"""
        SELECT
            dispute_id,
            customer_email,
            dispute_amount,
            dispute_currency,
            reason,
            due_by_utc,
            TIMESTAMP_DIFF(due_by_utc, CURRENT_TIMESTAMP(), DAY) as days_remaining
        FROM {TABLE}
        WHERE status = 'needs_response'
            AND due_by_utc IS NOT NULL
        ORDER BY due_by_utc ASC
    """)
    if rows:
        print(f"  {len(rows)} disputes with needs_response status:\n")
        print(f"  {'Dispute ID':<30} {'Amount':>8} {'Days Left':>9} {'Due By':<12}")
        print(f"  {'-'*59}")
        for r in rows:
            due = r.due_by_utc.strftime('%Y-%m-%d') if r.due_by_utc else "N/A"
            amt = fmt_money(r.dispute_amount, r.dispute_currency)
            days = r.days_remaining if r.days_remaining is not None else "?"
            urgency = " ⚠️" if isinstance(days, int) and days <= 7 else ""
            print(f"  {r.dispute_id:<30} {amt:>8} {days:>9} {due:<12}{urgency}")
    else:
        print("  No pending disputes with deadlines.")

    print(f"\n{'='*60}")
    print("  Report complete.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
