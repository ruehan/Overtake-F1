import requests
from bs4 import BeautifulSoup
import json
from typing import List, Dict, Any, Optional

class MotorsportStatsRaceScraper:
    def __init__(self):
        self.base_url = "https://motorsportstats.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def get_race_statistics(self, year: int, grand_prix_slug: str) -> Optional[List[Dict[str, Any]]]:
        url = f"{self.base_url}/results/fia-formula-one-world-championship/{year}/{grand_prix_slug}/stats/race"
        print(f"Fetching race statistics from: {url}")
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            tables = soup.find_all('table')
            if not tables:
                print(f"Statistics 테이블을 찾을 수 없습니다: {grand_prix_slug}")
                return None
            table = tables[0]
            rows = table.find_all('tr')
            if len(rows) < 2:
                print(f"테이블에 데이터가 없습니다: {grand_prix_slug}")
                return None
            headers = [th.get_text(strip=True) for th in rows[0].find_all(['th', 'td'])]
            results = []
            for row in rows[1:]:
                cells = [td.get_text(strip=True) for td in row.find_all(['td', 'th'])]
                if len(cells) == len(headers):
                    result = dict(zip(headers, cells))
                    results.append(result)
            return results
        except requests.RequestException as e:
            print(f"Request failed: {e}")
            return None
        except Exception as e:
            print(f"Error parsing race statistics: {e}")
            return None

if __name__ == "__main__":
    scraper = MotorsportStatsRaceScraper()
    year = 2025
    grand_prix_slugs = [
        'australian-grand-prix', 'chinese-grand-prix', 'japanese-grand-prix', 'bahrain-grand-prix',
        'saudi-arabian-grand-prix', 'miami-grand-prix', 'emilia-romagna-grand-prix', 'monaco-grand-prix',
        'spanish-grand-prix', 'canadian-grand-prix', 'austrian-grand-prix', 'british-grand-prix',
        'belgian-grand-prix', 'hungarian-grand-prix', 'dutch-grand-prix', 'italian-grand-prix',
        'azerbaijan-grand-prix', 'singapore-grand-prix', 'us-grand-prix', 'mexican-grand-prix',
        'brazilian-grand-prix', 'las-vegas-grand-prix', 'qatar-grand-prix', 'abu-dhabi-grand-prix'
    ]
    all_results = {}
    for slug in grand_prix_slugs:
        stats = scraper.get_race_statistics(year, slug)
        if stats:
            all_results[slug] = stats
        else:
            print(f"{slug}: 진행되지 않았거나 데이터 없음.")
    # 결과를 json 파일로 저장
    with open('motorsportstats_2025_race_results.json', 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print("\n모든 결과가 motorsportstats_2025_race_results.json 파일에 저장되었습니다.") 