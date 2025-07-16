import React, { useState, useEffect } from 'react';
import { useLanguage } from '../contexts/LanguageContext';
import { API_ENDPOINTS } from '../config/api';

interface DriverDetail {
  driver_number: number;
  full_name: string;
  name: string;
  abbreviation: string;
  team_name: string;
  team_colour: string;
  country_code?: string;
  headshot_url?: string;
  nationality?: string;
  date_of_birth?: string;
  place_of_birth?: string;
  championship_wins?: number;
  race_wins?: number;
  podiums?: number;
  pole_positions?: number;
  fastest_laps?: number;
  career_points?: number;
  first_entry?: number;
  world_championships?: number;
}

interface DriverDetailPageProps {
  driverNumber: number;
  onBack: () => void;
}

const DriverDetailPage: React.FC<DriverDetailPageProps> = ({ driverNumber, onBack }) => {
  const { t } = useLanguage();
  const [driver, setDriver] = useState<DriverDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDriverDetail();
  }, [driverNumber]);

  const fetchDriverDetail = async () => {
    setLoading(true);
    setError(null);
    
    try {
      console.log('🔄 Fetching driver detail for driver number:', driverNumber);
      const response = await fetch(`${API_ENDPOINTS.drivers}/${driverNumber}`);
      console.log('📥 Driver detail response:', response.status, response.statusText);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch driver detail: ${response.status} ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('✅ Driver detail data:', data);
      setDriver(data.data);
    } catch (err) {
      console.error('❌ Driver detail fetch error:', err);
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="f1-loading">{t('common.loading')} driver information...</div>;
  if (error) return <div className="f1-error">{t('common.error')}: {error}</div>;
  if (!driver) return <div className="f1-error">Driver not found</div>;

  return (
    <div>
      {/* Back Button */}
      <div className="f1-card" style={{ marginBottom: '1rem' }}>
        <button
          onClick={onBack}
          style={{
            background: 'rgba(255, 255, 255, 0.1)',
            border: '1px solid rgba(255, 255, 255, 0.2)',
            color: '#fff',
            padding: '0.5rem 1rem',
            cursor: 'pointer',
            borderRadius: '4px',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}
        >
          ← {t('common.back')}
        </button>
      </div>

      {/* Driver Header */}
      <div className="f1-card">
        <div style={{ display: 'flex', alignItems: 'center', gap: '2rem', flexWrap: 'wrap' }}>
          {driver.headshot_url && (
            <img 
              src={driver.headshot_url.startsWith('/') ? driver.headshot_url : `/${driver.headshot_url}`} 
              alt={driver.full_name}
              style={{
                width: '120px',
                height: '120px',
                borderRadius: '50%',
                objectFit: 'cover',
                border: '3px solid rgba(255, 255, 255, 0.2)',
                background: '#333'
              }}
              onError={(e) => {
                const target = e.target as HTMLImageElement;
                target.src = '/images/drivers/default.svg';
              }}
            />
          )}
          <div style={{ flex: 1 }}>
            <h1 style={{ 
              fontSize: '2.5rem', 
              margin: '0 0 0.5rem 0',
              background: `linear-gradient(45deg, #ff6b35, ${driver.team_colour || '#f7931e'})`,
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text'
            }}>
              {driver.full_name}
            </h1>
            <div style={{ fontSize: '1.2rem', color: '#ccc', marginBottom: '1rem' }}>
              #{driver.driver_number} • {driver.abbreviation}
            </div>
            <div style={{ 
              display: 'inline-block',
              background: driver.team_colour || '#ff6b35',
              color: '#fff',
              padding: '0.5rem 1rem',
              borderRadius: '20px',
              fontWeight: '600',
              fontSize: '1rem'
            }}>
              {driver.team_name}
            </div>
          </div>
        </div>
      </div>

      {/* Driver Information */}
      <div className="f1-grid f1-grid-2">
        {/* Personal Information */}
        <div className="f1-card">
          <h3 className="f1-card-title">👤 Personal Information</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {driver.nationality && (
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ fontWeight: '600' }}>Nationality:</span>
                <span>{driver.nationality}</span>
              </div>
            )}
            {driver.date_of_birth && (
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ fontWeight: '600' }}>Date of Birth:</span>
                <span>{new Date(driver.date_of_birth).toLocaleDateString()}</span>
              </div>
            )}
            {driver.place_of_birth && (
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ fontWeight: '600' }}>Place of Birth:</span>
                <span>{driver.place_of_birth}</span>
              </div>
            )}
            {driver.first_entry && (
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ fontWeight: '600' }}>F1 Debut:</span>
                <span>{driver.first_entry}</span>
              </div>
            )}
          </div>
        </div>

        {/* Career Statistics */}
        <div className="f1-card">
          <h3 className="f1-card-title">🏆 Career Statistics</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ fontWeight: '600' }}>World Championships:</span>
              <span style={{ color: '#ffd700' }}>{driver.world_championships || 0}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ fontWeight: '600' }}>Race Wins:</span>
              <span style={{ color: '#ff6b35' }}>{driver.race_wins || 0}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ fontWeight: '600' }}>Podiums:</span>
              <span>{driver.podiums || 0}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ fontWeight: '600' }}>Pole Positions:</span>
              <span>{driver.pole_positions || 0}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ fontWeight: '600' }}>Fastest Laps:</span>
              <span>{driver.fastest_laps || 0}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ fontWeight: '600' }}>Career Points:</span>
              <span>{driver.career_points || 0}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Current Season Performance */}
      <div className="f1-card">
        <h3 className="f1-card-title">📊 2025 Season Performance</h3>
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', 
          gap: '1rem',
          textAlign: 'center'
        }}>
          <div style={{ 
            background: 'rgba(255, 107, 53, 0.1)', 
            border: '1px solid rgba(255, 107, 53, 0.3)',
            padding: '1rem',
            borderRadius: '8px'
          }}>
            <div style={{ fontSize: '1.5rem', fontWeight: '700', color: '#ff6b35' }}>
              {driver.championship_wins || 0}
            </div>
            <div style={{ fontSize: '0.9rem', color: '#ccc' }}>Race Wins</div>
          </div>
          <div style={{ 
            background: 'rgba(255, 215, 0, 0.1)', 
            border: '1px solid rgba(255, 215, 0, 0.3)',
            padding: '1rem',
            borderRadius: '8px'
          }}>
            <div style={{ fontSize: '1.5rem', fontWeight: '700', color: '#ffd700' }}>
              {driver.podiums || 0}
            </div>
            <div style={{ fontSize: '0.9rem', color: '#ccc' }}>Podiums</div>
          </div>
          <div style={{ 
            background: 'rgba(16, 185, 129, 0.1)', 
            border: '1px solid rgba(16, 185, 129, 0.3)',
            padding: '1rem',
            borderRadius: '8px'
          }}>
            <div style={{ fontSize: '1.5rem', fontWeight: '700', color: '#10b981' }}>
              {driver.career_points || 0}
            </div>
            <div style={{ fontSize: '0.9rem', color: '#ccc' }}>Points</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DriverDetailPage;