"""
Cash Flow Report Generator

Pulls financial data from the local QuickBooks server (localhost:3456)
and generates a cash flow summary.
"""

import requests
import pandas as pd
from io import StringIO
from datetime import datetime, timedelta

QBO_SERVER = "http://localhost:3456"


def fetch_report(report_type, start_date, end_date, **kwargs):
    """Fetch a report from the QuickBooks server as a DataFrame."""
    payload = {
        "report_type": report_type,
        "start_date": start_date,
        "end_date": end_date,
        **kwargs,
    }
    resp = requests.post(f"{QBO_SERVER}/api/report", json=payload)
    resp.raise_for_status()
    return pd.read_csv(StringIO(resp.text))


def get_date_range():
    """Return start and end date for the current month."""
    today = datetime.today()
    start = today.replace(day=1).strftime("%Y-%m-%d")
    end = today.strftime("%Y-%m-%d")
    return start, end


def generate_cashflow_report():
    """Pull P&L and Balance Sheet, then print a cash flow summary."""
    start, end = get_date_range()
    print(f"Cash Flow Report: {start} to {end}\n")

    # Fetch Profit & Loss
    print("Fetching Profit & Loss...")
    pnl = fetch_report("profit_loss", start, end)
    print(pnl.to_string(index=False))

    print("\n" + "=" * 60 + "\n")

    # Fetch Balance Sheet
    print("Fetching Balance Sheet...")
    bs = fetch_report("balance_sheet", start, end)
    print(bs.to_string(index=False))


if __name__ == "__main__":
    generate_cashflow_report()
