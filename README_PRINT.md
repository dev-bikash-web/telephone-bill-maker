# C-DOT Telephone Bill Invoice Printer Tool

Automate extracting the 3rd page of all PDF invoices and uploading/submitting them to your print machine portal using Selenium browser automation.

---

## Features
* **Separate Configuration**: Printer URL and credentials (username, password) are loaded from a dedicated configuration file (`print_config.cfg`) separate from the filler tool.
* **Dynamic Page Extraction**: Uses `pypdf` to extract the 3rd page (index 2) of each PDF invoice in the `telephone_bill/` directory, saving it to a temporary PDF file for printing.
* **Fully Automated Selenium Workflow**: Handles browser navigation, login, printer selection (`7tf`), pages option (`custom`), document upload, submission, verification, and browser closing.
* **Headless Compatibility**: Detects if a display server is running and automatically falls back to headless mode to prevent crashes in non-graphic server environments.
* **Clean State Cleanup**: Automatically deletes temporary page-3 PDF files after submission.

---

## Setup & Installation

1. Make sure you have python3 and selenium installed (run `run.sh` to install baseline dependencies first).
2. Copy the configuration template file to create `print_config.cfg`:
   ```bash
   cp print_config.cfg.template print_config.cfg
   ```
3. Open `print_config.cfg` and configure your printer URL and user credentials:
   ```ini
   [PrintCredentials]
   url = http://your-printer-portal-url
   username = your-username
   password = your-password
   ```

---

## Usage

Run the printing script directly:
```bash
.venv/bin/python print_bills.py
```

The script will scan for bills, extract their 3rd page, submit them to the print web portal one by one, verify the confirmation text, and output success status messages to the console.

---

## Documentation
More technical details are located in the `PrintDocument/` directory:
* **Project Plan**: [PrintDocument/plan.md](file:///home/bikash/workera/personal_git/telephone-bill-maker/PrintDocument/plan.md)
* **Architecture Design**: [PrintDocument/architecture_design.md](file:///home/bikash/workera/personal_git/telephone-bill-maker/PrintDocument/architecture_design.md)
