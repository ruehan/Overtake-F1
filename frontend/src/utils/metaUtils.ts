// 메타데이터 유틸리티 함수들

interface MetaData {
  title: string;
  description: string;
  keywords: string;
  ogTitle: string;
  ogDescription: string;
  twitterTitle: string;
  twitterDescription: string;
}

export const updateMetaTags = (metaData: MetaData) => {
  // 페이지 타이틀 업데이트
  document.title = metaData.title;

  // 메타 태그 업데이트 함수
  const updateMetaTag = (name: string, content: string, property = false) => {
    const attribute = property ? 'property' : 'name';
    let meta = document.querySelector(`meta[${attribute}="${name}"]`) as HTMLMetaElement;
    
    if (!meta) {
      meta = document.createElement('meta');
      meta.setAttribute(attribute, name);
      document.head.appendChild(meta);
    }
    
    meta.setAttribute('content', content);
  };

  // 기본 메타 태그들
  updateMetaTag('description', metaData.description);
  updateMetaTag('keywords', metaData.keywords);

  // Open Graph 태그들
  updateMetaTag('og:title', metaData.ogTitle, true);
  updateMetaTag('og:description', metaData.ogDescription, true);

  // Twitter 태그들
  updateMetaTag('twitter:title', metaData.twitterTitle, true);
  updateMetaTag('twitter:description', metaData.twitterDescription, true);
};

// 언어별 메타데이터 정의
export const getMetaData = (language: 'ko' | 'en'): MetaData => {
  if (language === 'ko') {
    return {
      title: 'Overtake F1 - 실시간 F1 대시보드',
      description: '실시간 F1 대시보드 - 레이스 결과, 순위, 통계, 캘린더를 한눈에 확인하세요',
      keywords: 'F1, Formula 1, 포뮬러원, 레이스, 순위, 실시간, 대시보드',
      ogTitle: 'Overtake F1 - 실시간 F1 대시보드',
      ogDescription: '실시간 F1 대시보드 - 레이스 결과, 순위, 통계, 캘린더를 한눈에 확인하세요',
      twitterTitle: 'Overtake F1 - 실시간 F1 대시보드',
      twitterDescription: '실시간 F1 대시보드 - 레이스 결과, 순위, 통계, 캘린더를 한눈에 확인하세요'
    };
  } else {
    return {
      title: 'Overtake F1 - Real-time F1 Dashboard',
      description: 'Real-time F1 Dashboard - Check race results, standings, statistics, and calendar at a glance',
      keywords: 'F1, Formula 1, racing, standings, real-time, dashboard, motorsport',
      ogTitle: 'Overtake F1 - Real-time F1 Dashboard',
      ogDescription: 'Real-time F1 Dashboard - Check race results, standings, statistics, and calendar at a glance',
      twitterTitle: 'Overtake F1 - Real-time F1 Dashboard',
      twitterDescription: 'Real-time F1 Dashboard - Check race results, standings, statistics, and calendar at a glance'
    };
  }
};

// 페이지별 메타데이터 정의
export const getPageMetaData = (page: string, language: 'ko' | 'en'): MetaData => {
  const baseMetaData = getMetaData(language);
  
  const pageData = {
    ko: {
      standings: {
        title: 'F1 순위 - Overtake F1',
        description: '2025 F1 드라이버 및 컨스트럭터 챔피언십 순위를 실시간으로 확인하세요',
        keywords: 'F1 순위, 드라이버 순위, 컨스트럭터 순위, 챔피언십'
      },
      results: {
        title: 'F1 레이스 결과 - Overtake F1',
        description: '최신 F1 레이스 결과와 모든 라운드의 상세 결과를 확인하세요',
        keywords: 'F1 결과, 레이스 결과, 예선 결과, 그랑프리'
      },
      calendar: {
        title: 'F1 캘린더 - Overtake F1',
        description: '2025 F1 레이스 일정과 서킷 정보를 확인하세요',
        keywords: 'F1 일정, 레이스 캘린더, 그랑프리 일정, 서킷'
      },
      statistics: {
        title: 'F1 통계 - Overtake F1',
        description: 'F1 드라이버와 팀의 상세 통계 정보를 확인하세요',
        keywords: 'F1 통계, 드라이버 통계, 팀 통계, 성과 분석'
      }
    },
    en: {
      standings: {
        title: 'F1 Standings - Overtake F1',
        description: 'Check real-time 2025 F1 Driver and Constructor Championship standings',
        keywords: 'F1 standings, driver standings, constructor standings, championship'
      },
      results: {
        title: 'F1 Race Results - Overtake F1',
        description: 'Check latest F1 race results and detailed results from all rounds',
        keywords: 'F1 results, race results, qualifying results, grand prix'
      },
      calendar: {
        title: 'F1 Calendar - Overtake F1',
        description: 'Check 2025 F1 race schedule and circuit information',
        keywords: 'F1 schedule, race calendar, grand prix schedule, circuits'
      },
      statistics: {
        title: 'F1 Statistics - Overtake F1',
        description: 'Check detailed statistics for F1 drivers and teams',
        keywords: 'F1 statistics, driver statistics, team statistics, performance analysis'
      }
    }
  };

  const currentPageData = pageData[language][page as keyof typeof pageData['ko']];
  
  if (currentPageData) {
    return {
      ...baseMetaData,
      title: currentPageData.title,
      description: currentPageData.description,
      keywords: currentPageData.keywords,
      ogTitle: currentPageData.title,
      ogDescription: currentPageData.description,
      twitterTitle: currentPageData.title,
      twitterDescription: currentPageData.description
    };
  }

  return baseMetaData;
};