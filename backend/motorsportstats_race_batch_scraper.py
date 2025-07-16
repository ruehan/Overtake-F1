from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time
import json

GP_SLUGS = [
    'australian-grand-prix', 'chinese-grand-prix', 'japanese-grand-prix', 'bahrain-grand-prix',
    'saudi-arabian-grand-prix', 'miami-grand-prix', 'emilia-romagna-grand-prix', 'monaco-grand-prix',
    'spanish-grand-prix', 'canadian-grand-prix', 'austrian-grand-prix', 'british-grand-prix',
    'belgian-grand-prix', 'hungarian-grand-prix', 'dutch-grand-prix', 'italian-grand-prix',
    'azerbaijan-grand-prix', 'singapore-grand-prix', 'us-grand-prix', 'mexican-grand-prix',
    'brazilian-grand-prix', 'las-vegas-grand-prix', 'qatar-grand-prix', 'abu-dhabi-grand-prix'
]

YEAR = 2025
OUTPUT_JSON = 'motorsportstats_2025_race_results.json'


def get_race_results_table(driver, wait, year, grand_prix_slug):
    url = f"https://motorsportstats.com/results/fia-formula-one-world-championship/{year}/{grand_prix_slug}/classification"
    print(f"Loading page: {url}")
    driver.get(url)
    time.sleep(3)
    try:
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
    except:
        print(f"Timeout waiting for table: {grand_prix_slug}")
        return None
    tables = driver.find_elements(By.TAG_NAME, "table")
    if not tables:
        print(f"No tables found: {grand_prix_slug}")
        return None
    # Results 테이블만 추출: 헤더가 'Pos'로 시작하는 테이블
    target_table = None
    for table in tables:
        headers = [cell.text.strip() for cell in table.find_elements(By.TAG_NAME, "th")]
        if headers and headers[0].lower() in ["pos", "position"]:
            target_table = table
            break
    if not target_table:
        print(f"No Results table found: {grand_prix_slug}")
        return None
    rows = target_table.find_elements(By.TAG_NAME, "tr")
    if len(rows) < 2:
        print(f"No data rows: {grand_prix_slug}")
        return None
    headers = [cell.text.strip() for cell in rows[0].find_elements(By.TAG_NAME, "th")]
    # 헤더 매핑: motorsportstats 표준 필드로 변환
    header_map = {
        'Pos': 'POS',
        '№': '№',
        'Driver': 'DRIVER',
        'Team': 'TEAM',
        'Laps': 'LAPS',
        'Time': 'TIME',
        'Gap': 'GAP',
        'Interval': 'INTERVAL',
        'KPH': 'KPH',
        'Best': 'BEST',
        'Lap': 'LAP',
    }
    mapped_headers = [header_map.get(h, h.upper()) for h in headers]
    results = []
    for row in rows[1:]:
        cells = [cell.text.strip() for cell in row.find_elements(By.TAG_NAME, "td")]
        if len(cells) == len(mapped_headers):
            results.append(dict(zip(mapped_headers, cells)))
    return results


def main():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    service = Service()
    driver = webdriver.Chrome(service=service, options=chrome_options)
    wait = WebDriverWait(driver, 10)
    all_results = {}
    try:
        for slug in GP_SLUGS:
            results = get_race_results_table(driver, wait, YEAR, slug)
            if results:
                all_results[slug] = results
            else:
                print(f"{slug}: 진행되지 않았거나 데이터 없음.")
        with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        print(f"\n모든 결과가 {OUTPUT_JSON} 파일에 저장되었습니다.")
    finally:
        driver.quit()

if __name__ == "__main__":
    main() 