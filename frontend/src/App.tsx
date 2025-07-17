import React, { useState } from 'react';
import { Routes, Route, Navigate, useLocation, useNavigate } from 'react-router-dom';
import './App.css';
import Dashboard from './pages/Dashboard';
import StandingsPage from './pages/StandingsPage';
import CalendarPage from './pages/CalendarPage';
import RaceResultsPage from './pages/RaceResultsPage';
import StandingsProgressionPage from './pages/StandingsProgressionPage';
import StatisticsPage from './pages/StatisticsPage';
import CircuitsPage from './pages/CircuitsPage';
import FavoritesPage from './pages/FavoritesPage';
import PersonalizedDashboard from './components/PersonalizedDashboard';
import DriverDetailModal from './components/DriverDetailModal';
import { LanguageProvider, useLanguage } from './contexts/LanguageContext';

const AppContent = () => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [selectedDriverNumber, setSelectedDriverNumber] = useState<number | null>(null);
  const [isDriverModalOpen, setIsDriverModalOpen] = useState(false);
  const { language, setLanguage, t } = useLanguage();
  const location = useLocation();
  const navigate = useNavigate();

  const handleDriverClick = (driverNumber: number) => {
    setSelectedDriverNumber(driverNumber);
    setIsDriverModalOpen(true);
  };

  const handlePageChange = (path: string) => {
    navigate(path);
    setIsMobileMenuOpen(false); // 모바일에서 페이지 변경 시 메뉴 닫기
  };

  // 현재 경로에 따라 활성 페이지 결정
  const getCurrentPage = () => {
    switch (location.pathname) {
      case '/':
      case '/dashboard':
        return 'dashboard';
      case '/personalized':
        return 'personalized';
      case '/standings':
        return 'standings';
      case '/progression':
        return 'progression';
      case '/statistics':
        return 'statistics';
      case '/circuits':
        return 'circuits';
      case '/calendar':
        return 'calendar';
      case '/results':
        return 'results';
      case '/favorites':
        return 'favorites';
      default:
        return 'dashboard';
    }
  };

  const currentPage = getCurrentPage();

  const menuItems = [
    { key: 'dashboard', label: t('대시보드'), path: '/dashboard', icon: '🏠' },
    { key: 'personalized', label: t('맞춤'), path: '/personalized', icon: '⭐' },
    { key: 'standings', label: t('순위표'), path: '/standings', icon: '🏆' },
    { key: 'progression', label: t('진행'), path: '/progression', icon: '📈' },
    { key: 'statistics', label: t('통계'), path: '/statistics', icon: '📊' },
    { key: 'circuits', label: t('서킷'), path: '/circuits', icon: '🛣️' },
    { key: 'calendar', label: t('캘린더'), path: '/calendar', icon: '📅' },
    { key: 'results', label: t('결과'), path: '/results', icon: '🏁' },
    { key: 'favorites', label: t('즐겨찾기'), path: '/favorites', icon: '💖' },
  ];

  const langToggleOptions = [
    { code: 'ko', label: '한국어', flag: '🇰🇷' },
    { code: 'en', label: 'English', flag: '🇺🇸' }
  ];

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-left">
          <h1 className="logo" onClick={() => handlePageChange('/dashboard')}>
            🏁 Overtake
          </h1>
        </div>

        {/* Desktop Navigation */}
        <nav className="desktop-nav">
          {menuItems.map((item) => (
            <button
              key={item.key}
              onClick={() => handlePageChange(item.path)}
              className={currentPage === item.key ? 'active' : ''}
            >
              <span className="nav-icon">{item.icon}</span>
              <span className="nav-label">{item.label}</span>
            </button>
          ))}
        </nav>

        {/* Header Right */}
        <div className="header-right">
          {/* Language Toggle */}
          <div className="language-toggle">
            <select 
              value={language} 
              onChange={(e) => setLanguage(e.target.value as 'en' | 'ko')}
              className="language-select"
            >
              {langToggleOptions.map(option => (
                <option key={option.code} value={option.code}>
                  {option.flag} {option.label}
                </option>
              ))}
            </select>
          </div>

          {/* Mobile Menu Button */}
          <button 
            className="mobile-menu-btn"
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          >
            ☰
          </button>
        </div>
      </header>

      {/* Mobile Menu */}
      <div className={`mobile-menu ${isMobileMenuOpen ? 'open' : ''}`}>
        {menuItems.map((item) => (
          <button
            key={item.key}
            onClick={() => handlePageChange(item.path)}
            className={currentPage === item.key ? 'active' : ''}
          >
            <span className="nav-icon">{item.icon}</span>
            <span className="nav-label">{item.label}</span>
          </button>
        ))}
      </div>

      {/* Main Content */}
      <main className="main-content">
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard onDriverClick={handleDriverClick} />} />
          <Route path="/personalized" element={<PersonalizedDashboard />} />
          <Route path="/standings" element={<StandingsPage onDriverClick={handleDriverClick} />} />
          <Route path="/progression" element={<StandingsProgressionPage />} />
          <Route path="/statistics" element={<StatisticsPage />} />
          <Route path="/circuits" element={<CircuitsPage />} />
          <Route path="/calendar" element={<CalendarPage />} />
          <Route path="/results" element={<RaceResultsPage />} />
          <Route path="/favorites" element={<FavoritesPage />} />
        </Routes>
      </main>

      {/* Driver Detail Modal */}
      {isDriverModalOpen && selectedDriverNumber && (
        <DriverDetailModal
          driverNumber={selectedDriverNumber}
          isOpen={isDriverModalOpen}
          onClose={() => {
            setIsDriverModalOpen(false);
            setSelectedDriverNumber(null);
          }}
        />
      )}
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