import os
import time
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

load_dotenv()

def run_automated_export():
    chrome_options = Options()
    download_dir = os.getcwd() 
    prefs = {"download.default_directory": download_dir}
    chrome_options.add_experimental_option("prefs", prefs)
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    wait = WebDriverWait(driver, 20)

    try:
        # 1. Login
        driver.get("https://www.imdb.com/")
        cookies = [
            {'name': 'at-main', 'value': os.getenv("IMDB_AT_MAIN"), 'domain': '.imdb.com'},
            {'name': 'ubid-main', 'value': os.getenv("IMDB_UBID_MAIN"), 'domain': '.imdb.com'},
            {'name': 'session-id', 'value': os.getenv("IMDB_SESSION_ID"), 'domain': '.imdb.com'}
        ]
        for c in cookies:
            if c['value']: driver.add_cookie(c)
        
        # 2. Trigger Exports via UI Interaction
        targets = [
            ("Ratings", f"https://www.imdb.com/user/{os.getenv('IMDB_USER_ID')}/ratings/"),
            ("Watchlist", f"https://www.imdb.com/user/{os.getenv('IMDB_USER_ID')}/watchlist/")
        ]

        for label, url in targets:
            print(f"📡 Navigating to {label} to trigger export...")
            driver.get(url)
            try:
                # Find the 'Settings' gear or 'More' menu icon and click it
                menu_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='List settings'], button[title='More']")))
                driver.execute_script("arguments[0].click();", menu_btn)
                
                # Find the 'Export' option in the dropdown
                export_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Export'] | //a[text()='Export']")))
                driver.execute_script("arguments[0].click();", export_btn)
                print(f"✅ Export requested for {label}.")
                time.sleep(2)
            except Exception:
                print(f"⚠️ UI Export button not found for {label}. Trying backup link...")
                driver.get(url + "export") # Final ditch effort at the direct URL

        # 3. Polling for the "Ready" state
        print("⏳ Polling the exports page until files are Ready...")
        for attempt in range(6): # Try for 60 seconds total
            driver.get("https://www.imdb.com/exports/")
            time.sleep(5)
            
            # Check if 'Ready' exists for both
            try:
                ready_btns = driver.find_elements(By.XPATH, "//span[contains(text(), 'Ready')]")
                if len(ready_btns) >= 2:
                    print("🎉 Newest files are ready!")
                    break
            except:
                pass
            print(f"   Wait attempt {attempt+1}/6...")
            time.sleep(5)

        # 4. Final Download
        for target in ["ratings", "Watchlist"]:
            try:
                xpath = f"//div[contains(translate(text(), 'WATCHLIST', 'watchlist'), '{target.lower()}')]/following::span[contains(text(), 'Ready')][1]"
                btn = driver.find_element(By.XPATH, xpath)
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", btn)
                print(f"💾 Downloaded: {target}")
                time.sleep(3)
            except:
                print(f"❌ Could not find newest {target} for download.")

    finally:
        driver.quit()
        print(f"Done. Check {download_dir}")

if __name__ == "__main__":
    run_automated_export()