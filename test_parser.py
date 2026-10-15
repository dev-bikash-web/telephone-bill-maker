import re
import os
import subprocess

def extract_text_from_pdf(pdf_path):
    txt_path = pdf_path.replace('.pdf', '.txt')
    if os.path.exists(txt_path):
        with open(txt_path, 'r', encoding='utf-8') as f:
            return f.read()
    result = subprocess.run(['pdftotext', pdf_path, '-'], capture_output=True, text=True)
    return result.stdout

def parse_bill_legacy(pdf_path, text=None):
    if text is None:
        text = extract_text_from_pdf(pdf_path)
    
    filename = os.path.basename(pdf_path).lower()
    is_broadband = 'broad_band' in filename or 'wifi' in text.lower() or 'broadband' in text.lower()
    bill_type = 'Broadband' if is_broadband else 'Postpaid'
    
    provider = ""
    provider_map = {
        'airtel': 'AIRTEL',
        'jio': 'JIO',
        'bsnl': 'BSNL',
        'vodafone': 'VI',
        'idea': 'VI',
        ' vi ': 'VI',
        'mtnl': 'MTNL'
    }
    for kw, prov_name in provider_map.items():
        if kw in text.lower() or kw in filename:
            provider = prov_name
            break
            
    invoice_no = None
    invoice_labels_regex = r'(?:Invoice\s*No|Invoice\s*Number|Bill\s*No|Bill\s*Number|Tax\s*Invoice|Invoice\s*#|Bill\s*#)[^\w\n]*([A-Z0-9\-\/]{6,22})\b'
    match_label = re.search(invoice_labels_regex, text, re.IGNORECASE)
    if match_label:
        invoice_no = match_label.group(1).strip()
    if not invoice_no:
        match = re.search(r'\b([MH]F[A-Z0-9]{14})\b', text)
        if match:
            invoice_no = match.group(1)
    if not invoice_no:
        lines = text.split('\n')
        for idx, line in enumerate(lines):
            if any(term in line.lower() for term in ['bill no', 'invoice', 'bill number']):
                for next_line in lines[idx+1:idx+5]:
                    cleaned = next_line.strip()
                    if cleaned and 6 <= len(cleaned) <= 22 and not any(kw in cleaned.lower() for kw in ['date', 'amount', 'period', 'statement']):
                        token_match = re.match(r'\b([A-Z0-9\-\/]{6,22})\b', cleaned, re.IGNORECASE)
                        if token_match:
                            invoice_no = token_match.group(1)
                            break
                if invoice_no:
                    break
                    
    amount = None
    amount_labels_regex = r'(?:Total\s*Amount\s*Payable|Amount\s*Payable|Total\s*Amount|Total\s*Due|Amount\s*Due|Total\s*Payable|Net\s*Payable|Grand\s*Total|Total\s*Bill\s*Amount|Payable\s*Amount|Total\s*Charges|Charges\s*Payable)\s*[:\-]?\s*(?:\n\s*)*[=\s`₹Rs\.]*([0-9,]+\.[0-9]{2})\b'
    match_amount = re.search(amount_labels_regex, text, re.IGNORECASE)
    if match_amount:
        try:
            amount = float(match_amount.group(1).replace(',', ''))
        except ValueError:
            amount = None
    
    month = None
    range_match = re.search(r'\b\d{1,2}\s*([A-Za-z]{3})\s*\d{2,4}\s*(?:to|\-)\s*\d{1,2}\s*[A-Za-z]{3}', text, re.IGNORECASE)
    if range_match:
        month = range_match.group(1).capitalize()
    else:
        month_match = re.search(r'Statement Period:\s*(\d{2})?\s*([A-Za-z]{3})', text, re.IGNORECASE)
        if month_match:
            month = month_match.group(2).capitalize()
        else:
            month_match_date = re.search(r'Statement Period:\s*(\d{2})/(\d{2})/(\d{2})', text, re.IGNORECASE)
            if month_match_date:
                month_num = int(month_match_date.group(2))
                months_map = {1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun', 7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'}
                month = months_map.get(month_num)
            
    if not month:
        for m in ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']:
            if m in filename:
                month = m.capitalize()
                break

    return {
        'filename': os.path.basename(pdf_path),
        'type': bill_type,
        'provider': provider,
        'invoice_no': invoice_no,
        'amount': amount,
        'month': month
    }

def parse_bill_page_separation(pdf_path, text=None):
    if text is None:
        text = extract_text_from_pdf(pdf_path)
    filename = os.path.basename(pdf_path)
    filename_lower = filename.lower()
    
    pages = text.split('\x0c')
    bills = []
    months_list = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    for page_idx, p in enumerate(pages):
        # Look for Bill NO on this page (anchored directly to Bill NO / Invoice NO)
        inv_match = re.search(r'(?:Bill\s*NO|Invoice\s*NO)\s*[:\-]?\s*(?:\n\s*)*([A-Z0-9\-\/]{6,22})', p, re.IGNORECASE)
        if not inv_match:
            continue
            
        invoice_no = inv_match.group(1).strip()
        
        # Provider
        provider = ""
        provider_map = {
            'airtel': 'AIRTEL',
            'jio': 'JIO',
            'bsnl': 'BSNL',
            'vodafone': 'VI',
            'idea': 'VI',
            ' vi ': 'VI',
            'mtnl': 'MTNL'
        }
        for kw, prov_name in provider_map.items():
            if kw in p.lower() or kw in filename_lower:
                provider = prov_name
                break
                
        # Service type: Broadband vs Postpaid
        p_lower = p.lower()
        is_broadband = any(k in p_lower for k in ['wifi', 'wi-fi', 'fixedline', 'fixed line', 'broadband'])
        bill_type = 'Broadband' if is_broadband else 'Postpaid'
        
        # Amount: Anchored to semantic total/payable labels
        amount = None
        amt_match = re.search(r'(?:Total\s*Amount\s*Payable|Amount\s*Payable|Total\s*Amount|Total\s*Due|Amount\s*Due|Total\s*Payable|Net\s*Payable|Grand\s*Total|Total\s*Bill\s*Amount|Payable\s*Amount|Total\s*Charges|Charges\s*Payable)\s*[:\-]?\s*(?:\n\s*)*[=\s`₹Rs\.]*([0-9,]+\.[0-9]{2})\b', p, re.IGNORECASE)
        if amt_match:
            try:
                amount = float(amt_match.group(1).replace(',', ''))
            except ValueError:
                amount = None
                    
        # Month: Start month of the billing period takes highest precedence
        month = None
        # Pattern 1: Direct date range e.g. "05 Jul 2026-04 Aug 2026" or "08 Jul 2026 to 07 Aug 2026"
        range_match = re.search(r'\b\d{1,2}\s*([A-Za-z]{3})\s*\d{2,4}\s*(?:to|\-)\s*\d{1,2}\s*[A-Za-z]{3}', p, re.IGNORECASE)
        if range_match:
            month = range_match.group(1).capitalize()
            
        if not month:
            # Pattern 2: Numeric date range e.g. "05/07/2026 - 04/08/2026"
            num_range = re.search(r'\b\d{1,2}[\/\-](\d{1,2})[\/\-]\d{2,4}\s*(?:to|\-)\s*\d{1,2}[\/\-]\d{1,2}[\/\-]', p)
            if num_range:
                month_num = int(num_range.group(1))
                if 1 <= month_num <= 12:
                    month = months_list[month_num - 1]
                    
        if not month:
            period_match = re.search(r'(?:Bill\s*Period|Statement\s*Period|Period)\s*[:\-]?\s*(?:\d{1,2}\s*)?([A-Za-z]{3})', p, re.IGNORECASE)
            if period_match:
                month = period_match.group(1).capitalize()
            
        if not month:
            period_date_match = re.search(r'(?:Bill\s*Period|Statement\s*Period|Period)\s*[:\-]?\s*\d{1,2}[\/\-](\d{1,2})[\/\-]', p, re.IGNORECASE)
            if period_date_match:
                month_num = int(period_date_match.group(1))
                if 1 <= month_num <= 12:
                    month = months_list[month_num - 1]
                    
        if not month:
            date_match = re.search(r'Bill Date\s*[:\-]?\s*(\d{2})?\s*([A-Za-z]{3})', p, re.IGNORECASE)
            if date_match:
                month = date_match.group(2).capitalize()
                
        if not month:
            for m in months_list:
                if m.lower() in filename_lower:
                    month = m
                    break
                    
        bills.append({
            'filename': filename,
            'type': bill_type,
            'provider': provider,
            'invoice_no': invoice_no,
            'amount': amount,
            'month': month
        })
        
    if not bills:
        bills = [parse_bill_legacy(pdf_path, text)]
        
    return bills

def parse_bill(pdf_path, single_bill=False):
    text = extract_text_from_pdf(pdf_path)
    if single_bill:
        return parse_bill_page_separation(pdf_path, text)
    else:
        return [parse_bill_legacy(pdf_path, text)]

bills_dir = 'telephone_bill'
connection_totals = {}
connection_counts = {}
grand_total = 0.0
total_bills = 0

if not os.path.exists(bills_dir):
    print(f"Directory '{bills_dir}' does not exist.")
    exit(1)

eligible_files = [
    f for f in sorted(os.listdir(bills_dir))
    if f.endswith('.pdf') and f not in ['template.pdf', 'jan_mar_26.pdf'] and not f.startswith('filled_claim_')
]

import sys

single_bill_flag = False
if '--single-bill' in sys.argv or '--single_bill' in sys.argv or '--single-bill=true' in sys.argv or '--single-bill=1' in sys.argv:
    single_bill_flag = True

for f in eligible_files:
    path = os.path.join(bills_dir, f)
    bills = parse_bill(path, single_bill=single_bill_flag)
    for res in bills:
        amt_str = f"{res['amount']:.2f}" if res['amount'] is not None else "None"
        print(f"{res['filename']}: Type={res['type']}, Month={res['month']}, Provider={res['provider']}, Invoice={res['invoice_no']}, Amount={amt_str}")
        
        b_type = res['type'] or 'Unknown'
        if res['amount'] is not None:
            connection_totals[b_type] = connection_totals.get(b_type, 0.0) + res['amount']
            connection_counts[b_type] = connection_counts.get(b_type, 0) + 1
            grand_total += res['amount']
            total_bills += 1
        else:
            print(f"  [WARNING] Could not parse amount for {res['filename']} ({res['type']})")

print("\n" + "=" * 55)
print("                 BILLING SUMMARY")
print("=" * 55)
if connection_totals:
    for conn_type in sorted(connection_totals.keys()):
        print(f"  {conn_type:<15} : ₹{connection_totals[conn_type]:>10,.2f}  ({connection_counts[conn_type]} bills)")
    print("-" * 55)
    print(f"  {'Grand Total':<15} : ₹{grand_total:>10,.2f}  ({total_bills} bills)")
else:
    print("  No eligible bills found.")
print("=" * 55)
