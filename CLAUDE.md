# Cash Flow Automation

## Project Purpose

Automated cash flow reporting tool that pulls financial data from an existing QuickBooks server and emails formatted reports via Gmail MCP.

## Architecture

This project does NOT connect to QuickBooks directly. It calls the existing Quickbooks Express server running locally.

- **Data source:** `POST http://localhost:3456/api/report` (see Quickbooks project at `C:\Users\chich\Automation\Quickbooks`)
- **Processing:** Python scripts parse CSV responses and build cash flow reports
- **Delivery:** Gmail MCP sends finished reports by email

## Project Structure

```
cashflow/
├── main.py           # Entry point — fetch reports, process, email
├── requirements.txt  # Python dependencies
├── CLAUDE.md         # This file — project conventions
├── README.md         # Project overview
└── .gitignore        # Excludes .env, credentials, Python cache
```

## Conventions

- **No QBO credentials in this project** — all QuickBooks access goes through localhost:3456
- **Start the Quickbooks server first** — `node server.js` in `C:\Users\chich\Automation\Quickbooks`
- **Never commit secrets** — .gitignore already excludes .env and credential files
- Use imperative commit messages (e.g., "Add cash flow report generator")

## Available Report Types

Fetched via `POST http://localhost:3456/api/report` with JSON body:

| report_type | Description |
|---|---|
| `profit_loss` | Profit & Loss |
| `profit_loss_detail` | P&L with transaction detail |
| `balance_sheet` | Balance Sheet |
| `trial_balance` | Trial Balance |
| `general_ledger` | General Ledger Detail |
| `transaction_list` | Transaction List |

Parameters: `start_date`, `end_date`, `department`, `summarize_by`, `account`, `transaction_type`, `accounting_method`

## Development Workflow

1. Ensure Quickbooks server is running on port 3456
2. Run `pip install -r requirements.txt`
3. Run `python main.py`
