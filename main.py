"""
Cash Flow Report Generator

Parses Chase credit card PDFs from Downloads/SOA/ and generates
an HTML cash flow report with editable fields and auto-calculated totals.
"""

import re
import os
import glob
from datetime import datetime

import fitz  # pymupdf

SOA_DIR = os.path.expanduser("~/Downloads/SOA")
OUTPUT = os.path.join(os.path.dirname(__file__), "index.html")

# Map last-4 digits to display name
CARD_NAMES = {
    "0889": "Chase Ink 0889",
    "4719": "Chase Ink 4719",
    "4462": "Chase Hyatt 4462",
    "8537": "Chase 8537",
}


def parse_chase_pdf(filepath):
    """Extract account last-4, new balance, and due date from a Chase statement."""
    doc = fitz.open(filepath)
    text = doc[0].get_text()
    doc.close()

    # Account number last 4
    acct_match = re.search(r"XXXX XXXX XXXX (\d{4})", text)
    last4 = acct_match.group(1) if acct_match else None

    # New Balance
    bal_match = re.search(r"New Balance[:\s]*\$([0-9,]+\.\d{2})", text)
    balance = float(bal_match.group(1).replace(",", "")) if bal_match else 0.0

    # Payment Due Date
    due_match = re.search(r"Payment Due Date[:\s]*(\d{2}/\d{2}/\d{2})", text)
    if due_match:
        due_date = datetime.strptime(due_match.group(1), "%m/%d/%y")
        due_str = due_date.strftime("%b %d")
    else:
        due_str = ""

    return last4, balance, due_str


def parse_all_pdfs():
    """Parse all Chase PDFs in the SOA folder."""
    cards = {}
    pdf_files = glob.glob(os.path.join(SOA_DIR, "*.pdf"))
    for f in pdf_files:
        last4, balance, due_str = parse_chase_pdf(f)
        if last4:
            name = CARD_NAMES.get(last4, f"Card {last4}")
            cards[last4] = {"name": name, "balance": balance, "due": due_str}
    return cards


def fmt(n):
    """Format number with commas and 2 decimals."""
    if n == 0:
        return ""
    return f"{n:,.2f}"


def generate_html(cards):
    """Generate the cash flow HTML report."""
    # Build credit card rows from PDFs
    card_order = ["0889", "4719", "4462", "8537"]
    cc_rows = ""
    for last4 in card_order:
        if last4 in cards:
            c = cards[last4]
            cc_rows += f"""    <tr>
      <td></td>
      <td>{c['name']}</td>
      <td class="r"></td>
      <td class="r" data-cc>{fmt(c['balance'])}</td>
      <td class="r"></td>
      <td>{c['due']}</td>
    </tr>\n"""
        else:
            name = CARD_NAMES.get(last4, f"Card {last4}")
            cc_rows += f"""    <tr>
      <td></td>
      <td>{name}</td>
      <td class="r"></td>
      <td class="r ed" contenteditable="true">0.00</td>
      <td class="r"></td>
      <td contenteditable="true"></td>
    </tr>\n"""

    today = datetime.today().strftime("%B %d, %Y")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Cash Flow</title>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #fff; padding: 20px; color: #333; }}
    .container {{ max-width: 850px; margin: 0 auto; }}

    h1 {{ font-size: 18px; margin-bottom: 3px; }}
    .date {{ font-size: 12px; color: #888; margin-bottom: 15px; }}
    table {{ width: 100%; border-collapse: collapse; }}
    td, th {{ padding: 4px 8px; font-size: 13px; vertical-align: top; }}
    th {{ text-align: left; font-weight: 400; color: #888; font-size: 12px; }}
    th.r {{ text-align: right; }}

    .r {{ text-align: right; font-variant-numeric: tabular-nums; }}
    .section-label {{ font-weight: 700; padding-top: 12px; }}
    .total-row td {{ font-weight: 700; border-top: 1.5px solid #333; }}
    .spacer td {{ height: 10px; }}
    .negative {{ color: #c00; }}
    .note {{ font-size: 11px; color: #888; text-align: right; }}

    .ed {{
      background: #fffde7;
      border: 1px dashed #e0c860;
      border-radius: 2px;
      min-width: 60px;
      padding: 2px 6px;
      outline: none;
    }}
    .ed:focus {{ background: #fff9c4; border-color: #f9a825; }}
  </style>
</head>
<body>

<div class="container">
  <h1>Cash Flow</h1>
  <p class="date">As of {today}</p>
  <table>
    <colgroup>
      <col style="width: 28%">
      <col style="width: 20%">
      <col style="width: 14%">
      <col style="width: 14%">
      <col style="width: 14%">
      <col style="width: 10%">
    </colgroup>
    <tr>
      <th></th>
      <th></th>
      <th class="r">Local Currency</th>
      <th class="r">USD</th>
      <th class="r">Total</th>
      <th></th>
    </tr>

    <!-- Cash Balances -->
    <tr>
      <td>Wells Fargo</td>
      <td></td>
      <td class="r"></td>
      <td class="r"></td>
      <td class="r ed" contenteditable="true" data-cash>0.00</td>
      <td></td>
    </tr>
    <tr>
      <td>Ping Pong USD</td>
      <td></td>
      <td class="r"></td>
      <td class="r"></td>
      <td class="r ed" contenteditable="true" data-cash>0.00</td>
      <td></td>
    </tr>
    <tr>
      <td>undeposited Amazon remittance</td>
      <td></td>
      <td class="r"></td>
      <td class="r"></td>
      <td class="r ed" contenteditable="true" data-cash>0.00</td>
      <td></td>
    </tr>
    <tr>
      <td>Ping Pong CAD</td>
      <td></td>
      <td class="r ed" contenteditable="true" data-fx="CAD">0.00</td>
      <td class="r" data-fx-usd></td>
      <td class="r"></td>
      <td></td>
    </tr>
    <tr>
      <td>Ping Pong EUR</td>
      <td></td>
      <td class="r ed" contenteditable="true" data-fx="EUR">0.00</td>
      <td class="r" data-fx-usd></td>
      <td class="r"></td>
      <td></td>
    </tr>
    <tr>
      <td>Ping Pong GBP</td>
      <td></td>
      <td class="r ed" contenteditable="true" data-fx="GBP">0.00</td>
      <td class="r" data-fx-usd></td>
      <td class="r"></td>
      <td></td>
    </tr>
    <tr>
      <td>Wise GBP</td>
      <td></td>
      <td class="r ed" contenteditable="true" data-fx="GBP">0.00</td>
      <td class="r" data-fx-usd></td>
      <td class="r"></td>
      <td></td>
    </tr>
    <tr>
      <td>Wise EUR</td>
      <td></td>
      <td class="r ed" contenteditable="true" data-fx="EUR">0.00</td>
      <td class="r" data-fx-usd></td>
      <td class="r" id="fx-subtotal"></td>
      <td></td>
    </tr>

    <tr class="spacer"><td colspan="6"></td></tr>

    <tr class="total-row">
      <td>Available Cash</td>
      <td></td>
      <td></td>
      <td></td>
      <td class="r" id="available-cash"></td>
      <td></td>
    </tr>

    <tr class="spacer"><td colspan="6"></td></tr>

    <!-- Recurring Expenses -->
    <tr>
      <td class="section-label">Recurring Expenses</td>
      <td>SBA Loan</td>
      <td class="r"></td>
      <td class="r ed" contenteditable="true" data-expense>0.00</td>
      <td class="r"></td>
      <td contenteditable="true" class="ed"></td>
    </tr>
    <tr>
      <td></td>
      <td>3PL Winner</td>
      <td class="r"></td>
      <td class="r ed" contenteditable="true" data-expense>0.00</td>
      <td class="r"></td>
      <td contenteditable="true" class="ed"></td>
    </tr>
    <tr>
      <td></td>
      <td>Kendrew</td>
      <td class="r"></td>
      <td class="r ed" contenteditable="true" data-expense>0.00</td>
      <td class="r" id="expense-total"></td>
      <td contenteditable="true" class="ed"></td>
    </tr>

    <tr class="spacer"><td colspan="6"></td></tr>

    <!-- Credit Cards -->
    <tr>
      <td class="section-label">Credit Card</td>
      <td>Capital One</td>
      <td class="r"></td>
      <td class="r ed" contenteditable="true" data-cc>0.00</td>
      <td class="r"></td>
      <td contenteditable="true" class="ed"></td>
    </tr>
{cc_rows}    <tr>
      <td></td>
      <td>Wells Fargo Credit Line</td>
      <td class="r"></td>
      <td class="r ed" contenteditable="true" data-cc>0.00</td>
      <td class="r"></td>
      <td contenteditable="true" class="ed"></td>
    </tr>
    <tr>
      <td></td>
      <td>Amex Hilton</td>
      <td class="r"></td>
      <td class="r ed" contenteditable="true" data-cc>0.00</td>
      <td class="r" id="cc-total"></td>
      <td contenteditable="true" class="ed"></td>
    </tr>

    <tr class="spacer"><td colspan="6"></td></tr>

    <!-- Payroll -->
    <tr>
      <td class="section-label">Payroll</td>
      <td>Jamie</td>
      <td class="r"></td>
      <td class="r ed" contenteditable="true" data-payroll>0.00</td>
      <td class="r"></td>
      <td></td>
    </tr>
    <tr>
      <td></td>
      <td>Cleaners</td>
      <td class="r"></td>
      <td class="r ed" contenteditable="true" data-payroll>0.00</td>
      <td class="r"></td>
      <td></td>
    </tr>
    <tr class="spacer"><td colspan="6"></td></tr>
    <tr>
      <td></td>
      <td>Mischelle</td>
      <td class="r ed" contenteditable="true" data-php>0.00</td>
      <td class="r" data-php-usd></td>
      <td class="r"></td>
      <td></td>
    </tr>
    <tr>
      <td></td>
      <td>Frances</td>
      <td class="r ed" contenteditable="true" data-php>0.00</td>
      <td class="r" data-php-usd></td>
      <td class="r"></td>
      <td></td>
    </tr>
    <tr>
      <td></td>
      <td>June</td>
      <td class="r ed" contenteditable="true" data-php>0.00</td>
      <td class="r" data-php-usd></td>
      <td class="r" id="payroll-total"></td>
      <td></td>
    </tr>

    <tr class="spacer"><td colspan="6"></td></tr>
    <tr class="spacer"><td colspan="6"></td></tr>

    <tr class="total-row">
      <td>Total Cash out</td>
      <td></td>
      <td></td>
      <td></td>
      <td class="r" id="total-cashout"></td>
      <td></td>
    </tr>

    <tr class="spacer"><td colspan="6"></td></tr>

    <tr class="total-row">
      <td>Excess Cash / Add Fund</td>
      <td></td>
      <td></td>
      <td></td>
      <td class="r" id="excess-cash"></td>
      <td></td>
    </tr>

    <tr class="spacer"><td colspan="6"></td></tr>

    <!-- Suppliers -->
    <tr>
      <td class="section-label">Supplier</td>
      <td class="ed" contenteditable="true">Zhou Yun</td>
      <td class="r"></td>
      <td class="r ed" contenteditable="true" data-supplier>0.00</td>
      <td class="r"></td>
      <td class="ed" contenteditable="true">thru Charles Schwab</td>
    </tr>
  </table>
</div>

<script>
  // Exchange rates — update these or fetch from an API
  const rates = {{ CAD: 0.73, EUR: 1.15, GBP: 1.34, PHP: 0.0168 }};

  function num(el) {{
    return parseFloat((el.textContent || '0').replace(/,/g, '')) || 0;
  }}

  function fmt(n) {{
    if (n === 0) return '';
    return n.toLocaleString('en-US', {{ minimumFractionDigits: 2, maximumFractionDigits: 2 }});
  }}

  function recalc() {{
    // FX conversions
    let fxTotal = 0;
    document.querySelectorAll('[data-fx]').forEach(el => {{
      const currency = el.getAttribute('data-fx');
      const local = num(el);
      const usd = local * (rates[currency] || 1);
      const usdCell = el.closest('tr').querySelector('[data-fx-usd]');
      if (usdCell) usdCell.textContent = fmt(usd);
      fxTotal += usd;
    }});
    document.getElementById('fx-subtotal').textContent = fmt(fxTotal);

    // Cash balances (direct USD entries)
    let cashDirect = 0;
    document.querySelectorAll('[data-cash]').forEach(el => {{
      cashDirect += num(el);
    }});
    const availableCash = cashDirect + fxTotal;
    document.getElementById('available-cash').textContent = fmt(availableCash);

    // Recurring expenses
    let expenseTotal = 0;
    document.querySelectorAll('[data-expense]').forEach(el => {{
      expenseTotal += num(el);
    }});
    document.getElementById('expense-total').textContent = fmt(expenseTotal);

    // Credit cards
    let ccTotal = 0;
    document.querySelectorAll('[data-cc]').forEach(el => {{
      ccTotal += num(el);
    }});
    document.getElementById('cc-total').textContent = fmt(ccTotal);

    // PHP payroll conversions
    let phpTotal = 0;
    document.querySelectorAll('[data-php]').forEach(el => {{
      const php = num(el);
      const usd = php * rates.PHP;
      const usdCell = el.closest('tr').querySelector('[data-php-usd]');
      if (usdCell) usdCell.textContent = fmt(usd);
      phpTotal += usd;
    }});

    // Payroll (USD direct + PHP converted)
    let payrollDirect = 0;
    document.querySelectorAll('[data-payroll]').forEach(el => {{
      payrollDirect += num(el);
    }});
    const payrollTotal = payrollDirect + phpTotal;
    document.getElementById('payroll-total').textContent = fmt(payrollTotal);

    // Totals
    const totalCashout = expenseTotal + ccTotal + payrollTotal;
    document.getElementById('total-cashout').textContent = fmt(totalCashout);

    const excess = availableCash - totalCashout;
    const excessEl = document.getElementById('excess-cash');
    excessEl.textContent = excess < 0 ? '(' + fmt(Math.abs(excess)) + ')' : fmt(excess);
    excessEl.classList.toggle('negative', excess < 0);
  }}

  // Recalculate on any edit
  document.addEventListener('input', recalc);
  recalc();
</script>

</body>
</html>"""
    return html


def main():
    print(f"Reading PDFs from {SOA_DIR}...")
    cards = parse_all_pdfs()
    for last4, info in cards.items():
        print(f"  {info['name']}: ${info['balance']:,.2f} due {info['due']}")

    html = generate_html(cards)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\nGenerated {OUTPUT}")
    print("Push to GitHub to update the live page.")


if __name__ == "__main__":
    main()
