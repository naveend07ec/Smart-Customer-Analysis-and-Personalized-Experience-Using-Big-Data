import React, { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import { api } from '../services/api';

const navItems = [
  { path: '/', label: 'Dashboard' },
  { path: '/analytics', label: 'Analytics' },
  { path: '/segmentation', label: 'Segmentation' },
  { path: '/customers', label: 'Customer 360' },
  { path: '/recommendations', label: 'Recommendations' },
  { path: '/churn', label: 'Retention AI' },
  { path: '/pipeline', label: 'Data Pipeline' },
];

export default function Navbar() {
  const [modeContext, setModeContext] = useState({
    mode: 'cumulative',
    batch_id: null,
    version_id: 'baseline',
    indicator_label: 'CUMULATIVE ANALYSIS — baseline',
    available_batch_only: []
  });
  const [isSwitching, setIsSwitching] = useState(false);

  const fetchModeContext = async () => {
    try {
      const res = await api.getDatasetMode();
      if (res && res.data) {
        setModeContext(res.data);
      }
    } catch {
      // Gracefully retain current state
    }
  };

  useEffect(() => {
    fetchModeContext();
    const interval = setInterval(fetchModeContext, 4000);
    window.addEventListener('smart-dataset-mode-changed', fetchModeContext);
    return () => {
      clearInterval(interval);
      window.removeEventListener('smart-dataset-mode-changed', fetchModeContext);
    };
  }, []);

  const handleToggleMode = async (targetMode, batchId = null) => {
    if (isSwitching) return;
    setIsSwitching(true);
    try {
      const res = await api.setDatasetMode(targetMode, batchId);
      if (res && res.data) {
        setModeContext(res.data);
        window.dispatchEvent(new CustomEvent('smart-dataset-mode-changed', { detail: res.data }));
      }
    } catch (e) {
      console.error('Mode switch failed:', e);
    } finally {
      setIsSwitching(false);
    }
  };

  const isBatchOnly = modeContext.mode === 'batch_only';
  const displayLabel = isBatchOnly
    ? `NEW BATCH ONLY — ${modeContext.batch_id || 'Preview'}`
    : `CUMULATIVE ANALYSIS — ${modeContext.version_id || 'Production'}`;

  return (
    <header className="top-header-bar">
      {/* Left: Purple Gradient Orb + S M A R T Logo */}
      <NavLink to="/" className="dune-brand-logo" title="SMART Customer Analytics">
        <span className="brand-orb" />
        <span className="brand-text">S M A R T</span>
      </NavLink>

      {/* Center: Floating Pill Navigation Capsule */}
      <nav className="pill-nav-container">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) => `pill-nav-item ${isActive ? 'active' : ''}`}
          >
            {item.label}
          </NavLink>
        ))}
      </nav>

      {/* Right: Persistent Dataset Processing Mode Indicator */}
      <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
        <div
          title={isBatchOnly ? "Currently viewing isolated New Batch Only analytics" : "Currently viewing integrated Cumulative Production dataset"}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.35rem 0.85rem',
            borderRadius: '9999px',
            fontSize: '0.74rem',
            fontWeight: '600',
            fontFamily: 'var(--font-mono)',
            letterSpacing: '0.04em',
            textTransform: 'uppercase',
            backgroundColor: 'var(--surface-elevated, #1A1A1E)',
            color: 'var(--text-secondary, #A1A1AA)',
            border: '1px solid var(--border-subtle, rgba(255, 255, 255, 0.12))',
            boxShadow: 'none'
          }}
        >
          <span
            style={{
              width: '6px',
              height: '6px',
              borderRadius: '50%',
              backgroundColor: isBatchOnly ? '#818CF8' : '#7047EB'
            }}
          />
          {displayLabel}
        </div>

        {/* Quick Mode Toggle Action */}
        {isBatchOnly ? (
          <button
            onClick={() => handleToggleMode('cumulative')}
            disabled={isSwitching}
            style={{
              padding: '0.3rem 0.65rem',
              borderRadius: '8px',
              border: '1px solid var(--border-subtle, rgba(255, 255, 255, 0.15))',
              backgroundColor: 'rgba(255, 255, 255, 0.06)',
              color: 'var(--text-secondary)',
              fontSize: '0.72rem',
              fontWeight: '500',
              cursor: isSwitching ? 'wait' : 'pointer'
            }}
            title="Restore cumulative historical baseline + accepted batches"
          >
            {isSwitching ? 'Restoring...' : 'Switch to Cumulative'}
          </button>
        ) : modeContext.available_batch_only && modeContext.available_batch_only.length > 0 ? (
          <button
            onClick={() => handleToggleMode('batch_only', modeContext.available_batch_only[0].batch_id)}
            disabled={isSwitching}
            style={{
              padding: '0.3rem 0.65rem',
              borderRadius: '8px',
              border: '1px solid var(--border-subtle, rgba(255, 255, 255, 0.15))',
              backgroundColor: 'rgba(255, 255, 255, 0.06)',
              color: 'var(--text-secondary)',
              fontSize: '0.72rem',
              fontWeight: '500',
              cursor: isSwitching ? 'wait' : 'pointer'
            }}
            title={`Switch to isolated preview of batch ${modeContext.available_batch_only[0].batch_id}`}
          >
            {isSwitching ? 'Switching...' : `View Batch Only (${modeContext.available_batch_only[0].batch_id.slice(-6)})`}
          </button>
        ) : null}
      </div>
    </header>
  );
}
