import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Activity, Cpu, HardDrive } from 'lucide-react';

export default function Navbar() {
  const [isBackendHealthy, setIsBackendHealthy] = useState(false);

  useEffect(() => {
    api.getHealth()
      .then(() => setIsBackendHealthy(true))
      .catch(() => setIsBackendHealthy(false));
  }, []);

  return (
    <header style={{
      height: '64px',
      backgroundColor: '#0f172a',
      borderBottom: '1px solid #1e293b',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 2rem',
      flexShrink: 0
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <h2 style={{ fontSize: '1rem', fontWeight: '600', color: '#f8fafc' }}>
          Smart Customer Analysis & Personalized Experience
        </h2>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        {/* Spark Indicator */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.4rem',
          fontSize: '0.75rem',
          backgroundColor: '#1e293b',
          padding: '0.35rem 0.75rem',
          borderRadius: '6px',
          color: '#94a3b8'
        }}>
          <Cpu size={14} color="#f59e0b" />
          <span>PySpark 3.5 (local[2])</span>
        </div>

        {/* HDFS / Storage Indicator */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.4rem',
          fontSize: '0.75rem',
          backgroundColor: '#1e293b',
          padding: '0.35rem 0.75rem',
          borderRadius: '6px',
          color: '#94a3b8'
        }}>
          <HardDrive size={14} color="#06b6d4" />
          <span>HDFS / Staged Parquet</span>
        </div>

        {/* Live Backend Connection Status */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          fontSize: '0.75rem',
          fontWeight: '500',
          backgroundColor: isBackendHealthy ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
          color: isBackendHealthy ? '#10b981' : '#ef4444',
          border: `1px solid ${isBackendHealthy ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
          padding: '0.35rem 0.75rem',
          borderRadius: '20px'
        }}>
          <span style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            backgroundColor: isBackendHealthy ? '#10b981' : '#ef4444',
            display: 'inline-block'
          }}></span>
          <span>{isBackendHealthy ? 'Backend Connected' : 'Backend Offline'}</span>
        </div>
      </div>
    </header>
  );
}
