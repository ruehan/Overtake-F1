import json
import time
from motorsport_selenium_scraper import MotorsportSeleniumScraper
from datetime import datetime
import os

class BulkDriverScraper:
    def __init__(self):
        self.scraper = MotorsportSeleniumScraper(headless=True)
        self.output_file = "driver_career_stats.json"
        self.season_2025_file = "driver_2025_season_stats.json"
        
        # F1 2025 드라이버 목록 (motorsportstats.com slug 형식)
        self.f1_drivers = {
            "max-verstappen": {"number": 33, "name": "Max Verstappen"},
            "lando-norris": {"number": 4, "name": "Lando Norris"},
            "oscar-piastri": {"number": 81, "name": "Oscar Piastri"},
            "charles-leclerc": {"number": 16, "name": "Charles Leclerc"},
            "lewis-hamilton": {"number": 44, "name": "Lewis Hamilton"},
            "george-russell": {"number": 63, "name": "George Russell"},
            "andrea-kimi-antonelli": {"number": 12, "name": "Andrea Kimi Antonelli"},
            "carlos-sainz": {"number": 55, "name": "Carlos Sainz"},
            "alexander-albon": {"number": 23, "name": "Alexander Albon"},
            "fernando-alonso": {"number": 14, "name": "Fernando Alonso"},
            "lance-stroll": {"number": 18, "name": "Lance Stroll"},
            "pierre-gasly": {"number": 10, "name": "Pierre Gasly"},
            "esteban-ocon": {"number": 31, "name": "Esteban Ocon"},
            "jack-doohan": {"number": 7, "name": "Jack Doohan"},
            "franco-colapinto": {"number": 43, "name": "Franco Colapinto"},
            "yuki-tsunoda": {"number": 22, "name": "Yuki Tsunoda"},
            "liam-lawson": {"number": 30, "name": "Liam Lawson"},
            "isack-hadjar": {"number": 6, "name": "Isack Hadjar"},
            "nico-hulkenberg": {"number": 27, "name": "Nico Hulkenberg"},
            "gabriel-bortoleto": {"number": 5, "name": "Gabriel Bortoleto"},
            "oliver-bearman": {"number": 87, "name": "Oliver Bearman"}
        }
    
    def scrape_all_drivers(self):
        """모든 드라이버의 커리어 통계를 스크래핑"""
        results = {
            "scraped_at": datetime.now().isoformat(),
            "total_drivers": len(self.f1_drivers),
            "successful_scrapes": 0,
            "failed_scrapes": 0,
            "drivers": {}
        }
        
        print(f"Starting bulk scraping for {len(self.f1_drivers)} drivers...")
        
        for i, (driver_slug, driver_info) in enumerate(self.f1_drivers.items(), 1):
            print(f"\n[{i}/{len(self.f1_drivers)}] Processing {driver_info['name']} ({driver_slug})...")
            
            try:
                # 스크래핑 실행
                driver_stats = self.scraper.get_driver_career_stats(driver_slug)
                
                if driver_stats and driver_stats.get('extracted_stats'):
                    # 성공적으로 데이터를 가져온 경우
                    results["drivers"][driver_slug] = {
                        "name": driver_info["name"],
                        "number": driver_info["number"],
                        "slug": driver_slug,
                        "scraped_at": datetime.now().isoformat(),
                        "stats": driver_stats["extracted_stats"],
                        "season_2025_data": driver_stats.get("season_2025_data", {}),
                        "url": driver_stats["url"],
                        "success": True
                    }
                    results["successful_scrapes"] += 1
                    
                    print(f"✅ Success: {driver_info['name']}")
                    print(f"   Stats: {driver_stats['extracted_stats']}")
                    if driver_stats.get("season_2025_data"):
                        print(f"   2025 Season: {driver_stats['season_2025_data']}")
                    
                else:
                    # 실패한 경우
                    results["drivers"][driver_slug] = {
                        "name": driver_info["name"],
                        "number": driver_info["number"],
                        "slug": driver_slug,
                        "scraped_at": datetime.now().isoformat(),
                        "stats": {},
                        "url": f"https://motorsportstats.com/driver/{driver_slug}/summary/series/fia-formula-one-world-championship",
                        "success": False,
                        "error": "No stats extracted"
                    }
                    results["failed_scrapes"] += 1
                    
                    print(f"❌ Failed: {driver_info['name']} - No stats extracted")
                    
            except Exception as e:
                # 예외 발생한 경우
                results["drivers"][driver_slug] = {
                    "name": driver_info["name"],
                    "number": driver_info["number"],
                    "slug": driver_slug,
                    "scraped_at": datetime.now().isoformat(),
                    "stats": {},
                    "url": f"https://motorsportstats.com/driver/{driver_slug}/summary/series/fia-formula-one-world-championship",
                    "success": False,
                    "error": str(e)
                }
                results["failed_scrapes"] += 1
                
                print(f"❌ Error: {driver_info['name']} - {str(e)}")
            
            # 요청 간 딜레이 (서버 부하 방지)
            if i < len(self.f1_drivers):
                print(f"   Waiting 3 seconds before next request...")
                time.sleep(3)
        
        return results
    
    def scrape_2025_season_data(self):
        """2025년 시즌 데이터 별도 스크래핑"""
        results = {
            "scraped_at": datetime.now().isoformat(),
            "season": 2025,
            "total_drivers": len(self.f1_drivers),
            "successful_scrapes": 0,
            "failed_scrapes": 0,
            "drivers": {}
        }
        
        print(f"\nScraping 2025 season data for {len(self.f1_drivers)} drivers...")
        
        for i, (driver_slug, driver_info) in enumerate(self.f1_drivers.items(), 1):
            print(f"\n[{i}/{len(self.f1_drivers)}] Getting 2025 season data for {driver_info['name']}...")
            
            try:
                # 2025년 시즌 결과 페이지 스크래핑
                season_data = self.scraper.get_driver_season_results(driver_slug, 2025)
                
                if season_data and season_data.get('race_results'):
                    # 2025년 시즌 통계 계산
                    race_results = season_data['race_results']
                    season_stats = {
                        "wins": 0,
                        "podiums": 0,
                        "poles": 0,
                        "fastest_laps": 0,
                        "points": 0,
                        "races_entered": len(race_results),
                        "dnf": 0,
                        "best_finish": None,
                        "average_finish": 0
                    }
                    
                    total_finish_positions = []
                    
                    for race in race_results:
                        # 결과 파싱 (테이블 헤더에 따라 조정 필요)
                        if len(race) >= 4:  # 최소 필요한 데이터가 있는 경우
                            try:
                                position = race.get('Position', race.get('Pos', ''))
                                if position and position.isdigit():
                                    pos = int(position)
                                    total_finish_positions.append(pos)
                                    
                                    if pos == 1:
                                        season_stats["wins"] += 1
                                    if pos <= 3:
                                        season_stats["podiums"] += 1
                                    
                                    # 최고 성적 업데이트
                                    if season_stats["best_finish"] is None or pos < season_stats["best_finish"]:
                                        season_stats["best_finish"] = pos
                                
                                # 포인트 계산
                                points = race.get('Points', race.get('Pts', '0'))
                                if points and points.replace('.', '').isdigit():
                                    season_stats["points"] += float(points)
                                
                            except (ValueError, KeyError):
                                continue
                    
                    # 평균 순위 계산
                    if total_finish_positions:
                        season_stats["average_finish"] = sum(total_finish_positions) / len(total_finish_positions)
                    
                    results["drivers"][driver_slug] = {
                        "name": driver_info["name"],
                        "number": driver_info["number"],
                        "slug": driver_slug,
                        "scraped_at": datetime.now().isoformat(),
                        "season_stats": season_stats,
                        "race_results": race_results,
                        "url": season_data["url"],
                        "success": True
                    }
                    results["successful_scrapes"] += 1
                    
                    print(f"✅ Success: {driver_info['name']} - {season_stats}")
                    
                else:
                    results["drivers"][driver_slug] = {
                        "name": driver_info["name"],
                        "number": driver_info["number"],
                        "slug": driver_slug,
                        "scraped_at": datetime.now().isoformat(),
                        "season_stats": {},
                        "race_results": [],
                        "url": f"https://motorsportstats.com/driver/{driver_slug}/results/series/fia-formula-one-world-championship/2025",
                        "success": False,
                        "error": "No race results found"
                    }
                    results["failed_scrapes"] += 1
                    
                    print(f"❌ Failed: {driver_info['name']} - No race results")
                    
            except Exception as e:
                results["drivers"][driver_slug] = {
                    "name": driver_info["name"],
                    "number": driver_info["number"],
                    "slug": driver_slug,
                    "scraped_at": datetime.now().isoformat(),
                    "season_stats": {},
                    "race_results": [],
                    "url": f"https://motorsportstats.com/driver/{driver_slug}/results/series/fia-formula-one-world-championship/2025",
                    "success": False,
                    "error": str(e)
                }
                results["failed_scrapes"] += 1
                
                print(f"❌ Error: {driver_info['name']} - {str(e)}")
            
            # 요청 간 딜레이
            if i < len(self.f1_drivers):
                time.sleep(2)
        
        return results
    
    def save_results(self, results):
        """결과를 JSON 파일로 저장"""
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"\n✅ Results saved to {self.output_file}")
            return True
        except Exception as e:
            print(f"❌ Error saving results: {e}")
            return False
    
    def load_existing_results(self):
        """기존 결과 파일 로드"""
        if os.path.exists(self.output_file):
            try:
                with open(self.output_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading existing results: {e}")
        return None
    
    def print_summary(self, results):
        """스크래핑 결과 요약 출력"""
        print("\n" + "="*60)
        print("BULK SCRAPING SUMMARY")
        print("="*60)
        print(f"Total drivers: {results['total_drivers']}")
        print(f"Successful: {results['successful_scrapes']}")
        print(f"Failed: {results['failed_scrapes']}")
        print(f"Success rate: {results['successful_scrapes']/results['total_drivers']*100:.1f}%")
        
        print("\n📊 SUCCESSFUL DRIVERS:")
        for slug, data in results["drivers"].items():
            if data["success"]:
                stats = data["stats"]
                print(f"  {data['name']} (#{data['number']}): "
                      f"Starts: {stats.get('starts', 'N/A')}, "
                      f"Wins: {stats.get('wins', 'N/A')}, "
                      f"Podiums: {stats.get('podiums', 'N/A')}")
        
        if results["failed_scrapes"] > 0:
            print("\n❌ FAILED DRIVERS:")
            for slug, data in results["drivers"].items():
                if not data["success"]:
                    print(f"  {data['name']} (#{data['number']}): {data.get('error', 'Unknown error')}")
    
    def save_season_results(self, results):
        """2025년 시즌 결과를 JSON 파일로 저장"""
        try:
            with open(self.season_2025_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"\n✅ 2025 season results saved to {self.season_2025_file}")
            return True
        except Exception as e:
            print(f"❌ Error saving 2025 season results: {e}")
            return False
    
    def run(self):
        """전체 스크래핑 프로세스 실행"""
        try:
            print("Starting bulk driver statistics scraping...")
            
            # 기존 결과 확인
            existing_results = self.load_existing_results()
            if existing_results:
                print(f"Found existing results from {existing_results.get('scraped_at', 'unknown time')}")
                user_input = input("Do you want to continue with fresh scraping? (y/n): ").strip().lower()
                if user_input != 'y':
                    print("Scraping cancelled.")
                    return
            
            # 1. 커리어 통계 스크래핑
            print("\n🏆 PHASE 1: Career Statistics Scraping")
            print("=" * 50)
            career_results = self.scrape_all_drivers()
            
            # 커리어 통계 저장
            if self.save_results(career_results):
                self.print_summary(career_results)
            
            # 2025년 시즌 데이터는 이제 career summary에서 함께 추출됨
            print("\n✅ 2025 season data is now extracted from career summary tables")
            
        except KeyboardInterrupt:
            print("\n⏹️  Scraping interrupted by user")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
        finally:
            # 브라우저 종료
            self.scraper.close()
            print("\n✅ Browser closed")
    
    def print_season_summary(self, results):
        """2025년 시즌 스크래핑 결과 요약 출력"""
        print("\n" + "="*60)
        print("2025 SEASON SCRAPING SUMMARY")
        print("="*60)
        print(f"Total drivers: {results['total_drivers']}")
        print(f"Successful: {results['successful_scrapes']}")
        print(f"Failed: {results['failed_scrapes']}")
        print(f"Success rate: {results['successful_scrapes']/results['total_drivers']*100:.1f}%")
        
        if results["successful_scrapes"] > 0:
            print("\n🏁 2025 SEASON LEADERS:")
            successful_drivers = [(slug, data) for slug, data in results["drivers"].items() if data["success"]]
            
            # 승수 순 정렬
            wins_leaders = sorted(successful_drivers, key=lambda x: x[1]["season_stats"].get("wins", 0), reverse=True)[:5]
            print("  Wins:")
            for slug, data in wins_leaders:
                wins = data["season_stats"].get("wins", 0)
                print(f"    {data['name']}: {wins}")
            
            # 포인트 순 정렬
            points_leaders = sorted(successful_drivers, key=lambda x: x[1]["season_stats"].get("points", 0), reverse=True)[:5]
            print("  Points:")
            for slug, data in points_leaders:
                points = data["season_stats"].get("points", 0)
                print(f"    {data['name']}: {points}")
        
        if results["failed_scrapes"] > 0:
            print("\n❌ FAILED DRIVERS:")
            for slug, data in results["drivers"].items():
                if not data["success"]:
                    print(f"  {data['name']} (#{data['number']}): {data.get('error', 'Unknown error')}")

if __name__ == "__main__":
    scraper = BulkDriverScraper()
    scraper.run()