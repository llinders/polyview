
import React, { useState, useEffect, useRef } from 'react';
import CogIcon from './icons/CogIcon';
import './Settings.css';

const Settings: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [useMockData, setUseMockData] = useState<boolean>(() => {
    const stored = localStorage.getItem('useMockData');
    return stored ? JSON.parse(stored) : false;
  });

  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    localStorage.setItem('useMockData', JSON.stringify(useMockData));
  }, [useMockData]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const handleToggle = () => {
    setUseMockData(prev => !prev);
  };

  return (
    <div className="settings-container" ref={containerRef}>
      <button className="settings-button" onClick={() => setIsOpen(prev => !prev)}>
        <CogIcon className="settings-icon" />
      </button>
      {isOpen && (
        <div className="settings-dropdown">
          <label>
            <span className="label-text">Use Mock Data</span>
            <div className="toggle-switch">
              <input type="checkbox" checked={useMockData} onChange={handleToggle} />
              <span className="slider"></span>
            </div>
          </label>
        </div>
      )}
    </div>
  );
};

export default Settings;
