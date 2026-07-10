# Project Plan: Telephone Bill Parser & Template Filler

This plan outlines the design and implementation details for programmatically parsing telephone bills and filling out the C-DOT reimbursement template (`template.pdf`).

## 1. Project Goal
Automate the extraction of billing details from PDF files in the `telephone_bill` directory and populate the corresponding fields of the interactive PDF form (`template.pdf`).

## 2. Technical Approach
We wrote a Python script ([make_bill.py](file:///home/bikash/workera/personal_git/telephone-bill-maker/make_bill.py)) in the workspace that performs the following steps:
1. **Load Configuration**:
   - Check if the configuration file `config.cfg` exists.
   - Parse employee details (Name, Staff No, Group, Product, Bank Account) and LAN Entry No from `config.cfg` using Python's native `configparser` module.
   - If not found, instruct the user to copy the reference template `config.cfg.template` to `config.cfg` and configure their details.
   - Validate that all required configuration fields are filled. If any field is empty or missing, print the errors and exit immediately before running.
   
   > [!TIP]
   > Spaces before or after the `=` sign in `config.cfg` are ignored by the parser. Both `name = Value` and `name=Value` are valid and parsed identically.

2. **Bill Parsing & Auto Quarter Detection**: 
   - Scan the `telephone_bill` directory for PDF bills (excluding templates and outputs).
   - Use `pdftotext` to extract text from each bill.
   - Run regular expressions on the text to extract the Provider Name, Bill/Invoice No, Amount Payable, and Bill Month.
   - Automatically determine the billing Quarter (Q1-Q4) by mapping the extracted billing months to their respective quarters and selecting the most common quarter among the bills.
3. **Missing Month Check**:
   - Check if there are any months in the detected quarter that do not have any bills in the directory.
   - If a month is missing, print a warning list of the missing month(s) and prompt the user to proceed (`yes`/`no`).
   - If the user says `no`, terminate the script without writing any changes. If `yes`, proceed and leave the fields for the missing month blank on the PDF claim.
4. **Template Filling**:
   - Map the extracted bills to the corresponding rows in the template based on their starting month.
   - Use the `pypdf` library to programmatically fill out the text fields and check the corresponding checkboxes.
   - Calculate box totals, total billed, and total claimed amounts.
   - Draw `"Broadband"` dynamically on the rightmost side above the dash.
   - Save the populated form to a new file, e.g., `filled_claim_[Quarter].pdf`.

---

## 3. Data Mapping & Constants
The following values are parsed from the `config.cfg` file and populated on the template:

| Field Name | Type | Section / Key in CFG | Description |
| :--- | :--- | :--- | :--- |
| **LAN Entry** | Text | `[EmployeeDetails] lan_entry` | User's LAN Entry No. |
| **Name** | Text | `[EmployeeDetails] name` | Employee Name |
| **Staff No** | Text | `[EmployeeDetails] staff_no` | Employee Staff No |
| **Date** | Text | Today's Date | Today's Date |
| **Group** | Text | `[EmployeeDetails] group_name` | Group Name |
| **Group Code** | Text | `[EmployeeDetails] group_code` | Group Code |
| **Product** | Text | `[EmployeeDetails] product_name` | Product Name |
| **Product code** | Text | `[EmployeeDetails] product_code` | Product Code |
| **A/C** | Text | `[EmployeeDetails] bank_account_no` | Bank Account Number |
| **Fin Year** | Text | Current Year | Financial Year |
| **Name_1** | Text | `[EmployeeDetails] name` | Bottom Certification Name |
| **Staff No_1** | Text | `[EmployeeDetails] staff_no` | Bottom Certification Staff No |
| **Text Field** | Text | Today's Date | Certification Date |

### Box Rules:
- **Box 1 (Postpaid Mobile)**: Fill using postpaid bills.
  - Rows 1, 2, and 3 correspond to the 3 months of the selected Quarter.
  - Mark the checkbox for the corresponding month of each row (e.g., for Q4: row 1 Jan, row 2 Feb, row 3 Mar).
  - Calculate `Total Amount` as the sum of postpaid bills.
- **Box 2 (Landline)**: Ignored completely (left blank).
- **Box 3 (Broadband/Dongle)**: Fill using broadband bills.
  - Write values only in **Row 1**, **Row 3**, and **Row 5** (index 6, 8, 10). Rows 2, 4, and 6 are left completely empty.
  - Mark the checkbox for the corresponding month of each row (e.g. for Q4: Jan -> `Check Box_16_4`, Feb -> `Check Box_16_1_4`, Mar -> `Check Box_16_1_1_3`).
  - Write `"Broadband"` overlay text (bold, size 12) at `X=460, Y=428` on the rightmost side slightly above the dash.
  - Calculate `Total Amount_2` as the sum of broadband bills written in Rows 1, 3, and 5.
- **Totals**:
  - `Total Billed Amount` = Box 1 Total + Box 3 Total.
  - `Total Claimed Amount` = Box 1 Total + Box 3 Total.
- **Quarter Select**: Check the corresponding checkbox based on *User Input*:
  - Q1 (Apr-Jun) -> `Check Box_17`
  - Q2 (Jul-Sep) -> `Check Box_18`
  - Q3 (Oct-Dec) -> `Check Box_19`
  - Q4 (Jan-Mar) -> `Check Box_20`
- **Level Selection**: Check the Level 13A to 10 checkbox (`Check Box_21`) by default.

---

## 4. Implementation Status
All requirements are successfully met:
- **Configuration File Integration**: Created `config.cfg` and `config.cfg.template` files in the repository. Removed all hardcoded employee detail macros from Python.
- **Zero-User Interaction**: Removed both the LAN Entry No and Quarter selection prompts from the command-line CLI. LAN Entry No is loaded from `config.cfg` and Quarter is detected automatically from the bills directory, enabling instant, single-run execution.
- **Plan-Independent Parser**: Removed hardcoded plan amount thresholds. The parser dynamically extracts amount values using amount labels and decimal scanning, meaning it is immune to future plan changes.
- **Automated Quarter Detection**: Removed quarter prompt from user inputs. The billing quarter is automatically analyzed from the parsed bills, resolving the appropriate box and checkbox mapping without manual intervention.
- **Missing Month Safety Check**: Checks if any month has zero bills in the target quarter, presenting the user with an interactive prompt to proceed (keeping the month blank) or exit.
- **Broadband Box 3 Mapping**: Filled Box 3 instead of Box 2; values are written in Rows 1, 3, and 5 of Box 3. Box 2 remains completely empty.
- **Broadband Connection Label**: Dynamic overlay draws the word `"Broadband"` in a larger, bold font (size 12) on the rightmost side slightly above the dash (`X=460, Y=428`).
- **Level Checkbox**: The `Level 13A to 10` checkbox is checked automatically.
- **Bottom Date Field**: The bottom-left date field (`Text Field`) next to the signature is populated with the current date.
- **Tailored Font Sizes**:
  - Resized metadata fields and `Amount`/`Total` fields to **10.0pt** for excellent legibility.
  - Resized `Invoice No` fields to **7.5pt** to avoid column truncation.
  - Other fields (such as `Service Provider`) preserve their default template auto-scaled sizes.
- **Forced Rendering**: Set `/NeedAppearances` to `False` and selectively deleted `/AP` streams for resized fields to guarantee custom rendering while leaving other fields untouched.
- **Warnings Logging**: The tool scans parsed bills and prints warning messages to the console for any fields (Provider, Invoice No, Amount, Month) that were not successfully found.
- **Documentation**: Formulated architectural layout and sequence flow charts in [architecture_design.md](file:///home/bikash/workera/personal_git/telephone-bill-maker/Document/architecture_design.md).
