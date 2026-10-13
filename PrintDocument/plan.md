# Project Plan: Selenium Print Automation Tool

This plan outlines the design and implementation details for automating the print submission of the 3rd page of all PDF invoices using the Selenium browser automation framework.

## 1. Project Goal
Automate the extraction of the configured page (default 3) from each PDF invoice in the blank `telephone_bill/` ingestion directory, alongside the final generated reimbursement claim form (`filled_claim_{quarter}.pdf`, default page 1), submitting each extracted page buffer to a custom printer web portal with minimal telemetry output showing only file name, page number, and printer details.

## 2. Technical Approach
The python script [print_bills.py](file:///home/bikash/workera/personal_git/telephone-bill-maker/print_bills.py) operates as follows:
1. **Load Configuration**:
   - Checks if the configuration file `print_config.cfg` exists (with template located in `templates/print_config.cfg.template`).
   - Loads the printer URL and user credentials (username, password) from the `[PrintCredentials]` section.
   - Loads print settings (target `page_number`, default 3; `printer`, default `7tf`) from the `[PrintSettings]` section.
   - Optionally loads custom `firefox_binary` from `[Browser]` section or environment variables.
   - If not configured, prompts the user and cleanly exits.
2. **Page Extraction & Buffer Management**:
   - Cleans up any stale temporary PDF buffers (`temp_p*.pdf`) from previous interrupted runs.
   - Scans the blank `telephone_bill/` directory for user-provided PDF invoices as well as generated claim reimbursement forms (`filled_claim_*.pdf`).
   - Partitions jobs into invoice bills (extracting `page_number`) followed by the final claim reimbursement document (extracting constant page `1`).
   - For each target document, extracts the designated page (`target_page - 1` in 0-indexed sequence) and writes it into a temporary PDF buffer in `templates/` within an explicit `try ... finally` lifecycle block.
3. **Selenium Browser Automation (Firefox & Snap Resolution)**:
   - Auto-discovers the actual Firefox ELF binary executable (resolving Canonical Snap wrapper conflicts such as `/snap/firefox/current/usr/lib/firefox/firefox`).
   - Configures `webdriver.Firefox` in headless mode (`-headless`) with standard viewport resolution (1920x1080).
   - Navigates to the configured print machine URL.
   - Fills in the username (`xpath=//*[@id="username"]`) and password (`xpath=//*[@id="password"]`) fields, then clicks the Login button.
   - Clicks on the print options dropdown (`xpath=//*[@id="dropdownUsers"]`).
   - Clicks the "Print Document" link (`xpath=/html/body/div/header/div/div[1]/ul/li[2]/ul/li[1]/a`).
   - Selects the target printer option (`xpath=/html/body/div[2]/main/div[2]/div[3]/form/div/div[2]/div[1]/div[2]/select/option[5]`).
   - Selects the pages option `custom` (`xpath=/html/body/div[2]/main/div[2]/div[3]/form/div/div[2]/div[2]/div[2]/select/option[2]`).
   - Uploads the temporary page PDF buffer using the file input field selector (`id="fileupload"`).
   - Submits the form (`xpath=//*[@id="submit"]`).
   - Verifies that the success text containing the word "print" is returned in the response element (`xpath=/html/body/div/main/div[2]/center/h9`).
   - Gracefully terminates the browser session (`driver.quit()`).
4. **Streamlined Telemetry & Resilience**:
   - Suppresses all verbose internal browser logs and outputs concise, clean telemetry: `[Success] File: <file> | Page: <page> | Printer: <printer>`.
   - Automatically unlinks and deletes the temporary page PDF from disk regardless of run success or unhandled exceptions.
   - Captures automated screenshots on failure silently for post-mortem debugging.

---

## 3. Configuration Properties
The printer credentials, print settings, and optional browser overrides are loaded from `print_config.cfg`:

| Configuration Section | Key | Description |
| :--- | :--- | :--- |
| `[PrintCredentials]` | **url** | The print machine portal URL |
| `[PrintCredentials]` | **username** | Your login username |
| `[PrintCredentials]` | **password** | Your login password |
| `[PrintSettings]` | **page_number** | Target invoice page number to extract (1-indexed, default: 3) |
| `[PrintSettings]` | **printer** | Target printer name (default: 7tf) |
| `[Browser]` *(optional)* | **firefox_binary** | Path to the Firefox ELF executable if auto-detection needs override |

---

## 4. Implementation Status
All requirements are successfully met:
- **Relocated Templates**: Templates isolated in `templates/`, leaving `telephone_bill/` completely blank for user files.
- **Configurable Page Extraction**: Page number dynamically loaded from config file rather than hardcoded.
- **Minimal Telemetry**: Verbose output eliminated in favor of clean `File | Page | Printer` status lines.
- **Selenium Browser Automation**: Full browser flow matching the XPaths specified by the user.
- **Headless Snap Compatibility**: Auto-discovery of Firefox ELF binary to resolve `InvalidArgumentException`.
- **Guaranteed Cleanup**: Robust `try ... finally` scoping ensuring no orphaned files or browser processes.
- **Verifications**: Implemented status output validation check.
