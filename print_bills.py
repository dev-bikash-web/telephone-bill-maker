import os
import sys
import pypdf
import configparser
import time

# ==============================================================================
# CONFIGURABLE PATHS
# ==============================================================================
BILLS_DIR = "telephone_bill"
TEMPLATE_PDF = os.path.join(BILLS_DIR, "template.pdf")
CONFIG_FILE = "print_config.cfg"
# ==============================================================================

# Parse configuration file (print_config.cfg)
config = configparser.ConfigParser()

if not os.path.exists(CONFIG_FILE):
    print(f"Error: Configuration file '{CONFIG_FILE}' not found.")
    print("Please copy 'print_config.cfg.template' to 'print_config.cfg' and configure your credentials.")
    sys.exit(1)

config.read(CONFIG_FILE)

# Read Print Credentials
if not config.has_section('PrintCredentials'):
    print(f"Error: [PrintCredentials] section not found in '{CONFIG_FILE}'.")
    print("Please add the [PrintCredentials] section with 'url', 'username', and 'password'.")
    sys.exit(1)

url = config.get('PrintCredentials', 'url', fallback='').strip()
username = config.get('PrintCredentials', 'username', fallback='').strip()
password = config.get('PrintCredentials', 'password', fallback='').strip()

# Validate that print credentials are configured
if url in ['', 'YOUR_PRINT_MACHINE_URL', 'http://example-print-machine-url.com'] or \
   username in ['', 'YOUR_PRINT_USERNAME', 'your-print-username'] or \
   password in ['', 'YOUR_PRINT_PASSWORD', 'your-print-password']:
    print(f"Error: Print credentials not configured in '{CONFIG_FILE}'.")
    print(f"Please set your real URL, username, and password under [PrintCredentials] in {CONFIG_FILE}.")
    sys.exit(1)

def is_elf_executable(filepath):
    """Verify that a path points to an executable ELF binary file."""
    if not (filepath and os.path.isfile(filepath) and os.access(filepath, os.X_OK)):
        return False
    try:
        with open(filepath, 'rb') as f:
            return f.read(4) == b'\x7fELF'
    except Exception:
        return False

def find_firefox_binary(config):
    """
    Locate the true Firefox ELF binary executable.
    Prioritizes:
    1. config.get('Browser', 'firefox_binary') or FIREFOX_BINARY env var
    2. Ubuntu snap Firefox binary location (/snap/firefox/current/usr/lib/firefox/firefox)
    3. Debian/Ubuntu native package location (/usr/lib/firefox/firefox)
    4. Path resolved from shutil.which('firefox') if it is an ELF binary
    """
    # 1. Configured override
    configured = ""
    if config.has_section('Browser'):
        configured = config.get('Browser', 'firefox_binary', fallback='').strip()
    if not configured:
        configured = os.environ.get('FIREFOX_BINARY', '').strip()

    if configured and os.path.exists(configured):
        return configured

    # 2. Known distribution binary candidates
    candidates = [
        "/snap/firefox/current/usr/lib/firefox/firefox",
        "/usr/lib/firefox/firefox",
        "/usr/lib/firefox/firefox-bin",
    ]
    for candidate in candidates:
        if is_elf_executable(candidate):
            return candidate

    # 3. Path from system PATH if it is a direct ELF binary
    import shutil
    which_firefox = shutil.which("firefox")
    if which_firefox and is_elf_executable(which_firefox):
        return which_firefox

    return None

def js_click(driver, element):
    driver.execute_script("arguments[0].click();", element)

def print_page_via_selenium(driver, pdf_file_path):
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    # Step 1: Open the URL
    print(f"Opening URL: {url}")
    driver.get(url)
    
    # Check if we need to log in (if username field is visible)
    try:
        username_field = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="username"]'))
        )
        print("Entering username...")
        username_field.clear()
        username_field.send_keys(username)
        
        print("Entering password...")
        password_field = driver.find_element(By.XPATH, '//*[@id="password"]')
        password_field.clear()
        password_field.send_keys(password)
        
        print("Logging in...")
        login_btn = driver.find_element(By.XPATH, '/html/body/section/div/div/div/div/div/div[2]/div/form/div[5]/button')
        js_click(driver, login_btn)
    except Exception:
        print("Already logged in or login page skipped.")
        
    # Step 5: Click on Print dropdown via JS
    print("Opening Print dropdown...")
    print_dropdown = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="dropdownUsers"]'))
    )
    js_click(driver, print_dropdown)
    
    # Step 6: Click Print Document via JS
    print("Clicking Print Document...")
    print_doc_link = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.XPATH, '/html/body/div/header/div/div[1]/ul/li[2]/ul/li[1]/a'))
    )
    js_click(driver, print_doc_link)
    
    # Step 7: Select Printer name 7tf via JS
    print("Selecting Printer '7tf'...")
    printer_option = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.XPATH, '/html/body/div[2]/main/div[2]/div[3]/form/div/div[2]/div[1]/div[2]/select/option[5]'))
    )
    js_click(driver, printer_option)
    
    # Step 8: Select pages custom via JS
    print("Selecting Pages Custom...")
    pages_option = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.XPATH, '/html/body/div[2]/main/div[2]/div[3]/form/div/div[2]/div[2]/div[2]/select/option[2]'))
    )
    js_click(driver, pages_option)
    
    # Step 9: Browse/Upload the file
    print("Uploading document...")
    file_input = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.ID, "fileupload"))
    )
    # Selenium requires absolute path for send_keys on file inputs
    abs_file_path = os.path.abspath(pdf_file_path)
    file_input.send_keys(abs_file_path)
    
    # Let the file finish uploading/buffering in the browser context (6 seconds)
    print("Waiting for file upload to complete...")
    time.sleep(6)
    
    # Step 10: Click print / submit via JS
    print("Clicking Print submit...")
    submit_btn = driver.find_element(By.XPATH, '//*[@id="submit"]')
    js_click(driver, submit_btn)
    
    # Step 11: Verify the word print
    print("Verifying response...")
    try:
        h9_element = WebDriverWait(driver, 40).until(
            EC.presence_of_element_located((By.XPATH, '/html/body/div/main/div[2]/center/h9'))
        )
        print(f"[Verification Output] Found text: '{h9_element.text}'")
        
        if "print" in h9_element.text.lower():
            print(f"[Success] Successfully automated print for {os.path.basename(pdf_file_path)}!")
        else:
            print(f"[Warning] Element found, but text did not contain 'print': '{h9_element.text}'")
            
    except Exception as ver_err:
        # Check if there is an error message visible on the page
        try:
            page_text = driver.find_element(By.TAG_NAME, "body").text
            if "error" in page_text.lower() or "not printed" in page_text.lower():
                err_lines = [line.strip() for line in page_text.split("\n") if any(kw in line.lower() for kw in ["error", "not printed", "exist", "upload"])]
                print(f"[Server Error Details] {'; '.join(err_lines)}")
        except:
            pass
        raise ver_err

def main():
    print("==============================================")
    print("      C-DOT Telephone Bill Printer Tool")
    print("==============================================")
    
    # Clean up any stale temporary page files from previous aborted runs
    for f in os.listdir(BILLS_DIR):
        if f.startswith('temp_p3_') and f.endswith('.pdf'):
            try:
                os.remove(os.path.join(BILLS_DIR, f))
            except Exception:
                pass

    # Scan for PDF bills (excluding templates, outputs, and temporary page-3 files)
    bills_to_process = []
    for f in sorted(os.listdir(BILLS_DIR)):
        if f.endswith('.pdf') and f not in [os.path.basename(TEMPLATE_PDF), 'jan_mar_26.pdf', 'template_bk.pdf', 'tst.pdf'] and not f.startswith('filled_claim_') and not f.startswith('temp_p3_'):
            bills_to_process.append(f)
            
    if not bills_to_process:
        print("No bill invoices found to print in 'telephone_bill/' folder.")
        return
        
    print(f"Found {len(bills_to_process)} bill(s) to process.")
    
    # Locate Firefox binary
    firefox_binary = find_firefox_binary(config)
    if firefox_binary:
        print(f"Using Firefox binary: {firefox_binary}")
    else:
        print("Warning: No specific Firefox ELF binary found; relying on default driver resolution.")

    # Import WebDriver modules
    from selenium import webdriver
    from selenium.webdriver.firefox.options import Options as FirefoxOptions
    
    for f in bills_to_process:
        bill_path = os.path.join(BILLS_DIR, f)
        
        # Extract the 3rd page
        reader = pypdf.PdfReader(bill_path)
        if len(reader.pages) < 3:
            print(f"Skipping '{f}' because it has only {len(reader.pages)} pages (less than 3).")
            continue
            
        print(f"\n--- Processing: {f} ---")
        print("Extracting page 3...")
        
        # Create a temporary PDF containing only the 3rd page
        temp_pdf_name = f"temp_p3_{f}"
        temp_pdf_path = os.path.join(BILLS_DIR, temp_pdf_name)
        
        writer = pypdf.PdfWriter()
        writer.add_page(reader.pages[2])  # 3rd page (index 2)
        
        with open(temp_pdf_path, 'wb') as temp_f:
            writer.write(temp_f)
            
        driver = None
        try:
            # Initialize browser session once per bill
            firefox_options = FirefoxOptions()
            firefox_options.add_argument("-headless")
            if firefox_binary:
                firefox_options.binary_location = firefox_binary
            
            print(f"Starting browser session for: {f}")
            driver = webdriver.Firefox(options=firefox_options)
            driver.set_window_size(1920, 1080)
            
            max_retries = 3
            success = False
            for attempt in range(1, max_retries + 1):
                if attempt > 1:
                    print(f"Print attempt {attempt} of {max_retries} (reusing browser session)...")
                try:
                    print_page_via_selenium(driver, temp_pdf_path)
                    success = True
                    break
                except Exception as e:
                    print(f"[Warning] Attempt {attempt} failed: {str(e)}")
                    # Save a screenshot in case of failure for debugging
                    try:
                        filename_clean = f.replace(".pdf", "")
                        screenshot_name = f"error_screenshot_{filename_clean}_attempt_{attempt}.png"
                        driver.save_screenshot(screenshot_name)
                        print(f"Saved error screenshot to: {screenshot_name}")
                    except Exception as screenshot_err:
                        print(f"Could not save screenshot: {str(screenshot_err)}")
                    
                    if attempt < max_retries:
                        print("Waiting 5 seconds before retrying...")
                        time.sleep(5)
            
            if not success:
                print(f"[Error] Failed to print '{f}' after {max_retries} attempts.")
        finally:
            # Close browser session
            if driver is not None:
                print("Closing browser session...")
                try:
                    driver.quit()
                except Exception:
                    pass
            
            # Delete temporary file
            if os.path.exists(temp_pdf_path):
                os.remove(temp_pdf_path)
        
        # Add 5 seconds delay between print jobs to avoid print server rate-limiting/overload
        print("Waiting 5 seconds before the next print job...")
        time.sleep(5)

if __name__ == '__main__':
    main()
