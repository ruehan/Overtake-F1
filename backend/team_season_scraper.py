import json
import time
from motorsport_selenium_scraper import MotorsportSeleniumScraper
from datetime import datetime
import os

class TeamSeasonScraper:
    def __init__(self):
        self.scraper = MotorsportSeleniumScraper(headless=True)
        self.output_file = "team_2025_season_stats.json"
        
        # F1 2025 팀 목록 (motorsportstats.com slug 형식)
        self.f1_teams = {
            "mclaren": {"name": "McLaren", "full_name": "McLaren Formula 1 Team"},
            "ferrari-2": {"name": "Ferrari", "full_name": "Scuderia Ferrari"},
            "mercedes": {"name": "Mercedes", "full_name": "Mercedes-AMG Petronas Formula One Team"},
            "red-bull-racing": {"name": "Red Bull", "full_name": "Oracle Red Bull Racing"},
            "aston-martin": {"name": "Aston Martin", "full_name": "Aston Martin Aramco Formula One Team"},
            "alpine": {"name": "Alpine", "full_name": "BWT Alpine F1 Team"},
            "williams": {"name": "Williams", "full_name": "Atlassian Williams Racing"},
            "haas": {"name": "Haas", "full_name": "MoneyGram Haas F1 Team"},
            "sauber": {"name": "Kick Sauber", "full_name": "Stake F1 Team Kick Sauber"},
            "visa-cash-app-rb-f1-team": {"name": "RB", "full_name": "Visa Cash App RB Formula One Team"}
        }
    
    def scrape_all_teams(self):
        """모든 팀의 2025 시즌 통계를 스크래핑"""
        results = {
            "scraped_at": datetime.now().isoformat(),
            "season": 2025,
            "total_teams": len(self.f1_teams),
            "successful_scrapes": 0,
            "failed_scrapes": 0,
            "teams": {}
        }
        
        print(f"Starting team scraping for {len(self.f1_teams)} teams...")
        
        for i, (team_slug, team_info) in enumerate(self.f1_teams.items(), 1):
            print(f"\n[{i}/{len(self.f1_teams)}] Processing {team_info['name']} ({team_slug})...")
            
            try:
                # 스크래핑 실행
                team_stats = self.scraper.get_team_season_stats(team_slug, 2025)
                
                if team_stats and team_stats.get('season_data'):
                    # 성공적으로 데이터를 가져온 경우
                    season_data = team_stats['season_data']
                    career_data = team_stats.get('career_stats', {})
                    
                    results["teams"][team_slug] = {
                        "name": team_info["name"],
                        "full_name": team_info["full_name"],
                        "slug": team_slug,
                        "scraped_at": datetime.now().isoformat(),
                        "season_data": season_data,
                        "career_data": career_data,
                        "url": team_stats["url"],
                        "success": True
                    }
                    results["successful_scrapes"] += 1
                    
                    print(f"✅ Success: {team_info['name']}")
                    print(f"   2025: {season_data.get('season_wins')} wins, {season_data.get('season_points')} points, {season_data.get('season_championship_position')} position")
                    
                else:
                    # 실패한 경우
                    results["teams"][team_slug] = {
                        "name": team_info["name"],
                        "full_name": team_info["full_name"],
                        "slug": team_slug,
                        "scraped_at": datetime.now().isoformat(),
                        "season_data": {},
                        "career_data": {},
                        "url": f"https://motorsportstats.com/team/{team_slug}/summary/series/fia-formula-one-world-championship",
                        "success": False,
                        "error": "No season data extracted"
                    }
                    results["failed_scrapes"] += 1
                    
                    print(f"❌ Failed: {team_info['name']} - No season data extracted")
                    
            except Exception as e:
                # 예외 발생한 경우
                results["teams"][team_slug] = {
                    "name": team_info["name"],
                    "full_name": team_info["full_name"],
                    "slug": team_slug,
                    "scraped_at": datetime.now().isoformat(),
                    "season_data": {},
                    "career_data": {},
                    "url": f"https://motorsportstats.com/team/{team_slug}/summary/series/fia-formula-one-world-championship",
                    "success": False,
                    "error": str(e)
                }
                results["failed_scrapes"] += 1
                
                print(f"❌ Error: {team_info['name']} - {str(e)}")
            
            # 요청 간 딜레이 (서버 부하 방지)
            if i < len(self.f1_teams):
                print(f"   Waiting 3 seconds before next request...")
                time.sleep(3)
        
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
    
    def print_summary(self, results):
        """스크래핑 결과 요약 출력"""
        print("\n" + "="*60)
        print("TEAM SCRAPING SUMMARY")
        print("="*60)
        print(f"Total teams: {results['total_teams']}")
        print(f"Successful: {results['successful_scrapes']}")
        print(f"Failed: {results['failed_scrapes']}")
        print(f"Success rate: {results['successful_scrapes']/results['total_teams']*100:.1f}%")
        
        print("\n🏆 2025 CONSTRUCTOR STANDINGS:")
        successful_teams = [(slug, data) for slug, data in results["teams"].items() if data["success"]]
        
        # 포인트 순으로 정렬
        standings = sorted(successful_teams, key=lambda x: x[1]["season_data"].get("season_points", 0), reverse=True)
        
        for i, (slug, data) in enumerate(standings, 1):
            season = data["season_data"]
            print(f"  {i}. {data['name']}: {season.get('season_points', 0)} points, {season.get('season_wins', 0)} wins")
        
        if results["failed_scrapes"] > 0:
            print("\n❌ FAILED TEAMS:")
            for slug, data in results["teams"].items():
                if not data["success"]:
                    print(f"  {data['name']}: {data.get('error', 'Unknown error')}")
    
    def run(self):
        """전체 스크래핑 프로세스 실행"""
        try:
            print("Starting team season statistics scraping...")
            
            # 팀 시즌 통계 스크래핑
            team_results = self.scrape_all_teams()
            
            # 결과 저장
            if self.save_results(team_results):
                self.print_summary(team_results)
            
        except KeyboardInterrupt:
            print("\n⏹️  Scraping interrupted by user")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
        finally:
            # 브라우저 종료
            self.scraper.close()
            print("\n✅ Browser closed")

if __name__ == "__main__":
    scraper = TeamSeasonScraper()
    scraper.run()