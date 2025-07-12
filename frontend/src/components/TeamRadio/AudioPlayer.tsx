import React, { useState, useRef, useEffect } from 'react';
import './AudioPlayer.css';

interface AudioPlayerProps {
  audioUrl?: string;
  title?: string;
  driverName?: string;
  driverNumber?: number;
  teamColor?: string;
  duration?: number;
  autoPlay?: boolean;
  onPlay?: () => void;
  onPause?: () => void;
  onEnded?: () => void;
}

const AudioPlayer: React.FC<AudioPlayerProps> = ({
  audioUrl,
  title = "Team Radio",
  driverName = "Unknown Driver",
  driverNumber,
  teamColor = "#666",
  duration,
  autoPlay = false,
  onPlay,
  onPause,
  onEnded
}) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [audioDuration, setAudioDuration] = useState(duration || 0);
  const [volume, setVolume] = useState(0.8);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [playbackRate, setPlaybackRate] = useState(1);
  
  const audioRef = useRef<HTMLAudioElement>(null);
  const progressRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const handleLoadStart = () => setIsLoading(true);
    const handleLoadedData = () => {
      setIsLoading(false);
      setAudioDuration(audio.duration);
      setError(null);
    };
    const handleTimeUpdate = () => setCurrentTime(audio.currentTime);
    const handleEnded = () => {
      setIsPlaying(false);
      setCurrentTime(0);
      onEnded?.();
    };
    const handleError = () => {
      setIsLoading(false);
      setError('Failed to load audio');
      setIsPlaying(false);
    };

    audio.addEventListener('loadstart', handleLoadStart);
    audio.addEventListener('loadeddata', handleLoadedData);
    audio.addEventListener('timeupdate', handleTimeUpdate);
    audio.addEventListener('ended', handleEnded);
    audio.addEventListener('error', handleError);

    return () => {
      audio.removeEventListener('loadstart', handleLoadStart);
      audio.removeEventListener('loadeddata', handleLoadedData);
      audio.removeEventListener('timeupdate', handleTimeUpdate);
      audio.removeEventListener('ended', handleEnded);
      audio.removeEventListener('error', handleError);
    };
  }, [onEnded]);

  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.volume = volume;
    }
  }, [volume]);

  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.playbackRate = playbackRate;
    }
  }, [playbackRate]);

  const togglePlayPause = async () => {
    const audio = audioRef.current;
    if (!audio || !audioUrl) return;

    try {
      if (isPlaying) {
        audio.pause();
        setIsPlaying(false);
        onPause?.();
      } else {
        await audio.play();
        setIsPlaying(true);
        onPlay?.();
      }
    } catch (err) {
      setError('Failed to play audio');
      setIsPlaying(false);
    }
  };

  const handleProgressClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const audio = audioRef.current;
    const progressBar = progressRef.current;
    if (!audio || !progressBar || !audioDuration) return;

    const rect = progressBar.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const width = rect.width;
    const newTime = (clickX / width) * audioDuration;
    
    audio.currentTime = newTime;
    setCurrentTime(newTime);
  };

  const formatTime = (time: number): string => {
    if (!time || isNaN(time)) return '0:00';
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  const getProgressPercentage = (): number => {
    if (!audioDuration) return 0;
    return (currentTime / audioDuration) * 100;
  };

  if (!audioUrl) {
    return (
      <div className="audio-player disabled">
        <div className="player-header">
          <div className="driver-info">
            {driverNumber && (
              <div 
                className="driver-number"
                style={{ backgroundColor: teamColor }}
              >
                {driverNumber}
              </div>
            )}
            <div className="audio-title">
              <div className="title">{title}</div>
              <div className="driver-name">{driverName}</div>
            </div>
          </div>
          <div className="no-audio-badge">
            🔇 No Audio
          </div>
        </div>
        
        <div className="player-controls disabled">
          <button className="play-btn" disabled>
            <span className="play-icon">▶️</span>
          </button>
          <div className="progress-container">
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: '0%' }}></div>
            </div>
            <div className="time-display">
              <span>0:00</span>
              <span>/</span>
              <span>0:00</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="audio-player error">
        <div className="player-header">
          <div className="driver-info">
            {driverNumber && (
              <div 
                className="driver-number"
                style={{ backgroundColor: teamColor }}
              >
                {driverNumber}
              </div>
            )}
            <div className="audio-title">
              <div className="title">{title}</div>
              <div className="driver-name">{driverName}</div>
            </div>
          </div>
          <div className="error-badge">
            ⚠️ Audio Error
          </div>
        </div>
        
        <div className="error-message">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="retry-audio-btn">
            🔄 Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="audio-player">
      <audio 
        ref={audioRef}
        src={audioUrl}
        preload="metadata"
        autoPlay={autoPlay}
      />
      
      <div className="player-header">
        <div className="driver-info">
          {driverNumber && (
            <div 
              className="driver-number"
              style={{ backgroundColor: teamColor }}
            >
              {driverNumber}
            </div>
          )}
          <div className="audio-title">
            <div className="title">{title}</div>
            <div className="driver-name">{driverName}</div>
          </div>
        </div>
        
        <div className="player-options">
          <div className="playback-speed">
            <label>Speed:</label>
            <select 
              value={playbackRate} 
              onChange={(e) => setPlaybackRate(Number(e.target.value))}
              className="speed-select"
            >
              <option value={0.5}>0.5x</option>
              <option value={0.75}>0.75x</option>
              <option value={1}>1x</option>
              <option value={1.25}>1.25x</option>
              <option value={1.5}>1.5x</option>
              <option value={2}>2x</option>
            </select>
          </div>
        </div>
      </div>

      <div className="player-controls">
        <button 
          className={`play-btn ${isLoading ? 'loading' : ''}`}
          onClick={togglePlayPause}
          disabled={isLoading}
          title={isPlaying ? 'Pause' : 'Play'}
        >
          {isLoading ? (
            <span className="loading-spinner">⏳</span>
          ) : (
            <span className="play-icon">
              {isPlaying ? '⏸️' : '▶️'}
            </span>
          )}
        </button>

        <div className="progress-container">
          <div 
            className="progress-bar"
            ref={progressRef}
            onClick={handleProgressClick}
          >
            <div 
              className="progress-fill"
              style={{ width: `${getProgressPercentage()}%` }}
            ></div>
            <div 
              className="progress-handle"
              style={{ left: `${getProgressPercentage()}%` }}
            ></div>
          </div>
          
          <div className="time-display">
            <span className="current-time">{formatTime(currentTime)}</span>
            <span className="separator">/</span>
            <span className="total-time">{formatTime(audioDuration)}</span>
          </div>
        </div>

        <div className="volume-control">
          <span className="volume-icon">
            {volume === 0 ? '🔇' : volume < 0.5 ? '🔉' : '🔊'}
          </span>
          <input
            type="range"
            min="0"
            max="1"
            step="0.1"
            value={volume}
            onChange={(e) => setVolume(Number(e.target.value))}
            className="volume-slider"
            title={`Volume: ${Math.round(volume * 100)}%`}
          />
        </div>
      </div>

      {audioDuration > 0 && (
        <div className="audio-info">
          <div className="audio-stats">
            <span className="duration-badge">
              📊 {formatTime(audioDuration)}
            </span>
            <span className="quality-badge">
              🎵 Audio Available
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

export default AudioPlayer;