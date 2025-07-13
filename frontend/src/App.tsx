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

  return (
    <div className="f1-app">
      <nav className="f1-nav">
        <div className="f1-nav-brand">
          <h1>🏎️ F1 LIVE</h1>
        </div>
        <div className="f1-nav-links">
          <button 
            className={currentPage === 'dashboard' ? 'active' : ''}
            onClick={() => setCurrentPage('dashboard')}
          >
            {t('nav.live')}
          </button>
          <button 
            className={currentPage === 'standings' ? 'active' : ''}
            onClick={() => setCurrentPage('standings')}
          >
            {t('nav.standings')}
          </button>
          <button 
            className={currentPage === 'progression' ? 'active' : ''}
            onClick={() => setCurrentPage('progression')}
          >
            {t('nav.progression')}
          </button>
          <button 
            className={currentPage === 'weekends' ? 'active' : ''}
            onClick={() => setCurrentPage('weekends')}
          >
            {t('nav.weekends')}
          </button>
          <button 
            className={currentPage === 'statistics' ? 'active' : ''}
            onClick={() => setCurrentPage('statistics')}
          >
            {t('nav.statistics')}
          </button>
          <button 
            className={currentPage === 'circuits' ? 'active' : ''}
            onClick={() => setCurrentPage('circuits')}
          >
            {t('nav.circuits')}
          </button>
          <button 
            className={currentPage === 'calendar' ? 'active' : ''}
            onClick={() => setCurrentPage('calendar')}
          >
            {t('nav.calendar')}
          </button>
          <button 
            className={currentPage === 'results' ? 'active' : ''}
            onClick={() => setCurrentPage('results')}
          >
            {t('nav.results')}
          </button>
        </div>
        
        {/* Language Toggle */}
        <div className="f1-nav-lang">
          <button
            onClick={() => setLanguage(language === 'en' ? 'ko' : 'en')}
            style={{
              background: 'rgba(255, 255, 255, 0.1)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              color: '#fff',
              padding: '0.5rem 1rem',
              cursor: 'pointer',
              borderRadius: '4px',
              fontSize: '0.8rem',
              fontWeight: '600'
            }}
          >
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