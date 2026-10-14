# C-DOT Telephone Bill Maker Tool

Automate the extraction of billing details from PDF invoices and populate the standard C-DOT reimbursement claim form.

---

## Features
* **Automatic Setup**: A single runner script (`./run.sh`) takes care of creating the Python virtual environment (`.venv`), upgrading `pip`, and installing all required dependencies.
* **Zero User Interaction**: Runs instantly and automatically with a single command. All constant inputs are read from `config.cfg` and the billing quarter is detected automatically by scanning the bills.
* **Configuration-Driven**: All constant employee and connection details are stored in a simple configuration file (`config.cfg`) rather than hardcoded in the script.
* **Pre-run Validation**: The tool automatically validates the configuration file before execution and lists any missing fields, exiting cleanly if setup is incomplete.
* **Vendor-Agnostic Parsing**: Dynamically extracts billing month, invoice number, payable totals, and provider names from bills representing various providers (Airtel, Jio, BSNL, Vodafone, MTNL, etc.) using regex and text patterns.
* **Graceful Missing Data Handling**: Missing details (such as a missing invoice number or amount) are rendered as blank spaces on the PDF form instead of causing crashes.
* **Auto Quarter Detection**: Automatically analyzes the invoice months present in your `telephone_bill` directory, maps them to the correct financial quarter (`Q1`–`Q4`), and selects the appropriate mapping without prompting the user.
* **Non-Interactive Missing Month Safeguard**: If any billing month in the detected quarter has zero bills, the script logs an informative warning and automatically proceeds with filling the remaining months without blocking execution.
* **Bundled & Combo Statements (`--single-bill`)**: Supports multi-service combo statements (such as Airtel Black containing both Wi-Fi/Broadband and Mobile tax invoices) via page separation and targeted `Bill NO` anchoring.
* **Box 2 Diagonal Strike-Through**: Automatically draws a diagonal "X" strike-through across Box 2 (Landline) to invalidate it.
* **Visual Precision Styling**: Keeps all form fonts exactly as styled in the template, while dynamically resizing long `Invoice No` fields and the signature `Text Field` to `7.5pt` to fit their cells perfectly.

---

## Installation & Setup

1. **System Requirements**: Make sure you have `python3` and `pdftotext` installed on your system.
   * On Debian/Ubuntu: `sudo apt install poppler-utils`
2. **Configuration**: Copy the template file `templates/config.cfg.template` to `config.cfg` and populate your personal details:
   ```bash
   cp templates/config.cfg.template config.cfg
   ```
   Open `config.cfg` and fill in your variables:
   ```ini
   [EmployeeDetails]
   lan_entry = MITLM00000
   name = FIRSTNAME LASTNAME
   staff_no = 0000
   group_name = YOUR_GROUP
   group_code = 0XX
   product_name = YOUR_PRODUCT
   product_code = X00
   bank_account_no = 000000000000
   ```
   > [!NOTE]
   > Spacing before or after the `=` sign does not matter. The parser automatically trims leading and trailing spaces for both keys and values.

---

## Usage

### 1. Mode A: Separate Individual Bills (Default)
Use this default mode when your `telephone_bill/` directory contains individual, separate PDF files for each service (e.g. separate Postpaid Mobile bills and separate Broadband bills).

* **Generate Reimbursement Claim Form**:
  ```bash
  ./run.sh
  ```
  Automatically detects the billing quarter, fills Box 1 (Mobile) and Box 3 (Broadband), applies the Box 2 strike-through overlay, and saves the output at `telephone_bill/filled_claim_[Quarter].pdf`.

* **Verify Bills & Calculate Totals (Diagnostic Mode)**:
  ```bash
  ./test_calculate_bill.sh
  ```
  Inspects parsed invoice metadata and streams connection subtotals and grand totals to terminal logs without modifying any files.

---

### 2. Mode B: Combined / Bundled Statements (`--single-bill`)
Use the `--single-bill` flag when you have multi-service combo statements (e.g. **Airtel Black** statements containing both Wi-Fi/Broadband and Mobile tax invoices bundled inside the same PDF file).

* **Generate Reimbursement Claim Form**:
  ```bash
  ./run.sh --single-bill
  ```
  Separates the invoice pages, extracts both Wi-Fi and Mobile tax invoices, resolves the billing period start month, and populates the claim form.

* **Verify Bills & Calculate Totals (Diagnostic Mode)**:
  ```bash
  ./test_calculate_bill.sh --single-bill
  ```
  Separates the pages, extracts all independent sub-bills (anchored directly to `Bill NO` and `Total Amount`), and displays the full billing breakdown in the logs.

> [!TIP]
> You can also make `--single-bill` the default by adding `single_bill = true` under a `[General]` section in your `config.cfg`:
> ```ini
> [General]
> single_bill = true
> ```

---

## Project Documentation
More details about the technical layout can be found in the `Document/` folder:
* **Architecture Design**: [Document/architecture_design.md](file:///home/bikash/workera/personal_git/telephone-bill-maker/Document/architecture_design.md)
* **Project Plan**: [Document/plan.md](file:///home/bikash/workera/personal_git/telephone-bill-maker/Document/plan.md)
* **Parser & Calculation Diagnostics Tool**: [Document/test_parser.md](file:///home/bikash/workera/personal_git/telephone-bill-maker/Document/test_parser.md)
