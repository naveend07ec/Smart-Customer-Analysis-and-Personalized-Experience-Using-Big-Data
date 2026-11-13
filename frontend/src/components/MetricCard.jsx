import React from 'react';

export default function MetricCard({ title, value, subtitle, icon: Icon, badgeText, badgeColor = 'emerald' }) {
  const getBadgeClass = (color) => {
    switch (color) {
      case 'emerald': return 'badge-emerald';
      case 'blue': return 'badge-blue';
      case 'amber': return 'badge-amber';
      case 'purple': return 'badge-purple';
      case 'rose': return 'badge-rose';
      default: return 'badge-blue';
    }
  };

  return (
    <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: '0.85rem', color: '#94a3b8', fontWeight: '500' }}>{title}</span>
        {Icon && (
          <div style={{
            padding: '0.5rem',
            borderRadius: '8px',
            backgroundColor: 'rgba(255, 255, 255, 0.05)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Icon size={18} color="#94a3b8" />
          </div>
        )}
      </div>

      <div style={{ fontSize: '1.85rem', fontWeight: '700', color: '#fff', letterSpacing: '-0.02em' }}>
        {value}
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8rem', color: '#64748b' }}>
        {badgeText && (
          <span className={`badge ${getBadgeClass(badgeColor)}`}>
            {badgeText}
          </span>
        )}
        <span>{subtitle}</span>
      </div>
    </div>
  );
}
