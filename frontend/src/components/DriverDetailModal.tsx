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
  // 현재 시즌 데이터
  season_wins?: number;
  season_podiums?: number;
  season_points?: number;
}

interface DriverDetailModalProps {
  driverNumber: number;
  isOpen: boolean;
  onClose: () => void;
}

const DriverDetailModal: React.FC<DriverDetailModalProps> = ({ driverNumber, isOpen, onClose }) => {
  const { t } = useLanguage();
  const [driver, setDriver] = useState<DriverDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && driverNumber) {
      fetchDriverDetail();
    }
  }, [isOpen, driverNumber]);

  // 모달 외부 클릭 시 닫기
  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  const fetchDriverDetail = async () => {
    setLoading(true);
    setError(null);
    
    try {
      console.log('🔄 Fetching driver detail for driver number:', driverNumber);
      
      // 기본 드라이버 정보, 시즌 통계, 경력 통계를 병렬로 가져오기
      const [driverResponse, seasonStatsResponse, careerStatsResponse] = await Promise.all([
        fetch(API_ENDPOINTS.driverDetail(driverNumber)),
        fetch(API_ENDPOINTS.driverSeasonStats(driverNumber)),
        fetch(API_ENDPOINTS.driverCareerStats(driverNumber))
      ]);
      
      console.log('📥 Driver detail response:', driverResponse.status, driverResponse.statusText);
      console.log('📥 Season stats response:', seasonStatsResponse.status, seasonStatsResponse.statusText);
      console.log('📥 Career stats response:', careerStatsResponse.status, careerStatsResponse.statusText);
      
      if (!driverResponse.ok) {
        throw new Error(`Failed to fetch driver detail: ${driverResponse.status} ${driverResponse.statusText}`);
      }
      
      const driverData = await driverResponse.json();
      console.log('✅ Driver detail data:', driverData);
      
      // 시즌 통계 데이터 가져오기
      let seasonStats = { season_wins: 0, season_podiums: 0, season_points: 0 };
      if (seasonStatsResponse.ok) {
        const seasonData = await seasonStatsResponse.json();
        seasonStats = seasonData.data;
        console.log('✅ Season stats data:', seasonStats);
      }
      
      // 경력 통계 데이터 가져오기
      let careerStats = { race_wins: 0, podiums: 0, pole_positions: 0, fastest_laps: 0, career_points: 0, world_championships: 0, first_entry: null };
      if (careerStatsResponse.ok) {
        const careerData = await careerStatsResponse.json();
        careerStats = careerData.data;
        console.log('✅ Career stats data:', careerStats);
      }
      
      // 드라이버 데이터에 시즌 통계와 경력 통계 병합
      const combinedData = {
        ...driverData.data,
        ...seasonStats,
        ...careerStats
      };
      
      setDriver(combinedData);
    } catch (err) {
      console.error('❌ Driver detail fetch error:', err);
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div 
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
        padding: '1rem'
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          onClose();
        }
      }}
    >
      <div 
        style={{
          backgroundColor: '#1a1a1a',
          borderRadius: '12px',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          maxWidth: '800px',
          width: '100%',
          maxHeight: '90vh',
          overflow: 'auto',
          position: 'relative'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* 모달 헤더 */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '1.5rem 2rem',
          borderBottom: '1px solid rgba(255, 255, 255, 0.1)'
        }}>
          <h2 style={{ margin: 0, color: '#ff6b35' }}>🏎️ {t('driver.personalInfo')}</h2>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              color: '#fff',
              fontSize: '1.5rem',
              cursor: 'pointer',
              padding: '0.5rem'
            }}
          >
            ✕
          </button>
        </div>

        {/* 모달 내용 */}
        <div style={{ padding: '2rem' }}>
          {loading && (
            <div style={{ textAlign: 'center', padding: '2rem', color: '#ccc' }}>
              {t('common.loading')} driver information...
            </div>
          )}

          {error && (
            <div style={{ textAlign: 'center', padding: '2rem', color: '#ff6b35' }}>
              {t('common.error')}: {error}
            </div>
          )}

          {!loading && !error && !driver && (
            <div style={{ textAlign: 'center', padding: '2rem', color: '#ccc' }}>
              Driver not found
            </div>
          )}

          {driver && (
            <div>
              {/* 드라이버 헤더 */}
              <div style={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: '2rem', 
                marginBottom: '2rem',
                flexWrap: 'wrap'
              }}>
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
                    fontSize: '2rem', 
                    margin: '0 0 0.5rem 0',
                    background: `linear-gradient(45deg, #ff6b35, ${driver.team_colour || '#f7931e'})`,
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    backgroundClip: 'text'
                  }}>
                    {driver.full_name}
                  </h1>
                  <div style={{ fontSize: '1rem', color: '#ccc', marginBottom: '1rem' }}>
                    #{driver.driver_number} • {driver.abbreviation}
                  </div>
                  <div style={{ 
                    display: 'inline-block',
                    background: driver.team_colour || '#ff6b35',
                    color: '#fff',
                    padding: '0.5rem 1rem',
                    borderRadius: '20px',
                    fontWeight: '600',
                    fontSize: '0.9rem'
                  }}>
                    {driver.team_name}
                  </div>
                </div>
              </div>

              {/* 정보 그리드 */}
              <div style={{ 
                display: 'grid', 
                gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', 
                gap: '1.5rem',
                marginBottom: '2rem'
              }}>
                {/* 개인 정보 */}
                <div style={{
                  background: 'rgba(255, 255, 255, 0.02)',
                  padding: '1.5rem',
                  borderRadius: '8px',
                  border: '1px solid rgba(255, 255, 255, 0.1)'
                }}>
                  <h3 style={{ 
                    color: '#ff6b35', 
                    marginBottom: '1rem',
                    fontSize: '1.1rem'
                  }}>
                    👤 {t('driver.personalInfo')}
                  </h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.8rem' }}>
                    {driver.nationality && (
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ fontWeight: '600', color: '#ccc' }}>{t('driver.nationality')}:</span>
                        <span>{driver.nationality}</span>
                      </div>
                    )}
                    {driver.date_of_birth && (
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ fontWeight: '600', color: '#ccc' }}>{t('driver.dateOfBirth')}:</span>
                        <span>{new Date(driver.date_of_birth).toLocaleDateString()}</span>
                      </div>
                    )}
                    {driver.place_of_birth && (
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ fontWeight: '600', color: '#ccc' }}>{t('driver.placeOfBirth')}:</span>
                        <span>{driver.place_of_birth}</span>
                      </div>
                    )}
                    {driver.first_entry && (
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ fontWeight: '600', color: '#ccc' }}>{t('driver.f1Debut')}:</span>
                        <span>{driver.first_entry}</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* 경력 통계 */}
                <div style={{
                  background: 'rgba(255, 255, 255, 0.02)',
                  padding: '1.5rem',
                  borderRadius: '8px',
                  border: '1px solid rgba(255, 255, 255, 0.1)'
                }}>
                  <h3 style={{ 
                    color: '#ff6b35', 
                    marginBottom: '1rem',
                    fontSize: '1.1rem'
                  }}>
                    🏆 {t('driver.careerStats')}
                  </h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.8rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ fontWeight: '600', color: '#ccc' }}>{t('driver.worldChampionships')}:</span>
                      <span style={{ color: '#ffd700' }}>{driver.world_championships || 0}</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ fontWeight: '600', color: '#ccc' }}>{t('driver.raceWins')}:</span>
                      <span style={{ color: '#ff6b35' }}>{driver.race_wins || 0}</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ fontWeight: '600', color: '#ccc' }}>{t('driver.podiums')}:</span>
                      <span>{driver.podiums || 0}</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ fontWeight: '600', color: '#ccc' }}>{t('driver.polePositions')}:</span>
                      <span>{driver.pole_positions || 0}</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ fontWeight: '600', color: '#ccc' }}>{t('driver.fastestLaps')}:</span>
                      <span>{driver.fastest_laps || 0}</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ fontWeight: '600', color: '#ccc' }}>{t('driver.careerPoints')}:</span>
                      <span>{driver.career_points || 0}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* 현재 시즌 성과 */}
              <div style={{
                background: 'rgba(255, 255, 255, 0.02)',
                padding: '1.5rem',
                borderRadius: '8px',
                border: '1px solid rgba(255, 255, 255, 0.1)'
              }}>
                <h3 style={{ 
                  color: '#ff6b35', 
                  marginBottom: '1rem',
                  fontSize: '1.1rem'
                }}>
                  📊 {t('driver.currentSeason')} 2025
                </h3>
                <div style={{ 
                  display: 'grid', 
                  gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', 
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
                      {driver.season_wins || 0}
                    </div>
                    <div style={{ fontSize: '0.8rem', color: '#ccc' }}>{t('driver.raceWins')}</div>
                  </div>
                  <div style={{ 
                    background: 'rgba(255, 215, 0, 0.1)', 
                    border: '1px solid rgba(255, 215, 0, 0.3)',
                    padding: '1rem',
                    borderRadius: '8px'
                  }}>
                    <div style={{ fontSize: '1.5rem', fontWeight: '700', color: '#ffd700' }}>
                      {driver.season_podiums || 0}
                    </div>
                    <div style={{ fontSize: '0.8rem', color: '#ccc' }}>{t('driver.podiums')}</div>
                  </div>
                  <div style={{ 
                    background: 'rgba(16, 185, 129, 0.1)', 
                    border: '1px solid rgba(16, 185, 129, 0.3)',
                    padding: '1rem',
                    borderRadius: '8px'
                  }}>
                    <div style={{ fontSize: '1.5rem', fontWeight: '700', color: '#10b981' }}>
                      {driver.season_points || 0}
                    </div>
                    <div style={{ fontSize: '0.8rem', color: '#ccc' }}>시즌 포인트</div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* 모달 푸터 */}
        <div style={{
          padding: '1rem 2rem',
          borderTop: '1px solid rgba(255, 255, 255, 0.1)',
          display: 'flex',
          justifyContent: 'flex-end'
        }}>
          <button
            onClick={onClose}
            style={{
              background: 'rgba(255, 255, 255, 0.1)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              color: '#fff',
              padding: '0.5rem 1.5rem',
              cursor: 'pointer',
              borderRadius: '4px'
            }}
          >
            {t('common.close')}
          </button>
        </div>
      </div>
    </div>
  );
};

export default DriverDetailModal;