from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time
import json
from typing import Dict, Any, Optional
import re

class MotorsportSeleniumScraper:
    def __init__(self, headless=True):
        self.setup_driver(headless)
    
    def setup_driver(self, headless=True):
        """Setup Chrome driver with options"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        
        service = Service()
        
        try:
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.wait = WebDriverWait(self.driver, 10)
        except Exception as e:
            print(f"Error setting up driver: {e}")
            raise
    
    def get_driver_career_stats(self, driver_slug: str) -> Optional[Dict[str, Any]]:
        """
        Get driver career statistics using Selenium
        """
        try:
            url = f"https://motorsportstats.com/driver/{driver_slug}/summary/series/fia-formula-one-world-championship"
            print(f"Loading page: {url}")
            
            self.driver.get(url)
            
            # Wait for page to load
            time.sleep(3)
            
            # Wait for content to load
            try:
                self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            except:
                print("Timeout waiting for page to load")
            
            # Get page source after JavaScript execution
            page_source = self.driver.page_source
            
            # Get text content
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            
            print(f"Page loaded, text length: {len(page_text)}")
            print(f"Page text sample: {page_text[:500]}...")
            
            # Look for statistics in the page
            extracted_stats = {}
            
            # Try to find specific stat elements
            try:
                # Look for stat containers
                stat_elements = self.driver.find_elements(By.CSS_SELECTOR, "[class*='stat'], [class*='number'], [class*='value']")
                print(f"Found {len(stat_elements)} potential stat elements")
                
                for element in stat_elements:
                    try:
                        text = element.text.strip()
                        if text and text.isdigit():
                            parent_text = element.find_element(By.XPATH, "..").text
                            print(f"Stat element: {text} (parent: {parent_text[:50]}...)")
                    except:
                        continue
                
                # Look for tables and extract 2025 season data
                tables = self.driver.find_elements(By.TAG_NAME, "table")
                print(f"Found {len(tables)} tables")
                
                season_2025_data = {}
                
                for i, table in enumerate(tables):
                    try:
                        table_text = table.text
                        print(f"Table {i+1}: {table_text[:200]}...")
                        
                        # Parse table for 2025 season data
                        rows = table.find_elements(By.TAG_NAME, "tr")
                        
                        if len(rows) > 1:  # Has header and data rows
                            # Get header row
                            header_cells = rows[0].find_elements(By.TAG_NAME, "th")
                            if not header_cells:
                                header_cells = rows[0].find_elements(By.TAG_NAME, "td")
                            
                            headers = [cell.text.strip() for cell in header_cells]
                            
                            # Look for 2025 data in subsequent rows
                            for row in rows[1:]:
                                cells = row.find_elements(By.TAG_NAME, "td")
                                if cells:
                                    row_data = [cell.text.strip() for cell in cells]
                                    
                                    # Check if this row contains 2025 data
                                    if row_data and "2025" in row_data[0]:
                                        print(f"Found 2025 row: {row_data}")
                                        
                                        # Map headers to values
                                        row_dict = {}
                                        for j, value in enumerate(row_data):
                                            if j < len(headers):
                                                row_dict[headers[j]] = value
                                        
                                        # Extract relevant 2025 season stats
                                        season_2025_data = {
                                            "season_wins": self._safe_int(row_dict.get("W", 0)),
                                            "season_podiums": self._safe_int(row_dict.get("PD", 0)),
                                            "season_poles": self._safe_int(row_dict.get("PP", 0)),
                                            "season_fastest_laps": self._safe_int(row_dict.get("FL", 0)),
                                            "season_points": self._safe_int(row_dict.get("P", 0)),
                                            "season_races": self._safe_int(row_dict.get("RS", 0)),
                                            "season_dnf": self._safe_int(row_dict.get("DNF", 0)),
                                            "season_best_finish": self._safe_int(row_dict.get("BR", None)),
                                            "season_best_grid": self._safe_int(row_dict.get("BG", None)),
                                            "season_avg_finish": self._safe_float(row_dict.get("AF", None)),
                                            "season_avg_grid": self._safe_float(row_dict.get("AG", None)),
                                            "season_championship_position": row_dict.get("WC", None),
                                            "season_entrant": row_dict.get("Entrant", None)
                                        }
                                        
                                        print(f"Extracted 2025 season data: {season_2025_data}")
                                        break
                    except:
                        continue
                
                # Look for CAREER STATISTICS section specifically
                career_stats_found = False
                career_stats_text = ""
                
                # Split text into lines and find CAREER STATISTICS section
                lines = page_text.split('\n')
                for i, line in enumerate(lines):
                    if 'CAREER STATISTICS' in line.upper():
                        career_stats_found = True
                        # Get the next ~50 lines after CAREER STATISTICS
                        career_stats_lines = lines[i:i+50]
                        career_stats_text = '\n'.join(career_stats_lines)
                        print(f"Found CAREER STATISTICS at line {i}")
                        print(f"Career Statistics text: {career_stats_text}")
                        break
                
                if career_stats_found:
                    # Extract specific stats from CAREER SUMMARY
                    # Pattern for "STAT VALUE" format
                    career_patterns = {
                        'starts': r'Starts\s*(\d+)',
                        'wins': r'Wins\s*(\d+)',
                        'podiums': r'Podiums\s*(\d+)', 
                        'poles': r'Poles\s*(\d+)',
                        'fastest_laps': r'Fastest Laps\s*(\d+)',
                        'points': r'Points\s*(\d+(?:\.\d+)?)',
                        'championships': r'Championships\s*(\d+)',
                        'best_finish': r'Best Finish\s*(\d+|DNF|DNS)',
                        'entries': r'Entries\s*(\d+)',
                        'dnf': r'DNF\s*(\d+)',
                        'retirements': r'Retirements\s*(\d+)',
                        'first_entry': r'First Entry\s*(\d{4})',
                        'last_entry': r'Last Entry\s*(\d{4})',
                        'years': r'Years\s*(\d+)',
                        'best_championship_position': r'Best Championship position\s*(\d+)',
                        'sprint_wins': r'Sprint Wins\s*(\d+)'
                    }
                    
                    for stat_name, pattern in career_patterns.items():
                        match = re.search(pattern, career_stats_text, re.IGNORECASE)
                        if match:
                            value = match.group(1)
                            try:
                                extracted_stats[stat_name] = int(value) if value.isdigit() else value
                                print(f"Extracted {stat_name}: {value}")
                            except ValueError:
                                extracted_stats[stat_name] = value
                else:
                    print("CAREER STATISTICS section not found, trying general patterns")
                    # Fallback to general patterns
                    general_patterns = {
                        'starts': r'[Ss]tarts[:\s]*(\d+)',
                        'wins': r'[Ww]ins[:\s]*(\d+)', 
                        'podiums': r'[Pp]odiums[:\s]*(\d+)',
                        'poles': r'[Pp]oles?[:\s]*(\d+)',
                        'fastest_laps': r'[Ff]astest [Ll]aps?[:\s]*(\d+)',
                        'points': r'[Pp]oints[:\s]*(\d+(?:\.\d+)?)',
                        'championships': r'[Cc]hampionships[:\s]*(\d+)'
                    }
                    
                    for stat_name, pattern in general_patterns.items():
                        match = re.search(pattern, page_text, re.IGNORECASE)
                        if match:
                            value = match.group(1)
                            try:
                                extracted_stats[stat_name] = int(value) if value.isdigit() else value
                            except ValueError:
                                extracted_stats[stat_name] = value
                
                # Extract from CAREER HIGHLIGHTS section (top of page)
                # Look for patterns like "468 POINTS" or "1 FASTEST LAPS"
                highlights_patterns = {
                    'total_points': r'(\d+(?:\.\d+)?)\s*POINTS',
                    'fastest_laps_total': r'(\d+)\s*FASTEST LAPS',
                    'total_starts': r'(\d+)\s*STARTS',
                    'total_wins': r'(\d+)\s*/\s*\d+\s*WINS',
                    'total_podiums': r'(\d+)\s*/\s*\d+\s*PODIUMS',
                    'total_poles': r'(\d+)\s*/\s*\d+\s*POLES',
                    'total_championships': r'(\d+)\s*/\s*\d+\s*CHAMPIONSHIPS'
                }
                
                for stat_name, pattern in highlights_patterns.items():
                    match = re.search(pattern, page_text, re.IGNORECASE)
                    if match:
                        value = match.group(1)
                        try:
                            # Only use if we don't already have this stat
                            base_name = stat_name.replace('total_', '').replace('_total', '')
                            if base_name not in extracted_stats:
                                extracted_stats[base_name] = int(value) if value.replace('.', '').isdigit() else value
                                print(f"Extracted from highlights {base_name}: {value}")
                        except ValueError:
                            pass
                
                # Try to find specific data by looking for numbers in context
                lines = page_text.split('\n')
                for line in lines:
                    line = line.strip()
                    if any(keyword in line.lower() for keyword in ['start', 'win', 'podium', 'pole', 'point', 'championship']):
                        print(f"Relevant line: {line}")
                
            except Exception as e:
                print(f"Error extracting stats: {e}")
            
            return {
                'driver_slug': driver_slug,
                'url': url,
                'extracted_stats': extracted_stats,
                'season_2025_data': season_2025_data if 'season_2025_data' in locals() else {},
                'tables_found': len(tables) if 'tables' in locals() else 0,
                'page_text_sample': page_text[:1000] + '...' if len(page_text) > 1000 else page_text
            }
            
        except Exception as e:
            print(f"Error scraping driver stats: {e}")
            return None
    
    def _safe_int(self, value):
        """Safely convert value to integer"""
        if value is None or value == '':
            return 0
        try:
            # Remove any non-digit characters except minus sign
            cleaned = ''.join(c for c in str(value) if c.isdigit() or c == '-')
            return int(cleaned) if cleaned else 0
        except (ValueError, TypeError):
            return 0
    
    def _safe_float(self, value):
        """Safely convert value to float"""
        if value is None or value == '':
            return 0.0
        try:
            # Remove any non-digit characters except minus sign and decimal point
            cleaned = ''.join(c for c in str(value) if c.isdigit() or c in '.-')
            return float(cleaned) if cleaned else 0.0
        except (ValueError, TypeError):
            return 0.0
    
    def get_team_season_stats(self, team_slug: str, year: int = 2025) -> Optional[Dict[str, Any]]:
        """
        Get team season statistics from motorsportstats.com
        """
        try:
            url = f"https://motorsportstats.com/team/{team_slug}/summary/series/fia-formula-one-world-championship"
            print(f"Loading team page: {url}")
            
            self.driver.get(url)
            
            # Wait for page to load
            time.sleep(3)
            
            # Wait for content to load
            try:
                self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            except:
                print("Timeout waiting for page to load")
            
            # Get page text
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            print(f"Page loaded, text length: {len(page_text)}")
            
            # Extract team statistics
            team_stats = {}
            
            # Look for tables and extract current season data
            tables = self.driver.find_elements(By.TAG_NAME, "table")
            print(f"Found {len(tables)} tables")
            
            season_data = {}
            
            for i, table in enumerate(tables):
                try:
                    table_text = table.text
                    print(f"Table {i+1}: {table_text[:200]}...")
                    
                    # Parse table for current season data
                    rows = table.find_elements(By.TAG_NAME, "tr")
                    
                    if len(rows) > 1:  # Has header and data rows
                        # Get header row
                        header_cells = rows[0].find_elements(By.TAG_NAME, "th")
                        if not header_cells:
                            header_cells = rows[0].find_elements(By.TAG_NAME, "td")
                        
                        headers = [cell.text.strip() for cell in header_cells]
                        
                        # Look for current year data in subsequent rows
                        for row in rows[1:]:
                            cells = row.find_elements(By.TAG_NAME, "td")
                            if cells:
                                row_data = [cell.text.strip() for cell in cells]
                                
                                # Check if this row contains current year data
                                if row_data and str(year) in row_data[0]:
                                    print(f"Found {year} row: {row_data}")
                                    
                                    # Map headers to values
                                    row_dict = {}
                                    for j, value in enumerate(row_data):
                                        if j < len(headers):
                                            row_dict[headers[j]] = value
                                    
                                    # Extract relevant season stats
                                    season_data = {
                                        "season_wins": self._safe_int(row_dict.get("W", 0)),
                                        "season_podiums": self._safe_int(row_dict.get("PD", 0)),
                                        "season_poles": self._safe_int(row_dict.get("PP", 0)),
                                        "season_fastest_laps": self._safe_int(row_dict.get("FL", 0)),
                                        "season_points": self._safe_int(row_dict.get("PTS", 0)),
                                        "season_races": self._safe_int(row_dict.get("ST", 0)),
                                        "season_dnf": self._safe_int(row_dict.get("DNF", 0)),
                                        "season_championship_position": row_dict.get("WC", None),
                                        "season_drivers": row_dict.get("Drivers", None)
                                    }
                                    
                                    print(f"Extracted {year} season data: {season_data}")
                                    break
                except:
                    continue
            
            # Look for CAREER STATISTICS section for team info
            career_stats_found = False
            career_stats_text = ""
            
            # Split text into lines and find team statistics
            lines = page_text.split('\n')
            for i, line in enumerate(lines):
                if 'CHAMPIONSHIPS' in line.upper() or 'CAREER HIGHLIGHTS' in line.upper():
                    career_stats_found = True
                    # Get the next ~30 lines after career highlights
                    career_stats_lines = lines[i:i+30]
                    career_stats_text = '\n'.join(career_stats_lines)
                    print(f"Found team career highlights at line {i}")
                    print(f"Career highlights text: {career_stats_text}")
                    break
            
            if career_stats_found:
                # Extract team career stats
                career_patterns = {
                    'total_championships': r'(\\d+)\\s*/\\s*\\d+\\s*CHAMPIONSHIPS',
                    'total_wins': r'(\\d+)\\s*/\\s*\\d+\\s*WINS',
                    'total_podiums': r'(\\d+)\\s*/\\s*\\d+\\s*PODIUMS',
                    'total_poles': r'(\\d+)\\s*/\\s*\\d+\\s*POLES',
                    'total_starts': r'STARTS\\s*(\\d+)',
                    'total_points': r'POINTS\\s*([\\d.]+)'
                }
                
                for stat_name, pattern in career_patterns.items():
                    match = re.search(pattern, career_stats_text, re.IGNORECASE)
                    if match:
                        value = match.group(1)
                        try:
                            team_stats[stat_name] = int(value)
                            print(f"Extracted {stat_name}: {value}")
                        except ValueError:
                            team_stats[stat_name] = value
            
            return {
                'team_slug': team_slug,
                'url': url,
                'career_stats': team_stats,
                'season_data': season_data,
                'year': year,
                'page_text_sample': page_text[:1000] + '...' if len(page_text) > 1000 else page_text
            }
            
        except Exception as e:
            print(f"Error scraping team stats: {e}")
            return None

    def close(self):
        """Close the driver"""
        if hasattr(self, 'driver'):
            self.driver.quit()
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        self.close()

# Test the scraper
if __name__ == "__main__":
    scraper = MotorsportSeleniumScraper(headless=False)  # Set to False to see the browser
    
    try:
        print("Testing with Esteban Ocon...")
        ocon_stats = scraper.get_driver_career_stats('esteban-ocon')
        
        if ocon_stats:
            print("\n=== Career Stats ===")
            print(json.dumps(ocon_stats, indent=2))
        else:
            print("Failed to get career stats")
            
    finally:
        scraper.close()