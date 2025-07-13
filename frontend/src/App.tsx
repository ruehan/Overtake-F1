import React, { useState } from 'react';
import './App.css';
import Dashboard from './pages/Dashboard';
import StandingsPage from './pages/StandingsPage';
import CalendarPage from './pages/CalendarPage';
import RaceResultsPage from './pages/RaceResultsPage';
import StandingsProgressionPage from './pages/StandingsProgressionPage';
import RaceWeekendsPage from './pages/RaceWeekendsPage';

function App() {
  const [currentPage, setCurrentPage] = useState('dashboard');

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
            LIVE
          </button>
          <button 
            className={currentPage === 'standings' ? 'active' : ''}
            onClick={() => setCurrentPage('standings')}
          >
            STANDINGS
          </button>
          <button 
            className={currentPage === 'progression' ? 'active' : ''}
            onClick={() => setCurrentPage('progression')}
          >
            PROGRESSION
          </button>
          <button 
            className={currentPage === 'weekends' ? 'active' : ''}
            onClick={() => setCurrentPage('weekends')}
          >
            WEEKENDS
          </button>
          <button 
            className={currentPage === 'calendar' ? 'active' : ''}
            onClick={() => setCurrentPage('calendar')}
          >
            CALENDAR
          </button>
          <button 
            className={currentPage === 'results' ? 'active' : ''}
            onClick={() => setCurrentPage('results')}
          >
            RESULTS
          </button>
        </div>
      </nav>
      
      <main className="f1-main">
        {renderPage()}
      </main>
    </div>
  );
}

export default App;