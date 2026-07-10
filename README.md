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
* **Missing Month Safeguard**: If any billing month in the detected quarter has zero bills, the script prints a warning and prompts you dynamically to proceed (leaving the month blank) or exit.
* **Visual Precision styling**: Keeps all form fonts exactly as styled in the template, while dynamically resizing long `Invoice No` fields to `7.5pt` to fit their cells perfectly.

---

## Installation & Setup

1. **System Requirements**: Make sure you have `python3` and `pdftotext` installed on your system.
   * On Debian/Ubuntu: `sudo apt install poppler-utils`
2. **Configuration**: Copy the template file `config.cfg.template` to `config.cfg` and populate your personal details:
   ```bash
   cp config.cfg.template config.cfg
   ```
   Open `config.cfg` and fill in your variables:
   ```ini
   [EmployeeDetails]
   lan_entry = MITLM29098
   name = BIKASH ROUT
   staff_no = 6171
   group_name = SRSW
   group_code = 3YA
   product_name = 5G NON SA
   product_code = G06
   bank_account_no = 110137962434
   ```
   > [!NOTE]
   > Spacing before or after the `=` sign does not matter. The parser automatically trims leading and trailing spaces for both keys and values.

---

## Usage

1. Put your PDF bills in the `telephone_bill/` directory.
2. Run the tool:
   ```bash
   ./run.sh
   ```
3. The tool will automatically:
   * Load and validate your `config.cfg` (extracting details and your LAN Entry No).
   * Parse the bills in the folder and detect the billing quarter (e.g. `Q4`).
   * Check for missing months and prompt for approval if found.
   * Output the populated claim PDF at `telephone_bill/filled_claim_[Quarter].pdf`.

---

## Project Documentation
More details about the technical layout can be found in the `Document/` folder:
* **Architecture Design**: [Document/architecture_design.md](file:///home/bikash/workera/personal_git/telephone-bill-maker/Document/architecture_design.md)
* **Project Plan**: [Document/plan.md](file:///home/bikash/workera/personal_git/telephone-bill-maker/Document/plan.md)
