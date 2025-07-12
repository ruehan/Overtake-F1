import React, { useState } from 'react';
import F1LiveMap from '../components/LiveMap/F1LiveMap';

const LiveMapPage: React.FC = () => {
  const [sessionKey] = useState<number>(9222); // Example session key

  return (
    <div>
      <div style={{ marginBottom: '1rem', textAlign: 'center' }}>
        <h2 style={{ margin: '0 0 0.5rem 0', color: '#333' }}>F1 Live Track Map</h2>
        <p style={{ margin: 0, color: '#666' }}>
          Real-time car positions, speed, and DRS status
        </p>
      </div>
      
      <div style={{ 
        height: 'calc(100vh - 200px)', 
        minHeight: '600px',
        background: '#fff',
        borderRadius: '8px',
        padding: '1rem',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
      }}>
        <F1LiveMap sessionKey={sessionKey} circuitId="bahrain" />
      </div>
    </div>
  );
};

export default LiveMapPage;