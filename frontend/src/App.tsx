import React from 'react';
import { Routes, Route, Link } from 'react-router-dom';
import './App.css';
import Dashboard from './pages/Dashboard';
import LiveMapPage from './pages/LiveMapPage';

function App() {
  return (
    <div className="App">
      <nav style={{ 
        padding: '1rem', 
        background: '#f8f9fa', 
        borderBottom: '1px solid #dee2e6',
        marginBottom: '1rem'
      }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto', display: 'flex', gap: '2rem', alignItems: 'center' }}>
          <h1 style={{ margin: 0, fontSize: '1.5rem', color: '#333' }}>OpenF1 Dashboard</h1>
          <div style={{ display: 'flex', gap: '1rem' }}>
            <Link 
              to="/" 
              style={{ 
                textDecoration: 'none', 
                color: '#007bff', 
                fontWeight: '500',
                padding: '0.5rem 1rem',
                borderRadius: '4px',
                transition: 'background-color 0.2s'
              }}
            >
              Dashboard
            </Link>
            <Link 
              to="/live-map" 
              style={{ 
                textDecoration: 'none', 
                color: '#007bff', 
                fontWeight: '500',
                padding: '0.5rem 1rem',
                borderRadius: '4px',
                transition: 'background-color 0.2s'
              }}
            >
              Live Map
            </Link>
          </div>
        </div>
      </nav>

      <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '0 1rem' }}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/live-map" element={<LiveMapPage />} />
        </Routes>
      </div>
    </div>
  );
}

export default App;
