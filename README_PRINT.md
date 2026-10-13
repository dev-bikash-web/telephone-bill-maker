# C-DOT Telephone Bill Invoice Printer Tool

Automate extracting the 3rd page of all PDF invoices and uploading/submitting them to your print machine portal using Selenium browser automation.

---

## Features
* **Separate Configuration**: Printer URL and credentials (username, password) are loaded from a dedicated configuration file (`print_config.cfg`) separate from the filler tool.
* **Configurable Page & Printer Selection**: Target page number (`page_number`, default `3`) and printer name (`printer`, default `7tf`) can be configured directly in `print_config.cfg`.
* **Dynamic Page Extraction**: Uses `pypdf` to extract the configured page of each PDF invoice in the blank `telephone_bill/` directory, saving it to a temporary PDF buffer for printing.
* **Fully Automated Selenium Workflow**: Handles browser navigation, login, printer selection (`7tf`), pages option (`custom`), document upload, submission, verification, and browser closing.
* **Streamlined Telemetry Output**: Clean, minimal console logging that outputs only the file name, page number, and printer details (`[Success] File: <file> | Page: <page> | Printer: <printer>`).
* **Headless Compatibility**: Detects if a display server is running and automatically falls back to headless mode to prevent crashes in non-graphic server environments.
* **Clean State Cleanup**: Automatically deletes temporary extracted page PDF files after submission.

---

## Setup & Installation

1. Make sure you have python3 and selenium installed (run `run.sh` to install baseline dependencies first).
2. Copy the configuration template file to create `print_config.cfg`:
   ```bash
   cp templates/print_config.cfg.template print_config.cfg
   ```
3. Open `print_config.cfg` and configure your printer URL, credentials, and settings:
   ```ini
   [PrintCredentials]
   url = http://your-printer-portal-url
   username = your-username
   password = your-password

   [PrintSettings]
   page_number = 3
   printer = 7tf
   ```

---

## Usage

Run the printing runner script directly:
```bash
./run_print.sh
```
Or execute the script inside the virtual environment:
```bash
.venv/bin/python print_bills.py
```

The script scans for bills in `telephone_bill/`, extracts the configured page, submits each to the print web portal, verifies the response, and outputs clean status lines containing only the file name, page number, and printer details.

---

## Documentation
More technical details are located in the `PrintDocument/` directory:
* **Project Plan**: [PrintDocument/plan.md](file:///home/bikash/workera/personal_git/telephone-bill-maker/PrintDocument/plan.md)
* **Architecture Design**: [PrintDocument/architecture_design.md](file:///home/bikash/workera/personal_git/telephone-bill-maker/PrintDocument/architecture_design.md)
