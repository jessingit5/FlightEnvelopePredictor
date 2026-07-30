import os
import time
import requests
import pandas as pd
import mwparserfromhell as mwp
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "portfolio-project/1.0 (personal learning project)"}
LIST_PAGE_URL = "https://en.wikipedia.org/wiki/List_of_active_United_States_military_aircraft"
OUTPUT_FILE = "data/aircraft_specs.csv"
DELAY_BETWEEN_REQUESTS = 1.0

FIELD_MAP = {
    "crew": "crew",
    "length ft": "length_ft",
    "span ft": "wingspan_ft",
    "height ft": "height_ft",
    "wing area sqft": "wing_area_sqft",
    "empty weight lb": "empty_weight_lb",
    "gross weight lb": "gross_weight_lb",
    "max takeoff weight lb": "max_takeoff_weight_lb",
    "eng1 number": "engine_count",
    "eng1 lbf": "engine_thrust_lbf",
    "eng1 lbf-ab": "engine_thrust_ab_lbf",
    "max speed mach": "max_speed_mach",
    "max speed kts": "max_speed_kts",
    "cruise speed kts": "cruise_speed_kts",
    "combat range nmi": "combat_range_nmi",
    "ferry range nmi": "ferry_range_nmi",
    "range nmi": "range_nmi",
    "ceiling ft": "service_ceiling_ft",
}

def get_aircraft_list():
    print("Requesting Wikipedia page...")
    try:
        response = requests.get(LIST_PAGE_URL, headers=HEADERS, timeout=15)
        print("Got response:", response.status_code)
        response.raise_for_status()
    except requests.RequestException as e:
        print("Request failed:", e)
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    tables = soup.find_all("table", class_="wikitable")
    print("Found tables:", len(tables))

    titles = []
    for table in tables:
        for row in table.find_all("tr"):
            first_cell = row.find("td")
            if first_cell is None:
                continue
            link = first_cell.find("a")
            if link is None:
                continue
            title = link.get("title")
            if title:
                titles.append(title)

    return list(dict.fromkeys(titles))

def get_wikitext(title, max_retries=3):
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "prop": "revisions",
        "rvprop": "content",
        "rvslots": "main",
        "format": "json",
        "titles": title,
        "redirects": 1,
    }
 
    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, headers=HEADERS, timeout=15)
        except requests.RequestException:
            return None
 
        if response.status_code == 429:
            wait_seconds = int(response.headers.get("retry-after", 30))
            print(f"    rate limited, waiting {wait_seconds}s...")
            time.sleep(wait_seconds)
            continue
 
        try:
            page = next(iter(response.json()["query"]["pages"].values()))
        except (ValueError, KeyError):
            return None
 
        if "revisions" not in page:
            return None
        return page["revisions"][0]["slots"]["main"]["*"]
 
    return None

def first_number(text):
    """Grab the first word in a string that can be read as a number."""
    if not text:
        return None
    for word in text.replace(",", "").split():
        try:
            return float(word)
        except ValueError:
            continue
    return None

def get_spec_template(wikitext):
    """Find the {{Aircraft specs ...}} template inside a page's wikitext."""
    parsed = mwp.parse(wikitext)
    for template in parsed.filter_templates():
        if template.name.strip().lower().startswith("aircraft spec"):
            return template
    return None

def extract_features(title):
    """Return a dict of numeric specs for one aircraft, or None if unavailable."""
    wikitext = get_wikitext(title)
    if wikitext is None:
        return None
 
    template = get_spec_template(wikitext)
    if template is None:
        return None
 
    row = {"aircraft": title}
    for wiki_field, column_name in FIELD_MAP.items():
        if template.has(wiki_field):
            clean_text = template.get(wiki_field).value.strip_code().strip()
            row[column_name] = first_number(clean_text)
        else:
            row[column_name] = None
    return row



def main():
    print("Step 1: fetching aircraft list...")
    aircraft_titles = get_aircraft_list()
    print(f"  found {len(aircraft_titles)} unique aircraft")
 
    print("Step 2: fetching specs for each aircraft...")
    rows = []
    skipped = []
    for i, title in enumerate(aircraft_titles, start=1):
        row = extract_features(title)
        if row is None:
            skipped.append(title)
        else:
            rows.append(row)
 
        if i % 20 == 0 or i == len(aircraft_titles):
            print(f"  processed {i}/{len(aircraft_titles)} "
                  f"({len(rows)} ok, {len(skipped)} skipped)")
 
        time.sleep(DELAY_BETWEEN_REQUESTS)
 
    df = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)
 
    print(f"\nDone. Saved {len(df)} aircraft to {OUTPUT_FILE}")
    print(f"Skipped {len(skipped)} pages with no usable spec template:")
    for title in skipped:
        print(f"  - {title}")
 
 
if __name__ == "__main__":
    main()