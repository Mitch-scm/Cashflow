"""
Cash Flow Report Generator

Parses Chase credit card PDFs from Downloads/SOA/ and generates
an HTML cash flow report matching the Design tab layout.
"""

import re
import os
import glob
from datetime import datetime

import requests
import fitz  # pymupdf

SOA_DIR = os.path.expanduser("~/Downloads/SOA")
OUTPUT = os.path.join(os.path.dirname(__file__), "index.html")

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


def fmt(n):
    if n == 0:
        return ""
    return f"{n:,.2f}"


def cc_row(name, data=None):
    if data:
        return (
            f'    <tr>\n'
            f'      <td>{name}</td>\n'
            f'      <td class="r" data-cc>{fmt(data["balance"])}</td>\n'
            f'      <td>{data["due"]}</td>\n'
            f'    </tr>'
        )
    return (
        f'    <tr>\n'
        f'      <td>{name}</td>\n'
        f'      <td class="r ed" contenteditable="true" data-cc>0.00</td>\n'
        f'      <td class="ed" contenteditable="true"></td>\n'
        f'    </tr>'
    )


def fetch_rates():
    """Fetch live exchange rates from USD base."""
    r = requests.get("https://api.exchangerate-api.com/v4/latest/USD")
    r.raise_for_status()
    data = r.json()
    usd_cad = data["rates"]["CAD"]
    usd_eur = data["rates"]["EUR"]
    usd_gbp = data["rates"]["GBP"]
    usd_php = data["rates"]["PHP"]
    return {
        "PHP_USD": round(1 / usd_php, 6),     # 1 PHP in USD
        "GBP": round(1 / usd_gbp, 4),         # 1 GBP in USD
        "GBP_EUR": round(usd_eur / usd_gbp, 4),  # 1 GBP in EUR
    }


def generate_html(cards, rates):
    today = datetime.today()
    current_month = today.strftime("%Y-%m")

    cc_rows = "\n".join([
        cc_row("Capital One", cards.get("capital_one")),
        cc_row("Chase 8537", cards.get("8537")),
        cc_row("Chase Ink 0889", cards.get("0889")),
        cc_row("Chase Ink 4719", cards.get("4719")),
        cc_row("Chase Hyatt 4462", cards.get("4462")),
        cc_row("Wells Fargo Credit Line"),
        cc_row("Amex Hilton"),
    ])

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Cash Flow</title>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #fff; padding: 20px; color: #333; font-size: 13px; }}
    .container {{ max-width: 700px; margin: 0 auto; }}
    h1 {{ font-size: 18px; margin-bottom: 8px; }}

    .date-picker {{ margin-bottom: 15px; }}
    .date-picker input {{ font-size: 13px; padding: 4px 8px; border: 1px solid #ccc; border-radius: 3px; }}

    .header-box {{
      background: #d6eaf8;
      padding: 14px 18px;
      border-radius: 4px;
      margin-bottom: 15px;
    }}
    .header-box h2 {{ font-size: 14px; margin-bottom: 10px; }}
    .header-box table {{ width: 100%; border-collapse: collapse; }}
    .header-box td {{ padding: 2px 8px; font-size: 13px; }}
    .header-box .val {{ font-weight: 700; }}
    .header-box .zhou {{ margin-top: 8px; padding-top: 8px; border-top: 1px solid #a8c8e8; }}

    table {{ width: 100%; border-collapse: collapse; margin-bottom: 6px; }}
    td {{ padding: 3px 8px; vertical-align: top; }}
    .r {{ text-align: right; font-variant-numeric: tabular-nums; }}
    .section {{ font-weight: 700; padding-top: 10px; }}
    .total-row td {{ font-weight: 700; border-top: 1.5px solid #333; padding-top: 6px; }}
    .spacer td {{ height: 8px; }}
    .negative {{ color: #c00; }}
    .currency {{ color: #666; font-size: 12px; }}

    .ed {{
      background: #fffde7;
      border: 1px dashed #e0c860;
      border-radius: 2px;
      min-width: 60px;
      padding: 2px 6px;
      outline: none;
    }}
    .ed:focus {{ background: #fff9c4; border-color: #f9a825; }}

    .calc-btn {{
      margin: 12px 0;
      padding: 8px 20px;
      background: #1a73e8;
      color: #fff;
      border: none;
      border-radius: 4px;
      font-size: 13px;
      cursor: pointer;
    }}
    .calc-btn:hover {{ background: #1557b0; }}
  </style>
</head>
<body>

<div class="container">
  <!-- Header Box -->
  <div class="header-box">
    <h1 style="font-size:18px; margin-bottom:8px;">Cash Flow</h1>
    <div class="date-picker">
      <input type="month" id="month-picker" value="{current_month}">
    </div>
    <table>
      <tr><td colspan="2" style="font-weight:600; padding-bottom:4px;">Excess Cash / Add Fund</td></tr>
      <tr>
        <td>USD</td>
        <td class="r val" id="excess-usd"></td>
      </tr>
      <tr>
        <td>CAD</td>
        <td class="r val" id="excess-cad"></td>
      </tr>
      <tr>
        <td>GBP</td>
        <td class="r val" id="excess-gbp"></td>
      </tr>
      <tr>
        <td>EUR</td>
        <td class="r val" id="excess-eur"></td>
      </tr>
      <tr class="zhou">
        <td>Pay to Zhou Yun</td>
        <td class="r ed" contenteditable="true" id="zhou-yun" style="background:#fff;">0.00</td>
      </tr>
      <tr>
        <td colspan="2" class="currency">thru Charles Schwab</td>
      </tr>
    </table>
  </div>

  <!-- Available Cash -->
  <table>
    <tr><td class="section">Available Cash</td><td></td><td></td></tr>
    <tr>
      <td>Wells Fargo</td>
      <td class="r ed" contenteditable="true" data-cash-usd>0.00</td>
      <td></td>
    </tr>
    <tr>
      <td>Ping Pong USD</td>
      <td class="r ed" contenteditable="true" data-cash-usd>0.00</td>
      <td></td>
    </tr>
    <tr>
      <td>undeposited Amazon remittance</td>
      <td class="r ed" contenteditable="true" data-cash-usd>0.00</td>
      <td></td>
    </tr>
    <tr>
      <td>Ping Pong CAD</td>
      <td class="r ed" contenteditable="true" data-cash-cad>0.00</td>
      <td class="currency">CAD</td>
    </tr>
    <tr>
      <td>Ping Pong EUR</td>
      <td class="r ed" contenteditable="true" data-cash-eur>0.00</td>
      <td class="currency">EUR</td>
    </tr>
    <tr>
      <td>Ping Pong GBP</td>
      <td class="r ed" contenteditable="true" data-cash-gbp>0.00</td>
      <td class="currency">GBP</td>
    </tr>
    <tr>
      <td>Wise GBP</td>
      <td class="r ed" contenteditable="true" data-cash-gbp>0.00</td>
      <td class="currency">GBP</td>
    </tr>
    <tr>
      <td>Wise EUR</td>
      <td class="r ed" contenteditable="true" data-cash-eur>0.00</td>
      <td class="currency">EUR</td>
    </tr>

    <tr class="spacer"><td colspan="3"></td></tr>

    <!-- Recurring Expenses -->
    <tr><td class="section">Recurring Expenses</td><td></td><td></td></tr>
    <tr>
      <td>SBA Loan</td>
      <td class="r" data-outlay>7,968.00</td>
      <td id="sba-due"></td>
    </tr>
    <tr>
      <td>3PL Winner</td>
      <td class="r ed" contenteditable="true" data-outlay>0.00</td>
      <td class="ed" contenteditable="true"></td>
    </tr>

    <!-- Credit Cards -->
{cc_rows}

    <!-- Other USD expenses -->
    <tr>
      <td>Jamie</td>
      <td class="r ed" contenteditable="true" data-outlay>0.00</td>
      <td class="ed" contenteditable="true"></td>
    </tr>
    <tr>
      <td>Cleaners</td>
      <td class="r ed" contenteditable="true" data-outlay>0.00</td>
      <td class="ed" contenteditable="true"></td>
    </tr>

    <tr class="spacer"><td colspan="3"></td></tr>

    <tr class="total-row">
      <td>Cash Outlay (USD only)</td>
      <td class="r" id="cash-outlay"></td>
      <td></td>
    </tr>

    <tr class="spacer"><td colspan="3"></td></tr>

    <!-- Foreign Currencies -->
    <tr><td class="section">Foreign Currencies</td><td></td><td></td></tr>
    <tr>
      <td>Kendrew</td>
      <td class="r ed" contenteditable="true" id="kendrew">0.00</td>
      <td class="currency">CAD</td>
    </tr>

    <tr class="spacer"><td colspan="3"></td></tr>

    <!-- Payroll -->
    <tr>
      <td class="section">Payroll</td>
      <td class="r" id="payroll-php"></td>
      <td class="currency">PHP</td>
    </tr>
  </table>

  <button class="calc-btn" id="calc-btn">Calculate</button>
</div>

<script>
  const rates = {{ PHP_USD: {rates['PHP_USD']}, GBP: {rates['GBP']}, GBP_EUR: {rates['GBP_EUR']} }};

  function num(el) {{
    return parseFloat((el.textContent || '0').replace(/[^0-9.-]/g, '')) || 0;
  }}

  function fmt(n) {{
    if (n === 0) return '';
    return n.toLocaleString('en-US', {{ minimumFractionDigits: 2, maximumFractionDigits: 2 }});
  }}

  function countWeekdays(year, month) {{
    let monThu = 0, monFri = 0;
    const daysInMonth = new Date(year, month, 0).getDate();
    for (let d = 1; d <= daysInMonth; d++) {{
      const day = new Date(year, month - 1, d).getDay();
      if (day >= 1 && day <= 5) monFri++;
      if (day >= 1 && day <= 4) monThu++;
    }}
    return {{ monThu, monFri }};
  }}

  function getNextMonthName(month) {{
    const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
    return months[month % 12];
  }}

  function recalc() {{
    const picker = document.getElementById('month-picker');
    const [year, month] = picker.value.split('-').map(Number);
    const {{ monThu, monFri }} = countWeekdays(year, month);

    // SBA Loan due date: 4th of next month
    const nextMonth = getNextMonthName(month);
    document.getElementById('sba-due').textContent = nextMonth + ' 04';

    // Payroll (PHP)
    const payrollPHP = (monThu * 10 * 399.58) + (monFri * 8 * 510);
    document.getElementById('payroll-php').textContent = fmt(payrollPHP);

    // Available Cash by currency
    let cashUSD = 0;
    document.querySelectorAll('[data-cash-usd]').forEach(el => cashUSD += num(el));
    let cashCAD = 0;
    document.querySelectorAll('[data-cash-cad]').forEach(el => cashCAD += num(el));
    let cashGBP = 0;
    document.querySelectorAll('[data-cash-gbp]').forEach(el => cashGBP += num(el));
    let cashEUR = 0;
    document.querySelectorAll('[data-cash-eur]').forEach(el => cashEUR += num(el));

    // Cash Outlay (USD only)
    let outlay = 0;
    document.querySelectorAll('[data-outlay]').forEach(el => outlay += num(el));
    document.querySelectorAll('[data-cc]').forEach(el => outlay += num(el));
    document.getElementById('cash-outlay').textContent = fmt(outlay);

    // Kendrew (CAD expense)
    const kendrew = num(document.getElementById('kendrew'));

    // Payroll converted to GBP
    const payrollGBP = payrollPHP * rates.PHP_USD / rates.GBP;

    // Excess Cash
    const excessUSD = cashUSD - outlay;
    const excessCAD = cashCAD - kendrew;
    let excessGBP = cashGBP - payrollGBP;
    let excessEUR;

    if (excessGBP >= 0) {{
      excessEUR = cashEUR;
    }} else {{
      const gbpDeficitInEUR = Math.abs(excessGBP) * rates.GBP_EUR;
      excessEUR = cashEUR - gbpDeficitInEUR;
      excessGBP = 0;
    }}

    // Display excess cash with currency symbols
    const usdEl = document.getElementById('excess-usd');
    if (excessUSD < 0) {{
      usdEl.textContent = '$(' + fmt(Math.abs(excessUSD)) + ')';
      usdEl.classList.add('negative');
    }} else {{
      usdEl.textContent = '$' + fmt(excessUSD);
      usdEl.classList.remove('negative');
    }}

    const cadEl = document.getElementById('excess-cad');
    if (excessCAD < 0) {{
      cadEl.textContent = 'CA$(' + fmt(Math.abs(excessCAD)) + ')';
      cadEl.classList.add('negative');
    }} else {{
      cadEl.textContent = 'CA$' + fmt(excessCAD);
      cadEl.classList.remove('negative');
    }}

    const gbpEl = document.getElementById('excess-gbp');
    gbpEl.textContent = excessGBP === 0 ? '0.00' : '\u00a3' + fmt(excessGBP);
    gbpEl.classList.remove('negative');

    const eurEl = document.getElementById('excess-eur');
    if (excessEUR < 0) {{
      eurEl.textContent = '\u20ac(' + fmt(Math.abs(excessEUR)) + ')';
      eurEl.classList.add('negative');
    }} else {{
      eurEl.textContent = '\u20ac' + fmt(excessEUR);
      eurEl.classList.remove('negative');
    }}
  }}

  document.getElementById('calc-btn').addEventListener('click', recalc);
  document.getElementById('month-picker').addEventListener('change', function() {{
    // Update SBA due date and payroll when month changes
    const picker = document.getElementById('month-picker');
    const [year, month] = picker.value.split('-').map(Number);
    const {{ monThu, monFri }} = countWeekdays(year, month);
    const nextMonth = getNextMonthName(month);
    document.getElementById('sba-due').textContent = nextMonth + ' 04';
    const payrollPHP = (monThu * 10 * 399.58) + (monFri * 8 * 510);
    document.getElementById('payroll-php').textContent = fmt(payrollPHP);
  }});

  // Initial SBA date and payroll only
  (function() {{
    const picker = document.getElementById('month-picker');
    const [year, month] = picker.value.split('-').map(Number);
    const {{ monThu, monFri }} = countWeekdays(year, month);
    const nextMonth = getNextMonthName(month);
    document.getElementById('sba-due').textContent = nextMonth + ' 04';
    const payrollPHP = (monThu * 10 * 399.58) + (monFri * 8 * 510);
    document.getElementById('payroll-php').textContent = fmt(payrollPHP);
  }})();
</script>

</body>
</html>"""
    return html


def main():
    print(f"Reading PDFs from {SOA_DIR}...")
    cards = parse_all_pdfs()
    for last4, info in cards.items():
        print(f"  {info['name']}: ${info['balance']:,.2f} due {info['due']}")

    print("Fetching live exchange rates...")
    rates = fetch_rates()
    print(f"  PHP/USD: {rates['PHP_USD']}")
    print(f"  GBP/USD: {rates['GBP']}")
    print(f"  GBP/EUR: {rates['GBP_EUR']}")

    html = generate_html(cards, rates)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\nGenerated {OUTPUT}")


if __name__ == "__main__":
    main()
