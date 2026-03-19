"""
Cash Flow Local Server

Serves the cash flow page and provides an API endpoint
to parse credit card PDFs and fetch live exchange rates.
"""

import re
import os
import glob
import json
from datetime import datetime

import requests
import fitz  # pymupdf
from flask import Flask, jsonify, send_file

app = Flask(__name__)

SOA_DIR = os.path.expanduser("~/Downloads/SOA")
HTML_FILE = os.path.join(os.path.dirname(__file__), "index.html")

CARD_NAMES = {
    "0889": "Chase Ink 0889",
    "4719": "Chase Ink 4719",
    "4462": "Chase Hyatt 4462",
    "8537": "Chase 8537",
}


def parse_chase_pdf(filepath):
    doc = fitz.open(filepath)
    text = doc[0].get_text()
    doc.close()

    acct_match = re.search(r"XXXX XXXX XXXX (\d{4})", text)
    last4 = acct_match.group(1) if acct_match else None

    bal_match = re.search(r"New Balance[:\s]*\$([0-9,]+\.\d{2})", text)
    balance = float(bal_match.group(1).replace(",", "")) if bal_match else 0.0

    due_match = re.search(r"Payment Due Date[:\s]*(\d{2}/\d{2}/\d{2})", text)
    if due_match:
        due_date = datetime.strptime(due_match.group(1), "%m/%d/%y")
        due_str = due_date.strftime("%b %d")
    else:
        due_str = ""

    return last4, balance, due_str


def parse_all_pdfs():
    cards = {}
    pdf_files = glob.glob(os.path.join(SOA_DIR, "*.pdf"))
    for f in pdf_files:
        last4, balance, due_str = parse_chase_pdf(f)
        if last4:
            name = CARD_NAMES.get(last4, f"Card {last4}")
            cards[last4] = {"name": name, "balance": balance, "due": due_str}
    return cards


def fetch_rates():
    r = requests.get("https://api.exchangerate-api.com/v4/latest/USD")
    r.raise_for_status()
    data = r.json()
    usd_php = data["rates"]["PHP"]
    usd_gbp = data["rates"]["GBP"]
    usd_eur = data["rates"]["EUR"]
    return {
        "PHP_USD": round(1 / usd_php, 6),
        "GBP": round(1 / usd_gbp, 4),
        "GBP_EUR": round(usd_eur / usd_gbp, 4),
    }


@app.route("/")
def index():
    return send_file(HTML_FILE)


@app.route("/api/calculate")
def calculate():
    cards = parse_all_pdfs()
    rates = fetch_rates()
    return jsonify({"cards": cards, "rates": rates})


if __name__ == "__main__":
    print("Cash Flow server running at http://localhost:5000")
    app.run(port=5000, debug=True)
