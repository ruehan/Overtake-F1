import React from 'react';
import RaceAnalyticsDashboard from '../components/Analytics/RaceAnalyticsDashboard';

const AnalyticsPage: React.FC = () => {
  return (
    <div style={{ minHeight: '100vh', background: '#f8f9fa' }}>
      <RaceAnalyticsDashboard sessionKey={9222} />
    </div>
  );
};

export default AnalyticsPage;