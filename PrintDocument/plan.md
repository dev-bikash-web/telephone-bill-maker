# Project Plan: Selenium Print Automation Tool

This plan outlines the design and implementation details for automating the print submission of the 3rd page of all PDF invoices using the Selenium browser automation framework.

## 1. Project Goal
Automate the extraction of only the 3rd page from each PDF invoice in the `telephone_bill/` directory, and submit each extracted page to a custom printer web portal.

## 2. Technical Approach
The python script [print_bills.py](file:///home/bikash/workera/personal_git/telephone-bill-maker/print_bills.py) operates as follows:
1. **Load Configuration**:
   - Checks if the configuration file `print_config.cfg` exists.
   - Loads the printer URL and user credentials (username, password) from the `[PrintCredentials]` section of `print_config.cfg` using Python's standard `configparser` module.
   - Optionally loads custom `firefox_binary` from `[Browser]` section or environment variables.
   - If not found or if the file contains default placeholder values, instructs the user to configure their real credentials and exits.
2. **Page Extraction & Buffer Management**:
   - Cleans up any stale temporary PDF buffers (`temp_p3_*.pdf`) from previous interrupted runs.
   - Scans the `telephone_bill/` directory for PDF invoices.
   - For each invoice, reads the PDF pages using the `pypdf` library.
   - Extracts the 3rd page (index 2 in 0-indexed sequence) and writes it into a temporary PDF file within an explicit `try ... finally` lifecycle block.
3. **Selenium Browser Automation (Firefox & Snap Resolution)**:
   - Auto-discovers the actual Firefox ELF binary executable (resolving Canonical Snap wrapper conflicts such as `/snap/firefox/current/usr/lib/firefox/firefox`).
   - Configures `webdriver.Firefox` in headless mode (`-headless`) with standard viewport resolution (1920x1080).
   - Navigates to the configured print machine URL.
   - Fills in the username (`xpath=//*[@id="username"]`) and password (`xpath=//*[@id="password"]`) fields, then clicks the Login button (`xpath=/html/body/section/div/div/div/div/div/div[2]/div/form/div[5]/button`).
   - Clicks on the print options dropdown (`xpath=//*[@id="dropdownUsers"]`).
   - Clicks the "Print Document" link (`xpath=/html/body/div/header/div/div[1]/ul/li[2]/ul/li[1]/a`).
   - Selects the printer named `7tf` (`xpath=/html/body/div[2]/main/div[2]/div[3]/form/div/div[2]/div[1]/div[2]/select/option[5]`).
   - Selects the pages option `custom` (`xpath=/html/body/div[2]/main/div[2]/div[3]/form/div/div[2]/div[2]/div[2]/select/option[2]`).
   - Uploads the temporary 3rd page PDF using the file input field selector (`id="fileupload"`).
   - Submits the form (`xpath=//*[@id="submit"]`).
   - Verifies that the success text containing the word "print" is returned in the response element (`xpath=/html/body/div/main/div[2]/center/h9`).
   - Gracefully terminates the browser session (`driver.quit()`).
4. **Cleanup & Resilience**:
   - Automatically unlinks and deletes the temporary page PDF from disk regardless of run success or unhandled exceptions.
   - Captures automated screenshots on failure for post-mortem debugging.

---

## 3. Configuration Properties
The printer credentials and optional browser overrides are loaded from `print_config.cfg`:

| Configuration Section | Key | Description |
| :--- | :--- | :--- |
| `[PrintCredentials]` | **url** | The print machine portal URL |
| `[PrintCredentials]` | **username** | Your login username |
| `[PrintCredentials]` | **password** | Your login password |
| `[Browser]` *(optional)* | **firefox_binary** | Path to the Firefox ELF executable if auto-detection needs override |

---

## 4. Implementation Status
All requirements are successfully met:
- **Separate Config File**: Read credentials from `print_config.cfg` and template from `print_config.cfg.template`.
- **Page Extraction**: Extract the 3rd page from each invoice.
- **Selenium Browser Automation**: Full browser flow matching the XPaths specified by the user.
- **Headless Snap Compatibility**: Auto-discovery of Firefox ELF binary to resolve `InvalidArgumentException`.
- **Guaranteed Cleanup**: Robust `try ... finally` scoping ensuring no orphaned files or browser processes.
- **Verifications**: Implemented status output validation check.
