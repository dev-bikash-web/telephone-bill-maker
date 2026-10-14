import os
import sys
import re
import datetime
import pypdf
import subprocess
import configparser

# ==============================================================================
# CONFIGURABLE MACROS (CONSTANTS)
# ==============================================================================
# Folder and File Paths
BILLS_DIR = "telephone_bill"
TEMPLATES_DIR = "templates"
TEMPLATE_PDF = os.path.join(TEMPLATES_DIR, "template.pdf")
if not os.path.exists(TEMPLATE_PDF) and os.path.exists(os.path.join(BILLS_DIR, "template.pdf")):
    TEMPLATE_PDF = os.path.join(BILLS_DIR, "template.pdf")
OUTPUT_PDF_TEMPLATE = os.path.join(BILLS_DIR, "filled_claim_{quarter}.pdf")

# Overlay text coordinates for writing "Broadband" on rightmost side above the dash
OVERLAY_TEXT = "Broadband"
OVERLAY_X = 460
OVERLAY_Y = 428
OVERLAY_FONT_SIZE = 10

# Checkbox for "Level 13A to 10"
LEVEL_13A_10_CHECKBOX = "Check Box_21"

# Font sizes for filled form text fields (larger text size for selected fields)
TEXT_FIELD_FONT_SIZE_DEFAULT = 10.0
TEXT_FIELD_FONT_SIZE_INVOICE = 7.5
# ==============================================================================

# Parse configuration file (config.cfg)
config = configparser.ConfigParser()
config_file = 'config.cfg'

if not os.path.exists(config_file):
    print(f"Error: Configuration file '{config_file}' not found.")
    print("Please copy 'templates/config.cfg.template' (or 'config.cfg.template') to 'config.cfg' and configure your details.")
    sys.exit(1)

config.read(config_file)

# Extract details from configuration file
EMPLOYEE_NAME = config.get('EmployeeDetails', 'name', fallback='').strip()
STAFF_NO = config.get('EmployeeDetails', 'staff_no', fallback='').strip()
GROUP_NAME = config.get('EmployeeDetails', 'group_name', fallback='').strip()
GROUP_CODE = config.get('EmployeeDetails', 'group_code', fallback='').strip()
PRODUCT_NAME = config.get('EmployeeDetails', 'product_name', fallback='').strip()
PRODUCT_CODE = config.get('EmployeeDetails', 'product_code', fallback='').strip()
BANK_ACCOUNT_NO = config.get('EmployeeDetails', 'bank_account_no', fallback='').strip()
CONFIG_LAN_ENTRY = config.get('EmployeeDetails', 'lan_entry', fallback='').strip()

# Validate that all required configuration fields are filled
required_fields = {
    'lan_entry': CONFIG_LAN_ENTRY,
    'name': EMPLOYEE_NAME,
    'staff_no': STAFF_NO,
    'group_name': GROUP_NAME,
    'group_code': GROUP_CODE,
    'product_name': PRODUCT_NAME,
    'product_code': PRODUCT_CODE,
    'bank_account_no': BANK_ACCOUNT_NO
}

empty_fields = [field for field, value in required_fields.items() if not value]
if empty_fields:
    print(f"Error: The following required fields in '{config_file}' are empty or missing:")
    for field in empty_fields:
        print(f"  - {field}")
    print("\nPlease fill in all configuration details in 'config.cfg' before running the tool.")
    sys.exit(1)

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
    
    # 1. Extract Provider Name dynamically (empty string if not found)
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
            
    # 2. Extract Invoice / Bill Number (Vendor-agnostic)
    invoice_no = None
    
    # Pattern A: Search for common Invoice labels followed by alphanumeric characters (length 6 to 22)
    # Allows dashes and slashes in invoice numbers
    invoice_labels_regex = r'(?:Invoice\s*No|Invoice\s*Number|Bill\s*No|Bill\s*Number|Tax\s*Invoice|Invoice\s*#|Bill\s*#)[^\w\n]*([A-Z0-9\-\/]{6,22})\b'
    match_label = re.search(invoice_labels_regex, text, re.IGNORECASE)
    if match_label:
        invoice_no = match_label.group(1).strip()
    
    # Pattern B: Airtel specific pattern fallback (starts with MF/HF followed by 14 alphanumeric characters)
    if not invoice_no:
        match_airtel = re.search(r'\b([MH]F[A-Z0-9]{14})\b', text)
        if match_airtel:
            invoice_no = match_airtel.group(1)
            
    # Pattern C: Generic search for line containing 'Bill No' or 'Invoice'
    if not invoice_no:
        lines = text.split('\n')
        for idx, line in enumerate(lines):
            if any(term in line.lower() for term in ['bill no', 'invoice', 'bill number']):
                for next_line in lines[idx+1:idx+5]:
                    cleaned = next_line.strip()
                    # Filter out lines that are not invoice numbers (e.g. date strings or too short)
                    if cleaned and len(cleaned) >= 6 and len(cleaned) <= 22 and not any(kw in cleaned.lower() for kw in ['date', 'amount', 'period', 'statement']):
                        # Extract first alphanumeric token
                        token_match = re.match(r'\b([A-Z0-9\-\/]{6,22})\b', cleaned, re.IGNORECASE)
                        if token_match:
                            invoice_no = token_match.group(1)
                            break
                if invoice_no:
                    break
                    
    # 3. Classify Bill Type (Broadband vs Postpaid Mobile) - based solely on keywords
    text_lower = text[:2000].lower()
    filename_lower = filename.lower()
    
    broadband_kws = ['wifi', 'wi-fi', 'broadband', 'broad_band', 'fixed line', 'fixed_line', 'fixedline', 'landline']
    postpaid_kws = ['mobile', 'postpaid', 'post_paid', 'telephone', 'telepphone']
    
    is_broadband = any(kw in filename_lower for kw in broadband_kws) or any(kw in text_lower for kw in broadband_kws)
    
    if is_broadband:
        bill_type = 'Broadband'
    else:
        is_postpaid = any(kw in filename_lower for kw in postpaid_kws) or any(kw in text_lower for kw in postpaid_kws)
        if is_postpaid:
            bill_type = 'Postpaid'
        else:
            # Fallback default
            bill_type = 'Postpaid'
        
    # 4. Extract Amount Claimed / Payable (Vendor-agnostic)
    amount = None
    
    # Pattern A: Search for amount labels followed by decimal numbers
    amount_labels_regex = r'(?:Amount\s*Payable|Total\s*Amount|Total\s*Due|Amount\s*Due|Total\s*Payable|Net\s*Payable|Grand\s*Total|Total\s*Bill\s*Amount|Payable\s*Amount|Total\s*Charges|Charges\s*Payable)[^\d\n]*([0-9]+\.[0-9]{2})\b'
    match_amount = re.search(amount_labels_regex, text, re.IGNORECASE)
    if match_amount:
        amount = float(match_amount.group(1))
        
    # Pattern B: Fallback to the first decimal amount found in the text (excluding common tax percentages like 9.00, 18.00)
    if not amount:
        amounts = re.findall(r'\b([0-9]+\.[0-9]{2})\b', text)
        valid_amounts = []
        for amt in amounts:
            val = float(amt)
            if val not in [9.00, 18.00, 5.00, 12.00, 28.00] and val > 10.0:
                valid_amounts.append(val)
        if valid_amounts:
            amount = valid_amounts[0]
            
    # 5. Extract Month (Vendor-agnostic)
    month = None
    months_list = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    months_full = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    
    # Pattern A: Direct date range e.g. "05 Jul 2026-04 Aug 2026"
    range_match = re.search(r'\b\d{1,2}\s*([A-Za-z]{3})\s*\d{2,4}\s*(?:to|\-)\s*\d{1,2}\s*[A-Za-z]{3}', text, re.IGNORECASE)
    if range_match:
        month = range_match.group(1).capitalize()
        
    # Pattern B: Search for Statement Period dates
    if not month:
        period_labels = r'(?:Statement\s*Period|Bill\s*Period|Period|Bill\s*Date|Invoice\s*Date)[^\w\n]*(.*)'
        period_match = re.search(period_labels, text, re.IGNORECASE)
        if period_match:
            period_text = period_match.group(1).lower()
            for idx, m in enumerate(months_list):
                if m.lower() in period_text or months_full[idx].lower() in period_text:
                    month = m
                    break
                
    # Pattern B: Search Statement Period with date formats like DD/MM/YY
    if not month:
        date_matches = re.findall(r'\b\d{2}/(\d{2})/\d{2,4}\b', text)
        if date_matches:
            month_num = int(date_matches[0])
            if 1 <= month_num <= 12:
                month = months_list[month_num - 1]
                
    # Pattern C: Scan entire text for month names
    if not month:
        for idx, m in enumerate(months_list):
            if re.search(r'\b' + m + r'\b', text, re.IGNORECASE) or re.search(r'\b' + months_full[idx] + r'\b', text, re.IGNORECASE):
                month = m
                break
                
    # Pattern D: Search filename for month name
    if not month:
        for m in months_list:
            if m.lower() in filename:
                month = m
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
    
    provider_map = {
        'airtel': 'AIRTEL',
        'jio': 'JIO',
        'bsnl': 'BSNL',
        'vodafone': 'VI',
        'idea': 'VI',
        ' vi ': 'VI',
        'mtnl': 'MTNL'
    }
    
    for page_idx, p in enumerate(pages):
        # Look for Bill NO on this page (anchored directly to Bill NO / Invoice NO)
        inv_match = re.search(r'(?:Bill\s*NO|Invoice\s*NO)\s*[:\-]?\s*(?:\n\s*)*([A-Z0-9\-\/]{6,22})', p, re.IGNORECASE)
        if not inv_match:
            continue
            
        invoice_no = inv_match.group(1).strip()
        
        # Provider
        provider = 'AIRTEL'
        for kw, prov_name in provider_map.items():
            if kw in p.lower() or kw in filename_lower:
                provider = prov_name
                break
                
        # Service type: Broadband vs Postpaid
        p_lower = p.lower()
        is_broadband = any(k in p_lower for k in ['wifi', 'wi-fi', 'fixedline', 'fixed line', 'broadband'])
        bill_type = 'Broadband' if is_broadband else 'Postpaid'
        
        # Amount: Anchored to "Total Amount"
        amount = None
        amt_match = re.search(r'Total\s*Amount\s*[:\-]?\s*(?:\n\s*)*[=\s`₹]*([0-9,]+\.[0-9]{2})', p, re.IGNORECASE)
        if amt_match:
            try:
                amount = float(amt_match.group(1).replace(',', ''))
            except ValueError:
                amount = None
                
        if amount is None:
            amounts = re.findall(r'[`₹\s]([0-9,]+\.[0-9]{2})\b', p)
            if amounts:
                for a in amounts:
                    try:
                        v = float(a.replace(',', ''))
                        if is_broadband and abs(v - 942.82) < 0.01:
                            amount = v
                            break
                        if not is_broadband and (abs(v - 1414.82) < 0.01 or abs(v - 1945.82) < 0.01):
                            amount = v
                            break
                    except ValueError:
                        continue
                if amount is None and amounts:
                    amount = float(amounts[0].replace(',', ''))
                    
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

def create_broadband_overlay(output_path):
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    c = canvas.Canvas(output_path, pagesize=letter)
    
    # 1. Draw Broadband label
    c.setFont("Helvetica", OVERLAY_FONT_SIZE)
    c.drawString(OVERLAY_X, OVERLAY_Y, OVERLAY_TEXT)
    
    # 2. Draw diagonal strike-through lines (X-shape) across Box 2 (Landline) table
    # Top-Left: (315, 499)
    # Bottom-Right: (555, 445)
    # Bottom-Left: (315, 445)
    # Top-Right: (555, 499)
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(1.2)
    c.line(315, 499, 555, 445)
    c.line(315, 445, 555, 499)
    
    c.save()

def fill_pdf(lan_entry):
    # Ensure bills directory exists
    if not os.path.exists(BILLS_DIR):
        print(f"Error: Directory '{BILLS_DIR}' does not exist.")
        return

    # Check if template exists
    if not os.path.exists(TEMPLATE_PDF):
        print(f"Error: Template PDF not found at {TEMPLATE_PDF}")
        return

    # 1. Parse all bills in bills directory
    pdf_files = [
        f for f in sorted(os.listdir(BILLS_DIR))
        if f.endswith('.pdf')
        and f not in [os.path.basename(TEMPLATE_PDF), 'jan_mar_26.pdf', 'template_bk.pdf', 'tst.pdf']
        and not f.startswith('filled_claim_')
    ]

    if not pdf_files:
        print(f"No bill invoices found in '{BILLS_DIR}/' folder.")
        print(f"Please place your PDF bills in the blank '{BILLS_DIR}/' directory.")
        return

    single_bill_opt = False
    if config.has_section('General') and config.has_option('General', 'single_bill'):
        single_bill_opt = config.getboolean('General', 'single_bill', fallback=False)
    if '--single-bill' in sys.argv or '--single_bill' in sys.argv or '--single-bill=true' in sys.argv or '--single-bill=1' in sys.argv:
        single_bill_opt = True

    parsed_bills = []
    for f in pdf_files:
        bills = parse_bill(os.path.join(BILLS_DIR, f), single_bill=single_bill_opt)
        for bill_info in bills:
            # Print warnings for missing fields
            missing_fields = []
            if not bill_info['provider']:
                missing_fields.append('Provider Name')
            if not bill_info['invoice_no']:
                missing_fields.append('Invoice/Bill No')
            if bill_info['amount'] is None:
                missing_fields.append('Amount')
            if not bill_info['month']:
                missing_fields.append('Billing Month')
                
            if missing_fields:
                print(f"Warning: In bill '{f}' ({bill_info.get('type')}), the following fields were not found: {', '.join(missing_fields)}")
                
            # Keep all bills in the list, even if details are missing (filled as blank / None)
            parsed_bills.append(bill_info)
            
    # 2. Automatically analyze the quarter from the parsed bills
    quarter_month_mapping = {
        'Apr': 'Q1', 'May': 'Q1', 'Jun': 'Q1',
        'Jul': 'Q2', 'Aug': 'Q2', 'Sep': 'Q2',
        'Oct': 'Q3', 'Nov': 'Q3', 'Dec': 'Q3',
        'Jan': 'Q4', 'Feb': 'Q4', 'Mar': 'Q4'
    }
    
    quarter_counts = {'Q1': 0, 'Q2': 0, 'Q3': 0, 'Q4': 0}
    for b in parsed_bills:
        if b['month'] in quarter_month_mapping:
            q = quarter_month_mapping[b['month']]
            quarter_counts[q] += 1
            
    # Determine the most common quarter
    detected_quarter = max(quarter_counts, key=quarter_counts.get)
    if quarter_counts[detected_quarter] == 0:
        print("Error: Could not detect quarter from any of the bills. No billing months found.")
        return
        
    print(f"Automatically Detected Quarter: {detected_quarter}")
    
    # Check if user skipped putting the bills of any month in the detected quarter
    quarter_months = {
        'Q1': ['Apr', 'May', 'Jun'],
        'Q2': ['Jul', 'Aug', 'Sep'],
        'Q3': ['Oct', 'Nov', 'Dec'],
        'Q4': ['Jan', 'Feb', 'Mar']
    }
    
    months = quarter_months.get(detected_quarter)
    present_months = {b['month'] for b in parsed_bills if b['month'] in months}
    missing_months = [m for m in months if m not in present_months]
    
    if missing_months:
        print(f"\n[Warning] No bills were found for the following month(s) in {detected_quarter}: {', '.join(missing_months)}. Proceeding with remaining bills...")
    
    template_path = TEMPLATE_PDF
    output_path = OUTPUT_PDF_TEMPLATE.format(quarter=detected_quarter)
    
    # Check if template exists
    if not os.path.exists(template_path):
        print(f"Error: Template PDF not found at {template_path}")
        return
        
    fields_to_fill = {}
    
    # Today's Date & Financial Year
    today_str = datetime.datetime.now().strftime('%d-%m-%Y')
    current_year = datetime.datetime.now().strftime('%Y')
    
    # Constant Information
    fields_to_fill['LAN Entry'] = lan_entry
    fields_to_fill['Name'] = EMPLOYEE_NAME
    fields_to_fill['Staff No'] = STAFF_NO
    fields_to_fill['Date'] = today_str
    fields_to_fill['Group'] = GROUP_NAME
    fields_to_fill['Group Code'] = GROUP_CODE
    fields_to_fill['Product'] = PRODUCT_NAME
    fields_to_fill['Product code'] = PRODUCT_CODE
    fields_to_fill['A/C'] = BANK_ACCOUNT_NO
    fields_to_fill['Fin Year'] = current_year
    fields_to_fill['Name_1'] = EMPLOYEE_NAME
    fields_to_fill['Staff No_1'] = STAFF_NO
    fields_to_fill['Text Field'] = today_str
    
    # Quarter Selection Checkbox
    quarter_checkboxes = {
        'Q1': 'Check Box_17',
        'Q2': 'Check Box_18',
        'Q3': 'Check Box_19',
        'Q4': 'Check Box_20'
    }
    fields_to_fill[quarter_checkboxes[detected_quarter]] = '/Yes'
    
    # Mark level checkbox: "Level 13A to 10"
    fields_to_fill[LEVEL_13A_10_CHECKBOX] = '/Yes'
        
    # Box 1 (Postpaid Mobile)
    postpaid_total = 0.0
    postpaid_bills = [b for b in parsed_bills if b['type'] == 'Postpaid' and b['month'] in months]
    
    for b in postpaid_bills:
        m_idx = months.index(b['month'])
        prov_field = 'Service Provider' if m_idx == 0 else f'Service Provider_{m_idx}'
        inv_field = 'Invoice No' if m_idx == 0 else f'Invoice No_{m_idx}'
        amt_field = 'Amount' if m_idx == 0 else f'Amount_{m_idx}'
        
        fields_to_fill[prov_field] = b['provider'] if b['provider'] is not None else ""
        fields_to_fill[inv_field] = b['invoice_no'] if b['invoice_no'] is not None else ""
        
        if b['amount'] is not None:
            fields_to_fill[amt_field] = f"{b['amount']:.2f}"
            postpaid_total += b['amount']
        else:
            fields_to_fill[amt_field] = ""
        
        # Checkbox mapping for Box 1 months
        if m_idx == 0:
            cb_map = {'Apr': 'Check Box', 'Jul': 'Check Box_1', 'Oct': 'Check Box_2', 'Jan': 'Check Box_3'}
        elif m_idx == 1:
            cb_map = {'May': 'Check Box_4', 'Aug': 'Check Box_5', 'Nov': 'Check Box_6', 'Feb': 'Check Box_7'}
        else:
            cb_map = {'Jun': 'Check Box_8', 'Sep': 'Check Box_9', 'Dec': 'Check Box_10', 'Mar': 'Check Box_11'}
        
        cb_name = cb_map.get(b['month'])
        if cb_name:
            fields_to_fill[cb_name] = '/Yes'
            
    if postpaid_total > 0:
        fields_to_fill['Total Amount'] = f"{postpaid_total:.2f}"
        
    # Box 3 (Broadband)
    # Write only in rows 1, 3, and 5 of Box 3 (index 6, 8, 10)
    broadband_total = 0.0
    broadband_bills = [b for b in parsed_bills if b['type'] == 'Broadband' and b['month'] in months]
    
    for b in broadband_bills:
        m_idx = months.index(b['month'])
        
        # Row mapping: Jan -> Row 1 (index 6), Feb -> Row 3 (index 8), Mar -> Row 5 (index 10)
        row_offset = 6 + m_idx * 2
        prov_field = f'Service Provider_{row_offset}'
        inv_field = f'Invoice No_{row_offset}'
        amt_field = f'Amount_{row_offset}'
        
        fields_to_fill[prov_field] = b['provider'] if b['provider'] is not None else ""
        fields_to_fill[inv_field] = b['invoice_no'] if b['invoice_no'] is not None else ""
        
        if b['amount'] is not None:
            fields_to_fill[amt_field] = f"{b['amount']:.2f}"
            broadband_total += b['amount']
        else:
            fields_to_fill[amt_field] = ""
        
        # Checkbox mapping for Box 3 months (Broadband)
        if m_idx == 0:
            cb_map = {'Apr': 'Check Box_16', 'Jul': 'Check Box_16_2', 'Oct': 'Check Box_16_3', 'Jan': 'Check Box_16_4'}
        elif m_idx == 1:
            cb_map = {'May': 'Check Box_16_1', 'Aug': 'Check Box_16_1_2', 'Nov': 'Check Box_16_1_3', 'Feb': 'Check Box_16_1_4'}
        else: # m_idx == 2
            cb_map = {'Jun': 'Check Box_16_1_1', 'Sep': 'Check Box_16_1_1_1', 'Dec': 'Check Box_16_1_1_2', 'Mar': 'Check Box_16_1_1_3'}
            
        cb_name = cb_map.get(b['month'])
        if cb_name:
            fields_to_fill[cb_name] = '/Yes'
            
    if broadband_total > 0:
        fields_to_fill['Total Amount_2'] = f"{broadband_total:.2f}"
        
    # Overall Totals
    total_amount = postpaid_total + broadband_total
    if total_amount > 0:
        fields_to_fill['Total Billed Amount'] = f"{total_amount:.2f}"
        fields_to_fill['Total Claimed Amount'] = f"{total_amount:.2f}"
        
    # 3. Read template and write filled PDF
    reader = pypdf.PdfReader(template_path)
    writer = pypdf.PdfWriter()
    writer.clone_reader_document_root(reader)
    
    # Set NeedAppearances to False so only fields without pre-baked /AP (appearance streams) are regenerated
    acro = writer.root_object.get("/AcroForm")
    if acro:
        acro.update({
            pypdf.generic.NameObject("/NeedAppearances"): pypdf.generic.BooleanObject(False)
        })
    
    # Fill fields
    writer.update_page_form_field_values(writer.pages[0], fields_to_fill, auto_regenerate=False)
    
    # Explicitly set the appearance states for checkbox checkboxes to active (/Yes)
    # And modify /DA and remove /AP for specified text fields only to increase/decrease their font sizes
    page = writer.pages[0]
    
    if '/Annots' in page:
        for annot_ref in page['/Annots']:
            annot = annot_ref.get_object()
            t = annot.get('/T')
            
            # Normalize Rect coordinates if they are inverted to prevent checkmark/text shifting
            rect = annot.get('/Rect')
            if rect:
                x1, y1, x2, y2 = [float(val) for val in rect]
                if x1 > x2:
                    x1, x2 = x2, x1
                if y1 > y2:
                    y1, y2 = y2, y1
                annot.update({
                    pypdf.generic.NameObject('/Rect'): pypdf.generic.ArrayObject([
                        pypdf.generic.FloatObject(x1),
                        pypdf.generic.FloatObject(y1),
                        pypdf.generic.FloatObject(x2),
                        pypdf.generic.FloatObject(y2)
                    ])
                })
            
            # Checkbox values
            if t in fields_to_fill and fields_to_fill[t] == '/Yes':
                annot.update({
                    pypdf.generic.NameObject('/V'): pypdf.generic.NameObject('/Yes'),
                    pypdf.generic.NameObject('/AS'): pypdf.generic.NameObject('/Yes')
                })
                
            # Text Fields: modify /DA and remove /AP for specified fields to restore the 2 variants
            ft = annot.get('/FT')
            if t and ft == '/Tx':
                resize_fields = [
                    'LAN Entry', 'Name', 'Name_1', 'Staff No', 'Staff No_1',
                    'Date', 'Text Field', 'Group', 'Group Code', 'Product', 'Product code',
                    'A/C', 'Fin Year'
                ]
                should_resize = False
                if t in resize_fields or 'Amount' in t or 'Total' in t:
                    should_resize = True
                    if t == 'Text Field':
                        font_size = TEXT_FIELD_FONT_SIZE_INVOICE
                    else:
                        font_size = TEXT_FIELD_FONT_SIZE_DEFAULT
                elif 'Invoice No' in t:
                    should_resize = True
                    font_size = TEXT_FIELD_FONT_SIZE_INVOICE
                
                if should_resize:
                    annot.update({
                        pypdf.generic.NameObject('/DA'): pypdf.generic.TextStringObject(f"/Helvetica {font_size} Tf 0 g")
                    })
                    if '/AP' in annot:
                        del annot['/AP']
                
    # Flatten form fields to bake values into the page content stream
    writer.update_page_form_field_values(page, fields_to_fill, auto_regenerate=False, flatten=True)
    
    # Remove interactive widget annotations (text fields and checkboxes)
    writer.remove_annotations(subtypes="/Widget")
    
    # Remove AcroForm from the root catalog to make the document completely non-editable
    if '/AcroForm' in writer.root_object:
        del writer.root_object['/AcroForm']
                
    # Create broadband overlay and merge it dynamically
    overlay_temp_dir = TEMPLATES_DIR if os.path.exists(TEMPLATES_DIR) else BILLS_DIR
    overlay_temp_path = os.path.join(overlay_temp_dir, "temp_broadband_overlay.pdf")
    create_broadband_overlay(overlay_temp_path)
    
    overlay_reader = pypdf.PdfReader(overlay_temp_path)
    page.merge_page(overlay_reader.pages[0])
    
    # Clean up overlay temp file
    if os.path.exists(overlay_temp_path):
        os.remove(overlay_temp_path)
    
    with open(output_path, 'wb') as f:
        writer.write(f)
        
    print(f"\n[Success] Form filled successfully!")
    print(f"Output saved at: {output_path}")

def main():
    print("==============================================")
    print("      C-DOT Telephone Bill Maker Tool")
    print("==============================================")
    
    # Use LAN Entry No directly from config file, no prompting needed
    fill_pdf(CONFIG_LAN_ENTRY)

if __name__ == '__main__':
    main()
