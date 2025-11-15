from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import os
import time
import json

# ------------------------------
# CONFIG
# ------------------------------
# Load accounts from accounts.json (expects a JSON object mapping username -> password)
_accounts_file = os.path.join(os.path.dirname(__file__), "accounts.json")
try:
    with open(_accounts_file, "r", encoding="utf-8") as f:
        accounts = json.load(f)
    if not isinstance(accounts, dict):
        raise ValueError("accounts.json must contain a JSON object mapping usernames to passwords")
except Exception as e:
    print(f"Error loading accounts from {_accounts_file}: {e}")
    accounts = {}

import base64
def b64(x): return base64.b64decode(x).decode()

# ------------------------------
# SELENIUM SETUP
# ------------------------------
opts = Options()
opts.add_argument("--no-sandbox")
opts.add_argument("--disable-blink-features=AutomationControlled")

driver = webdriver.Chrome(options=opts)
# ------------------------------
# MAIN LOOP
# ------------------------------
all_results = {}

for username, pwd in accounts.items():

    print(f"Logging in: {username}")
    driver.get("https://store.steampowered.com/login")
    
    time.sleep(3)

    # Get all matching inputs
    inputs = driver.find_elements(
        By.XPATH, "//input[@type='text' and @value='' and not(@tabindex='-1')]"
    )
    # Pick the second one (index 1)
    inputs[1].send_keys(username)

    # Password
    inputs = driver.find_element(By.XPATH, "//input[@type='password']").send_keys(b64(pwd))
    time.sleep(2)
    # Click login
    inputs = driver.find_elements(By.XPATH, "//button[@type='submit']")
    # pick the second one (index 1)
    inputs[1].click()
    time.sleep(3)  # wait for login to process
    # Go to licenses page and collect Steam Store entries
    driver.get("https://store.steampowered.com/account/licenses/")
    time.sleep(3)

    try:
        tables = driver.find_elements(By.CSS_SELECTOR, "table.account_table")
        if not tables:
            print(f"Password for {username} appears to be incorrect or no licenses found.")
            continue
        table = tables[0]
        rows = table.find_elements(By.CSS_SELECTOR, "tbody tr")
    except Exception as e:
        print("Could not locate licenses table:", e)
        rows = []

    matches = []
    for idx, row in enumerate(rows):
        # ignore the first tr
        if idx == 0:
            continue
        try:
            acq_td = row.find_element(By.CSS_SELECTOR, "td.license_acquisition_col")
            if "steam" in acq_td.text.lower():
                # save each td as a separate line for this tr
                cells = [td.text.strip() for td in row.find_elements(By.TAG_NAME, "td")]
                matches.append("\n".join(cells))
        except Exception:
            # skip rows that don't match the expected structure
            continue

    # write results to a per-account txt file
    out_file = f"{username}_licenses.txt"
    with open(out_file, "w", encoding="utf-8") as fh:
        if matches:
            fh.write("\n\n".join(matches))
        else:
            fh.write("No Steam Store licenses found.")

    print(f"Wrote {len(matches)} Steam Store license(s) to {out_file}")

    # Logout / reset session for next account: clear cookies and go back to login
    driver.execute_script("Logout();")
    time.sleep(4)  # wait for reload after clearing cookies

driver.quit()
print("ALL DONE!")
