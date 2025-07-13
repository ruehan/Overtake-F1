import React, { useState } from 'react';
import './App.css';
import Dashboard from './pages/Dashboard';
import StandingsPage from './pages/StandingsPage';
import CalendarPage from './pages/CalendarPage';
import RaceResultsPage from './pages/RaceResultsPage';
import StandingsProgressionPage from './pages/StandingsProgressionPage';
import RaceWeekendsPage from './pages/RaceWeekendsPage';
import StatisticsPage from './pages/StatisticsPage';
import CircuitsPage from './pages/CircuitsPage';
import { LanguageProvider, useLanguage } from './contexts/LanguageContext';

const AppContent = () => {
  const [currentPage, setCurrentPage] = useState('dashboard');
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const { language, setLanguage, t } = useLanguage();

  const renderPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return <Dashboard />;
      case 'standings':
        return <StandingsPage />;
      case 'progression':
        return <StandingsProgressionPage />;
      case 'weekends':
        return <RaceWeekendsPage />;
      case 'statistics':
        return <StatisticsPage />;
      case 'circuits':
        return <CircuitsPage />;
      case 'calendar':
        return <CalendarPage />;
      case 'results':
        return <RaceResultsPage />;
      default:
        return <Dashboard />;
    }
  };

  const handlePageChange = (page: string) => {
    setCurrentPage(page);
    setIsMobileMenuOpen(false); // 모바일에서 페이지 변경 시 메뉴 닫기
  };

  return (
    <div className="f1-app">
      <nav className="f1-nav">
        <div className="f1-nav-brand">
          <h1>🏎️ OVERTAKE</h1>
        </div>

        {/* Mobile Menu Toggle */}
        <button 
          className="f1-nav-toggle"
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          aria-label="Toggle navigation"
        >
          <span></span>
          <span></span>
          <span></span>
        </button>

        <div className={`f1-nav-links ${isMobileMenuOpen ? 'mobile-open' : ''}`}>
          <button 
            className={currentPage === 'dashboard' ? 'active' : ''}
            onClick={() => handlePageChange('dashboard')}
          >
            <span className="nav-icon">🏠</span>
            {t('nav.live')}
          </button>
          <button 
            className={currentPage === 'standings' ? 'active' : ''}
            onClick={() => handlePageChange('standings')}
          >
            <span className="nav-icon">🏆</span>
            {t('nav.standings')}
          </button>
          <button 
            className={currentPage === 'progression' ? 'active' : ''}
            onClick={() => handlePageChange('progression')}
          >
            <span className="nav-icon">📈</span>
            {t('nav.progression')}
          </button>
          <button 
            className={currentPage === 'weekends' ? 'active' : ''}
            onClick={() => handlePageChange('weekends')}
          >
            <span className="nav-icon">🏁</span>
            {t('nav.weekends')}
          </button>
          <button 
            className={currentPage === 'statistics' ? 'active' : ''}
            onClick={() => handlePageChange('statistics')}
          >
            <span className="nav-icon">📊</span>
            {t('nav.statistics')}
          </button>
          <button 
            className={currentPage === 'circuits' ? 'active' : ''}
            onClick={() => handlePageChange('circuits')}
          >
            <span className="nav-icon">🛣️</span>
            {t('nav.circuits')}
          </button>
          <button 
            className={currentPage === 'calendar' ? 'active' : ''}
            onClick={() => handlePageChange('calendar')}
          >
            <span className="nav-icon">📅</span>
            {t('nav.calendar')}
          </button>
          <button 
            className={currentPage === 'results' ? 'active' : ''}
            onClick={() => handlePageChange('results')}
          >
            <span className="nav-icon">🏁</span>
            {t('nav.results')}
          </button>
        </div>
        
        {/* Language Toggle */}
        <div className="f1-nav-lang">
          <button
            className="f1-lang-toggle"
            onClick={() => setLanguage(language === 'en' ? 'ko' : 'en')}
          >
            <span className="lang-flag">{language === 'en' ? '🇰🇷' : '🇺🇸'}</span>
            {language === 'en' ? '한글' : 'ENG'}
          </button>
        </div>
      </nav>
      
      <main className="f1-main">
        {renderPage()}
      </main>
    </div>
  );
};

function App() {
  return (
    <LanguageProvider>
      <AppContent />
    </LanguageProvider>
  );
}

export default App;