import csv
import re
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

# ── CONFIGURE CHROMEDRIVER ─────────────────────────────────────────────────────
CHROMEDRIVER_PATH = '/opt/homebrew/bin/chromedriver'
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--lang=en-US")

service = Service(CHROMEDRIVER_PATH)
driver = webdriver.Chrome(service=service, options=chrome_options)
wait = WebDriverWait(driver, 20)
print("→ Driver started")

DATASOURCES = '../links/spain_links.csv'
OUTPUT_FILE = '../results/all_spain_matches.csv'

# -- HELPER FUNCTIONS ───────────────────────────────────────────────────────────

def parse_iso_date(match_time, url):
    """
    Extract day/month from strings like "30.05. 12:30" and infer year
    from the season in the URL (e.g. ".../2014-2015/...").
    Months July-Dec -> start year (2014), Jan-June -> end year (2015).
    Returns "YYYY-MM-DD".
    """

    # extract DD.MM
    m = re.search(r'(\d{1,2})\.(\d{1,2})\.', match_time)
    if not m:
        print("Date not found:", match_time)
        return None
    day, mon = int(m.group(1)), int(m.group(2))

    # find the YYYY-YYYY in the url or else YYYY
    season = re.search(r'(\d{4})-(\d{4})', url)
    if season:
        start_year, end_year = map(int, season.groups())
        year = start_year if mon >= 7 else end_year
    else:
        # 3) Fallback: first YYYY in the URL
        single = re.search(r'(\d{4})', url)
        if not single:
            print("No year found in URL:", url)
            return None
        year = int(single.group(1))

    return f"{year:04d}-{mon:02d}-{day:02d}"


# ── LOAD URLS FROM links.csv ──────────────────────────────────────────────────
with open(DATASOURCES, newline='', encoding='utf-8') as infile:
    reader = csv.reader(infile)
    urls = [row[0] for row in reader if row]

# ── OPEN matches.csv FOR OUTPUT ────────────────────────────────────────────────
with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as outfile:
    writer = csv.writer(outfile)
    writer.writerow(['team', 'iso_date'])
    
    # ── PROCESS EACH URL ─────────────────────────────────────────────────────
    for url in urls:
        print(f"→ Opening page: {url}")
        driver.get(url)
        print("→ Page opened")
        
        # Accept cookie banner if it appears
        try:
            cookie_btn = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "button#onetrust-accept-btn-handler")
            ))
            print("→ Clicking cookie banner")
            cookie_btn.click()
            time.sleep(1)
        except Exception as e:
            print("→ No cookie banner or click failed:", e)
        
        # Wait for initial matches
        try:
            wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.event__match")))
            print("→ Initial matches are present")
        except Exception as e:
            print("× Timeout waiting for initial matches:", e)
        
        # Load all fixtures via "Show more"
        print("→ Loading all fixtures via 'Show more' links…")
        while True:
            more_links = driver.find_elements(
                By.CSS_SELECTOR,
                "a.event__more.event__more--static[href='#']"
            )
            if not more_links:
                print("→ No more 'Show more' links found; all fixtures loaded")
                break

            link = more_links[0]
            # remove any overlaying iframes that grab clicks
            driver.execute_script("""
              document.querySelectorAll('iframe.zone__content').forEach(el => el.remove());
            """)
            # scroll into view and click
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", link)
            time.sleep(0.5)
            try:
                # use JS click to bypass any overlay issues
                driver.execute_script("arguments[0].click();", link)
                print("   • JS-clicked 'Show more matches'")
                time.sleep(1)
            except Exception as e:
                print("→ JS click failed; exiting load loop:", e)
                break
        
        # Scrape matches
        print("→ Scraping matches…")
        elements = driver.find_elements(By.CSS_SELECTOR, "div.event__match")
        print(f"→ Found {len(elements)} matches to process")
        
        for el in elements:
            try:
                raw_time = el.find_element(By.CSS_SELECTOR, ".event__time").text.replace("\n", " ").strip()
                dt = re.search(r"\d{1,2}\.\d{1,2}\.\s*\d{1,2}:\d{2}", raw_time)
                match_time = dt.group(0) if dt else raw_time

                raw_home = el.find_element(By.CSS_SELECTOR, ".event__homeParticipant").text
                raw_away = el.find_element(By.CSS_SELECTOR, ".event__awayParticipant").text
                home = re.sub(r"\s*\d+$", "", raw_home).strip()
                away = re.sub(r"\s*\d+$", "", raw_away).strip()

                # write to CSV
                iso_date = parse_iso_date(match_time, url)
                writer.writerow([home, iso_date])
                writer.writerow([away, iso_date])
                # still print to terminal (execution trace)
                print(f"  {match_time} — {home} vs {away} (ISO: {iso_date})")
            except NoSuchElementException as e:
                print("  PARSE ERROR:", e)

driver.quit()
print("→ Driver quit, script complete")
