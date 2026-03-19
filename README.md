# Cash Flow Automation

Python automation that generates a monthly Cash Flow Google Sheet from QuickBooks balances, Google Drive credit card statements, and computed payroll. Runs every 20th of the month.

## Data Sources

| Source | Method |
|--------|--------|
| **Wells Fargo & Wise** | QuickBooks linked bank balance (not book balance) |
| **Ping Pong (USD/CAD/EUR/GBP)** | Manual input |
| **Credit card balances** | Parsed from Google Drive bank statements (only statements with due date after current month) |
| **Exchange rates** | Google Sheets `GOOGLEFINANCE` formula |
| **SBA Loan & 3PL Winner** | Fixed amounts |

## Payroll Computation

Salaries are in PHP, converted to USD. Monthly hours are computed based on working days in the current month.

| Employee | Hours/Day | Schedule |
|----------|-----------|----------|
| Mischelle | 10 hrs | Mon–Thu |
| Frances | 4 hrs | Mon–Fri |
| June | 4 hrs | Mon–Fri |

## Tech Stack

- **Python** — gspread, google-auth, google-api-python-client
- **QuickBooks MCP** — pull bank/account balances from QBO
- **Google Drive API** — read credit card statement PDFs
- **Google Sheets API** — create the output spreadsheet

## Setup

1. Clone the repo
2. Copy `.env.example` to `.env` and fill in your credentials:
   - QuickBooks OAuth tokens
   - Google service account path
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run:
   ```bash
   python main.py
   ```

## Project Structure

```
cashflow/
├── main.py              # Entry point
├── .env                 # Credentials (git-ignored)
├── .gitignore
├── requirements.txt
├── CLAUDE.md            # Project instructions for Claude
└── README.md
```
