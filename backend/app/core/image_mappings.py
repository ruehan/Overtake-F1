# F1 드라이버와 팀의 이미지 URL 매핑

# 2025 시즌 드라이버 이미지 매핑 (실제 파일명 기반)
DRIVER_IMAGES = {
    # 전체 이름 매핑
    "Lewis Hamilton": "/images/drivers/Lewis Hamilton.webp",
    "George Russell": "/images/drivers/George Russell.webp",
    "Max Verstappen": "/images/drivers/Max Verstappen.webp",
    "Charles Leclerc": "/images/drivers/Charles Leclerc.webp",
    "Carlos Sainz": "/images/drivers/Carlos Sainz.webp",
    "Lando Norris": "/images/drivers/Lando Norris.webp",
    "Oscar Piastri": "/images/drivers/Oscar Piastri.webp",
    "Pierre Gasly": "/images/drivers/Pierre Gasly.webp",
    "Esteban Ocon": "/images/drivers/Esteban Ocon.webp",
    "Fernando Alonso": "/images/drivers/Fernando Alonso.webp",
    "Lance Stroll": "/images/drivers/Lance Stroll.webp",
    "Alexander Albon": "/images/drivers/Alexander Albon.webp",
    "Yuki Tsunoda": "/images/drivers/Yuki Tsunoda.webp",
    "Nico Hülkenberg": "/images/drivers/Nico Hülkenberg.webp",
    "Oliver Bearman": "/images/drivers/Oliver Bearman.webp",
    "Liam Lawson": "/images/drivers/Liam Lawson.webp",
    "Andrea Kimi Antonelli": "/images/drivers/Andrea Kimi Antonelli.webp",
    "Gabriel Bortoleto": "/images/drivers/Gabriel Bortoleto.webp",
    "Jack Doohan": "/images/drivers/Jack Doohan.webp",
    "Isack Hadjar": "/images/drivers/Isack Hadjar.webp",
}

# 팀 로고 매핑
TEAM_LOGOS = {
    "Mercedes": "/images/teams/mercedes.png",
    "Red Bull Racing": "/images/teams/redbull.png",
    "Ferrari": "/images/teams/ferrari.png",
    "McLaren": "/images/teams/mclaren.png",
    "Alpine": "/images/teams/alpine.png",
    "Aston Martin": "/images/teams/astonmartin.png",
    "Williams": "/images/teams/williams.png",
    "AlphaTauri": "/images/teams/alphatauri.png",
    "Alfa Romeo": "/images/teams/alfaromeo.png",
    "Haas": "/images/teams/haas.png",
}

def get_driver_image(driver_name: str) -> str:
    """드라이버 이름으로 이미지 URL 가져오기"""
    # 전체 이름으로 먼저 찾기
    if driver_name in DRIVER_IMAGES:
        return DRIVER_IMAGES[driver_name]
    
    # 없으면 기본 이미지 반환
    return "/images/drivers/default.svg"

def get_team_logo(team_name: str) -> str:
    """팀 이름으로 로고 URL 가져오기"""
    return TEAM_LOGOS.get(team_name, "/images/teams/default.png")