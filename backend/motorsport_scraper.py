import requests
from bs4 import BeautifulSoup
import json
import time
from typing import Dict, Any, Optional

class MotorsportStatsScraper:
    def __init__(self):
        self.base_url = "https://motorsportstats.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def get_driver_career_stats(self, driver_slug: str) -> Optional[Dict[str, Any]]:
        """
        Get driver career statistics from motorsportstats.com
        
        Args:
            driver_slug: Driver name in URL format (e.g., 'esteban-ocon')
            
        Returns:
            Dictionary containing career statistics or None if failed
        """
        try:
            url = f"{self.base_url}/driver/{driver_slug}/summary/series/fia-formula-one-world-championship"
            
            print(f"Fetching data from: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for JSON data in script tags
            career_stats = {}
            
            # Find tables (if any)
            tables = soup.find_all('table')
            if tables:
                print(f"Found {len(tables)} tables")
                for i, table in enumerate(tables):
                    print(f"Table {i+1}: {table.get('class', 'no-class')}")
            
            # Look for statistics in various formats
            # Method 1: Check for JSON data in script tags
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string and 'stats' in script.string.lower():
                    try:
                        # Try to extract JSON data
                        script_content = script.string
                        if 'window.__INITIAL_STATE__' in script_content:
                            # Extract initial state data
                            start = script_content.find('window.__INITIAL_STATE__ = ') + len('window.__INITIAL_STATE__ = ')
                            end = script_content.find('};', start) + 1
                            json_str = script_content[start:end]
                            data = json.loads(json_str)
                            career_stats.update(data)
                    except (json.JSONDecodeError, ValueError):
                        continue
            
            # Method 2: Look for specific stat elements
            stat_elements = soup.find_all(['div', 'span', 'td'], class_=lambda x: x and ('stat' in x.lower() or 'result' in x.lower()))
            
            # Method 3: Look for data attributes
            data_elements = soup.find_all(attrs={'data-stat': True})
            
            # Method 4: Parse text content for common F1 statistics
            page_text = soup.get_text()
            
            # Print the page text to debug
            print(f"Page text sample: {page_text[:1000]}...")
            
            # Extract common F1 statistics patterns
            import re
            
            patterns = {
                'starts': r'[Ss]tarts[:\s]*(\d+)',
                'wins': r'[Ww]ins[:\s]*(\d+)',
                'podiums': r'[Pp]odiums[:\s]*(\d+)',
                'poles': r'[Pp]oles?[:\s]*(\d+)',
                'fastest_laps': r'[Ff]astest [Ll]aps?[:\s]*(\d+)',
                'points': r'[Pp]oints[:\s]*(\d+(?:\.\d+)?)',
                'championships': r'[Cc]hampionships[:\s]*(\d+)',
                'best_finish': r'[Bb]est [Ff]inish[:\s]*(\d+|DNF|DNS)',
                'first_entry': r'[Ff]irst [Ee]ntry[:\s]*(\d{4})',
                'last_entry': r'[Ll]ast [Ee]ntry[:\s]*(\d{4})',
                'entries': r'[Ee]ntries[:\s]*(\d+)',
                'position': r'[Pp]osition[:\s]*(\d+)'
            }
            
            extracted_stats = {}
            for stat_name, pattern in patterns.items():
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    value = match.group(1)
                    try:
                        extracted_stats[stat_name] = int(value) if value.isdigit() else value
                    except ValueError:
                        extracted_stats[stat_name] = value
            
            return {
                'driver_slug': driver_slug,
                'url': url,
                'career_stats': career_stats,
                'extracted_stats': extracted_stats,
                'tables_found': len(tables),
                'raw_text_sample': page_text[:500] + '...' if len(page_text) > 500 else page_text
            }
            
        except requests.RequestException as e:
            print(f"Request failed: {e}")
            return None
        except Exception as e:
            print(f"Error parsing data: {e}")
            return None
    
    def get_driver_season_results(self, driver_slug: str, year: int) -> Optional[Dict[str, Any]]:
        """
        Get driver season results for a specific year
        
        Args:
            driver_slug: Driver name in URL format
            year: Season year
            
        Returns:
            Dictionary containing season results or None if failed
        """
        try:
            url = f"{self.base_url}/driver/{driver_slug}/results/series/fia-formula-one-world-championship/{year}"
            
            print(f"Fetching season data from: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for race results table
            tables = soup.find_all('table')
            race_results = []
            
            for table in tables:
                rows = table.find_all('tr')
                if len(rows) > 1:  # Has header and data rows
                    headers = [th.get_text(strip=True) for th in rows[0].find_all(['th', 'td'])]
                    
                    for row in rows[1:]:
                        cells = [td.get_text(strip=True) for td in row.find_all(['td', 'th'])]
                        if len(cells) == len(headers):
                            race_result = dict(zip(headers, cells))
                            race_results.append(race_result)
            
            return {
                'driver_slug': driver_slug,
                'year': year,
                'url': url,
                'race_results': race_results,
                'tables_found': len(tables)
            }
            
        except requests.RequestException as e:
            print(f"Request failed: {e}")
            return None
        except Exception as e:
            print(f"Error parsing season data: {e}")
            return None

# Test the scraper
if __name__ == "__main__":
    scraper = MotorsportStatsScraper()
    
    # Test with Esteban Ocon
    print("Testing with Esteban Ocon...")
    ocon_stats = scraper.get_driver_career_stats('esteban-ocon')
    
    if ocon_stats:
        print("\n=== Career Stats ===")
        print(json.dumps(ocon_stats, indent=2))
    
    # Add delay to be respectful
    time.sleep(2)
    
    # Test season results
    print("\nTesting season results...")
    ocon_2024 = scraper.get_driver_season_results('esteban-ocon', 2024)
    
    if ocon_2024:
        print("\n=== 2024 Season Results ===")
        print(json.dumps(ocon_2024, indent=2))